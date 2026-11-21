
import uuid

from app import app


def register_and_login(client):
    email = f"{uuid.uuid4().hex}@example.com"

    register_response = client.post(
        "/register",
        json={
            "name": "Test Student",
            "email": email,
            "password": "password123"
        }
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/login",
        json={
            "email": email,
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    return register_response.json["id"]


def test_create_profile():
    client = app.test_client()

    register_and_login(client)

    response = client.post(
        "/profile",
        json={
            "name": "Bhavini",
            "headline": "Computer Science Student",
            "skills": ["UI/UX", "HTML"],
            "specialization": "Web Development",
            "bio": "I enjoy building projects."
        }
    )

    assert response.status_code == 201
    assert response.json["name"] == "Bhavini"
    assert response.json["skills"] == ["UI/UX", "HTML"]


def test_create_profile_missing_name():
    client = app.test_client()

    register_and_login(client)

    response = client.post(
        "/profile",
        json={
            "skills": ["HTML"]
        }
    )

    assert response.status_code == 400


def test_edit_existing_profile():
    client = app.test_client()

    register_and_login(client)

    create_response = client.post(
        "/profile",
        json={
            "name": "Student One",
            "skills": ["Python"]
        }
    )

    profile_id = create_response.json["id"]

    update_response = client.put(
        f"/profile/{profile_id}",
        json={
            "name": "Updated Student",
            "headline": "Backend Developer",
            "skills": ["Python", "Flask"],
            "specialization": "Backend Development",
            "bio": "Updated biography."
        }
    )

    assert update_response.status_code == 200
    assert update_response.json["profile"]["name"] == "Updated Student"
    assert update_response.json["profile"]["skills"] == [
        "Python",
        "Flask"
    ]


def test_user_cannot_edit_another_users_profile():
    client = app.test_client()

    register_and_login(client)

    create_response = client.post(
        "/profile",
        json={
            "name": "First Student",
            "skills": ["Python"]
        }
    )

    profile_id = create_response.json["id"]

    client.post("/logout", json={})

    register_and_login(client)

    update_response = client.put(
        f"/profile/{profile_id}",
        json={
            "name": "Unauthorized Update",
            "skills": ["Hacking"]
        }
    )

    assert update_response.status_code == 403


def test_unauthenticated_user_cannot_create_profile():
    client = app.test_client()

    response = client.post(
        "/profile",
        json={
            "name": "Student",
            "skills": ["Python"]
        }
    )

    assert response.status_code == 401


def test_profile_rejects_empty_skills():
    client = app.test_client()

    register_and_login(client)

    response = client.post(
        "/profile",
        json={
            "name": "Student",
            "skills": []
        }
    )

    assert response.status_code == 400


def test_profile_rejects_long_name():
    client = app.test_client()

    register_and_login(client)

    response = client.post(
        "/profile",
        json={
            "name": "A" * 101,
            "skills": ["Python"]
        }
    )

    assert response.status_code == 400
