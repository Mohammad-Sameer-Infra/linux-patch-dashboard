import json

from flask import Flask, Response, request
from werkzeug.security import check_password_hash

from app import store
from app.documentation import documentation_bp

app = Flask(__name__)

store.init_db()

with open(store.ROOT / "config" / "product.json", encoding="utf-8") as f:
    PRODUCT = json.load(f)

# Managed nodes call these without a password: the key is public,
# and registering needs a one-time token.
PUBLIC_ENDPOINTS = {"public_key", "api_register"}


@app.before_request
def require_login():
    if request.endpoint in PUBLIC_ENDPOINTS:
        return None

    password_hash = store.SETTINGS.get("admin_password_hash")
    if not password_hash:
        return Response(
            "No admin password is set. Run: python run.py set-password\n",
            503, mimetype="text/plain",
        )

    auth = request.authorization
    if (auth and auth.type == "basic"
            and auth.username == store.SETTINGS.get("admin_user", "admin")
            and check_password_hash(password_hash, auth.password or "")):
        return None

    return Response(
        "Login required\n", 401,
        {"WWW-Authenticate": f'Basic realm="{PRODUCT["name"]}"'},
    )


@app.context_processor
def inject_globals():
    return {
        "product": PRODUCT,
        "refresh_seconds": store.SETTINGS.get("dashboard_refresh_seconds", 30),
    }


app.register_blueprint(documentation_bp)

from app import routes  # noqa: E402,F401  (registers the routes)
