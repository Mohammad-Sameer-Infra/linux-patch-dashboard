# Installation

This guide installs Patchli on the **dashboard server**. It takes about five minutes. Run every command on the dashboard server as a user with `sudo`.

## Step 1: Install prerequisites

Pick your distribution. Not sure which Python you need? See [Requirements](requirements.md#python-version-by-distribution).

**Ubuntu 24.04 / Debian 12**

```bash
sudo apt update
sudo apt install -y git openssh-client python3 python3-venv
```

**Ubuntu 22.04**

```bash
sudo apt update
sudo apt install -y git openssh-client python3.11 python3.11-venv
```

**Rocky Linux / RHEL 8 or 9**

```bash
sudo dnf install -y git openssh-clients python3.12
```

Optional, for inspecting the history database by hand: `sqlite3` (Ubuntu/Debian) or `sqlite` (Rocky/RHEL).

## Step 2: Download Patchli

```bash
sudo git clone https://github.com/Mohammad-Sameer-Infra/linux-patch-dashboard.git /opt/linux-patch-dashboard
cd /opt/linux-patch-dashboard
```

> **Install into `/opt/linux-patch-dashboard`.** The dashboard runs as a separate service account that must be able to read this folder. A folder inside your home directory usually isn't readable by other users.

## Step 3: Run the installer

```bash
sudo ./install.sh
```

The installer asks two questions:

1. **Dashboard URL**: the address managed nodes will use to reach the dashboard. Press Enter to accept the suggested `http://<this-server-ip>:5000`, or type another address (for example a DNS name).
2. **Admin password**: at least 8 characters, entered twice. You log in to the dashboard with the username `admin` and this password.

Then it sets everything up:

| Step | What it does |
| --- | --- |
| Prerequisites | Checks for `python3`, `ssh`, `ssh-keygen` and `systemctl`, and picks Python 3.11+ |
| Service account | Creates the system user `patchdashboard` with home `/var/lib/patchdashboard` |
| SSH key | Generates `/var/lib/patchdashboard/.ssh/id_ed25519` (never overwritten if it exists) |
| Settings | Creates `config/settings.json` and sets the dashboard URL, key path and data folder |
| Data | Creates `/var/lib/patchdashboard` for the inventory, tokens and history; copies data from older versions |
| Python | Creates `venv/` and installs the dependencies from `requirements.txt` |
| Password | Asks for the admin password (first run only) |
| Service | Installs, enables and starts the `linux-patch-dashboard` systemd service |
| Health check | Runs `install.sh --check` |

A successful run ends with the health check:

```text
== Check
[PASS] Virtual environment uses Python 3.11+
[PASS] settings.json exists
[PASS] Dashboard URL configured
[PASS] Admin password set
[PASS] Dashboard public key found
[PASS] linux-patch-dashboard is running
System ready.

Dashboard: http://192.168.1.50:5000
```

The installer is **safe to run again** at any time, for example to repair an installation or after an upgrade. It never overwrites the SSH key, your settings or your data.

## Step 4: Open the firewall

Skip this step if the server has no firewall enabled.

**Ubuntu / Debian (ufw)**

```bash
sudo ufw allow 5000/tcp
```

**Rocky / RHEL (firewalld)**

```bash
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

## Step 5: Log in

Open `http://<dashboard-server-ip>:5000` in your browser. The browser asks for a username and password: enter `admin` and the password you chose in step 3.

The dashboard is empty until you add nodes. The documentation, which you're reading now, is available at `/documentation/` without logging in.

> **Security:** the login is sent over plain HTTP. On an untrusted network, put the dashboard behind an HTTPS reverse proxy. See [Security](security.md#serve-the-dashboard-over-https).

## Next step

[Add your first node](adding-nodes.md).
