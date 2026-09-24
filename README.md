# Linux Patch Dashboard

A lightweight, agentless, web-based dashboard for collecting and viewing Linux patch information across multiple servers without logging into each machine individually.

The dashboard securely connects to managed nodes over SSH, detects the operating system, gathers available package updates, classifies important updates, and presents the information through a simple web interface.

---

# Features

* Centralized Linux patch visibility.
* Agentless architecture (no daemon required on managed nodes).
* Supports:

  * Ubuntu / Debian
  * Rocky Linux / RHEL
* Secure SSH key-based communication (one SSH session per node per collection).
* Password-protected dashboard (HTTP Basic authentication).
* One-time node registration using tokens.
* Package classification:

  * Total Updates
  * Kernel Updates
  * Security Updates (from the Ubuntu/Debian security pocket or dnf/yum security advisories)
  * Critical Packages (kernel, OpenSSL, OpenSSH, sudo, systemd, glibc)
* Automatic background collection on a configurable interval.
* Historical telemetry storage using SQLite.
* Online / Offline node monitoring.
* Historical telemetry dashboard.
* Built-in documentation center.
* Automated installer with a built-in health check.
* Systemd service deployment.
* Dedicated runtime service account.

---

# Architecture

```text
+------------------------+             SSH              +------------------------+
|   Dashboard Server     | ---------------------------> |     Managed Node       |
|                        |                              |                        |
| Flask Web Application  |                              | Ubuntu / Debian        |
| Telemetry Collector    |                              | Rocky / RHEL           |
| SQLite Database        |                              | SSH Server             |
| Registration API       |                              | Dashboard Public Key   |
| Token Management       |                              | No Agent Required      |
+------------------------+                              +------------------------+
```

No software agent runs continuously on managed nodes.

The dashboard securely connects over SSH whenever telemetry is collected.

---

# Minimum Requirements

## Dashboard Server

| Component        | Requirement                            |
| ---------------- | -------------------------------------- |
| Operating System | Ubuntu 22.04+, Rocky Linux 8+, RHEL 8+ |
| Python           | Python 3.11 or newer                   |
| Git              | Installed                              |
| OpenSSH Client   | Installed                              |
| ssh-keygen       | Installed                              |
| SQLite CLI       | Installed                              |
| systemd          | Installed                              |

> The dashboard requires Python 3.11 or newer.

---

## Managed Nodes

Managed nodes require only:

* SSH server running.
* Network connectivity from dashboard server.
* SSH user capable of running:

  * apt list --upgradable
  * dnf check-update
  * yum check-update

Python is **not required** on managed nodes.

No persistent agent is installed.

---

# Recommended Deployment Model

| Component                  | Recommended Value                                 |
| -------------------------- | ------------------------------------------------- |
| Service Account            | patchdashboard                                    |
| Service Account Home       | /var/lib/patchdashboard                           |
| Installation Directory     | /opt/linux-patch-dashboard                        |
| Dashboard SSH Key          | /var/lib/patchdashboard/.ssh/id_ed25519           |
| Dashboard Public Key       | /var/lib/patchdashboard/.ssh/id_ed25519.pub       |
| Python Virtual Environment | /opt/linux-patch-dashboard/venv                   |
| Service File               | /etc/systemd/system/linux-patch-dashboard.service |
| Runtime User               | patchdashboard                                    |
| Service Manager            | systemd                                           |

---

# Ownership Model

The recommended deployment separates source-code ownership from runtime ownership.

| Purpose            | User                |
| ------------------ | ------------------- |
| Source Code        | Administrative User |
| Git Operations     | Administrative User |
| Dashboard Runtime  | patchdashboard      |
| Dashboard SSH Keys | patchdashboard      |
| Systemd Service    | patchdashboard      |

The installer intentionally does not modify ownership of the application source tree.

---

# Installation

## Step 1 - Install Prerequisites

### Ubuntu / Debian

