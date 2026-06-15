# Linux Patch & Compliance Dashboard

A lightweight, agentless, web-based dashboard for collecting and viewing Linux patch information across multiple servers without logging into each machine individually.

The dashboard connects to managed nodes over SSH, detects the operating system, gathers available package updates, classifies important updates, and presents the information in a simple web interface.

---

# Features

* Centralized Linux patch visibility.
* Supports Debian/Ubuntu and Red Hat/Rocky Linux families.
* No software agent required on managed nodes.
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
* Historical telemetry collection for trend analysis.

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

# Quick Start

## Dashboard Server

```bash
git clone https://github.com/Mohammad-Sameer-Infra/linux-patch-dashboard.git

cd linux-patch-dashboard

chmod +x bootstrap.sh

./bootstrap.sh

source venv/bin/activate

python3 run.py
```

Access the dashboard:

```
http://<dashboard-server-ip>:5000
```

## Managed Node

1. Generate a registration token.
2. Copy `registration/register-node.sh` to the managed node.
3. Run the registration script.
4. The node appears automatically in the dashboard inventory.

---

# Minimum Requirements

## Dashboard Server

| Component        | Minimum Requirement                    |
| ---------------- | -------------------------------------- |
| Operating System | Ubuntu 22.04+, Rocky Linux 8+, RHEL 8+ |
| Python           | **Python 3.11 or newer**               |
| pip              | Automatically upgraded by bootstrap    |
| Git              | Installed                              |
| OpenSSH Client   | Installed                              |
| SQLite3          | Installed                              |

> **Important**
>
> The dashboard server requires **Python 3.11 or newer**. Older Python versions (for example Python 3.6 included with Rocky Linux 8) are not supported because modern project dependencies no longer support end-of-life Python releases.
>
> The supplied `bootstrap.sh` script validates the Python version before installation begins.
>
> **Managed nodes do not require Python 3.11.**

## Managed Nodes

* SSH server running.
* Reachable from the dashboard server.
* Python is **not required**.
* SSH user with permission to execute:

  * `apt list --upgradable` (Ubuntu/Debian)
  * `dnf check-update` or `yum check-update` (Rocky/RHEL)

---

# Dashboard Server Installation

## Step 1: Clone Repository

```bash
git clone https://github.com/Mohammad-Sameer-Infra/linux-patch-dashboard.git

cd linux-patch-dashboard
```

## Step 2: Run Bootstrap

```bash
chmod +x bootstrap.sh

./bootstrap.sh
```

The bootstrap script automatically validates:

* Python version.
* Runtime directories.
* Configuration files.
* Inventory files.
* Registration token files.
* Virtual environment.
* Dashboard service status.

## Step 3: Generate Dashboard SSH Key (First Time Only)

If no SSH key exists:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519
```

Accept the default location.

## Step 4: Configure Dashboard Settings

Edit:

```
config/settings.json
```

Example:

```json
{
    "inventory_file": "inventory/servers.json",
    "default_ssh_user": "vmadmin",
    "public_key_file": "/home/vmadmin/.ssh/id_ed25519.pub"
}
```

Adjust values for your environment.

## Step 5: Test the Dashboard

```bash
source venv/bin/activate

python3 run.py
```

Browse to:

```
http://<dashboard-server-ip>:5000
```

---

# Installing the Dashboard as a Systemd Service

Create:

```
/etc/systemd/system/linux-patch-dashboard.service
```

Example:

```ini
[Unit]
Description=Linux Patch & Compliance Dashboard
After=network.target

[Service]
Type=simple
User=vmadmin
WorkingDirectory=/home/vmadmin/projects/linux-patch-dashboard
ExecStart=/home/vmadmin/projects/linux-patch-dashboard/venv/bin/python /home/vmadmin/projects/linux-patch-dashboard/run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Reload systemd:

```bash
sudo systemctl daemon-reload
```

Enable the service:

```bash
sudo systemctl enable linux-patch-dashboard
```

Start the service:

```bash
sudo systemctl start linux-patch-dashboard
```

Verify:

```bash
sudo systemctl status linux-patch-dashboard
```

View logs:

```bash
sudo journalctl -u linux-patch-dashboard.service -f
```

---

# Managed Node Registration

## Step 1: Generate Registration Token

Open:

```
http://<dashboard-server-ip>:5000/generate-token
```

Copy the generated token.

## Step 2: Copy Registration Script

Copy:

```
registration/register-node.sh
```

to the managed node.

Make it executable:

```bash
chmod +x register-node.sh
```

## Step 3: Run Registration

```bash
./register-node.sh
```

Provide:

* Dashboard URL.
* Registration Token.
* SSH Username (optional).
* SSH Port (optional).

Example:

```
Enter dashboard URL: http://192.168.29.152:5000
Enter registration token: abc123xyz
Enter SSH username [vmadmin]:
Enter SSH port [22]:
```

The script automatically:

1. Detects hostname and IP.
2. Installs the dashboard SSH public key.
3. Registers the node.
4. Updates the dashboard inventory.

---

# Collecting Telemetry

Run manually:

```bash
source venv/bin/activate

python3 collector.py
```

Or configure the telemetry collector service and timer.

Verify:

```bash
systemctl status telemetry-collector.service

systemctl status telemetry-collector.timer
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

# Removing a Managed Node

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

## Option 2: Remove Completely

Delete the node entry from:

```
inventory/servers.json
```

Optionally remove historical telemetry:

```sql
DELETE FROM telemetry
WHERE hostname = '<hostname>';
```

## Remove Dashboard SSH Access

On the managed node:

```bash
nano ~/.ssh/authorized_keys
```

Remove the dashboard public key.

---

# Removing the Dashboard Service

Stop the service:

```bash
sudo systemctl stop linux-patch-dashboard
```

Disable automatic startup:

```bash
sudo systemctl disable linux-patch-dashboard
```

Remove the service file:

```bash
sudo rm -f /etc/systemd/system/linux-patch-dashboard.service
```

Reload systemd:

```bash
sudo systemctl daemon-reload
```

Verify removal:

```bash
systemctl list-unit-files | grep linux-patch-dashboard
```

---

# Troubleshooting

## Check Dashboard Service

```bash
sudo systemctl status linux-patch-dashboard
```

## View Dashboard Logs

```bash
sudo journalctl -u linux-patch-dashboard.service -f
```

## View Collector Logs

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

## Validate Inventory JSON

```bash
python3 -m json.tool inventory/servers.json
```

## Validate Registration Token File

```bash
python3 -m json.tool security/registration_tokens.json
```

---

# First-Time Deployment Checklist

## Dashboard Server

* [ ] Python 3.11+ installed.
* [ ] Repository cloned.
* [ ] `./bootstrap.sh` completed successfully.
* [ ] SSH key generated.
* [ ] `config/settings.json` configured.
* [ ] Dashboard starts successfully.
* [ ] `linux-patch-dashboard.service` enabled and running.

## Managed Node

* [ ] SSH server enabled.
* [ ] Dashboard public key installed.
* [ ] Registration completed successfully.
* [ ] Node visible in dashboard.

---

# Project Goal

The primary objective of this project is to provide a simple, lightweight, secure, and agentless Linux patch visibility platform that allows administrators to view pending updates across their infrastructure from a single dashboard without logging into every server individually.

The current focus is **patch visibility and inventory management**. Patch execution through automation platforms such as Ansible can be integrated later as an optional capability.

