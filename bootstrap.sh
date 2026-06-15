#!/bin/bash

RECOMMENDATIONS=0

VENV_OK=0
SERVICE_INSTALLED=0
SERVICE_RUNNING=0
SETTINGS_OK=0
PUBLIC_KEY_OK=0

step() {

echo
echo "====================================="
echo "$1"
echo "====================================="
echo

sleep 1

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

echo
echo "====================================="
echo " Linux Patch Dashboard Bootstrap"
echo "====================================="
echo

step "[1/7] Python Validation"

echo "Checking python installation..."

if ! command -v python3 >/dev/null 2>&1
then

    print_fail "python3 is not installed"

    echo
    echo "Please install Python 3.11 or newer."
    exit 1

fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")

echo "Detected Python version: ${PYTHON_VERSION}"

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)'
then

    echo

    print_fail "Unsupported Python version"

    echo
    echo "Required : Python 3.11 or newer"
    echo "Detected : ${PYTHON_VERSION}"
    echo
    echo "The dashboard server requires Python 3.11+."
    echo "Managed nodes do NOT require Python 3.11."
    echo
    echo "Ubuntu:"
    echo "  sudo apt update"
    echo "  sudo apt install -y python3.11 python3.11-venv python3-pip"
    echo
    echo "Rocky / RHEL:"
    echo "  sudo dnf install -y python3.11 python3.11-pip"
    echo
    echo "After installing Python 3.11:"
    echo "  rm -rf venv"
    echo "  python3.11 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  python -m pip install --upgrade pip setuptools wheel"
    echo

    exit 1

fi

print_pass "Python ${PYTHON_VERSION}"

echo

echo "Checking pip installation..."

PIP_VERSION=$(python3 -m pip --version | awk '{print $2}')

print_pass "pip ${PIP_VERSION}"

step "[2/7] Requirements Validation"

echo "Checking requirements file..."

if [ -f requirements.txt ]
then

    print_pass "requirements.txt found"

else

    print_fail "requirements.txt missing"

    exit 1

fi

step "[3/7] Runtime Directory Setup"

echo "Checking inventory directory..."

mkdir -p inventory

print_pass "inventory directory ready"

echo

echo "Checking security directory..."

mkdir -p security

print_pass "security directory ready"

echo

echo "Checking config directory..."

mkdir -p config

print_pass "config directory ready"

step "[4/7] Inventory And Token Validation"

echo "Checking inventory file..."

if [ ! -f inventory/servers.json ]
then

    cp inventory/servers.example.json \
       inventory/servers.json

    print_pass "Created inventory/servers.json"

else

    print_pass "inventory/servers.json already exists"

fi

echo

echo "Validating inventory JSON..."

python3 -m json.tool inventory/servers.json >/dev/null 2>&1

if [ $? -eq 0 ]
then

    print_pass "inventory JSON valid"

else

    print_fail "inventory JSON invalid"

fi

echo

echo "Checking registration token file..."

if [ ! -f security/registration_tokens.json ]
then

    cp security/registration_tokens.example.json \
       security/registration_tokens.json

    print_pass \
    "Created security/registration_tokens.json"

else

    print_pass \
    "security/registration_tokens.json already exists"

fi

echo

echo "Validating registration token JSON..."

python3 -m json.tool security/registration_tokens.json >/dev/null 2>&1

if [ $? -eq 0 ]
then

    print_pass "registration token JSON valid"

else

    print_fail "registration token JSON invalid"

fi

step "[5/7] Settings Validation"

echo "Checking settings file..."

if [ ! -f config/settings.json ]
then

    cp config/settings.example.json \
       config/settings.json

    print_pass "Created config/settings.json"

else

    print_pass "config/settings.json already exists"

fi

echo

echo "Checking dashboard URL..."

grep -q "YOUR_SERVER_IP" config/settings.json

if [ $? -eq 0 ]
then

    print_warn \
    "Dashboard URL still uses placeholder"

else

    print_pass \
    "Dashboard URL configured"

    SETTINGS_OK=1

fi

echo

echo "Checking public key configuration..."

PUBLIC_KEY=$(python3 -c "import json; print(json.load(open('config/settings.json'))['public_key_file'])")

if [ -f "$PUBLIC_KEY" ]
then

    print_pass "Public key found: $PUBLIC_KEY"

    PUBLIC_KEY_OK=1

else

    print_warn "Public key not found: $PUBLIC_KEY"

    RECOMMENDATIONS=1

fi

echo

echo "Checking linux-patch-dashboard.service..."

if systemctl list-unit-files | grep -q "^linux-patch-dashboard.service"
then

    print_pass \
    "linux-patch-dashboard.service detected"

else

    print_warn \
    "linux-patch-dashboard.service not installed"

fi

step "[6/7] Runtime Validation"

echo "Checking virtual environment..."

if [ -d venv ]
then

    VENV_PYTHON_VERSION=$(./venv/bin/python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)

    if ./venv/bin/python -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null
    then

        print_pass "Virtual environment exists (Python ${VENV_PYTHON_VERSION})"

        VENV_OK=1

    else

        print_warn "Virtual environment uses unsupported Python version (${VENV_PYTHON_VERSION})"

        RECOMMENDATIONS=1

    fi

else

    print_warn "Virtual environment missing"

    RECOMMENDATIONS=1

fi

echo

echo "Checking service installation..."

if systemctl list-unit-files | grep -q "^linux-patch-dashboard.service"
then

    print_pass "linux-patch-dashboard.service installed"

    SERVICE_INSTALLED=1

else

    print_warn "linux-patch-dashboard.service not installed"

    RECOMMENDATIONS=1

fi

echo

echo "Checking service status..."

if systemctl is-active --quiet linux-patch-dashboard
then

    print_pass "linux-patch-dashboard.service running"

    SERVICE_RUNNING=1

else

    print_warn "linux-patch-dashboard.service stopped"

    RECOMMENDATIONS=1

fi

step "[7/7] System Readiness Summary"

echo
echo "====================================="
echo " Overall Status"
echo "====================================="
echo

if [ $RECOMMENDATIONS -eq 0 ]
then

    print_pass "System Ready"

else

    print_warn "Action Required"

    echo
    echo "Recommended Actions:"
    echo

    if [ $SETTINGS_OK -eq 0 ]
    then
        echo "- Configure dashboard URL in config/settings.json"
    fi

    if [ $PUBLIC_KEY_OK -eq 0 ]
    then
        echo "- Configure a valid public key path"
    fi

    if [ $VENV_OK -eq 0 ]
    then
        echo "- Create or recreate the virtual environment using Python 3.11+"
    fi

    if [ $SERVICE_INSTALLED -eq 0 ]
    then
        echo "- Install linux-patch-dashboard.service"
    fi

    if [ $SERVICE_RUNNING -eq 0 ]
    then
        echo "- Start linux-patch-dashboard.service"
    fi

fi

echo
echo "====================================="
echo " Bootstrap Completed"
echo "====================================="
echo
