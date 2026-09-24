# FAQ

## General

### Does Patchli install updates?

No. Patchli shows which updates are pending; you install them with your usual tools. Patch orchestration is on the [roadmap](roadmap.md).

### Do I need to install anything on my servers?

No agent and no Python. Registration adds one line to a user's `~/.ssh/authorized_keys`, and that's all. See [What registration changes on the node](adding-nodes.md#what-registration-changes-on-the-node).

### Which distributions are supported?

Anything using `apt` (Ubuntu, Debian) or `dnf`/`yum` (Rocky Linux, RHEL, AlmaLinux, CentOS, Oracle Linux) on managed nodes. The dashboard server itself needs Ubuntu 22.04+, Debian 12+, or Rocky/RHEL 8+. SUSE (`zypper`) and Arch (`pacman`) aren't supported yet.

### How many nodes can it handle?

It checks 10 nodes at a time, and a typical collection takes a few seconds per node, so a few hundred nodes fit comfortably within the default 5-minute interval. Pages load instantly at any size because they read stored results.

### Is it free?

Yes. Patchli Community edition is licensed under the Apache License 2.0.

## Access and security

### Why doesn't the dashboard need root on my servers?

Listing available updates (`apt list --upgradable`, `dnf check-update`, `dnf updateinfo`) works as a normal user. Patchli never changes anything on the nodes.

### Can I have multiple users or roles?

Not yet. There's one admin account. Put the dashboard behind a reverse proxy with your own authentication if you need more.

### Why can anyone read the documentation?

Like most products, the documentation is public so people can read it before installing and without an account. It contains no information about your servers. Everything that does (nodes, history, tokens) requires the login.

### How do I log out?

Close the browser. The browser remembers Basic authentication credentials until then.

### Is the connection encrypted?

The connections to nodes are SSH, so yes. The web interface is plain HTTP unless you add an HTTPS reverse proxy, which is recommended. See [Security](security.md#serve-the-dashboard-over-https).

## Data

### Why do my Ubuntu nodes show zero security updates?

Ubuntu installs security updates automatically every day, so they rarely wait. The dashboard is working correctly. See [Update classification](update-classification.md#debian-and-ubuntu).

### How often is data collected?

Every 5 minutes by default, and once when the service starts. Change it with `collect_interval_seconds` in the [configuration](configuration.md), or collect immediately with `collector.py`.

### How long is history kept?

Indefinitely. See [History size](administration.md#history-size) to prune it.

### Can I export the data?

The history is a standard SQLite database at `/var/lib/patchdashboard/telemetry.db`. Query it with `sqlite3` or any SQLite tool. See [Architecture](architecture.md#telemetrydb-collection-history) for the schema. For example, to export a CSV:

```bash
sudo sqlite3 -header -csv /var/lib/patchdashboard/telemetry.db \
  "SELECT hostname, status, updates, security_updates, kernel_updates, critical_packages, last_check FROM telemetry;" > patchli.csv
```

### Does the dashboard server monitor its own updates?

Not automatically. Register it as a node like any other server (you can use the same machine's IP address).

## Operations

### Can I run it without the installer, for testing?

Yes, on any machine with Python 3.11+:

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp config/settings.example.json config/settings.json
venv/bin/python run.py set-password
venv/bin/python run.py
```

Data goes into `data/` inside the folder. For production, use the installer, which adds the service account, SSH key and systemd service.

### Can I change the port?

Not through settings in this version; it listens on port 5000. To serve it on another port (such as 443), use a reverse proxy.
