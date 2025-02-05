#! /bin/bash

uvicorn --app-dir src server.app:app --host 0.0.0.0 --port 8000 --ssl-keyfile ./tls/key.pem --ssl-certfile ./tls/cert.pem --ssl-keyfile-password cuicuisine --http h11