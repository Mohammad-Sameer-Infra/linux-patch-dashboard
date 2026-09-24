# Dashboard guide

This page explains every screen in the dashboard and what the numbers and statuses mean.

## Logging in and out

The dashboard uses your browser's built-in login prompt. Enter the username `admin` (or the `admin_user` you configured) and your password.

Browsers keep this login until you **close the browser**; there is no logout button. On a shared computer, close all browser windows when you're done.

The **Documentation** pages are public and don't need a login.

## Overview

The home page (`/`) answers "what needs patching?" at a glance. It reloads itself every 30 seconds (see `dashboard_refresh_seconds` in the [configuration reference](configuration.md)).

### Summary tiles

| Tile | Meaning |
| --- | --- |
| **Nodes online** | Nodes whose last collection succeeded, out of all registered nodes. Click to list them. |
| **Pending updates** | Total available updates across all nodes. |
| **Security updates** | Updates that fix published security issues. The most important number. |
| **Kernel updates** | New kernel packages. Installing them usually requires a reboot. |
| **Critical packages** | Updates to core packages such as the kernel, OpenSSL, OpenSSH, sudo, systemd and glibc. |

How each category is decided is explained in [Update classification](update-classification.md).

### Fleet health

A bar showing how many nodes are in each patch status. Each node is counted once, by its most urgent state:

| Status | Meaning |
| --- | --- |
| **Security updates** | Online, with at least one security update pending. |
| **Updates pending** | Online, with updates pending but none of them security updates. |
| **Up to date** | Online, with no updates pending. |
| **Offline** | The last collection could not connect or timed out. |
| **Not collected yet** | Registered, but not collected since registration. |

Every status is shown with an icon and a label, never color alone.

### Managed nodes table

One row per registered node:

- **Node**: hostname, IP address and operating system.
- **Patch status**: as in the table above.
- **Updates / Security / Kernel / Critical**: counts from the latest collection. Non-zero values have a colored dot; zeros are greyed out.
- **Uptime**: as reported by the node.
- **Last check**: when the node was last collected, for example "5 min ago". Hover to see the exact time.

Type in the search box to filter by hostname, IP address, OS or status. Click a row to open the node's page.

The **Last collected** note at the top right shows when the most recent collection finished.

### Dashboard server

The hostname, OS, kernel and uptime of the machine running Patchli. The dashboard server doesn't monitor its own updates; to see them, register it as a node like any other server.

## Online and Offline

`/online` and `/offline` list only the nodes in that state, using the same table and search as the overview. They are also linked from the sidebar and the **Nodes online** tile.

## Node page

Click any node to open `/node/<hostname>`.

### Header

The node's hostname, IP address, OS, patch status and when it was last checked. If the node is **Offline** or **Not collected yet**, a notice explains why there is no current data and when it was last seen online.

### Summary tiles and package filter

Four tiles show **All updates**, **Security**, **Kernel** and **Critical** counts. Click a tile, or use the filter buttons above the package list, to show only that category. The search box narrows the list further.

### Node details

Hostname, IP address, the SSH login the dashboard uses (`user@ip:port`), OS, uptime, registration time, when it was last online, and its node ID.

### Pending updates over time

A line chart of the node's total and security updates across its last 60 successful collections. Hover over the chart to see the exact values at each point. **View as table** shows the same data as a table.

The chart appears after two successful collections. A typical pattern is a slow rise as updates are released, then a drop to zero after patching.

### Available updates

Every pending update, exactly as the node's package manager reports it:

- **Debian/Ubuntu:** `package/repository version architecture [upgradable from: old-version]`
- **RHEL family:** `package.architecture version repository`

Tags mark **Security**, **Kernel** and **Critical** packages. A node with no updates shows **Fully patched**.

Links from older versions (`/node/<hostname>/security-updates` and similar) still work and open this page with that filter selected.

## History

`/history` lists the latest 500 collection results for all nodes, newest first: time, node, status and the four counts. Use it to see when a node went offline or when it was patched. Search filters by node, OS or status.

History is kept indefinitely. To delete a node's history, see [Removing a node](administration.md#remove-a-node).

## Add node

`/generate-token` creates a new one-time registration token each time it's opened, and shows the dashboard's SSH key fingerprint together with the registration steps. See [Adding nodes](adding-nodes.md).

## Light and dark mode

Use **Dark mode** / **Light mode** at the bottom of the sidebar. Your choice is remembered in this browser. Until you choose, the dashboard follows your operating system's setting.
