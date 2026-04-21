import base64
from cryptography.hazmat.primitives.asymmetric import padding
from app.keys import private_key


def decrypt_password(encrypted_password_b64: str) -> str:
    """
    Decrypt a base64-encoded RSA-encrypted password sent from the client.
    The client should encrypt using the public key from GET /auth/public-key
    with PKCS1v15 padding (compatible with JSEncrypt and similar JS libraries).
    """
    try:
        encrypted_bytes = base64.b64decode(encrypted_password_b64)
    except Exception as exc:
        raise ValueError("Invalid base64-encoded password") from exc

    try:
        decrypted_bytes = private_key.decrypt(encrypted_bytes, padding.PKCS1v15())
    except Exception as exc:
        raise ValueError("Failed to decrypt password") from exc

    try:
        return decrypted_bytes.decode("utf-8")
    except Exception as exc:
        raise ValueError("Decrypted password is not valid UTF-8") from exc
