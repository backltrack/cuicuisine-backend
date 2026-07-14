#! /bin/bash
# Executed from project root

# Send IP to duckdns
echo url="https://www.duckdns.org/update?domains=mycuicuisine&token=7916ea28-fc78-4a68-9959-acf29d88a04a&ip=" | curl -k -o ./duck.log -K -

# get latest version
cd "$(dirname "$0")"
git pull

# fetch latest frontend web build + apk from the cuicuisine repo's GitHub releases
bash ./fetch-frontend-build.sh

# Load secrets from .env at project root
if [ ! -f ../.env ]; then
    echo "Error: .env file not found. Copy .env.example to .env and fill in your values."
    exit 1
fi
source ../.env

# SET ENV VARS
root="/server/cuicuisine-data"
storage="$root/storage"
db="$root/db"
logdirpath="$root/logs"
mongovers="4.4.18"
loglevel="DEBUG" #"INFO"
domain="mycuicuisine.duckdns.org"

echo "STORAGE=$storage
DB=$db
MONGOVERS=$mongovers
LOGLEVEL=$loglevel
LOGDIRPATH=$logdirpath
GMAIL_ADDRESS=$GMAIL_ADDRESS
GMAIL_APP_PASSWORD=$GMAIL_APP_PASSWORD
SECRET_KEY_ACCESS=$SECRET_KEY_ACCESS
SECRET_KEY_REFRESH=$SECRET_KEY_REFRESH
DOMAIN=$domain" > .docker-env

# Check if directories exist
if [ ! -d "$root" ]; then
    mkdir "$root"
    chmod -R 777 $root
fi

if [ ! -d "$storage" ]; then
    mkdir "$storage"
    chmod -R 777 $storage
fi

if [ ! -d "$db" ]; then
    mkdir "$db"
    chmod -R 777 $db
fi
if [ ! -d "$db/config" ]; then
    mkdir "$db/config"
    chmod -R 777 $db/config
fi
if [ ! -f "$db/config/mongodb.conf" ]; then
    cp ../config/mongodb.conf $db/config/mongodb.conf
fi

if [ ! -d "$db/data" ]; then
    mkdir "$db/data"
    chmod -R 777 $db/data
fi

if [ ! -d "$logdirpath" ]; then
    mkdir "$logdirpath"
    chmod -R 777 $logdirpath
fi

# Start docker
docker compose --env-file .docker-env up --build
