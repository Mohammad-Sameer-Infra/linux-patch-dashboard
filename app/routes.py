from flask import render_template

from app import app
from app.system_info import get_system_info
from app.inventory import load_servers
from app.remote_info import get_remote_system_info


@app.route("/")
def home():

    local_system = get_system_info()

    servers = load_servers()

    remote_servers = []

    for server in servers:

        remote_data = get_remote_system_info(server)

        remote_servers.append(remote_data)

    return render_template(
        "index.html",
        system_info=local_system,
        remote_servers=remote_servers
    )
