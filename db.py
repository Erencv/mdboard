import sqlite3
from datetime import datetime

def get_db(path):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_schema(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER NOT NULL,
            quote TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            author TEXT NOT NULL,
            start_pos INTEGER NOT NULL,
            end_pos INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    ''')
    conn.commit()

def init_db(path):
    conn = get_db(path)
    init_schema(conn)
    conn.close()
