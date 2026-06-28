#!/bin/bash
# Fetches the latest web build + APK from the cuicuisine (frontend) repo's
# GitHub releases and drops them into static/ and downloads/.
# Replaces manually copying build output from a sibling checkout.
set -e

REPO="backltrack/cuicuisine"
cd "$(dirname "$0")/.."

echo "Fetching latest release info for $REPO..."
release_json="$(mktemp)"
trap 'rm -f "$release_json"' EXIT
curl -sf "https://api.github.com/repos/$REPO/releases/latest" -o "$release_json"

web_url=$(python3 -c "import json; d=json.load(open('$release_json')); print(next((a['browser_download_url'] for a in d['assets'] if a['name']=='cuicuisine-web.zip'), ''))")
apk_name=$(python3 -c "import json; d=json.load(open('$release_json')); print(next((a['name'] for a in d['assets'] if a['name'].endswith('.apk')), ''))")
apk_url=$(python3 -c "import json; d=json.load(open('$release_json')); print(next((a['browser_download_url'] for a in d['assets'] if a['name'].endswith('.apk')), ''))")

if [ -z "$web_url" ] || [ -z "$apk_url" ]; then
    echo "Error: latest release of $REPO is missing the web build or APK asset." >&2
    exit 1
fi

echo "Updating static/ ..."
web_zip="$(mktemp)"
curl -sfL "$web_url" -o "$web_zip"
rm -rf static && mkdir static
python3 -c "import zipfile; zipfile.ZipFile('$web_zip').extractall('static')"
rm -f "$web_zip"

echo "Updating downloads/ ($apk_name) ..."
rm -rf downloads && mkdir downloads
curl -sfL "$apk_url" -o "downloads/$apk_name"

echo "Done."
