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


def test_optional_title_derived_from_heading(client):
    r = client.post("/api/docs", json={"content": "# Hello World\n\nbody", "author": "e"})
    assert r.status_code == 201 and r.json["title"] == "Hello World"

def test_optional_title_from_first_line(client):
    r = client.post("/api/docs", json={"content": "plain first line\nsecond", "author": "e"})
    assert r.status_code == 201 and r.json["title"] == "plain first line"

def test_optional_title_untitled_when_no_text(client):
    r = client.post("/api/docs", json={"content": "# ", "author": "e"})
    assert r.status_code == 201 and r.json["title"] == "Untitled"


# ---- mermaid chart rendering ----

MERMAID_PIE = '```mermaid\npie showData\n    title T\n    "A" : 3\n```'

def test_mermaid_block_renders_as_div(client):
    doc_id = _mk(client, content="# Charts\n\n" + MERMAID_PIE + "\n\ntail").json["id"]
    html = client.get(f"/api/docs/{doc_id}").json["html"]
    assert '<div class="mermaid">pie showData' in html
    assert "&quot;A&quot; : 3" in html           # source kept for client-side rendering
    assert "codehilite" not in html         # not rendered as a code block
    assert "<h1" in html and "tail" in html  # rest of the doc unaffected

def test_mermaid_source_is_html_escaped(client):
    content = '```mermaid\nflowchart TB\n    A["<&>"] --> B\n```'
    doc_id = _mk(client, content=content).json["id"]
    html = client.get(f"/api/docs/{doc_id}").json["html"]
    assert 'A[&quot;&lt;&amp;&gt;&quot;]' in html  # nothing raw reaches the page
    assert "--> B" not in html

def test_multiple_mermaid_blocks_keep_order(client):
    content = ("intro\n\n```mermaid\npie\n    \"one\" : 1\n```\n\n"
               "mid\n\n```mermaid\npie\n    \"two\" : 2\n```\n")
    doc_id = _mk(client, content=content).json["id"]
    html = client.get(f"/api/docs/{doc_id}").json["html"]
    assert html.count('<div class="mermaid">') == 2
    assert html.index("&quot;one&quot;") < html.index("&quot;two&quot;")
    assert "intro" in html and "mid" in html

def test_normal_code_block_still_codehilite(client):
    doc_id = _mk(client, content="```python\nx = 1\n```").json["id"]
    html = client.get(f"/api/docs/{doc_id}").json["html"]
    assert '<div class="codehilite">' in html
    assert '<div class="mermaid">' not in html

def test_mermaid_token_literal_not_swallowed(client):
    # a user literally typing the internal placeholder must not become a chart
    doc_id = _mk(client, content="MDBoardMermaidToken0").json["id"]
    html = client.get(f"/api/docs/{doc_id}").json["html"]
    assert "<p>MDBoardMermaidToken0</p>" in html
    assert '<div class="mermaid">' not in html
