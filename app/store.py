"""Settings, the inventory and token files, and the SQLite telemetry store."""

import ipaddress
import json
import re
import secrets
import sqlite3
import threading
import uuid
from contextlib import closing
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

with open(ROOT / "config" / "settings.json", encoding="utf-8") as f:
    SETTINGS = json.load(f)

# Runtime data lives outside the source tree when data_dir is absolute
# (the installer uses /var/lib/patchdashboard).
DATA_DIR = ROOT / SETTINGS.get("data_dir", "data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

INVENTORY_FILE = DATA_DIR / "servers.json"
TOKEN_FILE = DATA_DIR / "registration_tokens.json"
DATABASE = DATA_DIR / "telemetry.db"

# Serialises read-modify-write of the JSON files between request threads.
_lock = threading.Lock()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []


def save_json(path, data):
    # Write to a temp file and rename, so a crash never leaves half a file.
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=4), encoding="utf-8")
    tmp.replace(path)


def load_servers():
    return load_json(INVENTORY_FILE)


# --- Telemetry database ---------------------------------------------------

def connect():
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hostname TEXT,
                ip TEXT,
                os TEXT,
                uptime TEXT,
                updates INTEGER,
                kernel_updates INTEGER,
                security_updates INTEGER,
                critical_packages INTEGER,
                status TEXT,
                last_check TEXT
            )
        """)
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(telemetry)")}
        if "packages" not in columns:
            conn.execute("ALTER TABLE telemetry ADD COLUMN packages TEXT")


COLUMNS = [
    "hostname", "ip", "os", "uptime", "updates", "kernel_updates",
    "security_updates", "critical_packages", "status", "last_check",
]


def insert_snapshot(snapshot):
    values = [snapshot[c] for c in COLUMNS] + [json.dumps(snapshot["packages"])]
    with closing(connect()) as conn, conn:
        conn.execute(
            f"INSERT INTO telemetry ({', '.join(COLUMNS)}, packages) "
            f"VALUES ({', '.join('?' * (len(COLUMNS) + 1))})",
            values,
        )


def latest_snapshots():
    """The newest snapshot per hostname, plus when it was last seen online."""
    with closing(connect()) as conn:
        rows = conn.execute("""
            SELECT * FROM telemetry
            WHERE id IN (SELECT MAX(id) FROM telemetry GROUP BY hostname)
        """).fetchall()
        last_seen = dict(conn.execute("""
            SELECT hostname, MAX(last_check) FROM telemetry
            WHERE status = 'Online' GROUP BY hostname
        """).fetchall())

    snapshots = {}
    for row in rows:
        snapshot = dict(row)
        snapshot["packages"] = json.loads(snapshot["packages"] or "[]")
        snapshot["last_seen"] = last_seen.get(snapshot["hostname"])
        snapshots[snapshot["hostname"]] = snapshot
    return snapshots


def telemetry_history(limit=500):
    with closing(connect()) as conn:
        return conn.execute(
            f"SELECT {', '.join(COLUMNS)} FROM telemetry ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()


# --- Registration -----------------------------------------------------------

HOSTNAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]{0,252}")
SSH_USER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]{0,31}")


def create_token():
    token = secrets.token_hex(16)
    with _lock:
        tokens = load_json(TOKEN_FILE)
        tokens.append({"token": token, "used": False, "created_at": now()})
        save_json(TOKEN_FILE, tokens)
    return token


def validate_node(data):
    """Check registration input strictly: these values become SSH arguments."""
    hostname = str(data.get("hostname", ""))
    if not HOSTNAME_RE.fullmatch(hostname):
        raise ValueError("Invalid hostname")

    try:
        ip = str(ipaddress.ip_address(str(data.get("ip", ""))))
    except ValueError:
        raise ValueError("Invalid IP address") from None

    ssh_user = str(data.get("ssh_user", ""))
    if not SSH_USER_RE.fullmatch(ssh_user):
        raise ValueError("Invalid SSH user")

    try:
        ssh_port = int(data.get("ssh_port", 22))
    except (TypeError, ValueError):
        ssh_port = 0
    if not 1 <= ssh_port <= 65535:
        raise ValueError("Invalid SSH port")

    return {"hostname": hostname, "ip": ip, "ssh_user": ssh_user, "ssh_port": ssh_port}


def register_node(data):
    """Add a node to the inventory. Returns (success, message)."""
    node = validate_node(data)
    token = str(data.get("token", "")).encode()

    with _lock:
        tokens = load_json(TOKEN_FILE)
        entry = next(
            (t for t in tokens
             if not t["used"] and secrets.compare_digest(t["token"].encode(), token)),
            None,
        )
        if entry is None:
            return False, "Invalid or used token"

        servers = load_servers()
        for server in servers:
            if server["hostname"] == node["hostname"]:
                return False, "Hostname already registered"
            if server["ip"] == node["ip"]:
                return False, "IP already registered"

        servers.append({
            "node_id": str(uuid.uuid4()),
            **node,
            "state": "active",
            "registered_at": now(),
        })
        save_json(INVENTORY_FILE, servers)

        entry["used"] = True
        save_json(TOKEN_FILE, tokens)

    return True, "Node registered successfully"