```bash
sudo apt update

sudo apt install -y \
    git \
    openssh-client \
    sqlite3 \
    python3 \
    python3-venv \
    python3-pip
```

### Rocky Linux / RHEL

```bash
sudo dnf install -y \
    git \
    openssh-clients \
    sqlite \
    python3.12 \
    python3.12-pip
```

Verify:

```bash
python3 --version
```

---

## Step 2 - Clone Repository

```bash
cd /opt

sudo git clone \
    https://github.com/Mohammad-Sameer-Infra/linux-patch-dashboard.git
```

Optional:

```bash
sudo chown -R <admin-user>:<admin-user> \
    /opt/linux-patch-dashboard
```

---

## Step 3 - Run Installer (Recommended)

Execute:

```bash
cd /opt/linux-patch-dashboard

sudo ./install.sh
```

The installer automatically:

* Validates prerequisites.
* Detects Python 3.11+.
* Creates the patchdashboard service account.
* Creates dashboard SSH keys.
* Creates the data directory `/var/lib/patchdashboard` (inventory, tokens, telemetry database).
* Creates and updates settings.json.
* Creates the Python virtual environment.
* Installs Python dependencies.
* Asks for the dashboard admin password (first run only).
* Creates, enables and starts the systemd service.
* Runs the health check.

The installer is safe to run multiple times.

The installer never:

* Overwrites existing SSH keys.
* Silently overwrites dashboard configuration.
* Deletes telemetry data.
* Installs operating-system packages automatically.

---

# Installer Components

| Command                   | Purpose                                     |
| ------------------------- | ------------------------------------------- |
| sudo ./install.sh         | Install or repair dashboard deployment      |
| sudo ./install.sh --check | Check deployment health (changes nothing)   |
| uninstall.sh              | Safe dashboard removal                      |

The health check verifies the virtual environment's Python version, settings.json (dashboard URL and admin password), the dashboard public key and the systemd service.

To change the admin password later:

```bash
sudo venv/bin/python run.py set-password
sudo systemctl restart linux-patch-dashboard
```

---

## uninstall.sh

Used for safe dashboard removal.

Future releases may include:

* Data preservation options
* Service account cleanup
* Runtime cleanup automation

---

# Configuration

Configuration file:

```text
config/settings.json
```

Example:

```json
{
    "dashboard_url": "http://192.168.110.128:5000",
    "data_dir": "/var/lib/patchdashboard",
    "public_key_file": "/var/lib/patchdashboard/.ssh/id_ed25519.pub",
    "admin_user": "admin",
    "admin_password_hash": "<set by run.py set-password>",
    "dashboard_refresh_seconds": 30,
    "collect_interval_seconds": 300
}
```

| Setting                   | Meaning                                                        |
| ------------------------- | -------------------------------------------------------------- |
| data_dir                  | Holds servers.json, registration_tokens.json and telemetry.db  |
| admin_user                | Username for logging in to the dashboard                       |
| admin_password_hash       | Password hash, written by `run.py set-password`                |
| dashboard_refresh_seconds | How often dashboard pages reload in the browser                |
| collect_interval_seconds  | How often the dashboard collects from all nodes in background  |

Every page requires the admin login except `/public-key` and `/api/register`, which managed nodes call during registration (registration still needs a one-time token). The login is sent over plain HTTP unless you put the dashboard behind an HTTPS reverse proxy, which is recommended.

---

# Managed Node Registration

## Generate Registration Token

Open:

```text
http://<dashboard-server-ip>:5000/generate-token
```

Copy the generated token, and note the SSH key fingerprint shown under it.

---

## Copy Registration Script

Copy:

```text
registration/register-node.sh
```

to the managed node.

Make executable:

```bash
chmod +x register-node.sh
```

---

## Register Node

Execute:

```bash
./register-node.sh
```

The script prompts for:

* Dashboard URL
* Registration Token

The script automatically detects:

* Hostname
* Primary IP Address
* Current User
* SSH Port

