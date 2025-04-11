import sqlite3

def create_tables():
    con = sqlite3.connect("database.db")
    cur = con.cursor()

    # 1. Luo users-taulu
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash TEXT
    );
    """)

    # 2. Luo categories-taulu
    cur.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE
    );
    """)

    # Lisää muutama esimerkkikategoria
    categories = [("Urheilu",), ("Historia",), ("Tiede",)]
    cur.executemany("""
    INSERT OR IGNORE INTO categories (name) VALUES (?)
    """, categories)

    # 3. Luo sets-taulu, jossa on category_id-sarake
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sets (
        id INTEGER PRIMARY KEY,
        title TEXT,
        description TEXT,
        user_id INTEGER REFERENCES users,
        category_id INTEGER REFERENCES categories,
        created_at TEXT
    );
    """)

    # 4. Luo questions-taulu
    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY,
        set_id INTEGER REFERENCES sets,
        question_text TEXT,
        answer1 TEXT,
        answer2 TEXT,
        answer3 TEXT,
        correct_answer INTEGER
    );
    """)

    # 5. Luo comments-taulu
    cur.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY,
        set_id INTEGER REFERENCES sets,
        user_id INTEGER REFERENCES users,
        comment_text TEXT,
        created_at TEXT
    );
    """)

    con.commit()
    con.close()
    print("Taulut luotu (tai olivat jo olemassa).")

if __name__ == "__main__":
    create_tables()
