#!/bin/bash

set -e

SERVICE_USER="patchdashboard"
SERVICE_HOME="/var/lib/patchdashboard"
SSH_DIR="${SERVICE_HOME}/.ssh"
PRIVATE_KEY="${SSH_DIR}/id_ed25519"
PUBLIC_KEY="${PRIVATE_KEY}.pub"
RECOMMENDED_INSTALL_DIR="/opt/linux-patch-dashboard"
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_INSTALL_DIR="$RECOMMENDED_INSTALL_DIR"
VENV_DIR="${APP_INSTALL_DIR}/venv"
SERVICE_FILE="/etc/systemd/system/linux-patch-dashboard.service"

print_header() {

echo
echo "====================================="
echo " Linux Patch Dashboard Installer"
echo "====================================="
echo

}

print_step() {

echo
echo "====================================="
echo "$1"
echo "====================================="
echo

}

print_pass() {

echo "[PASS] $1"

}

print_warn() {

echo "[WARN] $1"

}

print_fail() {

echo "[FAIL] $1"

}

print_header

#
# Root Validation
#

print_step "[1/15] Root Validation"

if [ "$(id -u)" -ne 0 ]
then

    print_fail \
    "install.sh must be run as root or with sudo."

    exit 1

fi

print_pass "Running with root privileges"

#
# Prerequisite Validation
#

print_step "[2/15] Prerequisite Validation"

REQUIRED_COMMANDS=(
    git
    python3
    sqlite3
    ssh-keygen
    systemctl
)

for CMD in "${REQUIRED_COMMANDS[@]}"
do

    if command -v "$CMD" >/dev/null 2>&1
    then

        print_pass "$CMD installed"

    else

        print_fail "$CMD not found"

        echo
        echo "Please install the required OS packages"
        echo "before running install.sh."
        echo
        exit 1

    fi

done

#
# Python Detection
#

print_step "[3/15] Python Runtime Detection"

PYTHON_CMD=""

for CANDIDATE in \
    python3.13 \
    python3.12 \
    python3.11 \
    python3
do

    if command -v "$CANDIDATE" >/dev/null 2>&1
    then

        if "$CANDIDATE" -c \
        'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)'
        then

            PYTHON_CMD=$(command -v "$CANDIDATE")

            break

        fi

    fi

done

if [ -z "$PYTHON_CMD" ]
then

    print_fail \
    "No supported Python interpreter found."

    echo
    echo "Python 3.11 or newer is required."
    echo

    exit 1

fi

PYTHON_VERSION=$(
"$PYTHON_CMD" -c \
'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")'
)

print_pass "Selected interpreter: $PYTHON_CMD"
print_pass "Python version: $PYTHON_VERSION"

#
# Service Account Validation
#

print_step "[4/15] Dashboard Service Account"

if getent passwd "$SERVICE_USER" >/dev/null 2>&1
then

    print_pass \
    "Service account already exists: $SERVICE_USER"

else

    useradd \
        --system \
        --home-dir "$SERVICE_HOME" \
        --create-home \
        --shell /sbin/nologin \
        "$SERVICE_USER"

    print_pass \
    "Created service account: $SERVICE_USER"

fi

#
# Installation Directory
#

print_step "[5/15] Installation Directory"

CURRENT_DIR="$INSTALL_DIR"

if [ "$CURRENT_DIR" = "$RECOMMENDED_INSTALL_DIR" ]
then

    print_pass \
    "Using recommended installation path"

else

    print_warn \
    "Recommended installation path:"

    echo "       $RECOMMENDED_INSTALL_DIR"
    echo
    echo "Current location:"
    echo "       $CURRENT_DIR"

fi

#
# Dashboard SSH Key
#

print_step "[6/15] Dashboard SSH Key"

if [ ! -d "$SSH_DIR" ]
then

    mkdir -p "$SSH_DIR"

    print_pass "Created SSH directory"

else

    print_pass "SSH directory already exists"

fi

chown "$SERVICE_USER:$SERVICE_USER" "$SSH_DIR"

chmod 700 "$SSH_DIR"

if [ -f "$PRIVATE_KEY" ] && [ -f "$PUBLIC_KEY" ]
then

    print_pass "Dashboard SSH key already exists"

else

    runuser -u "$SERVICE_USER" -- ssh-keygen \
            -t ed25519 \
            -N "" \
            -f "$PRIVATE_KEY"
    print_pass "Generated dashboard SSH key"

fi

#
# Dashboard Configuration
#

print_step "[7/15] Dashboard Configuration"

SETTINGS_FILE="${INSTALL_DIR}/config/settings.json"
SETTINGS_EXAMPLE="${INSTALL_DIR}/config/settings.example.json"

if [ ! -f "$SETTINGS_EXAMPLE" ]
then

    print_fail "settings.example.json not found"

    exit 1

fi

