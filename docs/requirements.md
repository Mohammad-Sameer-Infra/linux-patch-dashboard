# Requirements

## Dashboard server

| | Requirement |
| --- | --- |
| **Operating system** | Ubuntu 22.04+, Debian 12+, Rocky Linux 8+ or RHEL 8+, with systemd |
| **Python** | 3.11 or newer (see the table below; older distributions need an extra package) |
| **Packages** | `git` and the OpenSSH client (`ssh`, `ssh-keygen`) |
| **CPU / memory** | Minimal. 1 vCPU and 512 MB RAM are enough for dozens of nodes |
| **Disk** | A few MB for the application; the history database grows by roughly 5–20 KB per node per collection |
| **Access** | A user with `sudo` |

### Python version by distribution

| Distribution | Default `python3` | Packages to install |
| --- | --- | --- |
| Ubuntu 24.04 | 3.12 ✅ | `python3 python3-venv` |
| Ubuntu 22.04 | 3.10 ❌ | `python3.11 python3.11-venv` |
| Debian 12 | 3.11 ✅ | `python3 python3-venv` |
| Rocky Linux / RHEL 8 | 3.6 ❌ | `python3.12` |
| Rocky Linux / RHEL 9 | 3.9 ❌ | `python3.12` |

You don't need to change the system's default `python3`. The installer looks for `python3.13`, `python3.12` and `python3.11` before falling back to `python3`.

### Network

| Direction | Port | Purpose |
| --- | --- | --- |
| Browser → dashboard | TCP 5000 | Web interface |
| Managed node → dashboard | TCP 5000 | Registration only (downloads the public key, calls the registration API) |
| Dashboard → managed node | TCP 22 (or the node's SSH port) | Collection |
| Dashboard → internet | TCP 443 | During installation and upgrades only: Python packages from PyPI |

## Managed nodes

| | Requirement |
| --- | --- |
| **Operating system** | Anything using `apt` (Ubuntu, Debian) or `dnf`/`yum` (Rocky, RHEL, AlmaLinux, CentOS) |
| **SSH** | SSH server running, public-key login allowed (the default) |
| **User account** | A normal user that can log in over SSH. **No sudo needed**: listing available updates works without root |
| **Tools** | `curl` and `ssh-keygen`, used once by the registration script (present on most servers) |
| **Python** | Not required |

The collector runs these read-only commands on each node:

- `hostname`, `uptime -p` and reads `/etc/os-release`
- Debian/Ubuntu: `apt list --upgradable`
- RHEL family: `dnf check-update` and `dnf updateinfo list --security` (or the `yum` equivalents)

> **Note:** on Debian/Ubuntu, Patchli reads the package lists as they are on the node. It doesn't refresh them, because that needs root. Ubuntu refreshes them daily by default (`apt-daily.timer`). If a node's lists are never refreshed, its counts will be out of date. See [Troubleshooting](troubleshooting.md#update-counts).

## Browser

Any current version of Chrome, Edge, Firefox or Safari. The dashboard needs no internet access from the browser: it uses no external fonts, scripts or CDNs.

## Next step

[Install the dashboard](installation.md).
