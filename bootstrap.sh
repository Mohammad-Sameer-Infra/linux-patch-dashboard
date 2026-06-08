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

step "[1/6] Python Validation"

if command -v python3 >/dev/null 2>&1
then

PYTHON_VERSION=$(python3 --version)

print_pass "$PYTHON_VERSION"

else

print_fail "Python3 not found, install Python3"

exit 1

fi

step "[2/6] Requirements Validation"

echo "Checking requirements file..."

if [ -f requirements.txt ]
then

print_pass "requirements.txt found"

else

print_fail "requirements.txt missing"

exit 1

fi

step "[3/6] Runtime Directory Setup"

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

step "[4/6] Inventory And Token Validation"

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

step "[5/6] Settings Validation"

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

echo "Checking linux-patch-dashboard.service"

if systemctl list-unit-files | grep -q linux-patch-dashboard.service
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

    print_pass "Virtual environment exists"

    VENV_OK=1

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
        echo "- Create virtual environment"
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
