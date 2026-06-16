import json


CONFIG_FILE = "config/settings.json"


def get_config():

    with open(CONFIG_FILE) as f:

        settings = json.load(f)

    settings.setdefault(
        "default_ssh_user",
        "vmadmin"
    )

    return settings


SETTINGS = get_config()
