#!/bin/bash
# Daily incremental backup of storage/ and MongoDB.
#
# What it does:
#   1. Dumps MongoDB via `docker exec mongodump` (safe logical dump while running).
#   2. Hashes the dump + storage/ to detect whether anything actually changed.
#   3. If changed: creates a timestamped .tar.gz and rotates old archives.
#   4. If RCLONE_DEST is set: uploads the new archive to a cloud remote.
#
# Cron setup (sudo crontab -e):
#   0 3 * * * /server/cuicuisine-backend/scripts/backup.sh >> /server/cuicuisine-backups/backup.log 2>&1
#
# Cloud upload setup:
#   1. Install rclone:  sudo apt install rclone
#   2. Configure once:  rclone config
#        Recommended providers:
#          - Google Drive  (free 15 GB — remote type: "drive")
#          - Backblaze B2  (near-free object storage — remote type: "b2")
#   3. Set RCLONE_DEST below to "<remote-name>:<folder>", e.g. "gdrive:cuicuisine-backups"
set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
DATA_ROOT="/server/cuicuisine-data"
STORAGE_DIR="$DATA_ROOT/storage"
BACKUP_DIR="/server/cuicuisine-backups"
MONGO_CONTAINER="mongodb"
MAX_BACKUPS=15

# Set to "<rclone-remote>:<path>" to upload each new archive to cloud storage.
# Leave empty to keep backups local only.
# Example: RCLONE_DEST="gdrive:cuicuisine-backups"
RCLONE_DEST=""
# ─────────────────────────────────────────────────────────────────────────────

LOG_PREFIX="[$(date '+%Y-%m-%d %H:%M:%S')]"
HASH_FILE="$BACKUP_DIR/.last_content_hash"

mkdir -p "$BACKUP_DIR"

# Dump MongoDB into a temp directory via docker exec (avoids copying raw
# WiredTiger files while the server is running, which can be inconsistent)
if ! docker inspect --format '{{.State.Running}}' "$MONGO_CONTAINER" 2>/dev/null | grep -q true; then
    echo "$LOG_PREFIX ERROR: container '$MONGO_CONTAINER' is not running, aborting backup." >&2
    exit 1
fi

DUMP_TMP="$(mktemp -d)"
trap 'rm -rf "$DUMP_TMP"' EXIT

docker exec "$MONGO_CONTAINER" mongodump --out /tmp/mongodump_backup --quiet 2>/dev/null
docker cp "$MONGO_CONTAINER:/tmp/mongodump_backup" "$DUMP_TMP/db"
docker exec "$MONGO_CONTAINER" rm -rf /tmp/mongodump_backup

# Hash the content of both the dump and storage to detect real changes
current_hash=$(
    {
        find "$DUMP_TMP/db" -type f | sort | xargs -r sha256sum
        find "$STORAGE_DIR" -type f | sort | xargs -r sha256sum
    } | sha256sum | awk '{print $1}'
)

last_hash=""
[ -f "$HASH_FILE" ] && last_hash=$(cat "$HASH_FILE")

if [ "$current_hash" = "$last_hash" ]; then
    echo "$LOG_PREFIX No changes since last backup, skipping."
    exit 0
fi

# Create timestamped archive
TIMESTAMP="$(date '+%Y-%m-%d_%H-%M-%S')"
ARCHIVE="$BACKUP_DIR/cuicuisine-$TIMESTAMP.tar.gz"

# Archive layout inside the .tar.gz:
#   db/          ← mongodump output
#   storage/     ← user-uploaded files
tar -czf "$ARCHIVE" \
    -C "$DUMP_TMP" db \
    -C "$DATA_ROOT" storage

echo "$current_hash" > "$HASH_FILE"

# Rotate: delete oldest archives beyond the limit
ls -t "$BACKUP_DIR"/cuicuisine-*.tar.gz 2>/dev/null \
    | tail -n +$((MAX_BACKUPS + 1)) \
    | xargs -r rm -f

echo "$LOG_PREFIX Backup saved: $ARCHIVE ($(du -sh "$ARCHIVE" | cut -f1))"

# Cloud upload (optional — configure RCLONE_DEST above)
if [ -n "$RCLONE_DEST" ] && command -v rclone &>/dev/null; then
    echo "$LOG_PREFIX Uploading to $RCLONE_DEST ..."
    rclone copy "$ARCHIVE" "$RCLONE_DEST"
    echo "$LOG_PREFIX Upload done."
elif [ -n "$RCLONE_DEST" ]; then
    echo "$LOG_PREFIX WARNING: RCLONE_DEST is set but rclone is not installed, skipping upload." >&2
fi