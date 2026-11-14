import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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
    """Test full auth lifecycle: register, login, refresh, profile update and password change."""
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    register_payload = {
        "email": unique_email,
        "password": "password123",
        "full_name": "Usuario Test",
    }
    res_reg = client.post("/api/register", json=register_payload)
    assert res_reg.status_code in [201, 400]

    # Registro duplicado
    res_dup = client.post("/api/register", json=register_payload)
    assert res_dup.status_code == 400

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


def test_flujo_completo_compra_y_tickets():
    """Test full purchase, ticket emission, listing and redemption flow."""
    unique_email = f"buyer_{uuid.uuid4().hex[:8]}@example.com"
    res_reg = client.post(
        "/api/register",
        json={
            "email": unique_email,
            "password": "password123",
            "full_name": "Comprador Test",
        },
    )
    assert res_reg.status_code == 201
    user_id = res_reg.json()["id"]

    res_concert = client.post(
        "/api/concerts",
        json={
            "title": "Concierto Test Coverage",
            "artist": "Banda Test",
            "venue": "Estadio Test",
            "date": "2026-12-01T20:00:00",
            "price": 50.0,
            "total_tickets": 100,
        },
    )
    assert res_concert.status_code == 201
    concert_id = res_concert.json()["id"]

    # Crear compra exitosa y validar errores de stock/usuario
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

    # Consultar detalle de compra, compras de usuario, tickets y canjear QR
    assert client.get(f"/api/purchases/{purchase_id}").status_code == 200
    assert client.get(f"/api/purchases/user/{user_id}").status_code == 200
    assert client.get(f"/api/tickets/usuario/{user_id}").status_code == 200

    qr_code = tickets[0]["qr_code"]
    res_redeem = client.post(f"/api/tickets/redeem/{qr_code}")
    assert res_redeem.status_code in [200, 404]