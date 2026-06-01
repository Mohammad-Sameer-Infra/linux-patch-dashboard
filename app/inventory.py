import json
from datetime import datetime

from app.config import get_config


CONFIG = get_config()

INVENTORY_FILE = CONFIG["inventory_file"]


def load_servers():

    with open(INVENTORY_FILE) as f:

        return json.load(f)


def save_servers(servers):

    with open(INVENTORY_FILE, "w") as f:

        json.dump(servers, f, indent=4)


def update_last_seen(hostname):

    servers = load_servers()

    for server in servers:

        if server["hostname"] == hostname:

            server["last_seen"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            break

    save_servers(servers)
