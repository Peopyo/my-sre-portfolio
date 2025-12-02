import pytest
from app import app

def test_app_starts():
    with app.test_client() as client:
        response = client.get("/")
        assert response.status_code != 500