The script:

1. Downloads the dashboard public key and shows its fingerprint.
2. Asks you to confirm it matches the fingerprint on the token page.
3. Adds the key to authorized_keys (once, even if run again).
4. Registers the node in the dashboard inventory.

No manual SSH-user configuration is required.

The first time the dashboard connects to a node it remembers the node's SSH host key. If a node is rebuilt and its host key changes, collection fails until you remove the old key on the dashboard server:

```bash
sudo -u patchdashboard ssh-keygen -R <managed-node-ip>
```

---

# Collecting Telemetry

The dashboard collects from every node in the background every `collect_interval_seconds` (5 minutes by default), checking up to 10 nodes in parallel. Pages show the latest collected data, so they load instantly.

To collect immediately:

```bash
sudo -u patchdashboard venv/bin/python collector.py
```

Nodes are read from `servers.json` and results are stored in `telemetry.db`, both in `data_dir`.

---

# Dashboard Pages

| URL              | Description                   |
| ---------------- | ----------------------------- |
| /                | Main Dashboard                |
| /history         | Historical Telemetry          |
| /online          | Online Nodes                  |
| /offline         | Offline Nodes                 |
| /node/<hostname> | Node Details                  |
| /generate-token  | Registration Token Generation |
| /documentation/  | Documentation Center          |

---

# Service Management

Check status:

```bash
sudo systemctl status linux-patch-dashboard
```

Restart:

```bash
sudo systemctl restart linux-patch-dashboard
```

View logs:

```bash
sudo journalctl -u linux-patch-dashboard.service -f
```

---

# De-registering a Managed Node

Remove the node from:

```text
/var/lib/patchdashboard/servers.json
```

Optional telemetry cleanup:

```sql
DELETE FROM telemetry
WHERE hostname = '<hostname>';
```

Optional SSH cleanup:

Remove dashboard public key from:

```text
~/.ssh/authorized_keys
```

on the managed node.

---

# Troubleshooting

## Validate Deployment

```bash
sudo ./install.sh --check
```

---

## Check Service

```bash
sudo systemctl status linux-patch-dashboard
```

---

## View Logs

```bash
sudo journalctl -u linux-patch-dashboard.service -f
```

---

## Test SSH Connectivity

Run it as the dashboard's service account, which owns the SSH key:

```bash
sudo -u patchdashboard ssh <user>@<managed-node-ip> hostname
```

---

## Test Public Key Endpoint

```bash
curl http://127.0.0.1:5000/public-key
```

---

## View Telemetry Database

```bash
sudo sqlite3 /var/lib/patchdashboard/telemetry.db
```

Example:

```sql
SELECT hostname,
       updates,
       security_updates,
       critical_packages,
       status
FROM telemetry;
```

---

# Project Status

## v1.0 - Completed

* Registration Workflow
* Telemetry Collection
* Online/Offline Monitoring
* Historical Telemetry
* Bootstrap Validation

---

## v1.1 - Completed

* install.sh
* bootstrap.sh
* Virtual Environment Management
* Dependency Management
* Service Account Deployment
* Systemd Service Deployment
* Service Validation
* Runtime Ownership Controls
* Installer-Based Deployment

---

## v1.2 - Planned

* Node Deregistration API
* Node Retirement Workflow
* Inventory Lifecycle Management
* Telemetry Cleanup Automation

---

## v2.0 - Planned

* Scheduled Telemetry Collection
* Ansible Integration
* Patch Orchestration
* Fleet Automation

---

## v3.0 - Planned

* Compliance Reporting
* Trend Analysis
* AI-Assisted Recommendations

---

# Project Goal

The primary objective of this project is to provide a lightweight, agentless Linux patch visibility platform that enables administrators to quickly determine the patch status of their infrastructure from a single dashboard without logging into every individual server.

Current development is focused on patch inventory and visibility.

Future enhancements may include automation, orchestration, compliance reporting, and AI-assisted operational insights.
