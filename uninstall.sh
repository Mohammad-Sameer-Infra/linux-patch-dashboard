#!/bin/bash
# Remove the Linux Patch Dashboard.
#
#   sudo ./uninstall.sh           Remove the service and virtual environment.
#                                 Keeps data, settings and this folder, so
#                                 install.sh can bring everything back.
#   sudo ./uninstall.sh --purge   Also delete the data (nodes, history, SSH key),
#                                 the patchdashboard account and this folder.
#                                 Saves a backup to /root first.
#
# Options: --no-backup (with --purge), --yes (don't ask for confirmation).
set -euo pipefail

SERVICE_USER="patchdashboard"
SERVICE="linux-patch-dashboard"
SERVICE_FILE="/etc/systemd/system/$SERVICE.service"
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
SETTINGS="$INSTALL_DIR/config/settings.json"

PURGE=0
BACKUP=1
ASSUME_YES=0
for arg in "$@"; do
    case "$arg" in
        --purge) PURGE=1 ;;
        --no-backup) BACKUP=0 ;;
        --yes | -y) ASSUME_YES=1 ;;
        -h | --help) sed -n '2,11p' "$0" | cut -c3-; exit 0 ;;
        *) echo "Unknown option: $arg (see --help)"; exit 1 ;;
    esac
done

[ "$(id -u)" -eq 0 ] || { echo "Run uninstall.sh as root or with sudo."; exit 1; }

# data_dir from settings.json (relative paths are inside the install folder).
DATA_DIR=$(python3 -c '
import json, os, sys
print(os.path.join(sys.argv[2], json.load(open(sys.argv[1])).get("data_dir", "data")))
' "$SETTINGS" "$INSTALL_DIR" 2>/dev/null || echo "/var/lib/patchdashboard")

# Refuse to delete anything that isn't clearly an application folder.
safe_rm_dir() {
    case "$1" in
        "" | / | /bin | /boot | /dev | /etc | /home | /lib | /opt | /proc | /root | /run | \
        /sbin | /srv | /sys | /tmp | /usr | /var | /var/lib)
            echo "[SKIP] Refusing to delete $1"; return ;;
    esac
    [[ "$1" == /* ]] || { echo "[SKIP] Not an absolute path: $1"; return; }
    if [ -d "$1" ]; then
        rm -rf -- "$1"
        echo "[DONE] Deleted $1"
    fi
}

BACKUP_FILE="/root/patchli-backup-$(date +%Y%m%d-%H%M%S).tar.gz"

echo "This will:"
echo "  - stop and remove the $SERVICE service"
echo "  - delete $INSTALL_DIR/venv"
if [ "$PURGE" -eq 1 ]; then
    [ "$BACKUP" -eq 1 ] && echo "  - back up $DATA_DIR and settings.json to $BACKUP_FILE"
    echo "  - PERMANENTLY delete $DATA_DIR (nodes, history, dashboard SSH key)"
    echo "  - delete the $SERVICE_USER account"
    echo "  - delete $INSTALL_DIR"
else
    echo "Kept: $DATA_DIR, $SETTINGS and $INSTALL_DIR"
fi
echo
if [ "$ASSUME_YES" -eq 0 ]; then
    read -rp "Type 'yes' to continue: " ANSWER
    [ "$ANSWER" = "yes" ] || { echo "Cancelled. Nothing was changed."; exit 1; }
fi

if [ "$PURGE" -eq 1 ] && [ "$BACKUP" -eq 1 ]; then
    items=()
    for path in "$DATA_DIR" "$SETTINGS"; do
        [ -e "$path" ] && items+=("${path#/}")
    done
    if [ "${#items[@]}" -gt 0 ]; then
        # The backup contains the dashboard's private SSH key.
        (umask 077 && tar -czf "$BACKUP_FILE" -C / "${items[@]}")
        echo "[DONE] Backup saved to $BACKUP_FILE (readable by root only)"
    fi
fi

systemctl disable --now "$SERVICE" 2>/dev/null || true
rm -f "$SERVICE_FILE"
systemctl daemon-reload
systemctl reset-failed "$SERVICE" 2>/dev/null || true
echo "[DONE] Removed the $SERVICE service"

rm -rf -- "$INSTALL_DIR/venv"
echo "[DONE] Deleted $INSTALL_DIR/venv"

if [ "$PURGE" -eq 1 ]; then
    # List the nodes before their inventory is deleted, so the admin knows
    # where to remove the dashboard's key from authorized_keys.
    NODES=$(python3 -c '
import json, sys
for n in json.load(open(sys.argv[1])):
    print("    %s@%s  (%s)" % (n["ssh_user"], n["ip"], n["hostname"]))
' "$DATA_DIR/servers.json" 2>/dev/null || true)

    safe_rm_dir "$DATA_DIR"

    if getent passwd "$SERVICE_USER" >/dev/null; then
        pkill -u "$SERVICE_USER" 2>/dev/null || true
        userdel "$SERVICE_USER"
        echo "[DONE] Deleted the $SERVICE_USER account"
    fi
    if getent group "$SERVICE_USER" >/dev/null; then
        groupdel "$SERVICE_USER"
    fi

    cd /
    safe_rm_dir "$INSTALL_DIR"

    echo
    echo "Patchli has been removed."
    if [ -n "$NODES" ]; then
        echo "On each managed node, remove the line ending in '$SERVICE_USER@...'"
        echo "from ~/.ssh/authorized_keys:"
        echo "$NODES"
    fi
else
    echo
    echo "Patchli has been removed. Your data and settings were kept."
    echo "To reinstall:      sudo $INSTALL_DIR/install.sh"
    echo "To remove it all:  sudo $INSTALL_DIR/uninstall.sh --purge"
fi
