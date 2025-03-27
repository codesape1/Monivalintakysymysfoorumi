import sqlite3

def get_connection():
    con = sqlite3.connect("database.db")
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con

def execute(sql, params=[]):
    con = get_connection()
    res = con.execute(sql, params)
    con.commit()
    last_id = res.lastrowid
    con.close()
    return last_id

def query(sql, params=[]):
    con = get_connection()
    rows = con.execute(sql, params).fetchall()
    con.close()
    return rows
