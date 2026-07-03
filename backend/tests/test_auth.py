from app.config import settings

def test_register_user(client):
    response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"username": "newuser", "email": "new@example.com", "password": "securepassword"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "id" in data
    assert data["credits"] == 100.0

def test_register_user_duplicate_username(client):
    client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"username": "dupuser", "email": "dup1@example.com", "password": "password123"}
    )
    response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"username": "dupuser", "email": "dup2@example.com", "password": "password123"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"

def test_login_user(client):
    client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"username": "loginuser", "email": "login@example.com", "password": "password123"}
    )
    response = client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": "loginuser", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_user_incorrect_password(client):
    client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"username": "badpassuser", "email": "badpass@example.com", "password": "password123"}
    )
    response = client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": "badpassuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
