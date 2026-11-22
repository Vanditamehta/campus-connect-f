
from app import app
from extensions import db
from models import User, Post


def create_user(client, name, email):
    response = client.post(
        "/register",
        json={
            "name": name,
            "email": email,
            "password": "password123"
        }
    )
    assert response.status_code == 201

    response = client.post(
        "/login",
        json={
            "email": email,
            "password": "password123"
        }
    )
    assert response.status_code == 200


def test_create_post():
    client = app.test_client()
    create_user(client, "User One", "post1@test.com")

    response = client.post(
        "/post",
        json={"content": "My first post", "kind": "status"}
    )

    assert response.status_code == 201
    assert response.json["content"] == "My first post"


def test_edit_own_post():
    client = app.test_client()
    create_user(client, "User Two", "post2@test.com")

    response = client.post(
        "/post",
        json={"content": "Original post", "kind": "status"}
    )
    post_id = response.json["id"]

    response = client.post(
        f"/post/{post_id}/edit",
        json={"content": "Updated post", "kind": "achievement"}
    )

    assert response.status_code == 200
    assert response.json["content"] == "Updated post"
    assert response.json["kind"] == "achievement"


def test_delete_own_post():
    client = app.test_client()
    create_user(client, "User Three", "post3@test.com")

    response = client.post(
        "/post",
        json={"content": "Post to delete", "kind": "status"}
    )
    post_id = response.json["id"]

    response = client.post(f"/post/{post_id}/delete")

    assert response.status_code == 200

    with app.app_context():
        assert db.session.get(Post, post_id) is None


def test_cannot_edit_another_users_post():
    owner = app.test_client()
    create_user(owner, "Owner", "owner@test.com")

    response = owner.post(
        "/post",
        json={"content": "Owner's post", "kind": "status"}
    )
    post_id = response.json["id"]

    other_user = app.test_client()
    create_user(other_user, "Other User", "other@test.com")

    response = other_user.post(
        f"/post/{post_id}/edit",
        json={"content": "Unauthorized edit", "kind": "status"}
    )

    assert response.status_code == 403


def test_cannot_delete_another_users_post():
    owner = app.test_client()
    create_user(owner, "Owner Two", "owner2@test.com")

    response = owner.post(
        "/post",
        json={"content": "Protected post", "kind": "status"}
    )
    post_id = response.json["id"]

    other_user = app.test_client()
    create_user(other_user, "Other User Two", "other2@test.com")

    response = other_user.post(f"/post/{post_id}/delete")

    assert response.status_code == 403

    with app.app_context():
        assert db.session.get(Post, post_id) is not None


def test_edit_post_empty_content():
    client = app.test_client()
    create_user(client, "User Four", "post4@test.com")

    response = client.post(
        "/post",
        json={"content": "Original content", "kind": "status"}
    )
    post_id = response.json["id"]

    response = client.post(
        f"/post/{post_id}/edit",
        json={"content": "   ", "kind": "status"}
    )

    assert response.status_code == 400


def test_edit_post_requires_login():
    client = app.test_client()

    response = client.post(
        "/post/1/edit",
        json={"content": "Unauthorized", "kind": "status"}
    )

    assert response.status_code == 401


def test_delete_post_requires_login():
    client = app.test_client()

    response = client.post("/post/1/delete")

    assert response.status_code == 401
