-- create_tables.sql

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS sets (
    id INTEGER PRIMARY KEY,
    title TEXT,
    description TEXT,
    user_id INTEGER REFERENCES users,
    category_id INTEGER REFERENCES categories,
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

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY,
    set_id INTEGER REFERENCES sets,
    user_id INTEGER REFERENCES users,
    comment_text TEXT,
    created_at TEXT
);
