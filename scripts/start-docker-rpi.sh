#! /bin/bash

# Send IP to duckdns
echo url="https://www.duckdns.org/update?domains=mycuicuisine&token=7916ea28-fc78-4a68-9959-acf29d88a04a&ip=" | curl -k -o ~/duckdns/duck.log -K -

# get latest version
cd "$(dirname "$0")"
git pull

# SET ENV VARS
root="$HOME/cuicuisine-data"
storage="$root/storage"
db="$root/db"
logdirpath="$root/logs"
mongovers="4.4.18"
loglevel="INFO"

echo "STORAGE=$storage
DB=$db
MONGOVERS=$mongovers
LOGLEVEL=$loglevel
LOGDIRPATH=$logdirpath" > .docker-env

# Check if directories exist
if [ ! -d "$root" ]; then
    mkdir "$root"
fi

if [ ! -d "$storage" ]; then
    mkdir "$storage"
fi

if [ ! -d "$db" ]; then
    mkdir "$db"
fi

if [ ! -d "$logdirpath" ]; then
    mkdir "$logdirpath"
fi

chmod -R 777 $root

# Start docker
docker compose --env-file .docker-env up --build