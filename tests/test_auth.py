
from app import app
from extensions import db
from models import User


def test_register():
    client = app.test_client()

    response = client.post(
        "/register",
        json={
            "name": "Vandita",
            "email": "v@test.com",
            "password": "password123"
        }
    )

    assert response.status_code == 201

    with app.app_context():
        user = User.query.filter_by(email="v@test.com").first()
        assert user is not None
        assert user.password_hash != "password123"


def test_register_missing_email():
    client = app.test_client()

    response = client.post(
        "/register",
        json={
            "name": "Vandita",
            "password": "password123"
        }
    )

    assert response.status_code == 400


def test_register_missing_password():
    client = app.test_client()

    response = client.post(
        "/register",
        json={
            "name": "Vandita",
            "email": "missing@test.com"
        }
    )

    assert response.status_code == 400


def test_login_success():
    client = app.test_client()

    client.post(
        "/register",
        json={
            "name": "Vandita",
            "email": "login@test.com",
            "password": "password123"
        }
    )

    response = client.post(
        "/login",
        json={
            "email": "login@test.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200

    with client.session_transaction() as session:
        assert "user_id" in session


def test_login_wrong_password():
    client = app.test_client()

    response = client.post(
        "/login",
        json={
            "email": "login@test.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401


def test_logout():
    client = app.test_client()

    client.post(
        "/register",
        json={
            "name": "Vandita",
            "email": "logout@test.com",
            "password": "password123"
        }
    )

    client.post(
        "/login",
        json={
            "email": "logout@test.com",
            "password": "password123"
        }
    )

    response = client.post("/logout", json={})

    assert response.status_code == 200

    with client.session_transaction() as session:
        assert "user_id" not in session
