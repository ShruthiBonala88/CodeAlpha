import pytest
import app as app_module


@pytest.fixture
def client(tmp_path):
    app_module.app.config.update(TESTING=True, DATABASE=str(tmp_path / "test.db"))
    app_module.init_db()
    return app_module.app.test_client()


def test_shorten_and_redirect(client):
    r = client.post("/api/shorten", json={"url": "https://example.com/long/path"})
    assert r.status_code == 201
    code = r.get_json()["short_code"]
    assert len(code) == 6
    r = client.get("/" + code)
    assert r.status_code == 302
    assert r.headers["Location"] == "https://example.com/long/path"
    assert client.get("/api/urls/" + code).get_json()["clicks"] == 1


def test_same_url_returns_same_code(client):
    a = client.post("/api/shorten", json={"url": "https://example.com"}).get_json()
    b = client.post("/api/shorten", json={"url": "https://example.com"})
    assert b.status_code == 200 and b.get_json()["short_code"] == a["short_code"]


def test_custom_code_and_conflict(client):
    assert client.post("/api/shorten", json={"url": "https://a.com", "custom_code": "mine"}).status_code == 201
    assert client.post("/api/shorten", json={"url": "https://b.com", "custom_code": "mine"}).status_code == 409


@pytest.mark.parametrize("bad", ["", "not a url", "ftp://x.com", "javascript:alert(1)"])
def test_invalid_urls(client, bad):
    assert client.post("/api/shorten", json={"url": bad}).status_code == 400


def test_unknown_code_404(client):
    assert client.get("/nope123").status_code == 404
    assert client.get("/api/urls/nope123").status_code == 404
