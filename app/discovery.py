import subprocess


def is_host_alive(ip):

    try:

        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        return result.returncode == 0

    except Exception:

        return False


def discover_hosts():

    discovered_hosts = []

    subnet = "192.168.110."

    for i in range(1, 255):

        ip = f"{subnet}{i}"

        if is_host_alive(ip):

            discovered_hosts.append(ip)

    return discovered_hosts
