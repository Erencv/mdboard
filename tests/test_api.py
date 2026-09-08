import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app(":memory:")
    with app.test_client() as c:
        yield c

def _mk(client, title="Notes", content="# Hi\n\nsome **text**", author="eren"):
    return client.post("/api/docs", json={"title": title, "content": content, "author": author})

def test_docs_empty_initially(client):
    r = client.get("/api/docs")
    assert r.status_code == 200 and r.json == []

def test_create_doc(client):
    r = _mk(client)
    assert r.status_code == 201
    assert r.json["id"] and r.json["title"] == "Notes" and r.json["author"] == "eren"

def test_create_doc_empty_content_400(client):
    r = client.post("/api/docs", json={"title": "x", "content": "", "author": "eren"})
    assert r.status_code == 400

def test_list_omits_content(client):
    _mk(client)
    r = client.get("/api/docs")
    assert len(r.json) == 1
    assert "content" not in r.json[0]
    assert r.json[0]["title"] == "Notes"

def test_get_doc_renders_html(client):
    doc_id = _mk(client).json["id"]
    r = client.get(f"/api/docs/{doc_id}")
    assert r.status_code == 200
    assert r.json["content"].startswith("# Hi")
    assert "<h1" in r.json["html"] and "<strong>" in r.json["html"]

def test_get_missing_doc_404(client):
    assert client.get("/api/docs/999").status_code == 404

def test_delete_doc(client):
    doc_id = _mk(client).json["id"]
    assert client.delete(f"/api/docs/{doc_id}").status_code == 204
    assert client.get(f"/api/docs/{doc_id}").status_code == 404

def test_delete_missing_doc_404(client):
    assert client.delete("/api/docs/999").status_code == 404

def test_notes_crud(client):
    doc_id = _mk(client).json["id"]
    assert client.get(f"/api/docs/{doc_id}/notes").json == []
    r = client.post(f"/api/docs/{doc_id}/notes",
                    json={"quote": "text", "note": "important", "author": "eren",
                          "start_pos": 5, "end_pos": 9})
    assert r.status_code == 201 and r.json["note"] == "important"
    note_id = r.json["id"]
    notes = client.get(f"/api/docs/{doc_id}/notes").json
    assert len(notes) == 1 and notes[0]["quote"] == "text"
    assert client.delete(f"/api/notes/{note_id}").status_code == 204
    assert client.get(f"/api/docs/{doc_id}/notes").json == []

def test_note_empty_quote_400(client):
    doc_id = _mk(client).json["id"]
    r = client.post(f"/api/docs/{doc_id}/notes",
                    json={"quote": "", "note": "x", "author": "e", "start_pos": 0, "end_pos": 0})
    assert r.status_code == 400
