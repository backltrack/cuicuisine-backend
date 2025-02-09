#! /bin/bash

root="$HOME/cuicuisine-data/"
storage="$root/storage/"
db="$root/db/"
mongovers="4.4.18"

echo "STORAGE=$storage
DB=$db
MONGOVERS=$mongovers" > .docker-env

if [ ! -d "$root" ]; then
    mkdir "$root"
fi

if [ ! -d "$storage" ]; then
    mkdir "$storage"
fi

if [ ! -d "$db" ]; then
    mkdir "$db"
fi

docker compose --env-file .docker-env up --build