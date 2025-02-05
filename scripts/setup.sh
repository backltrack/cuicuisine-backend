#! /bin/bash

if [ -d "venv" ]; then
    source deactivate
    rm -r venv
fi

if [ -d ".venv" ]; then
    source deactivate
    rm -r .venv
fi

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt