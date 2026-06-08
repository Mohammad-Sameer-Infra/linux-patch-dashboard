import subprocess

from app.config import SETTINGS


def run_remote_command(ip, command):

    ssh_user = SETTINGS["default_ssh_user"]

    ssh_command = (
        f"ssh -o StrictHostKeyChecking=no "
        f"-o ConnectTimeout=5 "
        f"{ssh_user}@{ip} "
        f"'{command}'"
    )

    output = subprocess.check_output(
        ssh_command,
        shell=True
    ).decode().strip()

    return output
