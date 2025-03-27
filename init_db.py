import sqlite3

def create_tables():
    con = sqlite3.connect("database.db")
    cur = con.cursor()

    # Luo users-taulu
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash TEXT
    );
    """)

    # Luo sets-taulu, ilman is_ready
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sets (
        id INTEGER PRIMARY KEY,
        title TEXT,
        description TEXT,
        user_id INTEGER REFERENCES users,
        created_at TEXT
    );
    """)

    # Luo questions-taulu (3 vastausvaihtoehtoa)
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

    con.commit()
    con.close()
    print("Taulut luotu (tai olivat jo olemassa).")

if __name__ == "__main__":
    create_tables()
