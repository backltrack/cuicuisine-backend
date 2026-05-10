#! /bin/bash
set -e

PYTHON=python3.13
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "ERROR: python3.13 is not installed."
    echo "This project requires Python 3.13 (Dockerfile and dependencies are built for 3.13)."
    echo "Please install Python 3.13 or use the Docker setup."
    exit 1
fi

PY_VERSION=$($PYTHON -c 'import sys; print("{}.{}.{}".format(*sys.version_info[:3]))')
if [[ "$PY_VERSION" != 3.13.* ]]; then
    echo "ERROR: Python 3.13 is required, but $PY_VERSION was found."
    exit 1
fi

if [ -d "venv" ]; then
    source deactivate || true
    rm -rf venv
fi

if [ -d ".venv" ]; then
    source deactivate || true
    rm -rf .venv
fi

$PYTHON -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt