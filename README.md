# HOW TO

# Create RSA key pair
`openssl genpkey -algorithm RSA -out private_key.pem`
`openssl rsa -in private_key.pem -pubout -out public_key.pem`

store private key in src/server/
store public key in client application