# Patchli — Linux Patch Dashboard

See which of your Linux servers need patches, from one web page, without logging in to each server.

Patchli connects to your servers over SSH, lists their pending package updates, highlights kernel, security and critical updates, and keeps a history. Nothing is installed on the servers you monitor: no agent, no Python.

---

## Contents

1. [How it works](#how-it-works)
2. [Requirements](#requirements)
3. [Install the dashboard](#install-the-dashboard)
4. [Add servers to monitor](#add-servers-to-monitor)
5. [Using the dashboard](#using-the-dashboard)
6. [Day-to-day administration](#day-to-day-administration)
7. [Configuration reference](#configuration-reference)
8. [Troubleshooting](#troubleshooting)
9. [Upgrading](#upgrading)
10. [Uninstalling](#uninstalling)
11. [Roadmap](#roadmap)

---

## How it works

```text
+-------------------------+          SSH (every 5 min)        +-------------------------+
|    Dashboard server     | --------------------------------> |      Managed node       |
|                         |                                   |                         |
|  Web dashboard (:5000)  |   runs: hostname, os-release,     |  Ubuntu / Debian        |
|  Background collector   |   uptime, apt / dnf / yum         |  Rocky / RHEL           |
|  SQLite history         |   update lists                    |  SSH server             |
|  Registration API       |                                   |  Dashboard's public key |
+-------------------------+                                   +-------------------------+
```

* The dashboard has its own SSH key. Each managed node trusts that key, added once during registration.
* Every 5 minutes the dashboard opens **one** SSH session per node (up to 10 nodes at a time), collects the update list and stores it.
* Web pages read the stored results, so they load instantly.
* Updates are classified as:

  | Category | How it is decided |
  | --- | --- |
  | **Total** | Every package with an available update |
  | **Kernel** | `linux-image*`, `linux-headers*` (Debian/Ubuntu) or `kernel*` (RHEL family) |
  | **Security** | Ubuntu/Debian: the update comes from the `-security` repository. RHEL family: the package appears in `dnf updateinfo --security` |
  | **Critical** | Kernel, OpenSSL, OpenSSH, sudo, systemd, glibc |

---

## Requirements

### Dashboard server

| | Requirement |
| --- | --- |
| Operating system | Ubuntu 22.04+, Debian 12+, Rocky Linux 8+, RHEL 8+ (with systemd) |
| Python | **3.11 or newer** (see below: older distributions need an extra package) |
| Packages | `git`, OpenSSH client (`ssh`, `ssh-keygen`) |
| Network | Internet access during install (Python packages come from PyPI). Inbound TCP **5000** from your browser and from managed nodes. Outbound SSH to managed nodes |
| Access | A user with `sudo` |

Which Python you get by default:

| Distribution | Default `python3` | What to install |
| --- | --- | --- |
| Ubuntu 24.04 | 3.12 ✅ | `python3 python3-venv` |
| Ubuntu 22.04 | 3.10 ❌ | `python3.11 python3.11-venv` |
| Debian 12 | 3.11 ✅ | `python3 python3-venv` |
| Rocky / RHEL 8 and 9 | 3.6 / 3.9 ❌ | `python3.12` |

You don't need to change the system's default `python3`. The installer finds `python3.11`, `python3.12` or `python3.13` by itself.

### Managed nodes (servers you want to monitor)

* Ubuntu / Debian (uses `apt`) or Rocky / RHEL / AlmaLinux / CentOS (uses `dnf` or `yum`).
* SSH server running, with key-based login allowed (the default).
* A normal user account that can log in over SSH. **No sudo needed**: listing available updates works without root.
* `curl` and `ssh-keygen`, both used once by the registration script (installed on most servers already).
* The node must be able to reach the dashboard on port 5000, and the dashboard must be able to reach the node on port 22.

---

## Install the dashboard

Run everything below **on the dashboard server**.

### Step 1: Install prerequisites

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

### Step 2: Download Patchli

```bash
sudo git clone https://github.com/Mohammad-Sameer-Infra/linux-patch-dashboard.git /opt/linux-patch-dashboard
cd /opt/linux-patch-dashboard
```

Install into `/opt/linux-patch-dashboard` as shown. The dashboard runs as a separate service account, which must be able to read this folder. A folder inside your home directory usually won't work.

### Step 3: Run the installer

```bash
sudo ./install.sh
```

The installer asks two questions:

1. **Dashboard URL**: the address managed nodes will use to reach the dashboard. Press Enter to accept the suggested `http://<this-server-ip>:5000`, or type another address.
2. **Admin password** (at least 8 characters, entered twice): this is how you log in to the dashboard, with the username `admin`.

It then:

* creates a service account `patchdashboard`, with home and data folder `/var/lib/patchdashboard`
* generates the dashboard's SSH key, `/var/lib/patchdashboard/.ssh/id_ed25519`
* creates `config/settings.json`
* creates a Python virtual environment in `venv/` and installs the dependencies
* installs, enables and starts the `linux-patch-dashboard` systemd service
* runs a health check. Every line should say `[PASS]` and end with `System ready.`

The installer is safe to run again at any time, for example to repair an installation. It never overwrites the SSH key, your settings or your data.

### Step 4: Open the firewall

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

### Step 5: Log in

Open `http://<dashboard-server-ip>:5000` in your browser. The browser asks for a username and password: enter `admin` and the password you chose in step 3.

The dashboard is empty until you add servers, which is the next section.

> **Security note:** the login is sent over plain HTTP. On an untrusted network, put the dashboard behind an HTTPS reverse proxy (for example nginx or Caddy) and allow port 5000 only from that proxy.

---

## Add servers to monitor

Repeat these steps for each server you want to monitor.

### Step 1: Create a registration token (in the browser)

In the dashboard, click **Add Node**. The page shows:

* a **registration token**: one-time use, create a new one for each server
* the **SSH key fingerprint** of the dashboard, which you will compare in step 3

Keep this page open.

### Step 2: Copy the registration script to the server

From the dashboard server (replace the user and address):

```bash
scp /opt/linux-patch-dashboard/registration/register-node.sh <user>@<node-ip>:~/
```

Or create the file on the node and paste the contents of `registration/register-node.sh` into it.

### Step 3: Run it on the server, as the user the dashboard should log in as

Log in to the node as a **normal user** (not root), for example `ubuntu` or `rocky`, then run:

```bash
chmod +x register-node.sh
./register-node.sh
```

The script:

1. Asks for the **dashboard URL** (for example `http://192.168.1.50:5000`) and the **token**.
2. Shows the hostname, IP address and user it detected.
3. Downloads the dashboard's public key and shows its fingerprint. **Type `y` only if it matches the fingerprint on the Add Node page.** If it doesn't, someone may be intercepting the connection.
4. Adds the key to `~/.ssh/authorized_keys`. Running the script again doesn't add it twice.
5. Registers the node. You should see:

   ```json
   {"message":"Node registered successfully","success":true}
   ```

**Check the detected IP address.** The script uses the server's first IP address, which on servers with several network interfaces (or Docker) may not be the one the dashboard can reach. The script also always registers SSH port 22. If either is wrong, fix them afterwards as described in [Editing a node's IP address or SSH port](#editing-a-nodes-ip-address-or-ssh-port).

### Step 4: Wait for the first collection, or collect now

A new node shows as **Pending** until the next collection, which can take up to 5 minutes. To collect immediately, run this on the dashboard server:

```bash
cd /opt/linux-patch-dashboard
sudo -u patchdashboard venv/bin/python collector.py
```

Each node is printed with its status, for example `web01: Online, 12 updates`. Refresh the dashboard to see the results.

---

## Using the dashboard

| Page | What it shows |
| --- | --- |
| **Dashboard** (`/`) | Node counts, the dashboard server's details and every managed node with its update count and status. Type in the search box to filter. Click a node for details |
| **Online / Offline** (`/online`, `/offline`) | Click the metric cards on the dashboard |
| **Node details** (`/node/<hostname>`) | Node information, when it was last seen online, and four cards: total, kernel, security and critical updates. Click a card to list the packages |
| **History** (`/history`) | The latest 500 collection results for all nodes |
| **Add Node** (`/generate-token`) | Creates a registration token. Each visit creates a new one |
| **Documentation** (`/documentation/`) | Built-in documentation |

Node statuses:

| Status | Meaning |
| --- | --- |
| **Online** | The last collection succeeded |
| **Offline** | The last collection could not connect or timed out. See [Troubleshooting](#troubleshooting) |
| **Pending** | Registered, not collected yet |

Pages reload themselves every 30 seconds. To log out, close the browser: HTTP Basic logins stay active until then.

---

## Day-to-day administration

Run these on the dashboard server, from `/opt/linux-patch-dashboard`.

| Task | Command |
| --- | --- |
| Check the installation | `sudo ./install.sh --check` |
| Uninstall | `sudo ./uninstall.sh` ([details](#uninstalling)) |
| Service status | `sudo systemctl status linux-patch-dashboard` |
| Restart | `sudo systemctl restart linux-patch-dashboard` |
| Follow the logs | `sudo journalctl -u linux-patch-dashboard -f` |
| Collect from all nodes now | `sudo -u patchdashboard venv/bin/python collector.py` |
| Test SSH to a node | `sudo -u patchdashboard ssh <user>@<node-ip> hostname` |

### Changing the admin password

```bash
cd /opt/linux-patch-dashboard
sudo venv/bin/python run.py set-password
sudo systemctl restart linux-patch-dashboard
```

### Editing a node's IP address or SSH port

Nodes are stored in `/var/lib/patchdashboard/servers.json`:

```json
[
    {
        "node_id": "8f0c…",
        "hostname": "web01",
        "ip": "192.168.1.10",
        "ssh_user": "ubuntu",
        "ssh_port": 22,
        "state": "active",
        "registered_at": "2026-09-24 10:00:00"
    }
]
```

Edit it with `sudo nano /var/lib/patchdashboard/servers.json`. Keep it valid JSON: commas between entries, none after the last one. No restart is needed; the change applies from the next collection.

### Removing a node

1. Delete its entry from `/var/lib/patchdashboard/servers.json`, as above. It disappears from the dashboard straight away. Its old results stay on the History page.
2. Optional: delete its history:

   ```bash
   sudo sqlite3 /var/lib/patchdashboard/telemetry.db "DELETE FROM telemetry WHERE hostname = '<hostname>';"
   ```

3. Optional: on the node, remove the dashboard's key (the line ending in `patchdashboard@…`) from `~/.ssh/authorized_keys`.

### Backups

Everything Patchli stores is in two places. Back these up:

* `/var/lib/patchdashboard/`: nodes, tokens, history and the dashboard's SSH key
* `/opt/linux-patch-dashboard/config/settings.json`: settings and the password hash

---

## Configuration reference

Settings live in `/opt/linux-patch-dashboard/config/settings.json`. The installer creates this file; you rarely need to edit it. Restart the service after changing it.

```json
{
    "dashboard_url": "http://192.168.1.50:5000",
    "data_dir": "/var/lib/patchdashboard",
    "public_key_file": "/var/lib/patchdashboard/.ssh/id_ed25519.pub",
    "admin_user": "admin",
    "admin_password_hash": "scrypt:…",
    "dashboard_refresh_seconds": 30,
    "collect_interval_seconds": 300
}
```

| Setting | Meaning | Default |
| --- | --- | --- |
| `dashboard_url` | Address shown by the installer for nodes to use | Set by the installer |
| `data_dir` | Folder for `servers.json`, `registration_tokens.json` and `telemetry.db` | `/var/lib/patchdashboard` |
| `public_key_file` | Dashboard public key handed out to nodes | `/var/lib/patchdashboard/.ssh/id_ed25519.pub` |
| `admin_user` | Dashboard login username | `admin` |
| `admin_password_hash` | Password hash. Set it with `run.py set-password`, never by hand | Set by the installer |
| `dashboard_refresh_seconds` | How often pages reload in the browser | `30` |
| `collect_interval_seconds` | How often all nodes are collected | `300` (5 minutes) |

The file is readable only by root and the service account, because it contains the password hash.

Every page requires the login except `/public-key` and `/api/register`. Nodes call these while registering, and registering still needs a valid one-time token.

---

## Troubleshooting

Start with the health check. It tells you what's wrong in most cases:

```bash
cd /opt/linux-patch-dashboard
sudo ./install.sh --check
```

### Dashboard

| Symptom | Cause and fix |
| --- | --- |
| Browser can't connect | Is the service running (`sudo systemctl status linux-patch-dashboard`)? Is port 5000 open ([Install step 4](#step-4-open-the-firewall))? |
| Page says "No admin password is set" | Run `sudo venv/bin/python run.py set-password`, then restart the service |
| Login prompt keeps coming back | Wrong username or password. The username is `admin` unless you changed `admin_user`. Reset the password as above |
| Service won't start | Check `sudo journalctl -u linux-patch-dashboard -n 50`. Usually a typo in `settings.json`: make sure it's valid JSON, or re-run `sudo ./install.sh` |
| Installer: "Python 3.11 or newer is required" | Install the Python package for your distribution ([Requirements](#dashboard-server)) and run the installer again |
| Installer fails during "Python environment" | The server can't reach PyPI (internet or proxy), or the `-venv` package is missing on Ubuntu/Debian |

### Registration

| Symptom | Cause and fix |
| --- | --- |
| "The dashboard did not return an SSH public key" | Wrong dashboard URL, dashboard down, or port 5000 blocked. Test from the node: `curl http://<dashboard-ip>:5000/public-key` |
| `curl: command not found` | Install curl on the node (`sudo apt install curl` or `sudo dnf install curl`) |
| "Invalid or used token" | Each token works once. Click **Add Node** for a new one |
| "Hostname already registered" / "IP already registered" | The node is already in the list. To re-register it, remove it first ([Removing a node](#removing-a-node)) |
| "Invalid hostname / IP address / SSH user" | The detected value contains unsupported characters. Check the output of `hostname`, `hostname -I` and `whoami` on the node |

### Nodes showing Offline

Test the exact connection the dashboard uses, from the dashboard server:

```bash
sudo -u patchdashboard ssh -p <port> <user>@<node-ip> hostname
```

| What you see | Cause and fix |
| --- | --- |
| It prints the hostname | SSH is fine. Wait for the next collection, or run `collector.py` |
| `Connection timed out` / `No route to host` | Wrong IP address, node down, or a firewall blocking port 22. Check the IP in `servers.json` |
| `Connection refused` | SSH isn't running on that port. Check `ssh_port` in `servers.json` |
| `Permission denied (publickey)` | The dashboard's key isn't in that user's `~/.ssh/authorized_keys` on the node. Re-run `register-node.sh` as that user, or add the output of `curl http://<dashboard-ip>:5000/public-key` to the file yourself |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | The node was rebuilt or its IP now belongs to another machine. If that's expected, remove the old host key: `sudo -u patchdashboard ssh-keygen -R <node-ip>` |

### Update counts

| Symptom | Cause and fix |
| --- | --- |
| Security count is always 0 on a RHEL-family node | That node's repositories don't publish security advisories (common with some mirrors and CentOS Stream). Totals and kernel counts are still correct |
| Counts look out of date | Pages show the last collection. Check "Last Updated" at the top of the dashboard, or collect now with `collector.py` |
| First collection of a RHEL-family node is slow | `dnf` downloads repository metadata the first time. Later collections are quicker |

---

## Upgrading

```bash
cd /opt/linux-patch-dashboard
sudo git pull
sudo ./install.sh
```

The installer updates the dependencies and restarts the service. Your nodes, history, SSH key and settings are kept.

**Upgrading from v1.1 or earlier:** the installer copies your existing `inventory/servers.json`, `security/registration_tokens.json` and `telemetry.db` into `/var/lib/patchdashboard/`, and asks you to set an admin password. The old files are left in place; delete them once you've checked the dashboard. The first time the dashboard connects to each existing node, it saves that node's SSH host key.

---

## Uninstalling

Both options below show what will be removed and ask you to type `yes` before changing anything.

### Remove the service, keep your data

```bash
cd /opt/linux-patch-dashboard
sudo ./uninstall.sh
```

This stops and removes the `linux-patch-dashboard` service and deletes the `venv/` folder. Your nodes, history, SSH key, settings and the `/opt/linux-patch-dashboard` folder are kept, so `sudo ./install.sh` brings everything back as it was.

### Remove everything

```bash
cd /opt/linux-patch-dashboard
sudo ./uninstall.sh --purge
```

This also:

1. Saves a backup of `/var/lib/patchdashboard` and `settings.json` to `/root/patchli-backup-<date>.tar.gz`. The file is readable only by root, because it contains the dashboard's private SSH key.
2. Permanently deletes `/var/lib/patchdashboard` (nodes, history, dashboard SSH key).
3. Deletes the `patchdashboard` service account.
4. Deletes `/opt/linux-patch-dashboard`.
5. Lists your managed nodes. On each one, remove the line ending in `patchdashboard@…` from that user's `~/.ssh/authorized_keys`.

| Option | Effect |
| --- | --- |
| `--purge` | Remove everything, as above |
| `--no-backup` | With `--purge`: don't save a backup |
| `--yes` | Don't ask for confirmation (for scripts) |
| `--help` | Show usage |

To restore from a backup: reinstall Patchli ([Install the dashboard](#install-the-dashboard)), stop the service, extract the backup with `sudo tar -xzf /root/patchli-backup-<date>.tar.gz -C /`, make the data folder owned by the service account with `sudo chown -R patchdashboard:patchdashboard /var/lib/patchdashboard`, then start the service again.

---

## Roadmap

**Done**

* v1.0: registration workflow, collection, online/offline monitoring, history
* v1.1: installer, virtual environment, service account, systemd service
* Next release (in progress): dashboard login, hardened registration and SSH, scheduled background collection, accurate security classification, one SSH session per node, built-in documentation, `uninstall.sh`, simpler codebase

**Planned**

* Node removal from the web interface, node retirement and history cleanup
* Ansible integration and patch orchestration
* Compliance reporting and trend analysis
* AI-assisted recommendations

---

## Project goal

Give administrators a lightweight, agentless way to see the patch status of their Linux servers from a single dashboard, without logging in to every server. The current focus is patch inventory and visibility; automation and compliance reporting come later.

Licensed under the Apache License 2.0. Maintained by Mohammad Sameer.
