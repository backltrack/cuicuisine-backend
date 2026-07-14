#! /bin/bash
# Executed from project root

export MONGO_PORT=27018
export ENV="production"
export LOGLEVEL="DEBUG"
export LOGDIRPATH="/server/cuicuisine-data/logs"

export INPUT_DIR="./imports"
export OUTPUT_DIR="/server/cuicuisine-data/storage/"

python src/feed.py

chmod -R 777 $OUTPUT_DIR