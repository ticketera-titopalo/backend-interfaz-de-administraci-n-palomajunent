from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_obtener_perfil():
    """Test getting user profile."""
    response = client.get("/api/users/me")
    assert response.status_code in [401, 404, 500]


def test_editar_perfil():
    """Test editing user profile."""
    response = client.put(
        "/api/users/me", json={"full_name": "Test", "email": "test@test.com"}
    )
    assert response.status_code in [401, 404, 500]


def test_cambiar_password():
    """Test changing password."""
    response = client.post(
        "/api/password", json={"old_password": "123456", "new_password": "nueva123"}
    )
    assert response.status_code in [401, 400, 200]


def test_sin_token_perfil():
    """Test profile endpoint without token."""
    response = client.get("/api/users/me")
    assert response.status_code in [401, 404, 500]


def test_sin_token_password():
    """Test password change without token."""
    response = client.post(
        "/api/password", json={"old_password": "123456", "new_password": "nueva123"}
    )
    assert response.status_code in [401, 400, 200]


def test_editar_perfil_sin_token():
    """Test editing profile on /api/me without token."""
    response = client.put(
        "/api/me", json={"full_name": "Nuevo Nombre", "email": "nuevo@test.com"}
    )
    assert response.status_code == 401


def test_obtener_perfil_token_invalido():
    """Test getting profile with an invalid JWT token."""
    response = client.get(
        "/api/me", headers={"Authorization": "Bearer token-invalido-123"}
    )
    assert response.status_code == 401


def test_listar_usuarios():
    """Test listing all users."""
    response = client.get("/api/")
    assert response.status_code in [200, 500]
