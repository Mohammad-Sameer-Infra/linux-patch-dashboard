#!/bin/bash

echo "Linux Patch Dashboard Registration"
echo

read -p "Enter dashboard URL: " DASHBOARD_URL

read -p "Enter registration token: " TOKEN

HOSTNAME=$(hostname)

IP=$(hostname -I | awk '{print $1}')

echo
echo "Installing dashboard SSH trust..."
echo

mkdir -p ~/.ssh

chmod 700 ~/.ssh

curl -s "$DASHBOARD_URL/public-key" >> ~/.ssh/authorized_keys

chmod 600 ~/.ssh/authorized_keys

echo
echo "Registering node..."
echo

curl -X POST "$DASHBOARD_URL/api/register" \
     -H "Content-Type: application/json" \
     -d "{
           \"hostname\": \"$HOSTNAME\",
           \"ip\": \"$IP\",
           \"token\": \"$TOKEN\"
         }"

echo
echo
echo "Node onboarding completed."
