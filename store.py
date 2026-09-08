import sqlite3
from sqlite3 import Row

def list_docs(conn):
    conn.row_factory = Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author, created_at FROM docs ORDER BY id DESC")
    return [dict(row) for row in cursor.fetchall()]

def get_doc(conn, doc_id):
    conn.row_factory = Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, author, created_at FROM docs WHERE id=?", (doc_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def create_doc(conn, title, content, author):
    if not content:
        raise ValueError("Content cannot be empty")
    conn.row_factory = Row
    cursor = conn.cursor()
    cursor.execute("INSERT INTO docs (title, content, author) VALUES (?, ?, ?)", (title, content, author))
    conn.commit()
    cursor.execute("SELECT id, title, content, author, created_at FROM docs WHERE id=?", (cursor.lastrowid,))
    return dict(cursor.fetchone())

def delete_doc(conn, doc_id):
    conn.row_factory = Row
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE doc_id=?", (doc_id,))
    cursor.execute("DELETE FROM docs WHERE id=?", (doc_id,))
    conn.commit()
    return cursor.rowcount > 0

def list_notes(conn, doc_id):
    conn.row_factory = Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, doc_id, quote, note, author, start_pos, end_pos, created_at FROM notes WHERE doc_id=? ORDER BY start_pos", (doc_id,))
    return [dict(row) for row in cursor.fetchall()]

def create_note(conn, doc_id, quote, note, author, start_pos, end_pos):
    if not quote:
        raise ValueError("Quote cannot be empty")
    conn.row_factory = Row
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (doc_id, quote, note, author, start_pos, end_pos) VALUES (?, ?, ?, ?, ?, ?)", (doc_id, quote, note, author, start_pos, end_pos))
    conn.commit()
    cursor.execute("SELECT id, doc_id, quote, note, author, start_pos, end_pos, created_at FROM notes WHERE id=?", (cursor.lastrowid,))
    return dict(cursor.fetchone())

def delete_note(conn, note_id):
    conn.row_factory = Row
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    return cursor.rowcount > 0
