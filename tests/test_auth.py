from app import app


def test_register():
    client = app.test_client()
    res = client.post(
        "/register",
        json={"name": "Vandita", "email": "v@test.com"}
    )
    assert res.status_code == 201


def test_register_missing_email():
    client = app.test_client()
    res = client.post(
        "/register",
        json={"name": "Vandita"}
    )
    assert res.status_code == 400