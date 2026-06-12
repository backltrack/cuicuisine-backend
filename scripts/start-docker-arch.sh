#! /bin/bash
# Executed from project root

cd "$(dirname "$0")"

# Load secrets from .env at project root
if [ ! -f ../.env ]; then
    echo "Error: .env file not found. Copy .env.example to .env and fill in your values."
    exit 1
fi
source ../.env

root="$HOME/cuicuisine-data"
storage="$root/storage"
db="$root/db"
logdirpath="$root/logs"
mongovers="latest"
loglevel="DEBUG"
domain="localhost"

echo "STORAGE=$storage
DB=$db
MONGOVERS=$mongovers
LOGLEVEL=$loglevel
LOGDIRPATH=$logdirpath
GMAIL_ADDRESS=$GMAIL_ADDRESS
GMAIL_APP_PASSWORD=$GMAIL_APP_PASSWORD
DOMAIN=$domain" > .docker-env

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

docker compose --env-file .docker-env up -d --build