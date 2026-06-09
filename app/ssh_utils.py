import subprocess

from app.config import SETTINGS


def run_remote_command(server, command):

    ip = server["ip"]

    ssh_user = server.get(
        "ssh_user",
        SETTINGS["default_ssh_user"]
    )

    ssh_port = server.get(
        "ssh_port",
        22
    )

    ssh_command = (
        f"ssh -p {ssh_port} "
        f"-o StrictHostKeyChecking=no "
        f"-o ConnectTimeout=5 "
        f"{ssh_user}@{ip} "
        f"'{command}'"
    )

    output = subprocess.check_output(
        ssh_command,
        shell=True
    ).decode().strip()

    return output
