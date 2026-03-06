import sqlite3
import uuid
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ตั้งค่าตำแหน่งไฟล์ Database ให้ถูกต้องเสมอ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'vn_game.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

# --- API 1: เริ่มเกม ---
@app.route('/api/start', methods=['POST'])
def start_game():
    session_id = str(uuid.uuid4())
    conn = get_db_connection()
    # เริ่มต้นที่ Dialogue ID 1
    conn.execute('INSERT INTO game_sessions (id, current_dialogue_id) VALUES (?, ?)', (session_id, 1))
    conn.commit()
    conn.close()
    return jsonify({'session_id': session_id})

# --- API 2: ดึงฉากปัจจุบัน ---
@app.route('/api/state/<session_id>', methods=['GET'])
def get_state(session_id):
    conn = get_db_connection()
    
    session = conn.execute('SELECT * FROM game_sessions WHERE id = ?', (session_id,)).fetchone()
    if not session:
        return jsonify({'error': 'Session not found'}), 404
        
    current_id = session['current_dialogue_id']
    

    # ดึงข้อมูลบทพูด + รูปพื้นหลัง (bg_image) จากตาราง scenes
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
            'scene': dict(scene) if scene else None, # คืนค่าข้อมูลฉากไปด้วย
            'choices': [dict(c) for c in choices]
            })

# --- API 3: เลือกช้อยส์ (Choice) ---
@app.route('/api/choose', methods=['POST'])
def choose_action():
    data = request.json
    session_id = data.get('session_id')
    choice_id = data.get('choice_id')

    conn = get_db_connection()
    
    # 1. ดึงข้อมูลช้อยส์เพื่อดูคะแนนและฉากถัดไป
    choice = conn.execute("SELECT * FROM choices WHERE id=?", (choice_id,)).fetchone()
    if not choice:
        return jsonify({'error': 'Invalid choice'}), 400

    # 2. อัปเดตคะแนน
    conn.execute("UPDATE game_sessions SET total_score = total_score + ? WHERE id=?", 
                 (choice['score_impact'], session_id))
    
    conn.execute("INSERT INTO choice_history (session_id, choice_id) VALUES (?, ?)", 
                 (session_id, choice_id))

    # 3. คำนวณฉากถัดไป (รวมถึงเช็คฉากจบ)
    next_id = calculate_next_scene(conn, session_id, choice['next_dialogue_id'])

    # 4. อัปเดตสถานะผู้เล่น
    conn.execute("UPDATE game_sessions SET current_dialogue_id=? WHERE id=?", (next_id, session_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

# --- API 4: กดถัดไป (Next Button) ---
@app.route('/api/next', methods=['POST'])
def next_dialogue():
    data = request.json
    session_id = data.get('session_id')

    conn = get_db_connection()
    
    # 1. หาว่าฉากปัจจุบันคืออะไร และฉากถัดไปคือเลขอะไร
    session = conn.execute("SELECT current_dialogue_id FROM game_sessions WHERE id=?", (session_id,)).fetchone()
    current_id = session['current_dialogue_id']
    
    dialogue = conn.execute("SELECT next_dialogue_id FROM dialogues WHERE id=?", (current_id,)).fetchone()
    
    if not dialogue or dialogue['next_dialogue_id'] is None:
        conn.close()
        return jsonify({'status': 'end'}) # จบเกมแล้ว ไม่มีให้ไปต่อ

    # 2. คำนวณฉากถัดไป (รวมถึงเช็คฉากจบ)
    next_id = calculate_next_scene(conn, session_id, dialogue['next_dialogue_id'])
    
    # 3. อัปเดตสถานะผู้เล่น
    conn.execute("UPDATE game_sessions SET current_dialogue_id=? WHERE id=?", (next_id, session_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

# ฟังก์ชันช่วยคำนวณฉากจบ (ใช้ซ้ำได้)
def calculate_next_scene(conn, session_id, target_next_id):
    if target_next_id == 999: # รหัสตรวจสอบฉากจบ
        score_row = conn.execute("SELECT total_score FROM game_sessions WHERE id=?", (session_id,)).fetchone()
        score = score_row['total_score']
        
        # เกณฑ์คะแนน
        if score >= 22: return 100  # Good End
        elif score >= 12: return 101 # Normal End
        else: return 102            # Bad End
        
    return target_next_id

# --- API 5: ดูสถิติ (ตอนจบ) ---
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