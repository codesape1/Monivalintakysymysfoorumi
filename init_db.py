import sqlite3

def create_tables():
    con = sqlite3.connect("database.db")
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    # ----- users -----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash TEXT
    );
    """)

    # ----- categories -----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE
    );
    """)
    cur.executemany(
        "INSERT OR IGNORE INTO categories (name) VALUES (?)",
        [("Urheilu",), ("Historia",), ("Tiede",)]
    )

    # ----- sets -----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sets (
        id INTEGER PRIMARY KEY,
        title TEXT,
        description TEXT,
        user_id INTEGER REFERENCES users,
        category_id INTEGER REFERENCES categories,
        created_at TEXT,
        published INTEGER DEFAULT 0
    );
    """)

    # ----- questions -----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY,
        set_id INTEGER REFERENCES sets(id) ON DELETE CASCADE,
        question_text TEXT,
        answer1 TEXT,
        answer2 TEXT,
        answer3 TEXT,
        correct_answer INTEGER
    );
    """)

    # ----- comments -----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY,
        set_id INTEGER REFERENCES sets(id) ON DELETE CASCADE,
        user_id INTEGER REFERENCES users,
        comment_text TEXT,
        created_at TEXT
    );
    """)

    con.commit()
    con.close()
    print("Taulut luotu / päivitetty.")

if __name__ == "__main__":
    create_tables()
