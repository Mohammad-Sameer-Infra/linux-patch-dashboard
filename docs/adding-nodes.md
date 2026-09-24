# Adding nodes

Repeat these steps for each server you want to monitor. Each registration takes about a minute.

## Before you start

- The node can reach the dashboard on port 5000, and the dashboard can reach the node on its SSH port (22 by default).
- You can log in to the node as a **normal user** (for example `ubuntu`, `rocky` or your own account). The dashboard will log in as this user. It does not need sudo.
- `curl` and `ssh-keygen` are installed on the node (they usually are).

## Step 1: Create a registration token

In the dashboard, click **Add node** in the sidebar. The page shows:

- A **registration token**. It works once; create a new one for each node by reloading the page.
- The dashboard's **SSH key fingerprint**. You will compare it in step 3.

Keep this page open.

## Step 2: Copy the registration script to the node

From the dashboard server (replace the user and address):

```bash
scp /opt/linux-patch-dashboard/registration/register-node.sh <user>@<node-ip>:~/
```

Alternatively, create `register-node.sh` on the node and paste in the contents of `registration/register-node.sh`.

## Step 3: Run the script on the node

Log in to the node **as the user the dashboard should use** (not root), then run:

```bash
chmod +x register-node.sh
./register-node.sh
```

The script:

1. Asks for the **dashboard URL** (for example `http://192.168.1.50:5000`) and the **token**.
2. Shows the hostname, IP address and user it detected.
3. Downloads the dashboard's public key and shows its **fingerprint**. Type `y` **only if it matches** the fingerprint on the Add node page. A mismatch means the key was changed in transit.
4. Adds the key to `~/.ssh/authorized_keys`. Running the script again doesn't add it twice.
5. Registers the node with the dashboard.

A successful run ends with:

```json
{"message":"Node registered successfully","success":true}
```

### Check the detected values

The script uses the **first IP address** reported by `hostname -I` and always registers **SSH port 22**. On a server with several network interfaces (or Docker), the first address may not be the one the dashboard can reach. If the IP address or port is wrong, correct it afterwards as described in [Editing a node's IP address or SSH port](administration.md#edit-a-nodes-ip-address-or-ssh-port).

## Step 4: Wait for the first collection

The node appears on the dashboard straight away with the status **Not collected yet**. The next background collection (within 5 minutes) fills in its details.

To collect immediately, run this on the dashboard server:

```bash
cd /opt/linux-patch-dashboard
sudo -u patchdashboard venv/bin/python collector.py
```

It prints one line per node, for example:

```text
web01: Online, 12 updates
db01: Online, 0 updates
```

Refresh the dashboard to see the results. If a node shows **Offline**, see [Troubleshooting](troubleshooting.md#nodes-showing-offline).

## Registering many nodes

Each node needs its own token, because tokens are single-use. For a handful of nodes, reload the Add node page between registrations. For large fleets, registration through the API is described in the [API reference](api.md), but you still need one token per node.

## What registration changes on the node

Only one thing: a line is added to `~/.ssh/authorized_keys` for the user who ran the script. It looks like:

```text
ssh-ed25519 AAAAC3Nza…  patchdashboard@dashboard-server
```

To stop the dashboard from connecting, delete that line. See [Removing a node](administration.md#remove-a-node).
