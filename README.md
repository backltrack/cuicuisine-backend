# Cuicuisine Backend

FastAPI backend for the Cuicuisine Flutter application.

## Prerequisites

- Python 3.10+
- Docker & Docker Compose
- A Gmail account with App Password enabled (for email sending)

## Initial setup

### 1. RSA key pair

Generate the key pair used to encrypt/decrypt sensitive data:

```bash
openssl genpkey -algorithm RSA -out src/private_key.pem
openssl rsa -in src/private_key.pem -pubout -out public_key.pem
```

Store `src/private_key.pem` in `src/` (already the correct location).  
Share `public_key.pem` with the Flutter client application.

### 2. Gmail App Password

The server sends emails (password reset) via Gmail SMTP. To generate an App Password:

1. Enable 2-Step Verification on the sender Gmail account
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Create a new App Password (e.g. "Cuicuisine Backend")
4. Copy the generated 16-character password

### 3. Environment file

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```
GMAIL_ADDRESS=your_address@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Generate with: openssl rand -hex 32
SECRET_KEY_ACCESS=
SECRET_KEY_REFRESH=
```

`SECRET_KEY_ACCESS`/`SECRET_KEY_REFRESH` sign the JWT access/refresh tokens (`HS256`) — keep them secret and unique per deployment. Rotating either value invalidates all outstanding tokens, signing every logged-in user out.

This file is gitignored. It is the single source of truth for secrets — used both by the local dev server and by the Docker start scripts to generate `.docker-env`.

### 4. TLS certificate

TLS is handled by a [Caddy](https://caddyserver.com/) reverse proxy in front of `uvicorn` (see `Caddyfile` and the `caddy` service in `compose.yaml`). `uvicorn` itself serves plain HTTP on the internal Docker network; no certificate files need to be generated manually.

- **Production (Raspberry Pi)**: `start-docker-rpi.sh` sets `DOMAIN=mycuicuisine.duckdns.org`. Caddy automatically requests and renews a trusted [Let's Encrypt](https://letsencrypt.org/) certificate for that domain. This requires ports `80` and `443` to be forwarded from your router to the Pi.
- **Local Docker (Arch / desktop)**: `start-docker-arch.sh` sets `DOMAIN=localhost`. Caddy automatically issues a certificate from its own local CA for `localhost` (no public CA involved).

---

## Running the server

### Docker (Arch / desktop)

```bash
./scripts/start-docker-arch.sh
```

### Docker (Raspberry Pi)

```bash
./scripts/start-docker-rpi.sh
```

The Docker scripts read `.env`, combine secrets with platform-specific paths, and generate `.docker-env` before starting Docker Compose.

## Backup

`scripts/backup.sh` backs up MongoDB and the user-uploaded files in `storage/`. It is already on the Pi after a `git pull` — it only needs a cron entry and, optionally, rclone for cloud upload.

### What it does

- Dumps MongoDB via `docker exec mongodump` (a safe logical dump while the server keeps running, unlike copying raw WiredTiger files).
- Hashes the dump + `storage/` to detect whether anything changed since the last run — skips archiving if not.
- Creates a `.tar.gz` named `cuicuisine-YYYY-MM-DD_HH-MM-SS.tar.gz` inside `/server/cuicuisine-backups/`.
- Rotates archives automatically, keeping the 15 most recent.

### Schedule (cron)

```bash
sudo crontab -e
```

Add this line to run nightly at 3 AM:

```
0 3 * * * /server/cuicuisine-backend/scripts/backup.sh >> /server/cuicuisine-backups/backup.log 2>&1
```

### Cloud upload (optional)

Backups are local-only by default. To upload each new archive to cloud storage:

**1. Install rclone**

```bash
sudo apt install rclone
```

**2. Configure a remote (one-time)**

```bash
rclone config
```

Recommended providers:

| Provider | Why |
|---|---|
| Google Drive | Free 15 GB — good choice if you already have a Google account |
| Backblaze B2 | ~$0.006/GB/month, effectively free at this scale, no Google dependency |

Follow the interactive wizard (choose the provider, authenticate via browser). Name the remote something recognisable, e.g. `gdrive` or `b2`.

**3. Enable upload in the script**

Edit `RCLONE_DEST` at the top of `scripts/backup.sh`:

```bash
RCLONE_DEST="gdrive:cuicuisine-backups"   # Google Drive
# or
RCLONE_DEST="b2:cuicuisine-backups"       # Backblaze B2
```

From that point on, every new archive is uploaded automatically after being saved locally.

---

## Updating the data model

When you change the shape of stored documents (rename/remove/add a field, restructure a collection, etc.), two separate things need updating:

### 1. Add a migration

Write a migration function in `src/server/migrations.py` and register it with the next unused integer version:

```python
@register_migration(2, "Describe what this migration does")
def migration_002(db: Database):
    ...
```

Migrations run automatically at startup (`apply_migrations`, called from the `lifespan` handler in `src/server/app.py`) and are tracked in the `migrations` collection so each one only runs once. Version numbers here are just a sequential counter for migrations — unrelated to the app/API versions below.

### 2. Bump the app/API version, if the change is breaking

`src/server/app.py` defines two constants, exposed to clients via `GET /version`:

```python
MINIMUM_APP_VERSION = "0.1.0"  # bump when shipping breaking API or model changes
API_VERSION = 1                # bump on any breaking API change
```

- Bump `API_VERSION` whenever the change breaks compatibility with how the API currently behaves (response shape changes, removed/renamed fields/endpoints, etc.).
- Bump `MINIMUM_APP_VERSION` (to the next Flutter app version you're shipping) when older app builds would actually break against the new backend — this is the floor the client checks to force users to update.

If the data model change is backward-compatible (e.g. adding an optional field), neither constant needs to change — just the migration.
