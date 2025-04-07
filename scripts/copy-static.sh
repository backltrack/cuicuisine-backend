#!/bin/bash

if [ -d "static/" ]; then
    rm -rf static/
fi

mkdir static/
cp -r /run/media/nicolas/DATA/1-Documents/Programmation/Android/cuicuisine/build/web/* static/