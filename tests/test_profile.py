from app import app


def test_create_profile():
    client = app.test_client()
    res = client.post(
        "/profile",
        json={"name": "Bhavini", "skills": ["UI/UX", "HTML"]}
    )
    assert res.status_code == 201


def test_create_profile_missing_name():
    client = app.test_client()
    res = client.post(
        "/profile",
        json={"skills": ["HTML"]}
    )
    assert res.status_code == 400