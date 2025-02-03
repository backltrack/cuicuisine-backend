#! /bin/bash

if [ ! -d "tls" ]; then
    mkdir tls
fi

#openssl req -newkey rsa:2048 -keyout tls/key.pem -x509 -days 365 -out tls/cert.pem

# echo "authorityKeyIdentifier=keyid,issuer
# basicConstraints=CA:FALSE
# subjectAltName = @atl_names
# [alt_names]
# DNS.1 = cuicuisine
# IP.1 = 192.168.1.28
# IP.2 = 192.168.156.248" > tls/san.ext

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
DNS.1 = talak.duckdns.org
IP.1 = 176.177.11.28
IP.2 = 192.168.1.85" > tls/san.cnf

# openssl req -newkey rsa:2048 -noenc -keyout tls/cuicuisine.key -out tls/cuicuisine.csr
# openssl req -x509 -sha256 -days 365 -newkey rsa:2048 -keyout tls/rootCA.key -out tls/rootCA.crt
# openssl x509 -req -CA tls/rootCA.crt -CAkey tls/rootCA.key -in tls/cuicuisine.csr -out tls/cuicuisine.crt -days 365 -CAcreateserial -extfile tls/san.ext

openssl req -x509 -nodes -days 730 -newkey rsa:2048 -keyout tls/cuicuisine.key -out tls/cuicuisine.crt -config tls/san.cnf