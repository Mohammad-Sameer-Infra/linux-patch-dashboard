import subprocess
from datetime import datetime


def run_remote_command(ip, command):

    ssh_command = (
        f"ssh -o StrictHostKeyChecking=no "
        f"-o ConnectTimeout=5 "
        f"vmadmin@{ip} '{command}'"
    )

    output = subprocess.check_output(
        ssh_command,
        shell=True
    ).decode().strip()

    return output


def get_remote_system_info(server):

    ip = server["ip"]

    try:

        hostname = run_remote_command(
            ip,
            "hostname"
        )

        os_info = run_remote_command(
            ip,
            "grep PRETTY_NAME /etc/os-release | cut -d= -f2"
        ).replace('"', '')

        uptime = run_remote_command(
            ip,
            "uptime -p"
        )

        updates = run_remote_command(
            ip,
            "apt list --upgradable 2>/dev/null | tail -n +2 | wc -l"
        )

        return {
            "hostname": hostname,
            "ip": ip,
            "os": os_info,
            "uptime": uptime,
            "updates": updates,
            "status": "Online",
            "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception:

        return {
            "hostname": server["hostname"],
            "ip": ip,
            "os": "Unknown",
            "uptime": "Unknown",
            "updates": "Unknown",
            "status": "Offline",
            "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
