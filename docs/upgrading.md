# Upgrading and uninstalling

## Upgrading

Optionally, take a backup first. It takes a second, and upgrades don't touch your data, but it costs nothing:

```bash
sudo tar -czf /root/patchli-backup-$(date +%F).tar.gz /var/lib/patchdashboard /opt/linux-patch-dashboard/config/settings.json
```

Then upgrade:

```bash
cd /opt/linux-patch-dashboard
sudo git pull
sudo ./install.sh
```

The installer updates the Python dependencies, rewrites the service file and restarts the service. The dashboard is unavailable for a few seconds while it restarts. The installer's output includes a line such as `[PASS] Data in /var/lib/patchdashboard: 12 registered node(s)`, so you can confirm your nodes are still there.

### What an upgrade keeps

Registered nodes keep working through an upgrade without re-registering. Specifically:

| Kept | Why it's safe |
| --- | --- |
| **Registered nodes, tokens and history** | They live in `/var/lib/patchdashboard`, outside the Git repository, so `git pull` never touches them. The installer only copies data from older versions when the destination is empty, and never overwrites existing files. |
| **The dashboard's SSH key** | Generated only if it doesn't exist. Nodes keep trusting the dashboard, so no re-registration is needed. |
| **Known host keys** | Kept in `/var/lib/patchdashboard/.ssh/known_hosts`. |
| **Settings and admin password** | `settings.json` is updated in place; the password is only asked for if none is set. The file is rewritten safely (temp file, then rename), so an interrupted upgrade can't leave it half-written. |
| **A custom data folder** | If `data_dir` points somewhere other than the default, the installer keeps it. |
| **The history database** | New versions only add columns when needed; rows are never deleted. |

Always run the installer after `git pull`, even for small releases. Besides updating dependencies, it re-applies file permissions, which matters on servers with a strict `umask`. There, files added by `git pull` are readable only by root until the installer runs. The installer is safe to run as often as you like.

### If `git pull` refuses to update

```text
error: Your local changes to the following files would be overwritten by merge:
        install.sh
```

A file in the installation folder was changed locally. Check what changed with `git diff <file>`. If you don't need the change, discard it and pull again:

```bash
sudo git checkout -- install.sh
sudo git pull
```

If you do need it, first save a copy (`sudo cp install.sh /root/install.sh.mine`), then discard and pull.

### Upgrading from v1.1 or earlier

Version 1.2 moved the runtime data out of the installation folder and added a login. The installer handles this automatically:

1. It copies `inventory/servers.json`, `security/registration_tokens.json` and `telemetry.db` into `/var/lib/patchdashboard/`, once, if they aren't there yet.
2. It replaces `inventory_file` and `token_file` in `settings.json` with `data_dir`.
3. It asks you to set an admin password.

The old files are left in place; delete them after checking the dashboard. On the first collection after the upgrade, the dashboard stores each node's SSH host key.

## Uninstalling

`uninstall.sh` shows what it will remove and waits for you to type `yes` before changing anything.

### Remove the service, keep your data

```bash
cd /opt/linux-patch-dashboard
sudo ./uninstall.sh
```

This stops and removes the `linux-patch-dashboard` service and deletes the `venv/` folder. Your nodes, history, SSH key, settings and the installation folder are kept, so running `sudo ./install.sh` brings everything back exactly as it was.

### Remove everything

```bash
cd /opt/linux-patch-dashboard
sudo ./uninstall.sh --purge
```

This also:

1. Saves a backup of `/var/lib/patchdashboard` and `settings.json` to `/root/patchli-backup-<date>.tar.gz`, readable only by root (it contains the private SSH key).
2. Permanently deletes `/var/lib/patchdashboard`.
3. Deletes the `patchdashboard` account.
4. Deletes `/opt/linux-patch-dashboard`.
5. Lists your managed nodes. On each, remove the line ending in `patchdashboard@…` from the registered user's `~/.ssh/authorized_keys`.

### Options

| Option | Effect |
| --- | --- |
| `--purge` | Remove everything, as above |
| `--no-backup` | With `--purge`: don't save a backup |
| `--yes` | Don't ask for confirmation (for automation) |
| `--help` | Show usage |

For safety, the script refuses to delete system folders such as `/`, `/opt`, `/var/lib` or `/home`, even if `settings.json` is misconfigured.

## Restoring from a backup

To restore a backup made by `uninstall.sh --purge` or by the [backup command](administration.md#backups):

1. [Install Patchli](installation.md) again. It generates a new SSH key and settings, which the backup replaces.
2. Stop the service:

   ```bash
   sudo systemctl stop linux-patch-dashboard
   ```

3. Extract the backup over the new installation:

   ```bash
   sudo tar -xzf /root/patchli-backup-<date>.tar.gz -C /
   ```

4. Fix ownership and permissions:

   ```bash
   sudo chown -R patchdashboard:patchdashboard /var/lib/patchdashboard
   sudo chown root:patchdashboard /opt/linux-patch-dashboard/config/settings.json
   sudo chmod 640 /opt/linux-patch-dashboard/config/settings.json
   ```

5. Start the service:

   ```bash
   sudo systemctl start linux-patch-dashboard
   ```

Your nodes, history, SSH key and admin password are back. The nodes still trust the restored key, so no re-registration is needed.
