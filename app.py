from flask import Flask, request, jsonify, send_from_directory
from db import get_db, init_schema
from store import (
    list_docs, get_doc, create_doc, delete_doc,
    list_notes, create_note, delete_note,
)
from render import render_markdown

def _derive_title(content):
    """Title is optional: fall back to the first non-empty line of the markdown
    (stripped of leading #), else 'Untitled'."""
    for line in (content or "").splitlines():
        s = line.strip().lstrip("#").strip()
        if s:
            return s[:80]
    return "Untitled"

def create_app(db_path=":memory:"):
    app = Flask(__name__, static_folder="static")
    conn = get_db(db_path)
    init_schema(conn)
    app.config["CONN"] = conn

    def db():
        return app.config["CONN"]

    @app.route("/")
    def index():
        return send_from_directory("static", "index.html")

    @app.route("/doc/<int:doc_id>")
    def doc_page(doc_id):
        return send_from_directory("static", "doc.html")

    @app.route("/api/docs", methods=["GET"])
    def api_list_docs():
        return jsonify(list_docs(db()))

    @app.route("/api/docs", methods=["POST"])
    def api_create_doc():
        data = request.get_json(silent=True) or {}
        content = data.get("content") or ""
        title = (data.get("title") or "").strip() or _derive_title(content)
        author = (data.get("author") or "").strip() or "anonymous"
        try:
            doc = create_doc(db(), title, content, author)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(doc), 201

    @app.route("/api/docs/<int:doc_id>", methods=["GET"])
    def api_get_doc(doc_id):
        doc = get_doc(db(), doc_id)
        if not doc:
            return jsonify({"error": "Document not found"}), 404
        doc["html"] = render_markdown(doc["content"])
        return jsonify(doc)

    @app.route("/api/docs/<int:doc_id>", methods=["DELETE"])
    def api_delete_doc(doc_id):
        if delete_doc(db(), doc_id):
            return "", 204
        return jsonify({"error": "Document not found"}), 404

    @app.route("/api/docs/<int:doc_id>/notes", methods=["GET"])
    def api_list_notes(doc_id):
        return jsonify(list_notes(db(), doc_id))

    @app.route("/api/docs/<int:doc_id>/notes", methods=["POST"])
    def api_create_note(doc_id):
        data = request.get_json(silent=True) or {}
        author = (data.get("author") or "").strip() or "anonymous"
        try:
            note = create_note(db(), doc_id, data.get("quote") or "",
                               data.get("note") or "", author,
                               int(data.get("start_pos", 0)),
                               int(data.get("end_pos", 0)))
        except (ValueError, TypeError) as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(note), 201

    @app.route("/api/notes/<int:note_id>", methods=["DELETE"])
    def api_delete_note(note_id):
        if delete_note(db(), note_id):
            return "", 204
        return jsonify({"error": "Note not found"}), 404

    return app

if __name__ == "__main__":
    create_app("mdboard.db").run(host="0.0.0.0", port=8000)
