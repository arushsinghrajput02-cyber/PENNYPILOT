def test_register_success(client):
    res = client.post("/api/auth/register", json={
        "name": "Aarav Patel",
        "email": "aarav@college.edu",
        "password": "securepassword123"
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "aarav@college.edu"
    assert data["user"]["name"] == "Aarav Patel"


def test_register_duplicate_email(client):
    payload = {
        "name": "Aarav Patel",
        "email": "duplicate@college.edu",
        "password": "securepassword123"
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_login_success(client):
    # Register first
    client.post("/api/auth/register", json={
        "name": "Kavya Singh",
        "email": "kavya@college.edu",
        "password": "mypassword999"
    })

    # Login
    res = client.post("/api/auth/login", json={
        "email": "kavya@college.edu",
        "password": "mypassword999"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["name"] == "Kavya Singh"


def test_login_invalid_credentials(client):
    res = client.post("/api/auth/login", json={
        "email": "unknown@college.edu",
        "password": "wrongpassword"
    })
    assert res.status_code == 401


def test_protected_me_route(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "rohan.test@pennypilot.in"


def test_protected_me_route_unauthorized(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
