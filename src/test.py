from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64
import random, string

from server.model import *
from server.mongo import *


def encrypt_data(data):
    with open("/run/media/nicolas/DATA/1-Documents/Programmation/Android/cuicuisine/assets/keys/public_key.pem", "rb") as f:
        key_str = f.read()
        print(key_str)
        key = RSA.importKey(key_str)

    encryptor = PKCS1_OAEP.new(key)

    cipher_text = encryptor.encrypt(data.encode())
    return base64.b64encode(cipher_text)


def decrypt_data(data):
    decoded_data = base64.b64decode(data)

    with open("private_key.pem", "rb") as k:
        key = RSA.importKey(k.read())

    decipher = PKCS1_OAEP.new(key)
    return decipher.decrypt(decoded_data)

enc = encrypt_data("ToChange01")
print(enc)

dec = decrypt_data(enc)
print(dec)