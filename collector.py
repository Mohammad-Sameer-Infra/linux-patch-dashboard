from app.inventory import (
    load_servers,
    update_last_seen
)
from app.remote_info import get_remote_system_info
from app.database import insert_telemetry

def main():

    servers = load_servers()

    for server in servers:

        remote_data = get_remote_system_info(server)

        insert_telemetry(remote_data)

        if remote_data["status"] == "Online":

            update_last_seen(
                server["hostname"]
            )

        print(
            f"Collected telemetry from "
            f"{server['hostname']}"
        )

if __name__ == "__main__":
    main()
