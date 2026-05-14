#!/bin/bash

if [ -d "static/" ]; then
    rm -rf static/
fi

mkdir static/
cp -r /run/media/DATA/Projets/cuicuisine/build/web/* static/

if [ -d "downloads/" ]; then
    rm -rf downloads/
fi

mkdir downloads/
cp -r /run/media/DATA/Projets/cuicuisine/build/app/outputs/flutter-apk/cuicuisine-*.apk downloads/