# Linux Patch & Compliance Dashboard

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

---

# Architecture

```
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

No software agent runs continuously on managed nodes. The dashboard securely connects over SSH whenever telemetry is collected.

---

# Minimum Requirements

## Dashboard Server

| Component              | Minimum Requirement                    |
| ---------------------- | -------------------------------------- |
| Operating System       | Ubuntu 22.04+, Rocky Linux 8+, RHEL 8+ |
| Python                 | **Python 3.11 or newer**               |
| pip                    | Current supported version              |
| Git                    | Installed                              |
| OpenSSH Client         | Installed                              |
| ssh-keygen             | Installed                              |
| SQLite CLI (`sqlite3`) | Installed                              |

> **Important**
>
> The dashboard server requires **Python 3.11 or newer**.
>
> Modern Python dependencies (Flask, Werkzeug, Blinker, etc.) no longer support older Python versions such as Python 3.6 that ship by default with some enterprise Linux distributions.
>
> The bootstrap script validates the Python version during installation.

### Selecting the Python Interpreter

The dashboard does not require a specific Python minor release. Any supported version (3.11 or newer) may be used.

Examples:

```bash
python3 --version

python3 -m venv venv
```

or, if your distribution provides Python 3.12:

```bash
python3.12 --version

python3.12 -m venv venv
```

Use whichever interpreter satisfies the minimum supported version.

---

## Managed Nodes

Managed nodes require only:

* SSH server running.
* Network connectivity from the dashboard server.
* SSH user permitted to execute:

  * `apt list --upgradable`
  * `dnf check-update`
  * `yum check-update`

**Python is NOT required on managed nodes.**

No persistent agent is installed.

---

# Recommended Deployment Model

The recommended production deployment uses a dedicated non-login service account.

| Component              | Recommended Value                             |
| ---------------------- | --------------------------------------------- |
| Service Account        | `patchdashboard`                              |
| Service Account Home   | `/var/lib/patchdashboard`                     |
| Installation Directory | `/opt/linux-patch-dashboard`                  |
| Dashboard SSH Key      | `/var/lib/patchdashboard/.ssh/id_ed25519`     |
| Dashboard Public Key   | `/var/lib/patchdashboard/.ssh/id_ed25519.pub` |

Existing deployments using another Linux account continue to work, but this deployment model is recommended for new installations.

---

# Dashboard Server Installation

## Step 1: Install Prerequisites

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

Install Python 3.11+ if necessary.

Example:

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

## Step 2: Create the Dashboard Service Account

Create a dedicated non-login service account:

```bash
sudo useradd \
    --system \
    --home-dir /var/lib/patchdashboard \
    --create-home \
    --shell /sbin/nologin \
    patchdashboard
```

Verify:

```bash
getent passwd patchdashboard
```

---

## Step 3: Clone the Repository

```bash
cd /opt

sudo git clone \
    https://github.com/Mohammad-Sameer-Infra/linux-patch-dashboard.git
```

Set ownership:

```bash
sudo chown -R patchdashboard:patchdashboard \
    /opt/linux-patch-dashboard
```

---

## Step 4: Create the Python Virtual Environment

Switch to the service account:

```bash
sudo -u patchdashboard -s
```

Navigate to the installation directory:

```bash
cd /opt/linux-patch-dashboard
```

Create the virtual environment using any supported Python interpreter (Python 3.11 or newer).

Examples:

```bash
python3.11 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Upgrade packaging tools:

```bash
python -m pip install --upgrade pip setuptools wheel
```

Install project dependencies:

```bash
pip install -r requirements.txt
```

---

## Step 5: Generate the Dashboard SSH Key

Create the SSH directory:

```bash
mkdir -p /var/lib/patchdashboard/.ssh

chmod 700 /var/lib/patchdashboard/.ssh
```

Generate the dashboard SSH keypair:

```bash
ssh-keygen \
    -t ed25519 \
    -N "" \
    -f /var/lib/patchdashboard/.ssh/id_ed25519
```

This keypair is used by the dashboard to authenticate to managed nodes.

---

## Step 6: Configure Dashboard Settings

Copy the example configuration:

```bash
cp config/settings.example.json config/settings.json
```

Edit:

```
config/settings.json
```

Example:

```json
{
    "dashboard_url": "http://YOUR_SERVER_IP:5000",
    "inventory_file": "inventory/servers.json",
    "token_file": "security/registration_tokens.json",
    "public_key_file": "/var/lib/patchdashboard/.ssh/id_ed25519.pub",
    "dashboard_refresh_seconds": 30
}
```

Update:

* `dashboard_url`
* `public_key_file` (if using a custom location)

---

## Step 7: Run Bootstrap Validation

Execute:

```bash
./bootstrap.sh
```

Bootstrap validates:

* Python version.
* pip installation.
* requirements.txt.
* SQLite CLI.
* ssh-keygen.
* Inventory and security directories.
* Configuration files.
* Dashboard SSH public key.
* Virtual environment.
* Dashboard systemd service.

Bootstrap also recommends (but does not require) using the `patchdashboard` service account.

---

## Step 8: Test the Dashboard

Activate the virtual environment:

