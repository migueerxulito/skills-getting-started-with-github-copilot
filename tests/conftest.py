import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Fixture que proporciona un cliente de test para la API"""
    return TestClient(app)
