#! /bin/bash

uvicorn --app-dir src server.app:app --host 0.0.0.0 --port 8000 --ssl-keyfile ./tls/cuicuisine.key --ssl-certfile ./tls/cuicuisine.crt --ssl-keyfile-password cuicuisine # --http h11