# Architecture

Patchli is a single Python (Flask) application with an SQLite database. There's no separate agent, message queue or web server to run.

## Components

```text
                    +----------------------- linux-patch-dashboard.service -----------------------+
 Browser  --HTTP--> |  Web interface (Flask)          Background collector (thread)                |
                    |   routes.py, templates/           collect.py                                 |
 Nodes    --HTTP--> |  Registration API                  |  every collect_interval_seconds         |
 (register only)    |   routes.py -> store.py            |  10 nodes in parallel                   |
                    |                                    v                                          |
                    |           store.py  <---- snapshots ----  ssh (one session per node)  ------> | --SSH--> Managed nodes
                    +---------------------------|-------------------------------------------------+
                                                v
                         /var/lib/patchdashboard: servers.json, registration_tokens.json, telemetry.db
```

| File | Responsibility |
| --- | --- |
| `run.py` | Entry point. Starts the collector thread and the web server on port 5000. Also provides `set-password`. |
| `collector.py` | Runs one collection from the command line. |
| `app/__init__.py` | Creates the Flask app, loads product info and enforces the login. |
| `app/store.py` | Settings, the inventory and token files, the SQLite database and registration. |
| `app/collect.py` | The SSH collection, output parsing and update classification. |
| `app/routes.py` | Dashboard pages and the registration API. |
| `app/documentation.py` | Renders the Markdown files in `docs/` as the public documentation. |
| `app/templates/`, `app/static/` | HTML templates and the stylesheet. |
| `install.sh`, `uninstall.sh` | Installation, health check and removal. |
| `registration/register-node.sh` | Run on a node to register it. |

## Collection

Every `collect_interval_seconds` (300 by default), and once when the service starts, the collector:

1. Reads the inventory (`servers.json`).
2. Connects to up to 10 nodes at a time, with one SSH session per node.
3. Runs a fixed script on each node (below) and parses its output.
4. Classifies every update (see [Update classification](update-classification.md)).
5. Stores one snapshot per node in `telemetry.db`.

The SSH command is equivalent to:

```bash
ssh -p <port> -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new -- <user>@<ip> sh -s
```

The script is sent on standard input. A node is marked **Offline** when:

- `ssh` itself fails (exit code 255: unreachable, refused, authentication failed, host key changed), or
- the whole collection takes longer than 120 seconds, or
- the output doesn't contain the expected sections.

A non-zero exit code from the script itself doesn't count as a failure; for example, `dnf check-update` exits with 100 when updates are available.

### What runs on a node

```sh
echo "##HOSTNAME"; hostname
echo "##OS"; . /etc/os-release; echo "$PRETTY_NAME"
echo "##UPTIME"; uptime -p
if command -v apt-get >/dev/null 2>&1; then
    echo "##FAMILY"; echo debian
    echo "##UPDATES"; apt list --upgradable 2>/dev/null | tail -n +2
else
    PM=dnf; command -v dnf >/dev/null 2>&1 || PM=yum
    echo "##FAMILY"; echo redhat
    echo "##UPDATES"; $PM -q check-update 2>/dev/null
    echo "##SECURITY"; $PM -q updateinfo list --security 2>/dev/null
fi
```

Every command is read-only and runs as the registered user, without sudo.

## Data

All runtime data is in `data_dir` (`/var/lib/patchdashboard` by default).

### `servers.json`: the inventory

A JSON list with one object per node: `node_id`, `hostname`, `ip`, `ssh_user`, `ssh_port`, `state` and `registered_at`. Written by registration; read at the start of each collection and on every page load.

### `registration_tokens.json`

A JSON list of `{"token", "used", "created_at"}` objects.

### `telemetry.db`: collection history

SQLite, with one table:

| Column | Type | Contents |
| --- | --- | --- |
| `id` | INTEGER | Auto-increment primary key |
| `hostname` | TEXT | Node hostname, as in the inventory |
| `ip` | TEXT | Node IP address |
| `os` | TEXT | `PRETTY_NAME` from `/etc/os-release` |
| `uptime` | TEXT | Output of `uptime -p` |
| `updates` | INTEGER | Total pending updates |
| `kernel_updates` | INTEGER | Kernel updates |
| `security_updates` | INTEGER | Security updates |
| `critical_packages` | INTEGER | Critical package updates |
| `status` | TEXT | `Online` or `Offline` |
| `last_check` | TEXT | Collection time, `YYYY-MM-DD HH:MM:SS` (dashboard server's local time) |
| `packages` | TEXT | JSON list of `{"line", "kernel", "security", "critical"}` |

The dashboard shows each node's **latest** row; the History page and node charts read older rows. Rows are never deleted automatically. See [History size](administration.md#history-size).

Example queries:

```sql
-- Latest result per node
SELECT hostname, status, updates, security_updates, last_check
FROM telemetry WHERE id IN (SELECT MAX(id) FROM telemetry GROUP BY hostname);

-- Nodes that had security updates pending in the last day
SELECT DISTINCT hostname FROM telemetry
WHERE security_updates > 0 AND last_check > datetime('now', 'localtime', '-1 day');
```

## Web requests

Every request passes a login check first. Documentation pages, the stylesheet, `/public-key` and `/api/register` are public; everything else needs the admin credentials. Pages read the inventory and the latest snapshots on each request and never contact nodes directly, which is why they load instantly regardless of fleet size.

## Design choices

- **Agentless:** nothing to install, update or secure on the nodes. The trade-off is that the dashboard needs SSH access.
- **SQLite and JSON files:** no database server to run or back up separately. They are ample for hundreds of nodes.
- **One process:** the web server and the collector share a process, so there's one service to manage.
- **Built-in development server:** Flask's server is adequate for a small admin audience. Put a reverse proxy in front for HTTPS (see [Security](security.md)).
