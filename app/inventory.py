import json


def load_servers():
    with open("inventory/servers.json") as f:
        return json.load(f)
