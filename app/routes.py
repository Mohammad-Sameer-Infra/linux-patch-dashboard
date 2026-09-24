"""Dashboard pages, read from the telemetry database, and the registration API."""

import platform
import socket
import subprocess

from flask import Response, abort, jsonify, render_template, request

from app import app, store

NOT_COLLECTED = {
    "os": "", "uptime": "", "updates": 0, "kernel_updates": 0,
    "security_updates": 0, "critical_packages": 0, "status": "Pending",
    "last_check": "Never", "last_seen": None, "packages": [],
}

# URL segment: (page title, package flag to filter on)
CATEGORIES = {
    "all-updates": ("All Updates", None),
    "kernel-updates": ("Kernel Updates", "kernel"),
    "security-updates": ("Security Updates", "security"),
    "critical-packages": ("Critical Packages", "critical"),
}


def get_nodes():
    """Every inventory node merged with its latest snapshot."""
    latest = store.latest_snapshots()
    return [
        {**NOT_COLLECTED, **latest.get(server["hostname"], {}), **server}
        for server in store.load_servers()
    ]


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


@app.route("/")
def home():
    nodes = get_nodes()
    checks = [n["last_check"] for n in nodes if n["last_check"] != "Never"]
    return render_template(
        "index.html",
        nodes=nodes,
        system_info=dashboard_server(),
        online_nodes=sum(n["status"] == "Online" for n in nodes),
        offline_nodes=sum(n["status"] == "Offline" for n in nodes),
        last_updated=max(checks, default="No Data"),
    )


@app.route("/online")
@app.route("/offline")
def nodes_by_status():
    status = request.path.strip("/").capitalize()
    return render_template(
        "nodes.html",
        title=f"{status} Nodes",
        nodes=[n for n in get_nodes() if n["status"] == status],
    )


@app.route("/history")
def history():
    return render_template("history.html", telemetry_history=store.telemetry_history())


@app.route("/node/<hostname>")
def node_details(hostname):
    return render_template("node_details.html", server=find_node(hostname))


@app.route("/node/<hostname>/<category>")
def package_details(hostname, category):
    if category not in CATEGORIES:
        abort(404)
    title, flag = CATEGORIES[category]
    node = find_node(hostname)
    packages = [p["line"] for p in node["packages"] if flag is None or p[flag]]
    return render_template(
        "package_details.html", hostname=hostname, title=title, packages=packages,
    )


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
