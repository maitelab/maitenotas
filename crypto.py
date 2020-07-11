""" 
Application: Maitenotas
Made by Taksan Tong
https://github.com/maitelab/maitenotas

Functions related to encrypt / decrypt data """
import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

def generateUserKey(userPassword):
    password_provided_bytes = bytes(userPassword, 'utf-8')
    password = userPassword.encode() # Convert to type bytes
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=password_provided_bytes,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password)) # Can only use kdf once
    fernetKey = Fernet(key)
    return fernetKey

def encryptTextToData(inputText, userKey):
    messageData = inputText.encode(encoding='UTF-8')
    encryptedData = userKey.encrypt(messageData)
    return encryptedData

def decryptDataToText(inputData, userKey):
    decryptedData = userKey.decrypt(inputData)
    clearText = decryptedData.decode(encoding='UTF-8')
    return clearText