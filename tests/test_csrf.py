
import re

from app import app


def test_csrf_protection():
    original_csrf_setting = app.config.get("WTF_CSRF_ENABLED")

    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=True
    )

    try:
        client = app.test_client()

        # 1. Request without a token must be rejected.
        response = client.post(
            "/login",
            data={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 400

        # 2. Request with an invalid token must be rejected.
        response = client.post(
            "/login",
            data={
                "email": "test@example.com",
                "password": "wrongpassword",
                "csrf_token": "invalid-token"
            }
        )
        assert response.status_code == 400

        # 3. Get a genuine token from the login page.
        page = client.get("/login")
        assert page.status_code == 200

        match = re.search(
            r'<meta name="csrf-token" content="([^"]+)"',
            page.get_data(as_text=True)
        )
        assert match is not None

        token = match.group(1)

        # A valid token should pass CSRF validation.
        response = client.post(
            "/login",
            data={
                "email": "test@example.com",
                "password": "wrongpassword"
            },
            headers={"X-CSRFToken": token}
        )

        assert response.status_code != 400

    finally:
        app.config["WTF_CSRF_ENABLED"] = original_csrf_setting