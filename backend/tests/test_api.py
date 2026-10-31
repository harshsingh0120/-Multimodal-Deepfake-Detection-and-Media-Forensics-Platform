"""API integration tests via FastAPI TestClient (F1, F10, N7)."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "engine" in body


def test_config():
    r = client.get("/api/config")
    assert r.status_code == 200
    assert ".png" in r.json()["image_ext"]


def _post(path, content_type):
    with open(path, "rb") as f:
        return client.post("/api/analyze",
                           files={"file": (path.name, f, content_type)})


def test_analyze_image_and_report(samples):
    r = _post(samples["suspect_image"], "image/png")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["media"]["media_type"] == "image"
    assert any(m["modality"] == "image" and m["available"] for m in data["modalities"])
    assert 0.0 <= data["fusion"]["overall_score"] <= 1.0
    assert "potential" in data["safety_notice"].lower()

    # Download the PDF report.
    rep = client.get(data["report_url"])
    assert rep.status_code == 200
    assert rep.headers["content-type"] == "application/pdf"
    assert rep.content[:4] == b"%PDF"


def test_analyze_audio(samples):
    r = _post(samples["suspect_audio"], "audio/wav")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["media"]["media_type"] == "audio"
    assert any(m["modality"] == "audio" and m["available"] for m in data["modalities"])


def test_reject_unsupported_type(tmp_path):
    bad = tmp_path / "notes.txt"
    bad.write_text("hello")
    with open(bad, "rb") as f:
        r = client.post("/api/analyze", files={"file": ("notes.txt", f, "text/plain")})
    assert r.status_code == 415


def test_reject_empty_file(tmp_path):
    empty = tmp_path / "empty.png"
    empty.write_bytes(b"")
    with open(empty, "rb") as f:
        r = client.post("/api/analyze", files={"file": ("empty.png", f, "image/png")})
    assert r.status_code in (400, 422)


def test_report_not_found():
    r = client.get("/api/report/deadbeefdead")
    assert r.status_code == 404
