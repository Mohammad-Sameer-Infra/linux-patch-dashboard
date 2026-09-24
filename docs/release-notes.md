# Release notes

## Version 1.2.0

A rewrite focused on security, accuracy and ease of use. Upgrading from 1.1? See [Upgrading](upgrading.md#upgrading-from-v11-or-earlier).

### Security

- The dashboard now requires a login (HTTP Basic authentication, admin password set during installation).
- Registration input is strictly validated, and `ssh` is started directly rather than through a shell, closing a command-injection risk.
- SSH host keys are trusted on first use and then enforced, instead of never being checked.
- `register-node.sh` shows the dashboard key's fingerprint for you to confirm, and no longer adds the key twice.
- Runtime data moved to `/var/lib/patchdashboard`, readable only by the service account; `settings.json` is readable only by root and the service.

### Accuracy

- Security updates come from the Debian/Ubuntu security repositories and `dnf`/`yum` security advisories, instead of package-name guesses.
- Kernel updates are detected on RHEL-family nodes too.
- Header lines, wrapped lines and obsolete-package sections in `dnf` output no longer inflate the counts.
- Nodes that time out are shown as Offline.

### Features

- Automatic background collection every 5 minutes (configurable), up to 10 nodes in parallel, with one SSH session per node.
- A redesigned interface: sidebar navigation, light and dark themes, fleet summary tiles, a fleet health bar, security, kernel and critical columns, a per-node update history chart, and a filterable package list.
- Public documentation center with this documentation.
- `install.sh --check` health check (replaces `bootstrap.sh`).
- `uninstall.sh`, with a keep-data default and `--purge` with automatic backup.

### Removed

- The `/discovery` network scan.
- `bootstrap.sh` (use `install.sh --check`).

## Version 1.1.0

- `install.sh` installer: service account, SSH key, virtual environment and systemd service.
- `bootstrap.sh` validation script.
- Runtime ownership separated from the source tree.

## Version 1.0.0 "Foundation"

Initial public release.

- Node registration with one-time tokens.
- SSH-based collection of available updates on Ubuntu/Debian and Rocky/RHEL.
- Online/offline monitoring and collection history.
- Product identity framework and documentation center.
