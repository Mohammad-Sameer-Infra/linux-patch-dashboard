# Linux Patch & Compliance Dashboard

A lightweight web-based dashboard for collecting and viewing Linux patch information across multiple servers without logging into each machine individually.

The dashboard connects to managed nodes over SSH, detects the operating system, gathers available package updates, classifies important updates, and presents the information in a simple web interface.

---

# Features

* Centralized Linux patch visibility.
* Supports Debian/Ubuntu and Red Hat/Rocky Linux families.
* No agent required on managed nodes.
* Secure SSH key-based communication.
* One-time node registration using tokens.
* Package classification:

  * Total Updates
  * Kernel Updates
  * Security Updates
  * Critical Packages
* Historical telemetry storage using SQLite.
* Online/Offline node monitoring.
* Fleet-wide patch inventory from a single dashboard.

---

# Architecture

```
+----------------------+           SSH            +----------------------+
|  Dashboard Server    | -----------------------> |    Managed Node      |
|                      |                           |                      |
| Flask Web UI         |                           | Ubuntu / Debian      |
| Telemetry Collector  |                           | Rocky / RHEL         |
| SQLite Database      |                           | SSH Server           |
| Token Management     |                           | Dashboard Public Key |
+----------------------+                           +----------------------+
```

No software agent runs continuously on the managed nodes. The dashboard securely connects over SSH whenever telemetry is collected.

---

# Prerequisites

## Dashboard Server

* Linux server (Ubuntu 22.04+ recommended)
* Python 3.11 or later
* Git
* OpenSSH client
* SQLite3
* SSH key pair generated for dashboard access

## Managed Nodes

* SSH server running.
* Dashboard server can reach the node over the network.
* Python is **not required** on the managed node.
* SSH user with permission to execute:

  * `apt list --upgradable` (Debian/Ubuntu)
  * `dnf check-update` or `yum check-update` (RHEL/Rocky)

---

# Step 1: Clone the Repository

```bash
git clone https://github.com/Mohammad-Sameer-Infra/linux-patch-dashboard.git

cd linux-patch-dashboard
```

---

# Step 2: Create Python Virtual Environment

```bash
python3 -m venv venv

source venv/bin/activate
```

---

# Step 3: Install Dependencies

```bash
pip install --upgrade pip

pip install -r requirements.txt
```

---

# Step 4: Generate Dashboard SSH Key (First Time Only)

If an SSH key does not already exist:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519
```

Press Enter to accept the default location.

---

# Step 5: Configure Dashboard Settings

Edit:

```
config/settings.json
```

Example:

```json
{
    "inventory_file": "inventory/servers.json",
    "default_ssh_user": "vmadmin"
}
```

Adjust values as needed for your environment.

---

# Step 6: Start the Dashboard

For testing:

```bash
source venv/bin/activate

python3 run.py
```

Access the dashboard:

```
http://<dashboard-server-ip>:5000
```

---

# Step 7: Install as a Systemd Service (Recommended)

Example service file:

```
/etc/systemd/system/linux-patch-dashboard.service
```

```ini
[Unit]
Description=Linux Patch & Compliance Dashboard
After=network.target

[Service]
User=vmadmin
WorkingDirectory=/home/vmadmin/projects/linux-patch-dashboard
ExecStart=/home/vmadmin/projects/linux-patch-dashboard/venv/bin/python /home/vmadmin/projects/linux-patch-dashboard/run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload

sudo systemctl enable linux-patch-dashboard

sudo systemctl start linux-patch-dashboard
```

Verify:

```bash
systemctl status linux-patch-dashboard
```

---

# Managed Node Registration

## Step 1: Generate a Registration Token

Open the dashboard and browse to:

```
http://<dashboard-server-ip>:5000/generate-token
```

Copy the generated token.

---

## Step 2: Copy Registration Script

Copy the registration script to the managed node:

```
registration/register-node.sh
```

Make it executable:

```bash
chmod +x register-node.sh
```

---

## Step 3: Run Registration

Execute:

```bash
./register-node.sh
```

You will be prompted for:

* Dashboard URL
* Registration Token
* SSH Username (optional, press Enter for default)
* SSH Port (optional, press Enter for 22)

Example:

```
Enter dashboard URL: http://192.168.29.152:5000
Enter registration token: abc123xyz
Enter SSH username [vmadmin]:
Enter SSH port [22]:
```

The script will:

1. Detect the node hostname and IP.
2. Install the dashboard SSH public key.
3. Register the node with the dashboard.
4. Add the node to the inventory.

---

# Collecting Telemetry

Run manually:

```bash
source venv/bin/activate

python3 collector.py
```

Or configure a scheduled service/timer to collect telemetry periodically.

Example:

```bash
systemctl status telemetry-collector
```

---

# Dashboard Pages

| URL                | Description                 |
| ------------------ | --------------------------- |
| `/`                | Main dashboard              |
| `/history`         | Historical telemetry        |
| `/online`          | Online nodes                |
| `/offline`         | Offline nodes               |
| `/node/<hostname>` | Node details                |
| `/generate-token`  | Generate registration token |

---

# Deregistering a Managed Node

## Option 1: Disable Monitoring (Recommended)

Edit:

```
inventory/servers.json
```

Change:

```json
"state": "active"
```

to:

```json
"state": "inactive"
```

Future telemetry collections can ignore inactive nodes while preserving historical data.

## Option 2: Remove Node Completely

Delete the node entry from:

```
inventory/servers.json
```

Optionally remove historical telemetry:

```sql
DELETE FROM telemetry
WHERE hostname = '<hostname>';
```

---

# Removing Dashboard SSH Access

On the managed node:

```bash
nano ~/.ssh/authorized_keys
```

Remove the dashboard public key entry and save the file.

---

# Troubleshooting

## Dashboard Service Status

```bash
sudo systemctl status linux-patch-dashboard
```

## Dashboard Logs

```bash
sudo journalctl -u linux-patch-dashboard.service -f
```

## Telemetry Collector Logs

```bash
sudo journalctl -u telemetry-collector.service -f
```

## Test SSH Connectivity

```bash
ssh <user>@<managed-node-ip> hostname
```

## Test Package Detection

Ubuntu/Debian:

```bash
ssh <user>@<managed-node-ip> "apt list --upgradable"
```

Rocky/RHEL:

```bash
ssh <user>@<managed-node-ip> "dnf check-update"
```

---

# Project Goal

The primary objective of this project is to provide a simple, lightweight, and agentless Linux patch visibility platform that allows administrators to view pending updates across their infrastructure from a single dashboard without logging into every server individually.

