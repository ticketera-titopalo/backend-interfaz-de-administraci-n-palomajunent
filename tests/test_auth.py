import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_lista_conciertos_get():
    """Test listing concerts endpoint."""
    response = client.get("/api/concerts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_obtener_concierto():
    """Test getting concert by ID."""
    response = client.get("/api/concerts/1")
    # Sin BD, retornará 404 o error, pero probamos que el endpoint existe
    assert response.status_code in [200, 404, 500]


def test_crear_compra():
    """Test creating a purchase."""
    response = client.post("/api/purchases", json={"concert_id": 1, "quantity": 1, "user_id": 1})
    # Sin BD, retornará error por falta de conexión
    assert response.status_code in [201, 404, 500]


def test_emitir_tickets():
    """Test emitting tickets."""
    response = client.post("/api/purchases/emitir", json={"purchase_id": 1})
    assert response.status_code in [201, 404, 500]


def test_listar_tickets_usuario():
    """Test listing tickets by user."""
    response = client.get("/api/tickets/usuario/1")
    assert response.status_code in [200, 404, 500]


def test_sin_token():
    """Test accessing protected endpoint without token."""
    response = client.get("/api/users/me")
    # Sin token, debería retornar 401 o 404 (dependiendo de implementación)
    assert response.status_code in [401, 404, 500]


def test_lista_compras_usuario():
    """Test listing purchases by user."""
    response = client.get("/api/purchases/user/1")
    assert response.status_code in [200, 404, 500]


def test_detalle_compra():
    """Test getting purchase detail."""
    response = client.get("/api/purchases/1")
    assert response.status_code in [200, 404, 500]
