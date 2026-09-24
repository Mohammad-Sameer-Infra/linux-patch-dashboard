# Introduction

Patchli is a lightweight, agentless dashboard that shows which of your Linux servers need patches, from one web page, without logging in to each server.

It connects to your servers over SSH, lists their pending package updates, highlights the ones that matter most (security, kernel and critical packages) and keeps a history so you can see how patch levels change over time.

## Who it is for

- **System administrators** who look after a handful to a few hundred Linux servers and want a quick answer to "what needs patching?"
- **Small teams** that don't want to run a full configuration-management or monitoring stack just to see patch status.
- **Anyone preparing a patch window** who needs a list of affected servers and packages.

Patchli **shows** patch status. It does not install updates; you still patch with your usual tools (`apt`, `dnf`, Ansible and so on). Patch orchestration is on the [roadmap](roadmap.md).

## How it works

```text
+-------------------------+        SSH, every 5 minutes        +-------------------------+
|    Dashboard server     | ---------------------------------> |      Managed node       |
|                         |                                    |                         |
|  Web dashboard (:5000)  |   runs: hostname, os-release,      |  Ubuntu / Debian        |
|  Background collector   |   uptime, apt / dnf / yum lists    |  Rocky / RHEL / Alma    |
|  SQLite history         |                                    |  SSH server             |
|  Registration API       |                                    |  Dashboard's public key |
+-------------------------+                                    +-------------------------+
```

1. You install Patchli on one **dashboard server**. The installer creates a service account with its own SSH key.
2. You **register** each server you want to monitor (a **managed node**). A small script adds the dashboard's public key to a user account on the node and records the node in the dashboard's inventory.
3. Every 5 minutes the dashboard opens **one SSH session per node** (up to 10 at a time), runs a short read-only script and stores the result.
4. The web pages read the stored results, so they load instantly, and the history builds up automatically.

Nothing is installed or left running on the managed nodes: no agent, no Python, no open ports beyond SSH.

## Key concepts

| Term | Meaning |
| --- | --- |
| **Dashboard server** | The machine running Patchli: the web interface, the collector and the database. |
| **Managed node** | A server Patchli monitors. It only needs SSH and a normal user account. |
| **Collection** | One run of the collector against a node. Produces a snapshot of its updates. |
| **Snapshot** | The stored result of a collection: status, OS, uptime, update counts and the package list. |
| **Registration token** | A one-time code that authorises a node to add itself to the inventory. |
| **Patch status** | A node's most urgent state: *Security updates*, *Updates pending*, *Up to date*, *Offline* or *Not collected yet*. |
| **Update categories** | Total, security, kernel and critical. See [Update classification](update-classification.md). |

## Features

- Agentless: SSH only, one session per node per collection.
- Ubuntu, Debian, Rocky Linux, RHEL, AlmaLinux and CentOS (anything using `apt`, `dnf` or `yum`).
- Security updates detected from real sources: the Debian/Ubuntu security repository and `dnf`/`yum` security advisories.
- Kernel and critical-package highlighting.
- Automatic background collection with history and per-node trend charts.
- Password-protected dashboard; public documentation.
- One-time registration tokens with SSH key fingerprint verification.
- Light and dark themes; works on phones.
- One-command installer with a health check, and a safe uninstaller.

## Next steps

1. Check the [requirements](requirements.md).
2. Follow the [installation guide](installation.md).
3. [Add your first node](adding-nodes.md).
