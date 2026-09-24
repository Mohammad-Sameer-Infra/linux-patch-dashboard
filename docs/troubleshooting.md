# Troubleshooting

Start with the health check. It finds most installation problems:

```bash
cd /opt/linux-patch-dashboard
sudo ./install.sh --check
```

Then find your symptom below.

## Installation

| Symptom | Cause and fix |
| --- | --- |
| `Python 3.11 or newer is required.` | Install the Python package for your distribution ([Requirements](requirements.md#python-version-by-distribution)) and run the installer again. |
| `ssh-keygen not found` (or `python3`, `ssh`, `systemctl`) | Install the prerequisites from [Installation, step 1](installation.md#step-1-install-prerequisites). |
| Fails at "Python environment" | The server can't reach PyPI (check internet access or proxy settings), or the `-venv` package is missing on Ubuntu/Debian. |
| `Run install.sh as root or with sudo.` | Run `sudo ./install.sh`. |
| `cd: /opt/linux-patch-dashboard: Permission denied` after cloning | The server uses a strict `umask`, so the cloned files are readable only by root. Run `sudo chmod -R go+rX /opt/linux-patch-dashboard`. The installer does this automatically as well. |
| `patchdashboard can't read /opt/…` | The installation folder is inside a private folder, such as a home directory. Move it to `/opt/linux-patch-dashboard` and run the installer again. |
| `git pull` says local changes would be overwritten | See [Upgrading](upgrading.md#if-git-pull-refuses-to-update). |

## Dashboard

| Symptom | Cause and fix |
| --- | --- |
| Browser can't connect | Check the service (`sudo systemctl status linux-patch-dashboard`) and that port 5000 is open ([Installation, step 4](installation.md#step-4-open-the-firewall)). |
| "No admin password is set" | Run `sudo venv/bin/python run.py set-password`, then `sudo systemctl restart linux-patch-dashboard`. |
| The login prompt keeps coming back | Wrong username or password. The username is `admin` unless you changed `admin_user`. Reset the password as above. |
| The service won't start | Check `sudo journalctl -u linux-patch-dashboard -n 50`. Usually `settings.json` isn't valid JSON: check it with `python3 -m json.tool config/settings.json`, or re-run `sudo ./install.sh`. |
| `PermissionError` in the log | The service can't read the application or `settings.json`, or can't write to `/var/lib/patchdashboard`. This can happen after `git pull` on servers with a strict `umask`. Re-run `sudo ./install.sh` to restore permissions. |
| Page looks unstyled or old after an upgrade | Restart the service and hard-refresh the browser (Ctrl+F5 or Cmd+Shift+R). |

## Registration

| Symptom | Cause and fix |
| --- | --- |
| "The dashboard did not return an SSH public key" | Wrong dashboard URL, the dashboard is down, or port 5000 is blocked. Test from the node: `curl http://<dashboard-ip>:5000/public-key`. |
| `curl: command not found` | Install curl on the node: `sudo apt install curl` or `sudo dnf install curl`. |
| `curl: (60) SSL certificate problem` | The dashboard uses HTTPS with a certificate the node doesn't trust. Install the CA certificate on the node, or use a trusted certificate. |
| The fingerprint doesn't match | **Don't continue.** Check that you used the right dashboard URL. If it's right, something between the node and the dashboard altered the key. Investigate before registering. |
| "Invalid or used token" | Each token works once. Reload the **Add node** page for a new one. |
| "Hostname already registered" / "IP already registered" | The node is already in the inventory. To re-register it, [remove it](administration.md#remove-a-node) first. |
| "Invalid hostname / IP address / SSH user" | The detected value has unsupported characters. Check `hostname`, `hostname -I` and `whoami` on the node. See the rules in the [API reference](api.md#post-apiregister). |

## Nodes showing Offline

Test the exact connection the dashboard uses, from the dashboard server:

```bash
sudo -u patchdashboard ssh -p <port> <user>@<node-ip> hostname
```

The user, IP address and port are on the node's page under **SSH**.

| What you see | Cause and fix |
| --- | --- |
| It prints the node's hostname | SSH works. The node will show Online after the next collection, or run `collector.py` now. |
| `Connection timed out` / `No route to host` | Wrong IP address, the node is down, or a firewall blocks the SSH port. Check `ip` in `servers.json` ([edit it](administration.md#edit-a-nodes-ip-address-or-ssh-port)). |
| `Connection refused` | SSH isn't listening on that port. Check `ssh_port` in `servers.json`. |
| `Permission denied (publickey)` | The dashboard's key isn't in that user's `~/.ssh/authorized_keys` on the node. Re-run `register-node.sh` as that user, or append the output of `curl http://<dashboard-ip>:5000/public-key` to the file. Also check the file permissions: `~/.ssh` must be `700` and `authorized_keys` `600`. |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | The node was rebuilt, or its IP address now belongs to another machine. If the change is expected, remove the old host key: `sudo -u patchdashboard ssh-keygen -R <node-ip>` (add `-R '[<node-ip>]:<port>'` for non-standard ports). |
| `Host key verification failed` | Same as above. |
| Works by hand, but the node is still Offline | Collection may be timing out (over 120 seconds). This is common on the first run on RHEL-family nodes while `dnf` downloads metadata. Wait for the next collection. |

## Update counts

| Symptom | Cause and fix |
| --- | --- |
| Security, kernel and critical are always 0 on Ubuntu | Usually correct: Ubuntu installs security updates automatically. Confirm with the commands in [Update classification](update-classification.md#checking-a-node-by-hand). |
| Security is always 0 on a RHEL-family node | The node's repositories don't publish advisory data (common with CentOS Stream and some mirrors). Check with `dnf updateinfo list --security`. |
| Counts look out of date | Pages show the latest collection. Check **Last collected** on the Overview, or run `collector.py`. |
| Counts on Ubuntu don't change after new updates are released | The node's package lists aren't being refreshed. Run `sudo apt update` on the node, and make sure `apt-daily.timer` is enabled: `systemctl is-enabled apt-daily.timer`. |
## Getting help

If none of this helps, [open an issue on GitHub](https://github.com/Mohammad-Sameer-Infra/linux-patch-dashboard/issues) with:

- the output of `sudo ./install.sh --check`
- the last 50 log lines: `sudo journalctl -u linux-patch-dashboard -n 50`
- your dashboard server's and nodes' distributions and versions

Remove IP addresses, hostnames and anything sensitive before posting.
