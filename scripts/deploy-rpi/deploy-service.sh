#!/bin/bash

sudo cp cuicuisine.service /lib/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cuicuisine
sudo systemctl start cuicuisine