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
* Secure SSH key-based communication.
* One-time node registration using tokens.
* Package classification:

  * Total Updates
  * Kernel Updates
  * Security Updates
  * Critical Packages
* Historical telemetry storage using SQLite.
* Online / Offline node monitoring.
* Historical telemetry dashboard.
* Fleet-wide patch inventory from a single interface.
* Automated installer.
* Bootstrap validation framework.
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
* Creates and updates settings.json.
* Creates the Python virtual environment.
* Installs Python dependencies.
* Creates the systemd service.
* Enables the service.
* Starts the service.
* Executes bootstrap validation.

The installer is safe to run multiple times.

The installer never:

* Overwrites existing SSH keys.
* Silently overwrites dashboard configuration.
* Deletes telemetry data.
* Installs operating-system packages automatically.

---

# Installer Components

| Script       | Purpose                                |
| ------------ | -------------------------------------- |
| install.sh   | Install or repair dashboard deployment |
| bootstrap.sh | Validate deployment health             |
| uninstall.sh | Safe dashboard removal                 |

---

## install.sh

Responsibilities:

* Service account creation
* SSH key management
* Configuration management
* Virtual environment creation
* Dependency installation
* Systemd service deployment
* Runtime validation
* Bootstrap execution

---

## bootstrap.sh

Validation only.

The bootstrap script never modifies the system.

It validates:

* Python version
* pip
* requirements.txt
* sqlite3
* ssh-keygen
* Inventory configuration
* Registration token database
* settings.json
* Dashboard public key
* Virtual environment
* Systemd service installation
* Systemd service health

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
    "inventory_file": "inventory/servers.json",
    "token_file": "security/registration_tokens.json",
    "public_key_file": "/var/lib/patchdashboard/.ssh/id_ed25519.pub",
    "dashboard_refresh_seconds": 30
}
```

---

# Managed Node Registration

## Generate Registration Token

Open:

```text
http://<dashboard-server-ip>:5000/generate-token
```

Copy the generated token.

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

1. Downloads dashboard public key.
2. Updates authorized_keys.
3. Registers node.
4. Updates dashboard inventory.

No manual SSH-user configuration is required.

---

# Collecting Telemetry

Manual collection:

```bash
source venv/bin/activate

python collector.py
```

Telemetry is collected from:

```text
inventory/servers.json
```

Results are stored in:

```text
telemetry.db
```

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
inventory/servers.json
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
./bootstrap.sh
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

```bash
ssh <user>@<managed-node-ip> hostname
```

---

## Test Public Key Endpoint

```bash
curl http://127.0.0.1:5000/public-key
```

---

## View Telemetry Database

```bash
sqlite3 telemetry.db
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
