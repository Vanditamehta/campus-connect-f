
from app import app
from extensions import db
from models import User


def test_register():
    with app.app_context():
        existing_user = User.query.filter_by(email="v@test.com").first()

        if existing_user:
            db.session.delete(existing_user)
            db.session.commit()

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
