import json
import secrets
from datetime import datetime
from app.config import get_config

CONFIG = get_config()

TOKEN_FILE = CONFIG["token_file"]

def load_tokens():

    with open(TOKEN_FILE) as f:

        return json.load(f)


def save_tokens(tokens):

    with open(TOKEN_FILE, "w") as f:

        json.dump(tokens, f, indent=4)


def generate_token():

    tokens = load_tokens()

    token = secrets.token_hex(16)

    tokens.append({
        "token": token,
        "used": False,
        "token_type": "enrollment",
        "plan": "community",
        "max_nodes": 1,
        "created_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "expires_at": None
    })

    save_tokens(tokens)

    return token


def validate_token(token):

    tokens = load_tokens()

    for entry in tokens:

        if entry["token"] == token:

            if entry["used"]:

                return False

            return True

    return False


def mark_token_used(token):

    tokens = load_tokens()

    for entry in tokens:

        if entry["token"] == token:

            entry["used"] = True

    save_tokens(tokens)
