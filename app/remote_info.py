import subprocess
from datetime import datetime

from app.package_manager import (
    get_available_updates
)

from app.ssh_utils import (
    run_remote_command
)

from app.os_detector import (
    get_os_family
)

from app.update_classifier import (
    classify_updates
)


def get_remote_system_info(server):

    ip = server["ip"]

    try:

        hostname = run_remote_command(
            server,
            "hostname"
        )

        os_info = run_remote_command(
            server,
            "grep PRETTY_NAME /etc/os-release | cut -d= -f2"
        ).replace('"', '')

        uptime = run_remote_command(
            server,
            "uptime -p"
        )

        updates_list = get_available_updates(
            server
        )

        update_packages = (
            updates_list.splitlines()
            if updates_list else []
        )

        updates = len(update_packages)

        os_family = get_os_family(
            server
        )

        classification = classify_updates(
            os_family,
            update_packages
        )

        kernel_updates = (
            classification["kernel_updates"]
        )

        security_updates = (
            classification["security_updates"]
        )

        critical_packages = (
            classification["critical_packages"]
        )

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
            "last_check": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }

    except Exception:

        return {
            "hostname": server["hostname"],
            "ip": ip,
            "os": "Unknown",
            "uptime": "Unknown",
            "updates": "0",
            "kernel_updates": 0,
            "security_updates": 0,
            "critical_packages": 0,
            "update_packages": [],
            "status": "Offline",
            "last_check": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }
