"""Collect telemetry from every node once. The dashboard also does this on a timer."""

from app.collect import collect_all

if __name__ == "__main__":
    for snapshot in collect_all():
        print(f"{snapshot['hostname']}: {snapshot['status']}, {snapshot['updates']} updates")
