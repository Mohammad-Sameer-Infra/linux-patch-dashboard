# Security

Patchli has SSH access to every managed node, so treat the dashboard server as sensitive infrastructure. This page describes how Patchli protects that access and how to harden it further.

## Security model at a glance

| Area | How it works |
| --- | --- |
| **Dashboard login** | HTTP Basic authentication with one admin account. The password is stored only as a salted hash. |
| **Public pages** | Only the documentation, the stylesheet, `/public-key` and `/api/register` work without a login. |
| **Registration** | Requires a single-use token. Input is strictly validated before anything is stored. |
| **SSH to nodes** | Key-based, from a dedicated service account. `ssh` is started directly, never through a shell. |
| **Host keys** | Trusted on first connection, then enforced: a changed host key stops collection. |
| **On the nodes** | Read-only commands as a normal user. No sudo, no agent, no open ports. |
| **Data at rest** | Data folder readable only by the service account; settings readable only by root and the service. |

## Dashboard login

- One admin account. The username is `admin` by default (`admin_user` in the [configuration](configuration.md)).
- The password must be at least 8 characters and is stored as a salted scrypt hash in `settings.json`.
- There are no sessions or cookies: the browser sends the credentials with each request and keeps them until it's closed.

Use a long, unique password. To change it, see [Changing the admin password](administration.md#changing-the-admin-password).

## Serve the dashboard over HTTPS

Basic authentication sends the password with every request. Over plain HTTP anyone on the network path can read it. On anything other than a trusted, isolated network, put Patchli behind an HTTPS reverse proxy.

Example with nginx on the dashboard server:

```nginx
server {
    listen 443 ssl;
    server_name patchli.example.com;

    ssl_certificate     /etc/ssl/certs/patchli.crt;
    ssl_certificate_key /etc/ssl/private/patchli.key;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then:

1. **Close port 5000 to the network**, so it's only reachable through the proxy. Patchli listens on all interfaces, so use the firewall: `sudo ufw delete allow 5000/tcp`, or `sudo firewall-cmd --permanent --remove-port=5000/tcp && sudo firewall-cmd --reload`. Open 443 instead.
2. **Update `dashboard_url`** to the HTTPS address and use it when registering nodes.
3. **Use a certificate the nodes trust.** `register-node.sh` uses `curl`, which rejects self-signed certificates unless their CA is installed on the node.

Caddy is a simpler alternative that obtains certificates automatically: `reverse_proxy 127.0.0.1:5000` in a site block is enough.

## Registration

- Tokens are 128-bit random values, valid for **one** successful registration. Unused tokens don't expire; delete them from `registration_tokens.json` to revoke them.
- Hostname, IP address, SSH user and port are validated strictly (letters, digits and a few safe characters; a real IP address; a port from 1 to 65535). Invalid registrations are rejected and don't use up the token.
- A hostname or IP address can only be registered once.

### Fingerprint verification

The node downloads the dashboard's public key from `/public-key`. Over plain HTTP, someone on the network path could substitute their own key and gain access to that node. That's why `register-node.sh` shows the key's fingerprint and asks you to confirm it against the **Add node** page, which you reached through your authenticated session. Always compare them.

## SSH access to nodes

- The dashboard logs in as the user who ran the registration script, with the key in `/var/lib/patchdashboard/.ssh/id_ed25519`.
- It runs a fixed, read-only script (see [Architecture](architecture.md#what-runs-on-a-node)). Node details from the inventory are passed to `ssh` as separate arguments, never through a shell.
- `BatchMode=yes`: `ssh` never prompts for a password.
- `StrictHostKeyChecking=accept-new`: a node's host key is saved on the first connection (in `/var/lib/patchdashboard/.ssh/known_hosts`) and checked on every later connection. If it changes, collection fails and the node shows Offline until you confirm the change. See [Troubleshooting](troubleshooting.md#nodes-showing-offline).

### Harden the key on each node (recommended)

Limit what the dashboard's key can do by adding options in front of it in `~/.ssh/authorized_keys` on the node:

```text
from="192.168.1.50",restrict ssh-ed25519 AAAAC3Nza… patchdashboard@dashboard-server
```

- `from="…"` accepts the key only from the dashboard's IP address.
- `restrict` disables port forwarding, agent forwarding, X11 and terminal allocation. Patchli doesn't need any of these.

### Use a dedicated account on nodes

For stricter separation, create a dedicated, unprivileged user on each node (for example `patchli`) and run `register-node.sh` as that user. It needs no sudo rights and no group memberships.

## If the dashboard key is compromised

1. Stop the service: `sudo systemctl stop linux-patch-dashboard`.
2. On every node, remove the old key from `authorized_keys`. The node list is in `/var/lib/patchdashboard/servers.json`.
3. Move the old key away: `sudo mv /var/lib/patchdashboard/.ssh/id_ed25519* /root/`.
4. Run `sudo ./install.sh`. It generates a new key and starts the service.
5. Add the new public key to each node, either by re-registering (remove the node from `servers.json` first) or by appending the output of `curl http://<dashboard>:5000/public-key` to the node's `authorized_keys`.

## File permissions

| Path | Owner | Mode |
| --- | --- | --- |
| `/var/lib/patchdashboard/` | `patchdashboard` | `700` |
| `/var/lib/patchdashboard/.ssh/` | `patchdashboard` | `700` |
| `config/settings.json` | `root:patchdashboard` | `640` |
| Backups made by `uninstall.sh --purge` | `root` | `600` |

The application code in `/opt/linux-patch-dashboard` stays owned by whoever cloned it. The service account can read it but not change it.

## Reporting a vulnerability

Please report security issues privately to the maintainer through GitHub rather than in a public issue.
