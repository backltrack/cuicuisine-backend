#! /bin/bash

root="$HOME/cuicuisine-data"
storage="$root/storage"
db="$root/db"
logdirpath="$root/logs"
mongovers="latest"
loglevel="DEBUG"

echo "STORAGE=$storage
DB=$db
MONGOVERS=$mongovers
LOGLEVEL=$loglevel
LOGDIRPATH=$logdirpath" > .docker-env

if [ ! -d "$root" ]; then
    mkdir "$root"
    chmod -R 777 $root
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

docker compose --env-file .docker-env up -d --build