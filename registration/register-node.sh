#!/bin/bash
# Register this machine with the Linux Patch Dashboard.
set -euo pipefail

echo "Linux Patch Dashboard Registration"
echo

read -rp "Enter dashboard URL: " DASHBOARD_URL
read -rp "Enter registration token: " TOKEN
DASHBOARD_URL="${DASHBOARD_URL%/}"

HOSTNAME=$(hostname)
IP=$(hostname -I | awk '{print $1}')
SSH_USER=$(whoami)
SSH_PORT=22

echo
echo "Detected hostname : $HOSTNAME"
echo "Detected IP       : $IP"
echo "Detected SSH User : $SSH_USER"
echo

KEY=$(curl -fsS "$DASHBOARD_URL/public-key")
case "$KEY" in
    ssh-*) ;;
    *) echo "The dashboard did not return an SSH public key. Aborting."; exit 1 ;;
esac

# Over plain HTTP someone could swap the key, so let the admin compare it
# with the fingerprint shown on the dashboard's token page.
echo "Dashboard SSH key fingerprint:"
echo "$KEY" | ssh-keygen -lf -
read -rp "Does this match the fingerprint on the dashboard? [y/N]: " CONFIRM
[[ "$CONFIRM" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }

mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
if grep -qxF "$KEY" ~/.ssh/authorized_keys; then
    echo "Dashboard key already trusted."
else
    echo "$KEY" >> ~/.ssh/authorized_keys
    echo "Dashboard key added to ~/.ssh/authorized_keys."
fi

echo
echo "Registering node..."
curl -sS -X POST "$DASHBOARD_URL/api/register" \
     -H "Content-Type: application/json" \
     -d "{\"hostname\": \"$HOSTNAME\", \"ip\": \"$IP\", \"ssh_user\": \"$SSH_USER\", \"ssh_port\": $SSH_PORT, \"token\": \"$TOKEN\"}"
echo
