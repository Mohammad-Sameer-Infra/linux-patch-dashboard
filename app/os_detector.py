from app.ssh_utils import run_remote_command


def get_os_family(server):

    os_release = run_remote_command(
        server,
        "cat /etc/os-release"
    ).lower()

    if any(x in os_release for x in [
        "ubuntu",
        "debian"
    ]):

        return "debian"

    if any(x in os_release for x in [
        "rhel",
        "red hat",
        "rocky",
        "almalinux",
        "oracle linux",
        "centos"
    ]):

        return "redhat"

    return "unknown"
