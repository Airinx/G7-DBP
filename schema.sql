DROP TABLE IF EXISTS choice_history;
DROP TABLE IF EXISTS game_sessions;
DROP TABLE IF EXISTS choices;
DROP TABLE IF EXISTS dialogues;
DROP TABLE IF EXISTS scenes;
DROP TABLE IF EXISTS expressions;
DROP TABLE IF EXISTS characters;

CREATE TABLE characters (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    color_code TEXT
);

CREATE TABLE expressions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    css_class TEXT NOT NULL
);

CREATE TABLE scenes (
    id INTEGER PRIMARY KEY,
    day INTEGER,
    location_name TEXT,
    bg_image TEXT
);

CREATE TABLE dialogues (
    id INTEGER PRIMARY KEY,
    scene_id INTEGER,
    character_id INTEGER,
    expression_id INTEGER,
    text_content TEXT NOT NULL,
    next_dialogue_id INTEGER,
    FOREIGN KEY(scene_id) REFERENCES scenes(id),
    FOREIGN KEY(character_id) REFERENCES characters(id),
    FOREIGN KEY(expression_id) REFERENCES expressions(id)
);

CREATE TABLE choices (
    id INTEGER PRIMARY KEY,
    parent_dialogue_id INTEGER,
    text_label TEXT NOT NULL,
    score_impact INTEGER DEFAULT 0,
    next_dialogue_id INTEGER,
    FOREIGN KEY(parent_dialogue_id) REFERENCES dialogues(id)
);

CREATE TABLE game_sessions (
    id TEXT PRIMARY KEY,
    current_dialogue_id INTEGER,
    total_score INTEGER DEFAULT 0,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE choice_history (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    choice_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(session_id) REFERENCES game_sessions(id),
    FOREIGN KEY(choice_id) REFERENCES choices(id)
);