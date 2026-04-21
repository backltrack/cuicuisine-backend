#! /bin/bash
# Executed from project root

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
    chmod -R 777 $storage
fi

if [ ! -d "$db" ]; then
    mkdir "$db"
    chmod -R 777 $db
    if [ ! -d "$db/config" ]; then
        mkdir "$db/config"
        chmod -R 777 $db/config
        cp ./config/mongodb.conf $db/config/mongodb.conf
    fi
    if [ ! -d "$db/data" ]; then
        mkdir "$db/data"
        chmod -R 777 $db/data
    fi
fi

if [ ! -d "$logdirpath" ]; then
    mkdir "$logdirpath"
    chmod -R 777 $logdirpath
fi

docker compose --env-file .docker-env up -d --build