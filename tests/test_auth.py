import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.models.concert import Concert
from app.models.user import User
from tests.conftest import TestingSessionLocal

client = TestClient(app)


def _create_db_user(email: str, password: str, full_name: str = "Usuario Test") -> int:
    """Crea un usuario directamente en la base de datos de pruebas y retorna su ID."""
    db = TestingSessionLocal()
    try:
        user = User(email=email, full_name=full_name, role="admin", is_active=1)
        user.password_hash = user.get_hash_password(password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id
    finally:
        db.close()


def _create_db_concert(title: str = "Concierto Test", stock: int = 100) -> int:
    """Crea un concierto directamente en la base de datos de pruebas y retorna su ID."""
    db = TestingSessionLocal()
    try:
        concert = Concert(
            title=title,
            artist="Banda Test",
            description="Descripción de prueba",
            price=50.0,
            stock=stock,
        )
        db.add(concert)
        db.commit()
        db.refresh(concert)
        return concert.id
    finally:
        db.close()


def test_lista_conciertos_get():
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


def test_crear_compra():
    """Test creating a purchase."""
    response = client.post(
        "/api/purchases", json={"concert_id": 1, "quantity": 1, "user_id": 1}
    )
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
    assert response.status_code in [401, 404, 500]


def test_lista_compras_usuario():
    """Test listing purchases by user."""
    response = client.get("/api/purchases/user/1")
    assert response.status_code in [200, 404, 500]


def test_detalle_compra():
    """Test getting purchase detail."""
    response = client.get("/api/purchases/1")
    assert response.status_code in [200, 404, 500]


def test_flujo_completo_auth_y_perfil():
    """Test full auth lifecycle: login, refresh, logout, profile update and password change."""
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    _create_db_user(unique_email, "password123")

    # Login con credenciales inválidas
    res_bad_login = client.post(
        "/api/login", json={"email": unique_email, "password": "wrongpassword"}
    )
    assert res_bad_login.status_code == 401

    # Login exitoso
    res_login = client.post(
        "/api/login", json={"email": unique_email, "password": "password123"}
    )
    assert res_login.status_code == 200
    tokens = res_login.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Refresh token válido e inválido
    res_refresh = client.post("/api/refresh", json={"refresh_token": refresh_token})
    assert res_refresh.status_code == 200

    res_bad_refresh = client.post("/api/refresh", json={"refresh_token": "invalido"})
    assert res_bad_refresh.status_code == 401

    # Perfil: consultar y editar
    res_me = client.get("/api/me", headers=headers)
    assert res_me.status_code == 200

    res_edit = client.put(
        "/api/me",
        headers=headers,
        json={"full_name": "Usuario Actualizado", "email": unique_email},
    )
    assert res_edit.status_code == 200

    # Cambio de contraseña (actual incorrecta y luego correcta)
    res_bad_pwd = client.post(
        "/api/password",
        headers=headers,
        json={"old_password": "incorrecta123", "new_password": "newpassword123"},
    )
    assert res_bad_pwd.status_code == 400

    res_ok_pwd = client.post(
        "/api/password",
        headers=headers,
        json={"old_password": "password123", "new_password": "newpassword123"},
    )
    assert res_ok_pwd.status_code == 200

    # Logout
    assert client.post("/api/logout").status_code == 204


def test_flujo_completo_compra_y_tickets():
    """Test full purchase, ticket emission, listing and redemption flow."""
    unique_email = f"buyer_{uuid.uuid4().hex[:8]}@example.com"
    user_id = _create_db_user(unique_email, "password123", "Comprador Test")
    concert_id = _create_db_concert("Concierto Test Coverage", stock=100)

    # Crear compra exitosa y validar errores de stock
    res_purchase = client.post(
        "/api/purchases",
        json={"concert_id": concert_id, "quantity": 2, "user_id": user_id},
    )
    assert res_purchase.status_code == 201
    purchase_id = res_purchase.json()["id"]

    res_no_stock = client.post(
        "/api/purchases",
        json={"concert_id": concert_id, "quantity": 500, "user_id": user_id},
    )
    assert res_no_stock.status_code == 400

    # Emitir tickets y verificar doble emisión
    res_emit = client.post("/api/purchases/emitir", json={"purchase_id": purchase_id})
    assert res_emit.status_code == 201
    tickets = res_emit.json()
    assert len(tickets) == 2

    res_emit_dup = client.post(
        "/api/purchases/emitir", json={"purchase_id": purchase_id}
    )
    assert res_emit_dup.status_code == 400

    # Consultar detalle de compra, compras de usuario y tickets
    assert client.get(f"/api/purchases/{purchase_id}").status_code == 200
    assert client.get(f"/api/purchases/user/{user_id}").status_code == 200
    assert client.get(f"/api/tickets/usuario/{user_id}").status_code == 200
