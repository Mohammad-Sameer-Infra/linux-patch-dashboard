import json

from flask import Flask, Response, g, request
from werkzeug.security import check_password_hash

from app import store
from app.documentation import documentation_bp

app = Flask(__name__)

store.init_db()

with open(store.ROOT / "config" / "product.json", encoding="utf-8") as f:
    PRODUCT = json.load(f)

# Managed nodes call the first two without a password: the key is public,
# and registering needs a one-time token. Documentation is public, like
# most products' docs, and needs the stylesheet.
PUBLIC_ENDPOINTS = {"public_key", "api_register", "static"}
PUBLIC_BLUEPRINTS = {"documentation"}


def logged_in():
    """True if the request carries the admin's credentials (checked once per request)."""
    if "logged_in" not in g:
        password_hash = store.SETTINGS.get("admin_password_hash")
        auth = request.authorization
        g.logged_in = bool(
            password_hash and auth and auth.type == "basic"
            and auth.username == store.SETTINGS.get("admin_user", "admin")
            and check_password_hash(password_hash, auth.password or "")
        )
    return g.logged_in


@app.before_request
def require_login():
    if request.endpoint in PUBLIC_ENDPOINTS or request.blueprint in PUBLIC_BLUEPRINTS:
        return None

    if not store.SETTINGS.get("admin_password_hash"):
        return Response(
            "No admin password is set. Run: python run.py set-password\n",
            503, mimetype="text/plain",
        )

    if logged_in():
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
        "logged_in": logged_in(),
    }


app.register_blueprint(documentation_bp)

from app import routes  # noqa: E402,F401  (registers the routes)
