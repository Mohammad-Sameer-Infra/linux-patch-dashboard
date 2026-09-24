#!/bin/bash
# Install or repair the Linux Patch Dashboard:   sudo ./install.sh
# Check an existing installation (no changes):    ./install.sh --check
# Safe to re-run: never overwrites SSH keys, settings or telemetry data.
set -euo pipefail

SERVICE_USER="patchdashboard"
DATA_DIR="/var/lib/patchdashboard"
PUBLIC_KEY="$DATA_DIR/.ssh/id_ed25519.pub"
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$INSTALL_DIR/venv"
SETTINGS="$INSTALL_DIR/config/settings.json"
SERVICE="linux-patch-dashboard"
SERVICE_FILE="/etc/systemd/system/$SERVICE.service"

pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; exit 1; }

# Read a key from settings.json (empty if missing).
setting() {
    python3 -c 'import json, sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ""))' \
        "$SETTINGS" "$1" 2>/dev/null || true
}

check() {
    local problems=0
    warn() { echo "[WARN] $1"; problems=1; }

    [ -x "$VENV_DIR/bin/python" ] && "$VENV_DIR/bin/python" -c \
        'import sys; sys.exit(sys.version_info < (3, 11))' \
        && pass "Virtual environment uses Python 3.11+" || warn "Virtual environment missing or Python < 3.11"
    if [ -f "$SETTINGS" ]; then
        pass "settings.json exists"
        [[ "$(setting dashboard_url)" != *YOUR_SERVER_IP* ]] && pass "Dashboard URL configured" || warn "Dashboard URL is still a placeholder"
        [ -n "$(setting admin_password_hash)" ] && pass "Admin password set" || warn "No admin password (run: venv/bin/python run.py set-password)"
        [ -f "$(setting public_key_file)" ] && pass "Dashboard public key found" || warn "Public key not found: $(setting public_key_file)"
    else
        warn "settings.json missing"
    fi
    runuser -u "$SERVICE_USER" -- test -r "$INSTALL_DIR/run.py" 2>/dev/null \
        && pass "Application readable by $SERVICE_USER" || warn "$SERVICE_USER can't read $INSTALL_DIR (re-run: sudo ./install.sh)"
    systemctl is-active --quiet "$SERVICE" && pass "$SERVICE is running" || warn "$SERVICE is not running"

    [ "$problems" -eq 0 ] && echo "System ready." || echo "Action required, see warnings above."
    return "$problems"
}

if [ "${1:-}" = "--check" ]; then
    check
    exit
fi

[ "$(id -u)" -eq 0 ] || fail "Run install.sh as root or with sudo."

echo "== Prerequisites"
for cmd in python3 ssh ssh-keygen systemctl; do
    command -v "$cmd" >/dev/null || fail "$cmd not found. Install the OS packages listed in the README first."
done
PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null &&
       "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then
        PYTHON=$(command -v "$candidate")
        break
    fi
done
[ -n "$PYTHON" ] || fail "Python 3.11 or newer is required."
pass "Using $PYTHON"

echo "== Service account and SSH key"
if ! getent passwd "$SERVICE_USER" >/dev/null; then
    useradd --system --home-dir "$DATA_DIR" --create-home --shell /sbin/nologin "$SERVICE_USER"
fi
install -d -m 700 -o "$SERVICE_USER" -g "$SERVICE_USER" "$DATA_DIR" "$DATA_DIR/.ssh"
if [ ! -f "$PUBLIC_KEY" ]; then
    runuser -u "$SERVICE_USER" -- ssh-keygen -q -t ed25519 -N "" -f "${PUBLIC_KEY%.pub}"
fi
pass "Account $SERVICE_USER, key $PUBLIC_KEY"

echo "== Settings"
[ -f "$SETTINGS" ] || cp "$INSTALL_DIR/config/settings.example.json" "$SETTINGS"
DASHBOARD_URL=$(setting dashboard_url)
if [ -z "$DASHBOARD_URL" ] || [[ "$DASHBOARD_URL" == *YOUR_SERVER_IP* ]]; then
    DEFAULT_URL="http://$(hostname -I | awk '{print $1}'):5000"
    read -rp "Dashboard URL [$DEFAULT_URL]: " DASHBOARD_URL
    DASHBOARD_URL="${DASHBOARD_URL:-$DEFAULT_URL}"
fi

# Older versions kept data files in the source tree; copy them over once.
OLD_INVENTORY=$(setting inventory_file)
OLD_TOKENS=$(setting token_file)
for pair in "${OLD_INVENTORY:-inventory/servers.json}:servers.json" \
            "${OLD_TOKENS:-security/registration_tokens.json}:registration_tokens.json" \
            "telemetry.db:telemetry.db"; do
    src="$INSTALL_DIR/${pair%%:*}"
    dest="$DATA_DIR/${pair##*:}"
    if [ -f "$src" ] && [ ! -f "$dest" ]; then
        cp "$src" "$dest"
        pass "Copied $src to $dest"
    fi
done
chown -R "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR"

URL="$DASHBOARD_URL" KEY="$PUBLIC_KEY" DATA="$DATA_DIR" "$PYTHON" - "$SETTINGS" <<'EOF'
import json, os, sys
path = sys.argv[1]
settings = json.load(open(path))
for old in ("inventory_file", "token_file"):
    settings.pop(old, None)
settings.update(dashboard_url=os.environ["URL"], public_key_file=os.environ["KEY"], data_dir=os.environ["DATA"])
json.dump(settings, open(path, "w"), indent=4)
EOF
pass "Updated $SETTINGS"

echo "== Python environment"
[ -d "$VENV_DIR" ] || "$PYTHON" -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install -q -r "$INSTALL_DIR/requirements.txt"
pass "Dependencies installed in $VENV_DIR"

echo "== Permissions"
# Servers with a strict umask (027, 077) create files other users can't read,
# so the service account couldn't load the code or the venv. Make them
# readable, not writable, by everyone; settings.json is locked down below.
chmod -R go+rX "$INSTALL_DIR"
runuser -u "$SERVICE_USER" -- test -r "$INSTALL_DIR/run.py" ||
    fail "$SERVICE_USER can't read $INSTALL_DIR. Install under /opt, not a private folder such as a home directory."
pass "Application readable by $SERVICE_USER"

if [ -z "$(setting admin_password_hash)" ]; then
    echo "Set the password for logging in to the dashboard (user: admin)."
    "$VENV_DIR/bin/python" "$INSTALL_DIR/run.py" set-password
fi
# The settings hold the password hash: readable by the service, not by everyone.
chown "root:$SERVICE_USER" "$SETTINGS"
chmod 640 "$SETTINGS"

echo "== Systemd service"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Linux Patch Dashboard
After=network.target

[Service]
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$VENV_DIR/bin/python $INSTALL_DIR/run.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --quiet "$SERVICE"
systemctl restart "$SERVICE"
sleep 2

echo "== Check"
check || true
echo
echo "Dashboard: $DASHBOARD_URL"
