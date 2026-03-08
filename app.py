import sqlite3
import uuid
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Always set the database file path correctly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'vn_game.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

# --- API 1: Start the game ---
@app.route('/api/start', methods=['POST'])
def start_game():
    session_id = str(uuid.uuid4())
    conn = get_db_connection()
    conn.execute('INSERT INTO game_sessions (id, current_dialogue_id) VALUES (?, ?)', (session_id, 1))
    conn.commit()
    conn.close()
    return jsonify({'session_id': session_id})

# --- API 2: Get the current scene ---
@app.route('/api/state/<session_id>', methods=['GET'])
def get_state(session_id):
    conn = get_db_connection()
    
    session = conn.execute('SELECT * FROM game_sessions WHERE id = ?', (session_id,)).fetchone()
    if not session:
        return jsonify({'error': 'Session not found'}), 404
        
    current_id = session['current_dialogue_id']
    

# Fetch dialogue data + background image (bg_image) from the scenes table
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
    
    choices = conn.execute('SELECT * FROM choices WHERE parent_dialogue_id = ?', (dialogue['id'],)).fetchall()
    
    scene = conn.execute('SELECT * FROM scenes WHERE id = ?', (dialogue['scene_id'],)).fetchone()
    
    conn.close()
    return jsonify({
            'dialogue': dict(dialogue),
            'scene': dict(scene) if scene else None, 
            'choices': [dict(c) for c in choices]
            })

# --- API 3: Select a choice ---
@app.route('/api/choose', methods=['POST'])
def choose_action():
    data = request.json
    session_id = data.get('session_id')
    choice_id = data.get('choice_id')

    conn = get_db_connection()
    
    # 1. Get the choice data to check the score and the next scene
    choice = conn.execute("SELECT * FROM choices WHERE id=?", (choice_id,)).fetchone()
    if not choice:
        return jsonify({'error': 'Invalid choice'}), 400

    # 2. Update the score
    conn.execute("UPDATE game_sessions SET total_score = total_score + ? WHERE id=?", 
                 (choice['score_impact'], session_id))
    
    conn.execute("INSERT INTO choice_history (session_id, choice_id) VALUES (?, ?)", 
                 (session_id, choice_id))

    # 3. Determine the next scene (including checking for an ending)
    next_id = calculate_next_scene(conn, session_id, choice['next_dialogue_id'])

    # 4. Update the player status
    conn.execute("UPDATE game_sessions SET current_dialogue_id=? WHERE id=?", (next_id, session_id))
    
    
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

# --- API 4: Next Button ---
@app.route('/api/next', methods=['POST'])
def next_dialogue():
    data = request.json
    session_id = data.get('session_id')

    conn = get_db_connection()
    
   # 1. Find the current scene and determine the number of the next scene
    session = conn.execute("SELECT current_dialogue_id FROM game_sessions WHERE id=?", (session_id,)).fetchone()
    current_id = session['current_dialogue_id']
    
    dialogue = conn.execute("SELECT next_dialogue_id FROM dialogues WHERE id=?", (current_id,)).fetchone()
    
    if not dialogue or dialogue['next_dialogue_id'] is None:
        conn.close()
        return jsonify({'status': 'end'}) # The game has ended. There is no next scene.

    # 2. Determine the next scene (including checking for an ending)
    next_id = calculate_next_scene(conn, session_id, dialogue['next_dialogue_id'])
    
    # 3. Update the player status
    conn.execute("UPDATE game_sessions SET current_dialogue_id=? WHERE id=?", (next_id, session_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

# Helper function to determine the ending (reusable)
def calculate_next_scene(conn, session_id, target_next_id):
    if target_next_id == 999: # Ending check code
        score_row = conn.execute("SELECT total_score FROM game_sessions WHERE id=?", (session_id,)).fetchone()
        score = score_row['total_score']
        
        # Score criteria
        if score >= 22: return 100  # Good End
        elif score >= 12: return 101 # Normal End
        else: return 102            # Bad End
        
    return target_next_id

# --- API 5: View statistics (ending) ---
@app.route('/api/stats/<session_id>', methods=['GET'])
def get_stats(session_id):
    conn = get_db_connection()
    window_query = """
    SELECT 
        ROW_NUMBER() OVER (ORDER BY h.timestamp) as turn_number,
        c.text_label, c.score_impact
    FROM choice_history h
    JOIN choices c ON h.choice_id = c.id
    WHERE h.session_id = ?
    """
    history = conn.execute(window_query, (session_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in history])

if __name__ == '__main__':
    app.run(debug=True)