import base64
import requests
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

BASE_URL = "http://127.0.0.1:8000"
PLAIN_PASSWORD = "10291029"


def encrypt_password(public_key_pem: str, plain_password: str) -> str:
    public_key = load_pem_public_key(public_key_pem.encode())
    encrypted = public_key.encrypt(plain_password.encode(), padding.PKCS1v15())
    return base64.b64encode(encrypted).decode()


r = requests.get(f"{BASE_URL}/auth/public-key")
r.raise_for_status()
public_key_pem = r.json()["public_key"]

print(encrypt_password(public_key_pem, PLAIN_PASSWORD))
