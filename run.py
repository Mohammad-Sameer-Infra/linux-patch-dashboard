"""Start the dashboard, or set the admin password with: python run.py set-password"""

import getpass
import json
import sys
import threading
from pathlib import Path

SETTINGS_FILE = Path(__file__).resolve().parent / "config" / "settings.json"


def set_password():
    from werkzeug.security import generate_password_hash

    password = getpass.getpass("New admin password: ")
    if len(password) < 8 or password != getpass.getpass("Repeat password: "):
        sys.exit("Passwords must match and be at least 8 characters.")

    settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    settings.setdefault("admin_user", "admin")
    settings["admin_password_hash"] = generate_password_hash(password)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=4), encoding="utf-8")
    print(f"Password set for user '{settings['admin_user']}'. Restart the dashboard to apply it.")


def main():
    from app import app, store
    from app.collect import collect_forever

    interval = store.SETTINGS.get("collect_interval_seconds", 300)
    threading.Thread(target=collect_forever, args=(interval,), daemon=True).start()
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    if sys.argv[1:] == ["set-password"]:
        set_password()
    else:
        main()
