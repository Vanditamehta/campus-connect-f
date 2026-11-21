
import uuid

from app import app
from models import Connection


def create_user(client, name):
    email = f"{uuid.uuid4().hex}@example.com"

    response = client.post(
        "/register",
        json={
            "name": name,
            "email": email,
            "password": "password123"
        }
    )

    assert response.status_code == 201

    return {
        "id": response.json["id"],
        "email": email
    }


def login_user(client, email):
    response = client.post(
        "/login",
        json={
            "email": email,
            "password": "password123"
        }
    )

    assert response.status_code == 200


def test_people_requires_login():
    client = app.test_client()

    response = client.get("/api/people")

    assert response.status_code == 401


def test_people_list_excludes_logged_in_user():
    client = app.test_client()

    first = create_user(client, "First Student")
    second = create_user(client, "Second Student")

    login_user(client, first["email"])

    response = client.get("/api/people")

    assert response.status_code == 200

    people = response.json["people"]
    people_ids = [person["id"] for person in people]

    assert first["id"] not in people_ids
    assert second["id"] in people_ids


def test_follow_user_successfully():
    client = app.test_client()

    first = create_user(client, "First Student")
    second = create_user(client, "Second Student")

    login_user(client, first["email"])

    response = client.post(
        f"/api/follow/{second['id']}"
    )

    assert response.status_code == 201
    assert response.json["message"] == "User followed successfully."


def test_duplicate_follow_is_rejected():
    client = app.test_client()

    first = create_user(client, "First Student")
    second = create_user(client, "Second Student")

    login_user(client, first["email"])

    first_response = client.post(
        f"/api/follow/{second['id']}"
    )

    second_response = client.post(
        f"/api/follow/{second['id']}"
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_user_cannot_follow_themselves():
    client = app.test_client()

    first = create_user(client, "First Student")

    login_user(client, first["email"])

    response = client.post(
        f"/api/follow/{first['id']}"
    )

    assert response.status_code == 400


def test_unfollow_user_successfully():
    client = app.test_client()

    first = create_user(client, "First Student")
    second = create_user(client, "Second Student")

    login_user(client, first["email"])

    follow_response = client.post(
        f"/api/follow/{second['id']}"
    )

    assert follow_response.status_code == 201

    unfollow_response = client.post(
        f"/api/unfollow/{second['id']}"
    )

    assert unfollow_response.status_code == 200

    repeated_response = client.post(
        f"/api/unfollow/{second['id']}"
    )

    assert repeated_response.status_code == 404


def test_followers_and_following_lists():
    client = app.test_client()

    first = create_user(client, "First Student")
    second = create_user(client, "Second Student")

    login_user(client, first["email"])

    follow_response = client.post(
        f"/api/follow/{second['id']}"
    )

    assert follow_response.status_code == 201

    following_response = client.get(
        f"/api/users/{first['id']}/following"
    )

    assert following_response.status_code == 200
    assert following_response.json["count"] == 1
    assert following_response.json["following"][0]["id"] == second["id"]

    followers_response = client.get(
        f"/api/users/{second['id']}/followers"
    )

    assert followers_response.status_code == 200
    assert followers_response.json["count"] == 1
    assert followers_response.json["followers"][0]["id"] == first["id"]


def test_follow_nonexistent_user():
    client = app.test_client()

    first = create_user(client, "First Student")

    login_user(client, first["email"])

    response = client.post("/api/follow/999999")

    assert response.status_code == 404


def test_connections_summary():
    client = app.test_client()

    first = create_user(client, "First Student")
    second = create_user(client, "Second Student")

    login_user(client, first["email"])

    client.post(f"/api/follow/{second['id']}")

    response = client.get("/api/connections")

    assert response.status_code == 200
    assert response.json["following_count"] == 1
    assert response.json["followers_count"] == 0
