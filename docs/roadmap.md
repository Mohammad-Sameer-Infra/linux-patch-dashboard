# Roadmap

Patchli's goal is to give administrators a lightweight, agentless way to see, and eventually act on, the patch status of their Linux servers from one place. This roadmap shows the direction, not fixed dates; priorities may change based on feedback.

## Done

| Version | Highlights |
| --- | --- |
| 1.0 | Registration, collection, online/offline monitoring, history |
| 1.1 | Installer, service account, systemd service |
| 1.2 | Login, hardened registration and SSH, background collection, accurate security classification, redesigned interface, public documentation, uninstaller |

## Next: node lifecycle

- Remove, retire and re-register nodes from the web interface (no more editing `servers.json`).
- Edit a node's IP address and SSH port in the interface.
- Automatic history retention (for example, keep 180 days).
- Token expiry and a list of unused tokens.
- "Collect now" button.

## Later: operations

- Configurable listening address and port.
- Multiple users and read-only roles.
- Reboot-required detection.
- Email or webhook alerts when security updates appear or a node goes offline.
- Support for SUSE (`zypper`).

## Future: automation and reporting

- Ansible integration and patch orchestration.
- Compliance reports (for example, "no security update older than 14 days").
- Trend analysis across the fleet.
- AI-assisted patch recommendations.

## Suggest a feature

Open an issue on [GitHub](https://github.com/Mohammad-Sameer-Infra/linux-patch-dashboard/issues) describing what you need and why.
