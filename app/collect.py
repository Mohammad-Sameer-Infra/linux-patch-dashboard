"""Collect patch data from managed nodes over SSH and store it."""

import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

from app import store

# Runs on the node with `sh -s` in a single SSH session.
# Each section starts with a "##NAME" marker line.
REMOTE_SCRIPT = r"""
echo "##HOSTNAME"; hostname
echo "##OS"; . /etc/os-release; echo "$PRETTY_NAME"
echo "##UPTIME"; uptime -p
if command -v apt-get >/dev/null 2>&1; then
    echo "##FAMILY"; echo debian
    echo "##UPDATES"; apt list --upgradable 2>/dev/null | tail -n +2
else
    PM=dnf; command -v dnf >/dev/null 2>&1 || PM=yum
    echo "##FAMILY"; echo redhat
    echo "##UPDATES"; $PM -q check-update 2>/dev/null
    echo "##SECURITY"; $PM -q updateinfo list --security 2>/dev/null
fi
"""

CRITICAL_PREFIXES = ("openssl", "libssl", "openssh", "sudo", "systemd", "glibc", "libc6")
KERNEL_PREFIXES = ("linux-image", "linux-headers", "kernel")


def parse_sections(output):
    sections, current = {}, None
    for line in output.splitlines():
        if line.startswith("##"):
            current = sections.setdefault(line[2:].strip(), [])
        elif current is not None and line.strip():
            current.append(line.strip())
    return sections


def debian_packages(lines):
    """apt prints "name/suite version arch [upgradable from: ...]"."""
    packages = []
    for line in lines:
        name, _, rest = line.partition("/")
        suite = rest.split(" ", 1)[0]
        packages.append((name, line, "-security" in suite))
    return packages


def redhat_packages(lines, security_lines):
    """dnf/yum print "name.arch version repo"; long names wrap onto a second line."""
    # Advisory lines end with the fixed package, e.g. "openssl-1:3.0.7-25.el9.x86_64".
    advisory_packages = [line.split()[-1] for line in security_lines]

    def is_security(name):
        prefix = name + "-"
        return any(
            p.startswith(prefix) and p[len(prefix):][:1].isdigit()
            for p in advisory_packages
        )

    packages, pending = [], []
    for line in lines:
        if line.startswith("Obsoleting"):
            break
        fields = pending + line.split()
        if "." not in fields[0]:
            pending = []
            continue
        if len(fields) < 3:
            pending = fields
            continue
        pending = []
        name = fields[0].rsplit(".", 1)[0]
        packages.append((name, " ".join(fields[:3]), is_security(name)))
    return packages


def classify(packages):
    return [
        {
            "line": line,
            "kernel": name.startswith(KERNEL_PREFIXES),
            "security": security,
            "critical": name.startswith(KERNEL_PREFIXES + CRITICAL_PREFIXES),
        }
        for name, line, security in packages
    ]


def collect_node(server):
    snapshot = {
        "hostname": server["hostname"],
        "ip": server["ip"],
        "os": "Unknown",
        "uptime": "Unknown",
        "updates": 0,
        "kernel_updates": 0,
        "security_updates": 0,
        "critical_packages": 0,
        "status": "Offline",
        "last_check": store.now(),
        "packages": [],
    }

    command = [
        "ssh",
        "-p", str(server.get("ssh_port", 22)),
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=5",
        # Trust a node's host key the first time, refuse it if it changes later.
        "-o", "StrictHostKeyChecking=accept-new",
        "--",
        f"{server['ssh_user']}@{server['ip']}",
        "sh -s",
    ]
    try:
        result = subprocess.run(
            command, input=REMOTE_SCRIPT, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=120,
        )
    except subprocess.TimeoutExpired:
        return snapshot

    sections = parse_sections(result.stdout)
    # 255 is ssh's own failure code; the script itself may exit non-zero
    # (dnf check-update returns 100 when updates exist).
    if result.returncode == 255 or "HOSTNAME" not in sections:
        return snapshot

    if sections.get("FAMILY") == ["debian"]:
        packages = debian_packages(sections.get("UPDATES", []))
    else:
        packages = redhat_packages(sections.get("UPDATES", []), sections.get("SECURITY", []))
    packages = classify(packages)

    snapshot.update(
        os=" ".join(sections.get("OS", [])) or "Unknown",
        uptime=" ".join(sections.get("UPTIME", [])) or "Unknown",
        updates=len(packages),
        kernel_updates=sum(p["kernel"] for p in packages),
        security_updates=sum(p["security"] for p in packages),
        critical_packages=sum(p["critical"] for p in packages),
        status="Online",
        packages=packages,
    )
    return snapshot


def collect_all():
    servers = store.load_servers()
    with ThreadPoolExecutor(max_workers=10) as pool:
        snapshots = list(pool.map(collect_node, servers))
    for snapshot in snapshots:
        store.insert_snapshot(snapshot)
    return snapshots


def collect_forever(interval_seconds):
    while True:
        try:
            collect_all()
        except Exception as error:
            print(f"Collection failed: {error}", flush=True)
        time.sleep(interval_seconds)
