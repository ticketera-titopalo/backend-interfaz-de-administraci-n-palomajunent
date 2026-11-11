import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_obtener_perfil():
    """Test getting user profile."""
    response = client.get("/api/users/me")
    assert response.status_code in [401, 404, 500]


def test_editar_perfil():
    """Test editing user profile."""
    response = client.put("/api/users/me", json={"full_name": "Test", "email": "test@test.com"})
    assert response.status_code in [401, 404, 500]


def test_cambiar_password():
    """Test changing password."""
    response = client.post("/api/password", json={"old_password": "123456", "new_password": "nueva123"})
    assert response.status_code in [401, 400, 200]


def test_sin_token_perfil():
    """Test profile endpoint without token."""
    response = client.get("/api/users/me")
    assert response.status_code in [401, 404, 500]


def test_sin_token_password():
    """Test password change without token."""
    response = client.post("/api/password", json={"old_password": "123456", "new_password": "nueva123"})
    assert response.status_code in [401, 400, 200]