from app.os_detector import get_os_family
from app.ssh_utils import run_remote_command


def get_available_updates(server):

    os_family = get_os_family(server)

    if os_family == "debian":

        updates = run_remote_command(
            server,
            "apt list --upgradable 2>/dev/null | tail -n +2"
        )

        return updates

    if os_family == "redhat":

        updates = run_remote_command(
            server,
            """
            if command -v dnf >/dev/null 2>&1
            then
                dnf check-update 2>/dev/null || true
            else
                yum check-update 2>/dev/null || true
            fi
            """
        )

        return updates

    return ""