```bash
source venv/bin/activate
```

Run:

```bash
python run.py
```

Access:

```
http://<dashboard-server-ip>:5000
```

---

## Step 9: Install as a systemd Service

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
User=patchdashboard
Group=patchdashboard
WorkingDirectory=/opt/linux-patch-dashboard
ExecStart=/opt/linux-patch-dashboard/venv/bin/python /opt/linux-patch-dashboard/run.py
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

---

# Managed Node Registration

## Step 1: Generate a Registration Token

Open:

```
http://<dashboard-server-ip>:5000/generate-token
```

Copy the generated token.

---

## Step 2: Copy the Registration Script

Copy:

```
registration/register-node.sh
```

to the managed node.

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

The script prompts for:

* Dashboard URL.
* Registration token.

The script automatically detects:

* Hostname.
* Primary IP address.
* Current Linux user (`whoami`).
* SSH port.

No manual SSH user configuration is required.

The script:

1. Downloads the dashboard public key.
2. Installs it into `~/.ssh/authorized_keys`.
3. Registers the node with the dashboard.
4. Updates the dashboard inventory.

---

# Collecting Telemetry

Run manually:

```bash
source venv/bin/activate

python collector.py
```

Telemetry is collected from every active node in:

```
inventory/servers.json
```

Collected data is stored in:

```
telemetry.db
```

---

# Dashboard Pages

| URL                | Description                   |
| ------------------ | ----------------------------- |
| `/`                | Main dashboard                |
| `/history`         | Historical telemetry          |
| `/online`          | Online nodes                  |
| `/offline`         | Offline nodes                 |
| `/node/<hostname>` | Node details                  |
| `/generate-token`  | Registration token generation |

---

# Removing the Dashboard Service

If you no longer wish to run the Linux Patch & Compliance Dashboard, stop and remove the systemd service.

## Step 1: Stop the Service

```bash
sudo systemctl stop linux-patch-dashboard
```

## Step 2: Disable Automatic Startup

```bash
sudo systemctl disable linux-patch-dashboard
```

## Step 3: Remove the systemd Service File

```bash
sudo rm -f /etc/systemd/system/linux-patch-dashboard.service

sudo systemctl daemon-reload

sudo systemctl reset-failed
```

## Step 4: Remove the Application (Optional)

If you wish to completely remove the dashboard application:

```bash
sudo rm -rf /opt/linux-patch-dashboard
```

> **Note:** This permanently removes the application code, Python virtual environment, configuration files, inventory, registration tokens, and the SQLite telemetry database stored under the installation directory.

## Step 5: Remove the Dashboard Service Account (Optional)

If you deployed the dashboard using the recommended `patchdashboard` service account, remove it only after confirming that the dashboard is no longer required.

Remove the service account and its home directory:

```bash
sudo userdel -r patchdashboard
```

If the command reports that the user is currently in use, ensure the dashboard service has been stopped and all related processes have terminated before retrying.

## Step 6: Remove Dashboard SSH Access from Managed Nodes (Optional)

Removing the dashboard server does not automatically remove its SSH public key from managed nodes.

To revoke dashboard access, log in to each managed node and remove the dashboard public key from:

```text
~/.ssh/authorized_keys
```

This prevents any future SSH access using the dashboard keypair.

> **Important:** Removing the dashboard service does not modify or deregister managed nodes. Managed nodes can continue operating normally after the dashboard has been removed.

# De-registering a Managed Node

## Remove the Node from Monitoring

Delete the node entry from:

```
inventory/servers.json
```

or, in future versions, mark the node inactive.

The dashboard inventory is controlled entirely by `inventory/servers.json`.

## Remove Historical Telemetry (Optional)

Delete telemetry history:

```sql
DELETE FROM telemetry
WHERE hostname = '<hostname>';
```

This removes historical records but does not affect inventory.

## Remove Dashboard SSH Access (Optional)

On the managed node:

```bash
nano ~/.ssh/authorized_keys
```

Remove the dashboard public key entry.

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

## Verify Bootstrap Status

```bash
./bootstrap.sh
```

## Test SSH Connectivity

```bash
ssh <user>@<managed-node-ip> hostname
```

## Test Dashboard Public Key Endpoint

```bash
curl http://127.0.0.1:5000/public-key
```

## View Telemetry Database

List telemetry records:

```bash
sqlite3 telemetry.db

SELECT hostname,
       updates,
       security_updates,
       critical_packages,
       status
FROM telemetry;
```

## SELinux Considerations

On SELinux-enabled systems (Rocky Linux / RHEL), ensure the dashboard service account can:

* access the application directory,
* access the configured SSH public key,
* read/write the SQLite database.

If troubleshooting a new deployment, temporarily setting SELinux to permissive mode can help identify policy-related issues.

---

# Project Goal

The primary objective of this project is to provide a lightweight, agentless Linux patch visibility platform that enables administrators to quickly determine the patch status of their infrastructure from a single dashboard without logging into every individual server.

Current development is focused on **patch inventory and visibility**. Automated patch deployment and Ansible integration may be considered as future enhancements once the dashboard and registration workflow are fully stabilized.

