# Patchli: Linux Patch Dashboard

See which of your Linux servers need patches, from one web page, without logging in to each server.

Patchli connects to your servers over SSH, lists their pending updates, highlights **security**, **kernel** and **critical** updates, and keeps a history. Nothing is installed on the servers you monitor: no agent, no Python.

- **Agentless:** one read-only SSH session per server, as a normal user without sudo.
- **Accurate:** security updates come from Ubuntu/Debian security repositories and `dnf`/`yum` advisories.
- **Clear:** fleet overview, per-server history charts, light and dark themes.
- **Simple to run:** one installer, one systemd service, SQLite storage.
- Ubuntu, Debian, Rocky Linux, RHEL, AlmaLinux and CentOS.

## Quick start

On an Ubuntu 24.04 / Debian 12 server (other distributions: see [Installation](docs/installation.md)):

```bash
sudo apt install -y git openssh-client python3 python3-venv
sudo git clone https://github.com/Mohammad-Sameer-Infra/linux-patch-dashboard.git /opt/linux-patch-dashboard
sudo chmod -R go+rX /opt/linux-patch-dashboard
cd /opt/linux-patch-dashboard
sudo ./install.sh
```

The installer asks for the dashboard URL and an admin password, then starts the service. Open `http://<server-ip>:5000` and log in as `admin`.

Then [add your first server](docs/adding-nodes.md): click **Add node** in the dashboard and run `registration/register-node.sh` on the server.

## Documentation

The full documentation is in [`docs/`](docs/introduction.md). It's also built into every installation at `http://<server-ip>:5000/documentation/`, readable without logging in.

| Getting started | Using and running Patchli | Reference |
| --- | --- | --- |
| [Introduction](docs/introduction.md) | [Dashboard guide](docs/dashboard.md) | [Architecture](docs/architecture.md) |
| [Requirements](docs/requirements.md) | [Update classification](docs/update-classification.md) | [API reference](docs/api.md) |
| [Installation](docs/installation.md) | [Administration](docs/administration.md) | [Troubleshooting](docs/troubleshooting.md) |
| [Adding nodes](docs/adding-nodes.md) | [Configuration](docs/configuration.md) | [FAQ](docs/faq.md) |
| | [Security](docs/security.md) | [Release notes](docs/release-notes.md) |
| | [Upgrading and uninstalling](docs/upgrading.md) | [Roadmap](docs/roadmap.md) |

## Upgrading

```bash
cd /opt/linux-patch-dashboard
sudo git pull
sudo ./install.sh
```

Your nodes, history and settings are kept. Coming from v1.1 or earlier? Read [Upgrading](docs/upgrading.md#upgrading-from-v11-or-earlier) first.

## Contributing and support

Bug reports and feature requests are welcome in [GitHub issues](https://github.com/Mohammad-Sameer-Infra/linux-patch-dashboard/issues). Please include the output of `sudo ./install.sh --check` when reporting a problem. Report security issues privately to the maintainer.

## License

Apache License 2.0. © 2026 Mohammad Sameer.
