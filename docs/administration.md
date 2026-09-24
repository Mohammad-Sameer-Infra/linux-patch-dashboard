# Day-to-day administration

Run these commands on the dashboard server from the installation folder:

```bash
cd /opt/linux-patch-dashboard
```

## Quick reference

| Task | Command |
| --- | --- |
| Check the installation | `sudo ./install.sh --check` |
| Service status | `sudo systemctl status linux-patch-dashboard` |
| Restart the dashboard | `sudo systemctl restart linux-patch-dashboard` |
| Follow the logs | `sudo journalctl -u linux-patch-dashboard -f` |
| Collect from all nodes now | `sudo -u patchdashboard venv/bin/python collector.py` |
| Test SSH to a node | `sudo -u patchdashboard ssh -p <port> <user>@<node-ip> hostname` |
| Change the admin password | `sudo venv/bin/python run.py set-password` |
| Upgrade | see [Upgrading](upgrading.md) |
| Uninstall | `sudo ./uninstall.sh` (see [Uninstalling](upgrading.md#uninstalling)) |

## The service

Patchli runs as the systemd service `linux-patch-dashboard`, under the `patchdashboard` account. One process serves the web interface on port 5000 and runs the background collector. It starts at boot and restarts automatically if it crashes.

```bash
sudo systemctl status linux-patch-dashboard     # is it running?
sudo systemctl restart linux-patch-dashboard    # after changing settings or upgrading
sudo systemctl stop linux-patch-dashboard       # stop until the next start or reboot
sudo journalctl -u linux-patch-dashboard -n 100 # last 100 log lines
```

The log shows web requests and any collection errors.

## Collecting now

The dashboard collects from every node every `collect_interval_seconds` (5 minutes by default), starting as soon as the service starts. To collect immediately, for example right after patching a server:

```bash
sudo -u patchdashboard venv/bin/python collector.py
```

Run it as `patchdashboard`: that account owns the SSH key and the data files.

## Changing the admin password

```bash
sudo venv/bin/python run.py set-password
sudo systemctl restart linux-patch-dashboard
```

The password must be at least 8 characters. Only a hash is stored, in `config/settings.json`.

### Forgotten password

Run the same two commands; setting a new password doesn't need the old one.

### Changing the admin username

Edit `admin_user` in `config/settings.json`, then restart the service:

```bash
sudo nano config/settings.json
sudo systemctl restart linux-patch-dashboard
```

## Managing nodes

Nodes are stored in `/var/lib/patchdashboard/servers.json`:

```json
[
    {
        "node_id": "5d30ac8a-f17b-44a2-b828-738f5a12fb32",
        "hostname": "web01",
        "ip": "192.168.1.10",
        "ssh_user": "ubuntu",
        "ssh_port": 22,
        "state": "active",
        "registered_at": "2026-09-24 10:00:00"
    }
]
```

Edit it with:

```bash
sudo nano /var/lib/patchdashboard/servers.json
```

Keep it valid JSON: commas between entries and none after the last one. You can check it with `python3 -m json.tool /var/lib/patchdashboard/servers.json`. Changes apply from the next collection; no restart is needed.

### Edit a node's IP address or SSH port

Change `ip` or `ssh_port` in the node's entry. This is needed when the registration script detected the wrong IP address, or the node's SSH server uses a port other than 22.

If you change the IP address, the dashboard stores the node's SSH host key again on the next connection.

### Remove a node

1. Delete the node's entry from `servers.json`. It disappears from the dashboard immediately; its past results remain on the History page.
2. Optional: delete its history.

   ```bash
   sudo sqlite3 /var/lib/patchdashboard/telemetry.db "DELETE FROM telemetry WHERE hostname = '<hostname>';"
   ```

3. Optional: on the node, remove the dashboard's key (the line ending in `patchdashboard@…`) from `~/.ssh/authorized_keys` of the registered user.

### Re-register a node

The dashboard rejects a registration whose hostname or IP address is already in the inventory. Remove the node (step 1 above), create a new token and run `register-node.sh` again.

## Registration tokens

Tokens are stored in `/var/lib/patchdashboard/registration_tokens.json`. Each token works once and is marked `"used": true` after a successful registration. Unused tokens don't expire; to revoke them, delete their entries from the file.

## Backups

Everything Patchli stores is in two places:

| Path | Contains |
| --- | --- |
| `/var/lib/patchdashboard/` | Nodes, tokens, history and the dashboard's SSH key |
| `/opt/linux-patch-dashboard/config/settings.json` | Settings and the admin password hash |

A simple backup:

```bash
sudo tar -czf /root/patchli-backup-$(date +%F).tar.gz /var/lib/patchdashboard /opt/linux-patch-dashboard/config/settings.json
```

The archive contains the dashboard's **private SSH key**, which can log in to every managed node. Store it as securely as the server itself.

To restore, see [Restoring from a backup](upgrading.md#restoring-from-a-backup).

## History size

Each collection stores one row per node, including its package list (a few KB). With 50 nodes collected every 5 minutes, expect roughly 50–150 MB per month. To keep the last 180 days only:

```bash
sudo systemctl stop linux-patch-dashboard
sudo sqlite3 /var/lib/patchdashboard/telemetry.db "DELETE FROM telemetry WHERE last_check < date('now', '-180 days'); VACUUM;"
sudo systemctl start linux-patch-dashboard
```

To collect less often, raise `collect_interval_seconds` in the [configuration](configuration.md).
