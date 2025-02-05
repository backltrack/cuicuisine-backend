#! /bin/bash

if [ ! -d "tls" ]; then
    mkdir tls
fi

## ROBIN
# echo "[req]
# default_bits  = 2048
# distinguished_name = req_distinguished_name
# req_extensions = req_ext
# x509_extensions = v3_req
# prompt = no

# [req_distinguished_name]
# countryName = FR
# stateOrProvinceName = N/A
# localityName = N/A
# organizationName = Self-signed certificate
# commonName = Self-signed certificate

# [req_ext]
# subjectAltName = @alt_names

# [v3_req]
# subjectAltName = @alt_names

# [alt_names]
# DNS.1 = talak.duckdns.org
# IP.1 = 176.177.11.28
# IP.2 = 192.168.1.85" > tls/san.cnf

## DEV
echo "[req]
default_bits  = 2048
distinguished_name = req_distinguished_name
req_extensions = req_ext
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
countryName = FR
stateOrProvinceName = N/A
localityName = N/A
organizationName = Self-signed certificate
commonName = Self-signed certificate

[req_ext]
subjectAltName = @alt_names

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = mycuicuisine.duckdns.org
IP.1 = 192.168.1.28
IP.2 = 192.168.1.48
IP.3 = 192.168.156.248" > tls/san.cnf

openssl req -x509 -nodes -days 730 -newkey rsa:2048 -keyout tls/cuicuisine.key -out tls/cuicuisine.crt -config tls/san.cnf