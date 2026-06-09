import json
import uuid
from datetime import datetime

from app.config import get_config

from app.token_manager import (
    validate_token,
    mark_token_used
)


CONFIG = get_config()

INVENTORY_FILE = CONFIG["inventory_file"]


def register_node(data):

    token = data.get("token")

    if not validate_token(token):

        return {
            "success": False,
            "message": "Invalid or used token"
        }

    with open(INVENTORY_FILE) as f:

        servers = json.load(f)

    hostname = data["hostname"]

    ip = data["ip"]

    ssh_user = data.get(
        "ssh_user",
        CONFIG["default_ssh_user"]
    )

    ssh_port = data.get(
        "ssh_port",
        22
    )

    for server in servers:

        if server["hostname"] == hostname:

            return {
                "success": False,
                "message": "Hostname already registered"
            }

        if server["ip"] == ip:

            return {
                "success": False,
                "message": "IP already registered"
            }

    new_server = {
        "node_id": str(uuid.uuid4()),
        "hostname": hostname,
        "ip": ip,
        "ssh_user": ssh_user,
        "ssh_port": ssh_port,
        "state": "active",
        "registered_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    servers.append(new_server)

    with open(INVENTORY_FILE, "w") as f:

        json.dump(
            servers,
            f,
            indent=4
        )

    mark_token_used(token)

    return {
        "success": True,
        "message": "Node registered successfully"
    }
