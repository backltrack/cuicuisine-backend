#! /bin/bash
# Executed from project root

export MONGO_PORT=27018
export ENV="production"
export LOGLEVEL="DEBUG"
export LOGDIRPATH="$HOME/cuicuisine-data/logs"

python src/feed.py