if [ ! -f "$SETTINGS_FILE" ]
then

    cp "$SETTINGS_EXAMPLE" "$SETTINGS_FILE"

    print_pass "Created settings.json"

else

    print_pass "settings.json already exists"

fi

#
# Dashboard URL Configuration
#

print_step "[8/15] Dashboard URL Configuration"

DEFAULT_IP=$(hostname -I | awk '{print $1}')
DEFAULT_URL="http://${DEFAULT_IP}:5000"

CURRENT_URL=$(
"$PYTHON_CMD" -c "
import json
with open('$SETTINGS_FILE') as f:
    data=json.load(f)
print(data.get('dashboard_url',''))
"
)

if [ -z "$CURRENT_URL" ] || \
   [ "$CURRENT_URL" = "http://YOUR_SERVER_IP:5000" ]
then

    echo
    read -rp \
    "Dashboard URL [$DEFAULT_URL]: " USER_URL

    DASHBOARD_URL="${USER_URL:-$DEFAULT_URL}"

else

    echo
    echo "Current Dashboard URL:"
    echo "$CURRENT_URL"
    echo

    read -rp \
    "Update dashboard URL? [y/N]: " UPDATE_URL

    if [[ "$UPDATE_URL" =~ ^[Yy]$ ]]
    then

        read -rp \
        "Dashboard URL [$CURRENT_URL]: " USER_URL

        DASHBOARD_URL="${USER_URL:-$CURRENT_URL}"

    else

        DASHBOARD_URL="$CURRENT_URL"

    fi

fi

"$PYTHON_CMD" <<EOF
import json

settings_file = "$SETTINGS_FILE"

with open(settings_file) as f:
    data = json.load(f)

data["dashboard_url"] = "$DASHBOARD_URL"
data["public_key_file"] = "$PUBLIC_KEY"

with open(settings_file, "w") as f:
    json.dump(data, f, indent=4)

EOF

print_pass "Updated settings.json"

#
# Python Virtual Environment
#

print_step "[9/15] Python Virtual Environment"

if [ -d "$VENV_DIR" ]
then

    print_pass "Virtual environment already exists"

else

    runuser -u "$SERVICE_USER" -- \
        "$PYTHON_CMD" -m venv "$VENV_DIR"

    print_pass "Created virtual environment"

fi


chown -R "$SERVICE_USER:$SERVICE_USER" "$VENV_DIR"

#
# Python Dependency Installation
#

print_step "[10/15] Python Dependency Installation"

REQUIREMENTS_FILE="${INSTALL_DIR}/requirements.txt"

if [ ! -f "$REQUIREMENTS_FILE" ]
then

    print_fail "requirements.txt not found"

    exit 1

fi

runuser -u "$SERVICE_USER" -- \
    "$VENV_DIR/bin/pip" install \
    -r "$REQUIREMENTS_FILE"

print_pass "Installed Python dependencies"

#
# Runtime Ownership
#

print_step "[11/15] Runtime Ownership"

chown -R "$SERVICE_USER:$SERVICE_USER" \
    "$SERVICE_HOME"

chown -R "$SERVICE_USER:$SERVICE_USER" \
    "$VENV_DIR"

print_pass "Runtime ownership verified"

#
# Systemd Service Creation
#

print_step "[12/15] Systemd Service Creation"

if [ -f "$SERVICE_FILE" ]
then

    cp "$SERVICE_FILE" \
       "${SERVICE_FILE}.bak"

    print_pass "Backed up existing service file"

fi

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Linux Patch Dashboard
After=network.target

[Service]
Type=simple

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

systemd-analyze verify "$SERVICE_FILE"

print_pass "Created systemd service"
#
# Service Enablement
#

print_step "[13/15] Service Enablement"

systemctl daemon-reload

systemctl enable linux-patch-dashboard

systemctl restart linux-patch-dashboard

print_pass "Service enabled and restarted"

#
# Service Validation
#

print_step "[14/15] Service Validation"

SERVICE_STATUS=$(
systemctl is-active linux-patch-dashboard
)

if [ "$SERVICE_STATUS" = "active" ]
then

    print_pass "Dashboard service is running"

else

    print_fail "Dashboard service failed to start"

    systemctl status \
        linux-patch-dashboard \
        --no-pager

    exit 1

fi

#
# Bootstrap Validation
#

print_step "[15/15] Bootstrap Validation"

if bash "$INSTALL_DIR/bootstrap.sh"
then

    print_pass "Bootstrap validation completed"

else

    print_warn "Bootstrap validation reported issues"

fi

echo
echo "====================================="
echo " Installation Summary"
echo "====================================="
echo
echo "Service Account : $SERVICE_USER"
echo "Installation Dir: $CURRENT_DIR"
echo "Python Runtime  : $PYTHON_CMD"
echo "Dashboard URL   : $DASHBOARD_URL"
echo "Public Key File : $PUBLIC_KEY"
echo "Service Status  : $SERVICE_STATUS"
echo
echo "Installer completed successfully."
echo
