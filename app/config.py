import json


CONFIG_FILE = "config/settings.json"


def get_config():

    with open(CONFIG_FILE) as f:

        return json.load(f)
