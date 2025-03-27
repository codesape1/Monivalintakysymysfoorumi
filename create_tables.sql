-- create_tables.sql
-- Ei saraketta is_ready
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE IF NOT EXISTS sets (
    id INTEGER PRIMARY KEY,
    title TEXT,
    description TEXT,
    user_id INTEGER REFERENCES users,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY,
    set_id INTEGER REFERENCES sets,
    question_text TEXT,
    answer1 TEXT,
    answer2 TEXT,
    answer3 TEXT,
    correct_answer INTEGER
);
