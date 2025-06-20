from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_keyword_research():
    response = client.post(
        "/api/keyword-research",
        json={
            "keywords": ["car loan", "personal loan"],
            "location_id": 1022378,
            "language_id": 1000
        }
    )
    print("Status code:", response.status_code)
    print("Response:", response.json())

if __name__ == "__main__":
    test_keyword_research()
