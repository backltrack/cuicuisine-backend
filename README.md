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
```

This file is gitignored. It is the single source of truth for secrets — used both by the local dev server and by the Docker start scripts to generate `.docker-env`.

### 4. TLS certificate

For local development, generate a self-signed certificate:

```bash
./scripts/gen-self-signed-ssl.sh
```

---

## Running the server

### Local development

```bash
./scripts/setup.sh          # create venv and install dependencies (first time)
./scripts/start-dev-server.sh
```

### Docker (Arch / desktop)

```bash
./scripts/start-docker-arch.sh
```

### Docker (Raspberry Pi)

```bash
./scripts/start-docker-rpi.sh
```

The Docker scripts read `.env`, combine secrets with platform-specific paths, and generate `.docker-env` before starting Docker Compose.
