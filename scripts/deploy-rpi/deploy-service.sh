#!/bin/bash

mkdir -p ~/.config/systemd/user
cp cuicuisine.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable cuicuisine
systemctl --user start cuicuisine