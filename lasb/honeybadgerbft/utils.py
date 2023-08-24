import hashlib

def hash(x):
    return hashlib.sha256(x).digest()