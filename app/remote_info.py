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

        updates_list = run_remote_command(
            ip,
            "apt list --upgradable 2>/dev/null | tail -n +2"
        )

        update_packages = (
                updates_list.splitlines()
                if updates_list else []
        )

        updates = len(update_packages)

        kernel_updates = len([
            p for p in update_packages
            if "linux-image" in p
            or "linux-headers" in p
        ])

        security_updates = len([
            p for p in update_packages
            if any(keyword in p.lower() for keyword in [
                "openssl",
                "sudo",
                "systemd",
                "curl",
                "bash",
                "ssh"
        ])
    ])

        critical_packages = len([
            p for p in update_packages
            if any(keyword in p.lower() for keyword in [
                "linux",
                "openssl",
                "systemd",
                "sudo"
        ])
    ])

        return {
            "hostname": hostname,
            "ip": ip,
            "os": os_info,
            "uptime": uptime,
            "updates": updates,
            "kernel_updates": kernel_updates,
            "security_updates": security_updates,
            "critical_packages": critical_packages,
            "update_packages": update_packages,
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
            "kernel_updates": 0,
            "security_updates": 0,
            "critical_packages": 0,
            "update_packages": [],
            "status": "Offline",
            "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
