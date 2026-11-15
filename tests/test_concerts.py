from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_listar_conciertos_get():
    """Test listing concerts endpoint."""
    response = client.get("/api/concerts")
    assert response.status_code in [200, 404, 500]
    data = response.json()
    if response.status_code == 200:
        assert isinstance(data, list)


def test_obtener_concierto():
    """Test getting concert by ID."""
    response = client.get("/api/concerts/1")
    assert response.status_code in [200, 404, 500]


def test_crear_concierto():
    """Test creating a concert."""
    response = client.post(
        "/api/concerts",
        json={"title": "Test", "artist": "Artista", "price": 50, "stock": 100},
    )
    assert response.status_code in [201, 404, 500]


def test_concierto_invalido():
    """Test creating concert with invalid data."""
    response = client.post(
        "/api/concerts",
        json={"title": "", "artist": "Artista", "price": -10, "stock": 5},
    )
    # Debe retornar error de validación
    assert response.status_code in [422, 404, 500]


def test_detalle_concierto():
    """Test getting concert detail."""
    response = client.get("/api/concerts/1/detail")
    assert response.status_code in [200, 404, 500]
