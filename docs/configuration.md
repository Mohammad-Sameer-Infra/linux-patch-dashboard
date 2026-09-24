# Configuration reference

Patchli's settings live in one JSON file:

```text
/opt/linux-patch-dashboard/config/settings.json
```

The installer creates and maintains it, so you rarely need to edit it. After editing, **restart the service**:

```bash
sudo nano /opt/linux-patch-dashboard/config/settings.json
sudo systemctl restart linux-patch-dashboard
```

## Example

```json
{
    "dashboard_url": "http://192.168.1.50:5000",
    "data_dir": "/var/lib/patchdashboard",
    "public_key_file": "/var/lib/patchdashboard/.ssh/id_ed25519.pub",
    "admin_user": "admin",
    "admin_password_hash": "scrypt:32768:8:1$…",
    "dashboard_refresh_seconds": 30,
    "collect_interval_seconds": 300
}
```

## Settings

### `dashboard_url`

The address managed nodes use to reach the dashboard, for example `http://192.168.1.50:5000` or `https://patchli.example.com`. The installer asks for it and shows it at the end. Operators type it into `register-node.sh`; it isn't used anywhere else.

**Default:** set by the installer.

### `data_dir`

The folder holding the runtime data:

| File | Contents |
| --- | --- |
| `servers.json` | Registered nodes (the inventory) |
| `registration_tokens.json` | Registration tokens |
| `telemetry.db` | Collection history (SQLite) |

A relative path is resolved against the installation folder. The service account must be able to write to this folder.

**Default:** `/var/lib/patchdashboard` (installer); `data` inside the installation folder when running without the installer.

### `public_key_file`

The dashboard's SSH public key, served at `/public-key` for registration and shown as a fingerprint on the Add node page. The matching private key (the same path without `.pub`) is what the collector logs in with; `ssh` finds it automatically in the service account's `~/.ssh`.

**Default:** `/var/lib/patchdashboard/.ssh/id_ed25519.pub`

### `admin_user`

The username for logging in to the dashboard.

**Default:** `admin`

### `admin_password_hash`

The hash of the admin password. **Don't edit it by hand**; set it with:

```bash
sudo /opt/linux-patch-dashboard/venv/bin/python /opt/linux-patch-dashboard/run.py set-password
```

If it's missing, every dashboard page shows *No admin password is set* until you set one.

**Default:** set by the installer.

### `dashboard_refresh_seconds`

How often the Overview, Online/Offline and History pages reload themselves in the browser.

**Default:** `30`

### `collect_interval_seconds`

How often the background collector checks all nodes. Lower values give fresher data but more SSH connections and a faster-growing history database. Values below 60 are not recommended.

**Default:** `300` (5 minutes)

## Fixed values

These aren't configurable in this version:

| Value | Setting |
| --- | --- |
| Listening address | `0.0.0.0:5000` (all interfaces) |
| Parallel collections | 10 nodes at a time |
| SSH connect timeout | 5 seconds |
| Collection timeout | 120 seconds per node |
| History page | Latest 500 results |
| Node chart | Last 60 successful collections |

To restrict who can reach port 5000, use a firewall or a reverse proxy. See [Security](security.md).

## File permissions

The installer sets `settings.json` to `640`, owned by `root:patchdashboard`: readable by the service, not by other users, because it contains the password hash. If you replace the file, restore these permissions:

```bash
sudo chown root:patchdashboard /opt/linux-patch-dashboard/config/settings.json
sudo chmod 640 /opt/linux-patch-dashboard/config/settings.json
```

## Older settings

Versions before 1.2 used `inventory_file` and `token_file`. The installer removes them and sets `data_dir` instead, copying your data once. See [Upgrading](upgrading.md).
