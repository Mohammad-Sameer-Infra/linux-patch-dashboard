# API reference

Patchli exposes two public HTTP endpoints, used by managed nodes during registration. Every other URL is a web page that requires the admin login; there is no JSON API for dashboard data in this version.

All examples use `http://192.168.1.50:5000` as the dashboard URL.

## `GET /public-key`

Returns the dashboard's SSH public key as plain text. Registration adds it to the node's `authorized_keys`.

**Authentication:** none.

```bash
curl http://192.168.1.50:5000/public-key
```

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI…  patchdashboard@dashboard-server
```

Compare its fingerprint with the one on the Add node page before trusting it:

```bash
curl -s http://192.168.1.50:5000/public-key | ssh-keygen -lf -
```

## `POST /api/register`

Adds a node to the inventory using a one-time registration token.

**Authentication:** a valid, unused registration token in the request body.

### Request

`Content-Type: application/json`

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `token` | string | yes | An unused token from the Add node page |
| `hostname` | string | yes | Starts with a letter or digit; letters, digits, `.` and `-`; up to 253 characters |
| `ip` | string | yes | A valid IPv4 or IPv6 address |
| `ssh_user` | string | yes | Starts with a letter or `_`; letters, digits, `_`, `.` and `-`; up to 32 characters |
| `ssh_port` | integer | no | 1–65535. Default `22` |

```bash
curl -X POST http://192.168.1.50:5000/api/register \
     -H "Content-Type: application/json" \
     -d '{"hostname": "web01", "ip": "192.168.1.10", "ssh_user": "ubuntu", "ssh_port": 22, "token": "3f9c…"}'
```

This only records the node. The node must also trust the dashboard's key (see `GET /public-key`) before collection can succeed; `register-node.sh` does both.

### Responses

**200 OK**: registered.

```json
{"message": "Node registered successfully", "success": true}
```

**400 Bad Request**: not registered. `message` is one of:

| Message | Cause |
| --- | --- |
| `Invalid or used token` | The token doesn't exist or was already used |
| `Hostname already registered` | A node with this hostname is in the inventory |
| `IP already registered` | A node with this IP address is in the inventory |
| `Invalid hostname` | The hostname breaks the rules above |
| `Invalid IP address` | Not a valid IPv4/IPv6 address |
| `Invalid SSH user` | The user name breaks the rules above |
| `Invalid SSH port` | Not an integer from 1 to 65535 |

```json
{"message": "Invalid or used token", "success": false}
```

A request that fails validation doesn't use up the token.

## Web pages

For reference, the pages that require the admin login:

| URL | Page |
| --- | --- |
| `/` | Overview |
| `/online`, `/offline` | Nodes in that state |
| `/node/<hostname>` | Node page |
| `/node/<hostname>/<category>` | Node page filtered to `all-updates`, `security-updates`, `kernel-updates` or `critical-packages` |
| `/history` | Collection history |
| `/generate-token` | Creates a registration token (each visit creates a new one) |

Public pages: `/documentation/` and `/documentation/<page>`.
