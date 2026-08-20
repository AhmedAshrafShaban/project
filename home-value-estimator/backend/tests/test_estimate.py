import pytest

from app import create_app

VALID_PAYLOAD = {
    "neighborhood": "Brookhaven",
    "sqft_living": 1800,
    "lot_size_sqft": 5200,
    "bedrooms": 3,
    "bathrooms": 2,
    "floors": 2,
    "year_built": 2005,
    "renovated": "N",
    "condition": 4,
    "grade": 7,
    "garage": "Y",
    "basement": "N",
    "pool": "N",
    "school_score": 7,
}


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True


def test_estimate_happy_path(client):
    resp = client.post("/api/estimate", json=VALID_PAYLOAD)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["estimated_value"] > 0
    assert body["range_low"] < body["estimated_value"] < body["range_high"]
    assert body["neighborhood_used"] == "Brookhaven"
    assert len(body["top_factors"]) > 0


def test_estimate_unknown_neighborhood_buckets_to_other(client):
    payload = dict(VALID_PAYLOAD, neighborhood="Nowhere Estates")
    resp = client.post("/api/estimate", json=payload)
    assert resp.status_code == 200
    assert resp.get_json()["neighborhood_used"] == "other"


def test_estimate_missing_field(client):
    payload = dict(VALID_PAYLOAD)
    del payload["sqft_living"]
    resp = client.post("/api/estimate", json=payload)
    assert resp.status_code == 422
    assert "sqft_living" in resp.get_json()["fields"]


def test_estimate_out_of_range_value(client):
    payload = dict(VALID_PAYLOAD, bedrooms=99)
    resp = client.post("/api/estimate", json=payload)
    assert resp.status_code == 422
    assert "bedrooms" in resp.get_json()["fields"]


def test_metrics_endpoint(client):
    resp = client.get("/api/metrics")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "r2" in body and "mae" in body
