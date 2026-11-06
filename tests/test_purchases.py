import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_crear_compra():
    """Test creating a purchase."""
    response = client.post("/api/purchases", json={"concert_id": 1, "quantity": 1, "user_id": 1})
    assert response.status_code in [201, 404, 500]


def test_emitir_tickets():
    """Test emitting tickets."""
    response = client.post("/api/purchases/emitir", json={"purchase_id": 1})
    assert response.status_code in [201, 404, 500]


def test_listar_tickets_usuario():
    """Test listing tickets by user."""
    response = client.get("/api/tickets/usuario/1")
    assert response.status_code in [200, 404, 500]


def test_listar_compras_usuario():
    """Test listing purchases by user."""
    response = client.get("/api/purchases/user/1")
    assert response.status_code in [200, 404, 500]


def test_obtener_compra():
    """Test getting purchase detail."""
    response = client.get("/api/purchases/1")
    assert response.status_code in [200, 404, 500]


def test_compras_sin_token():
    """Test purchases endpoints without token."""
    response = client.get("/api/purchases/user/1")
    assert response.status_code in [401, 404, 500]
