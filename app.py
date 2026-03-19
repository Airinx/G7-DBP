import sqlite3
import uuid
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- Database setup ---
# get absolute path to avoid path issues when running from different locations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'vn_game.db')


def get_db_connection():
    """
    Create and return a database connection.
    Uses Row factory so we can access columns like a dictionary.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    """
    Render the main page (frontend entry point).
    """
    return render_template('index.html')


# --- API 1: Start the game ---
@app.route('/api/start', methods=['POST'])
def start_game():
    """
    Initialize a new game session.

    - generate unique session_id
    - set starting dialogue (id = 1)
    - store session in database
    """
    session_id = str(uuid.uuid4())

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO game_sessions (id, current_dialogue_id) VALUES (?, ?)',
        (session_id, 1)
    )
    conn.commit()
    conn.close()

    return jsonify({'session_id': session_id})


# --- API 2: Get the current scene ---
@app.route('/api/state/<session_id>', methods=['GET'])
def get_state(session_id):
    """
    Return current game state for a session:
    - dialogue data (text, character, image, etc.)
    - scene data (background, day)
    - available choices
    """
    conn = get_db_connection()
    
    session = conn.execute(
        'SELECT * FROM game_sessions WHERE id = ?', 
        (session_id,)
    ).fetchone()

    if not session:
        return jsonify({'error': 'Session not found'}), 404
        
    current_id = session['current_dialogue_id']
    

    # fetch dialogue + related data (character, expression, scene)
    dialogue_query = """
        SELECT 
            d.id,
            d.text_content,
            d.next_dialogue_id,
            d.scene_id,
            s.bg_image,
            s.day,
            c.name as char_name,
            c.color_code,
            e.css_class as char_image_file
        FROM dialogues d
        LEFT JOIN characters c ON d.character_id = c.id
        LEFT JOIN expressions e ON d.expression_id = e.id
        LEFT JOIN scenes s ON d.scene_id = s.id
        WHERE d.id = ?
    """
    dialogue = conn.execute(dialogue_query, (current_id,)).fetchone()
    
    # fetch choices for this dialogue
    choices = conn.execute(
        'SELECT * FROM choices WHERE parent_dialogue_id = ?', 
        (dialogue['id'],)
    ).fetchall()
    
    # fetch scene separately (used for day logic)
    scene = conn.execute(
        'SELECT * FROM scenes WHERE id = ?', 
        (dialogue['scene_id'],)
    ).fetchone()
    
    conn.close()

    return jsonify({
        'dialogue': dict(dialogue),
        'scene': dict(scene) if scene else None,
        'choices': [dict(c) for c in choices]
    })


# --- API 3: Select a choice ---
@app.route('/api/choose', methods=['POST'])
def choose_action():
    """
    Handle player choice:
    - update score
    - save choice history
    - determine next dialogue (including ending logic)
    """
    data = request.json
    session_id = data.get('session_id')
    choice_id = data.get('choice_id')

    conn = get_db_connection()
    
    # get selected choice
    choice = conn.execute(
        "SELECT * FROM choices WHERE id=?", 
        (choice_id,)
    ).fetchone()

    if not choice:
        return jsonify({'error': 'Invalid choice'}), 400

    # update total score
    conn.execute(
        "UPDATE game_sessions SET total_score = total_score + ? WHERE id=?", 
        (choice['score_impact'], session_id)
    )
    
    # save history
    conn.execute(
        "INSERT INTO choice_history (session_id, choice_id) VALUES (?, ?)", 
        (session_id, choice_id)
    )

    # determine next dialogue (may redirect to ending)
    next_id = calculate_next_scene(conn, session_id, choice['next_dialogue_id'])

    # update session state
    conn.execute(
        "UPDATE game_sessions SET current_dialogue_id=? WHERE id=?", 
        (next_id, session_id)
    )
    
    conn.commit()
    conn.close()

    return jsonify({'status': 'ok'})


# --- API 4: Next button ---
@app.route('/api/next', methods=['POST'])
def next_dialogue():
    """
    Move to the next dialogue (no choice case).

    - find current dialogue
    - follow next_dialogue_id
    - apply ending logic if needed
    """
    data = request.json
    session_id = data.get('session_id')

    conn = get_db_connection()
    
    # get current dialogue id
    session = conn.execute(
        "SELECT current_dialogue_id FROM game_sessions WHERE id=?", 
        (session_id,)
    ).fetchone()

    current_id = session['current_dialogue_id']
    
    dialogue = conn.execute(
        "SELECT next_dialogue_id FROM dialogues WHERE id=?", 
        (current_id,)
    ).fetchone()
    
    # if no next → game ended
    if not dialogue or dialogue['next_dialogue_id'] is None:
        conn.close()
        return jsonify({'status': 'end'})

    # calculate next scene (handle endings)
    next_id = calculate_next_scene(conn, session_id, dialogue['next_dialogue_id'])
    
    # update session
    conn.execute(
        "UPDATE game_sessions SET current_dialogue_id=? WHERE id=?", 
        (next_id, session_id)
    )

    conn.commit()
    conn.close()

    return jsonify({'status': 'ok'})


def calculate_next_scene(conn, session_id, target_next_id):
    """
    Helper function to determine next dialogue.

    Special case:
    - if target_next_id == 999 → this is an ending checkpoint
    - decide ending based on player's total score
    """
    if target_next_id == 999:
        score_row = conn.execute(
            "SELECT total_score FROM game_sessions WHERE id=?", 
            (session_id,)
        ).fetchone()

        score = score_row['total_score']
        
        # simple score-based branching
        if score >= 22:
            return 100  # Good Ending
        elif score >= 12:
            return 101  # Normal Ending
        else:
            return 102  # Bad Ending
        
    return target_next_id


# --- API 5: Player stats ---
@app.route('/api/stats/<session_id>', methods=['GET'])
def get_stats(session_id):
    """
    Return player's choice history:
    - turn order
    - selected choice
    - score impact
    """
    conn = get_db_connection()

    window_query = """
        SELECT 
            ROW_NUMBER() OVER (ORDER BY h.timestamp) as turn_number,
            c.text_label, 
            c.score_impact
        FROM choice_history h
        JOIN choices c ON h.choice_id = c.id
        WHERE h.session_id = ?
    """

    history = conn.execute(window_query, (session_id,)).fetchall()
    conn.close()

    return jsonify([dict(row) for row in history])


# --- API 6: What-if (parallel world) ---
@app.route('/api/what_if/<session_id>', methods=['GET'])
def get_what_if(session_id):
    """
    Generate an alternative timeline based on the last unchosen option.

    Logic:
    - find latest choice
    - pick the unselected option from the same decision point
    - simulate next few steps (limited depth)
    """
    conn = get_db_connection()
    
    recursive_query = """
    WITH RECURSIVE 
    LatestChoice AS (
        SELECT choice_id 
        FROM choice_history  
        WHERE session_id = ? 
        ORDER BY timestamp DESC, id DESC
        LIMIT 1
    ),
    WhatIf AS (
        SELECT 
            unpicked.text_label AS missed_choice,
            d.id,
            d.text_content,
            d.next_dialogue_id,
            d.scene_id,  
            1 AS step
        FROM LatestChoice lc
        JOIN choices picked ON lc.choice_id = picked.id
        JOIN choices unpicked 
            ON picked.parent_dialogue_id = unpicked.parent_dialogue_id 
            AND unpicked.id != picked.id
        JOIN dialogues d ON unpicked.next_dialogue_id = d.id
        
        UNION ALL
        
        SELECT 
            w.missed_choice,
            d.id,
            d.text_content,
            d.next_dialogue_id,
            d.scene_id,  
            w.step + 1
        FROM dialogues d
        JOIN WhatIf w ON d.id = w.next_dialogue_id
        WHERE w.step < 3 
          AND d.next_dialogue_id IS NOT NULL 
          AND d.scene_id = w.scene_id
    )
    SELECT missed_choice, step, text_content FROM WhatIf;
    """

    what_if_data = conn.execute(recursive_query, (session_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in what_if_data])


# --- Run app ---
if __name__ == '__main__':
    # debug=True → auto reload + show errors (for development)
    app.run(debug=True)