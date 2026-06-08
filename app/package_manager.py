from app.os_detector import get_os_family
from app.ssh_utils import run_remote_command


def get_available_updates(server):

    ip = server["ip"]

    os_family = get_os_family(ip)

    if os_family == "debian":

        updates = run_remote_command(
            ip,
            "apt list --upgradable 2>/dev/null | tail -n +2"
        )

        return updates

    if os_family == "redhat":

        updates = run_remote_command(
            ip,
            "dnf check-update 2>/dev/null || true"
        )

        return updates

    return ""
