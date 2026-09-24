"""Dashboard pages, read from the telemetry database, and the registration API."""

import platform
import socket
import subprocess
from collections import Counter
from datetime import datetime

from flask import Response, abort, jsonify, render_template, request

from app import app, store

NOT_COLLECTED = {
    "os": "", "uptime": "", "updates": 0, "kernel_updates": 0,
    "security_updates": 0, "critical_packages": 0, "status": "Pending",
    "last_check": "Never", "last_seen": None, "packages": [],
}

# Worst first: the order of the fleet health bar and its legend.
POSTURES = ["security", "updates", "current", "offline", "pending"]

# Old package-list URLs open the node page with that filter selected.
CATEGORIES = {
    "all-updates": "all",
    "kernel-updates": "kernel",
    "security-updates": "security",
    "critical-packages": "critical",
}


def posture(node):
    """One word for a node's patch state, used for its status pill."""
    if node["status"] == "Offline":
        return "offline"
    if node["status"] != "Online":
        return "pending"
    if node["security_updates"]:
        return "security"
    return "updates" if node["updates"] else "current"


def get_nodes():
    """Every inventory node merged with its latest snapshot."""
    latest = store.latest_snapshots()
    nodes = []
    for server in store.load_servers():
        node = {**NOT_COLLECTED, **latest.get(server["hostname"], {}), **server}
        node["posture"] = posture(node)
        nodes.append(node)
    return nodes


def find_node(hostname):
    for node in get_nodes():
        if node["hostname"] == hostname:
            return node
    abort(404)


def dashboard_server():
    try:
        os_info = platform.freedesktop_os_release()["PRETTY_NAME"]
    except (OSError, KeyError):
        os_info = platform.platform()
    try:
        with open("/proc/uptime") as f:
            seconds = int(float(f.read().split()[0]))
        uptime = f"up {seconds // 86400} days, {seconds % 86400 // 3600} hours"
    except OSError:
        uptime = "Unknown"
    return {
        "hostname": socket.gethostname(),
        "os_info": os_info,
        "kernel": platform.release(),
        "uptime": uptime,
    }


def key_fingerprint():
    try:
        output = subprocess.run(
            ["ssh-keygen", "-lf", store.SETTINGS["public_key_file"]],
            capture_output=True, text=True,
        ).stdout.split()
    except OSError:
        output = []
    return output[1] if len(output) > 1 else "unavailable"


@app.template_filter("ago")
def ago(timestamp):
    """ "2026-09-24 10:00:00" -> "5 min ago"."""
    try:
        then = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return timestamp or "Never"
    seconds = int((datetime.now() - then).total_seconds())
    for unit, size in (("day", 86400), ("hr", 3600), ("min", 60)):
        if seconds >= size:
            return f"{seconds // size} {unit} ago"
    return "just now"


@app.route("/")
def home():
    nodes = get_nodes()
    checks = [n["last_check"] for n in nodes if n["last_check"] != "Never"]
    postures = Counter(n["posture"] for n in nodes)
    return render_template(
        "index.html",
        nodes=nodes,
        system_info=dashboard_server(),
        postures=[(p, postures[p]) for p in POSTURES if postures[p]],
        totals={
            key: sum(n[key] for n in nodes)
            for key in ("updates", "security_updates", "kernel_updates", "critical_packages")
        },
        online_nodes=sum(n["status"] == "Online" for n in nodes),
        offline_nodes=sum(n["status"] == "Offline" for n in nodes),
        last_updated=max(checks, default=None),
    )


@app.route("/online")
@app.route("/offline")
def nodes_by_status():
    status = request.path.strip("/").capitalize()
    return render_template(
        "nodes.html",
        title=f"{status} nodes",
        nodes=[n for n in get_nodes() if n["status"] == status],
    )


@app.route("/history")
def history():
    return render_template("history.html", telemetry_history=store.telemetry_history())


@app.route("/node/<hostname>")
def node_details(hostname, category="all"):
    node = find_node(hostname)
    return render_template(
        "node_details.html",
        server=node,
        history=store.node_history(hostname),
        category=category,
    )


@app.route("/node/<hostname>/<category>")
def package_details(hostname, category):
    if category not in CATEGORIES:
        abort(404)
    return node_details(hostname, CATEGORIES[category])


@app.route("/generate-token")
def generate_registration_token():
    return render_template(
        "token.html", token=store.create_token(), fingerprint=key_fingerprint(),
    )


@app.route("/api/register", methods=["POST"])
def api_register():
    try:
        success, message = store.register_node(request.get_json(silent=True) or {})
    except ValueError as error:
        success, message = False, str(error)
    return jsonify(success=success, message=message), 200 if success else 400


@app.route("/public-key")
def public_key():
    with open(store.SETTINGS["public_key_file"]) as f:
        return Response(f.read(), mimetype="text/plain")
