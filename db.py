import sqlite3


def get_connection():
    con = sqlite3.connect("database.db")
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con


def execute(sql, params=None):
    if params is None:
        params = []
    con = get_connection()
    try:
        res = con.execute(sql, params)
        con.commit()
        return res.lastrowid
    except Exception:
        con.rollback()             # vapauttaa lukon virhetilanteessa
        raise
    finally:
        con.close()


def query(sql, params=None):
    if params is None:
        params = []
    con = get_connection()
    try:
        return con.execute(sql, params).fetchall()
    finally:
        con.close()
