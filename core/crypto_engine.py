"""
Aegis – Cryptographic Engine
============================
Hybrid RSA-2048 / AES-256-GCM encryption for end-to-end encrypted messaging.

Protocol
--------
1. Generate a fresh AES-256 key + 12-byte nonce per message/file.
2. Encrypt the plaintext payload with AES-GCM → ciphertext + tag.
3. Encrypt the AES key with the recipient's RSA-2048 public key (OAEP/SHA-256).
4. For group chats, the AES key is encrypted once per recipient public key.
5. The sender's RSA private key is locally encrypted with AES-GCM using a
   key derived from the user's password via PBKDF2-HMAC-SHA256 (600 000 iters).
"""

from __future__ import annotations

import base64
import json
import os
import secrets
from typing import Any, Dict, List, Optional, Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    RSAPublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.bip39_english import BIP39_ENGLISH

# ─────────────────── Constants ───────────────────────────
RSA_KEY_SIZE: int = 2048
AES_KEY_BYTES: int = 32          # 256-bit
AES_NONCE_BYTES: int = 12        # 96-bit (GCM standard)
PBKDF2_ITERATIONS: int = 600_000
PBKDF2_SALT_BYTES: int = 16


# ═══════════════════════════════════════════════════════════
#  KEY GENERATION
# ═══════════════════════════════════════════════════════════

def generate_rsa_keypair() -> Tuple[RSAPrivateKey, RSAPublicKey]:
    """Generate a fresh RSA-2048 key pair.

    Returns
    -------
    Tuple[RSAPrivateKey, RSAPublicKey]
        The generated private and public keys.
    """
    private_key: RSAPrivateKey = rsa.generate_private_key(
        public_exponent=65537,
        key_size=RSA_KEY_SIZE,
    )
    public_key: RSAPublicKey = private_key.public_key()
    return private_key, public_key


def generate_aes_key() -> bytes:
    """Return a cryptographically random 256-bit AES key."""
    return AESGCM.generate_key(bit_length=AES_KEY_BYTES * 8)


def generate_nonce() -> bytes:
    """Return a cryptographically random 96-bit nonce for AES-GCM."""
    return secrets.token_bytes(AES_NONCE_BYTES)


# ═══════════════════════════════════════════════════════════
#  RSA SERIALIZATION
# ═══════════════════════════════════════════════════════════

def serialize_public_key(public_key: RSAPublicKey) -> str:
    """Serialize an RSA public key to a PEM-encoded Base64 string.

    Parameters
    ----------
    public_key : RSAPublicKey
        The RSA public key to serialize.

    Returns
    -------
    str
        Base64-encoded PEM string (safe for Firebase storage).
    """
    pem_bytes: bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return base64.b64encode(pem_bytes).decode("utf-8")


def deserialize_public_key(b64_pem: str) -> RSAPublicKey:
    """Reconstruct an RSA public key from a Base64-encoded PEM string.

    Parameters
    ----------
    b64_pem : str
        Base64-encoded PEM string from Firebase.

    Returns
    -------
    RSAPublicKey
    """
    pem_bytes: bytes = base64.b64decode(b64_pem)
    key = serialization.load_pem_public_key(pem_bytes)
    if not isinstance(key, RSAPublicKey):
        raise TypeError("Loaded key is not an RSA public key.")
    return key


# ═══════════════════════════════════════════════════════════
#  PRIVATE KEY PROTECTION  (password-based AES-GCM wrapping)
# ═══════════════════════════════════════════════════════════

def _derive_key_from_password(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from a user password using PBKDF2-HMAC-SHA256.

    Parameters
    ----------
    password : str
        User-supplied password or PIN.
    salt : bytes
        16-byte random salt.

    Returns
    -------
    bytes
        32-byte derived key.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=AES_KEY_BYTES,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_private_key(private_key: RSAPrivateKey, password: str) -> str:
    """Encrypt the RSA private key with a password-derived AES-GCM key.

    The output JSON contains *salt*, *nonce*, and *ciphertext* (all
    Base64-encoded) so the key can be safely persisted on disk.

    Parameters
    ----------
    private_key : RSAPrivateKey
    password : str

    Returns
    -------
    str
        JSON string ``{"salt": ..., "nonce": ..., "ct": ...}``.
    """
    pem_bytes: bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    salt: bytes = secrets.token_bytes(PBKDF2_SALT_BYTES)
    derived_key: bytes = _derive_key_from_password(password, salt)
    nonce: bytes = generate_nonce()
    aesgcm = AESGCM(derived_key)
    ct: bytes = aesgcm.encrypt(nonce, pem_bytes, None)

    payload: Dict[str, str] = {
        "salt": base64.b64encode(salt).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "ct": base64.b64encode(ct).decode(),
    }
    return json.dumps(payload)


def decrypt_private_key(encrypted_json: str, password: str) -> RSAPrivateKey:
    """Decrypt the RSA private key from the encrypted JSON envelope.

    Parameters
    ----------
    encrypted_json : str
        JSON produced by :func:`encrypt_private_key`.
    password : str

    Returns
    -------
    RSAPrivateKey

    Raises
    ------
    cryptography.exceptions.InvalidTag
        If the password is wrong.
    """
    payload: Dict[str, str] = json.loads(encrypted_json)
    salt: bytes = base64.b64decode(payload["salt"])
    nonce: bytes = base64.b64decode(payload["nonce"])
    ct: bytes = base64.b64decode(payload["ct"])

    derived_key: bytes = _derive_key_from_password(password, salt)
    aesgcm = AESGCM(derived_key)
    pem_bytes: bytes = aesgcm.decrypt(nonce, ct, None)

    key = serialization.load_pem_private_key(pem_bytes, password=None)
    if not isinstance(key, RSAPrivateKey):
        raise TypeError("Loaded key is not an RSA private key.")
    return key


# ═══════════════════════════════════════════════════════════
#  RECOVERY SEED PHRASE
# ═══════════════════════════════════════════════════════════

def generate_recovery_phrase() -> List[str]:
    """Generate a 24-word recovery phrase from the BIP39 wordlist."""
    return [secrets.choice(BIP39_ENGLISH) for _ in range(24)]


def _derive_key_from_phrase(phrase: List[str], salt: bytes) -> bytes:
    """Derive a 256-bit AES key from a seed phrase using PBKDF2-HMAC-SHA256."""
    password = " ".join(phrase).lower().strip()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=AES_KEY_BYTES,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_private_key_with_phrase(private_key: RSAPrivateKey, phrase: List[str]) -> str:
    """Encrypt the RSA private key with a seed-phrase-derived AES-GCM key."""
    pem_bytes: bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    salt: bytes = secrets.token_bytes(PBKDF2_SALT_BYTES)
    derived_key: bytes = _derive_key_from_phrase(phrase, salt)
    nonce: bytes = generate_nonce()
    aesgcm = AESGCM(derived_key)
    ct: bytes = aesgcm.encrypt(nonce, pem_bytes, None)

    payload: Dict[str, str] = {
        "salt": base64.b64encode(salt).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "ct": base64.b64encode(ct).decode(),
    }
    return json.dumps(payload)


def decrypt_private_key_with_phrase(encrypted_json: str, phrase: List[str]) -> RSAPrivateKey:
    """Decrypt the RSA private key from the recovery JSON envelope."""
    payload: Dict[str, str] = json.loads(encrypted_json)
    salt: bytes = base64.b64decode(payload["salt"])
    nonce: bytes = base64.b64decode(payload["nonce"])
    ct: bytes = base64.b64decode(payload["ct"])

    derived_key: bytes = _derive_key_from_phrase(phrase, salt)
    aesgcm = AESGCM(derived_key)
    pem_bytes: bytes = aesgcm.decrypt(nonce, ct, None)

    key = serialization.load_pem_private_key(pem_bytes, password=None)
    if not isinstance(key, RSAPrivateKey):
        raise TypeError("Loaded key is not an RSA private key.")
    return key


# ═══════════════════════════════════════════════════════════
#  AES-GCM SYMMETRIC ENCRYPTION
# ═══════════════════════════════════════════════════════════

def aes_encrypt(plaintext: bytes) -> Tuple[bytes, bytes, bytes]:
    """Encrypt plaintext with a fresh AES-256-GCM key and nonce.

    Parameters
    ----------
    plaintext : bytes
        Raw data to encrypt.

    Returns
    -------
    Tuple[bytes, bytes, bytes]
        ``(aes_key, nonce, ciphertext_with_tag)``
    """
    aes_key: bytes = generate_aes_key()
    nonce: bytes = generate_nonce()
    aesgcm = AESGCM(aes_key)
    ciphertext: bytes = aesgcm.encrypt(nonce, plaintext, None)
    return aes_key, nonce, ciphertext


def aes_decrypt(aes_key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    """Decrypt AES-256-GCM ciphertext.

    Parameters
    ----------
    aes_key : bytes
    nonce : bytes
    ciphertext : bytes
        Ciphertext including the 16-byte authentication tag.

    Returns
    -------
    bytes
        Decrypted plaintext.

    Raises
    ------
    cryptography.exceptions.InvalidTag
        If authentication fails (tampered data).
    """
    aesgcm = AESGCM(aes_key)
    return aesgcm.decrypt(nonce, ciphertext, None)


# ═══════════════════════════════════════════════════════════
#  RSA ASYMMETRIC WRAPPING  (encrypt the AES key)
# ═══════════════════════════════════════════════════════════

def rsa_encrypt_aes_key(aes_key: bytes, recipient_pub: RSAPublicKey) -> bytes:
    """Encrypt an AES key using the recipient's RSA public key (OAEP/SHA-256).

    Parameters
    ----------
    aes_key : bytes
        32-byte AES-256 key.
    recipient_pub : RSAPublicKey
        Recipient's RSA-2048 public key.

    Returns
    -------
    bytes
        RSA-encrypted AES key (256 bytes for RSA-2048).
    """
    return recipient_pub.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def rsa_decrypt_aes_key(
    encrypted_key: bytes, private_key: RSAPrivateKey
) -> bytes:
    """Decrypt an RSA-wrapped AES key using the local private key.

    Parameters
    ----------
    encrypted_key : bytes
        RSA-encrypted AES key (256 bytes).
    private_key : RSAPrivateKey
        Local user's RSA private key (held in RAM).

    Returns
    -------
    bytes
        32-byte AES-256 key.
    """
    return private_key.decrypt(
        encrypted_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


# ═══════════════════════════════════════════════════════════
#  HIGH-LEVEL HELPERS  (compose encrypt / decrypt pipelines)
# ═══════════════════════════════════════════════════════════

def encrypt_message(
    plaintext: str,
    recipient_public_keys: Dict[str, RSAPublicKey],
) -> Dict[str, Any]:
    """Encrypt a text message for one or more recipients.

    The payload is AES-GCM encrypted, and the AES key is RSA-wrapped
    separately for each recipient (enabling group chats).

    Parameters
    ----------
    plaintext : str
        The message text.
    recipient_public_keys : Dict[str, RSAPublicKey]
        Mapping of user IDs to their public keys.

    Returns
    -------
    Dict[str, Any]
        JSON-serializable dictionary ready for Firebase::

            {
                "nonce": "<base64>",
                "ciphertext": "<base64>",
                "keys": {
                    "<key_fingerprint_index>": "<base64 RSA-encrypted AES key>",
                    ...
                }
            }
    """
    plaintext_bytes: bytes = plaintext.encode("utf-8")
    aes_key, nonce, ciphertext = aes_encrypt(plaintext_bytes)

    encrypted_keys: Dict[str, str] = {}
    for uid, pub_key in recipient_public_keys.items():
        wrapped: bytes = rsa_encrypt_aes_key(aes_key, pub_key)
        encrypted_keys[uid] = base64.b64encode(wrapped).decode()

    return {
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "keys": encrypted_keys,
    }


def decrypt_message(
    payload: Dict[str, Any],
    key_index: str,
    private_key: RSAPrivateKey,
) -> str:
    """Decrypt an E2EE message payload.

    Parameters
    ----------
    payload : Dict[str, Any]
        Encrypted payload from Firebase.
    key_index : str
        Index of *our* RSA-wrapped AES key inside ``payload["keys"]``.
    private_key : RSAPrivateKey
        Local user's private key.

    Returns
    -------
    str
        Decrypted plaintext message.
    """
    nonce: bytes = base64.b64decode(payload["nonce"])
    ciphertext: bytes = base64.b64decode(payload["ciphertext"])
    wrapped_key: bytes = base64.b64decode(payload["keys"][key_index])

    aes_key: bytes = rsa_decrypt_aes_key(wrapped_key, private_key)
    plaintext_bytes: bytes = aes_decrypt(aes_key, nonce, ciphertext)
    return plaintext_bytes.decode("utf-8")


def encrypt_file_bytes(
    raw_data: bytes,
    recipient_public_keys: Dict[str, RSAPublicKey],
) -> Dict[str, Any]:
    """Encrypt a raw file for one or more recipients.

    Returns the ciphertext blob and separately the RSA-wrapped AES keys
    plus nonce (stored as message metadata in Firebase DB).

    Parameters
    ----------
    raw_data : bytes
        Raw file content.
    recipient_public_keys : Dict[str, RSAPublicKey]
        Mapping of user IDs to their public keys.

    Returns
    -------
    Dict[str, Any]
        ``{"blob": bytes, "metadata": {"nonce": ..., "keys": {...}}}``
    """
    aes_key, nonce, ciphertext = aes_encrypt(raw_data)

    encrypted_keys: Dict[str, str] = {}
    for uid, pub_key in recipient_public_keys.items():
        wrapped = rsa_encrypt_aes_key(aes_key, pub_key)
        encrypted_keys[uid] = base64.b64encode(wrapped).decode()

    return {
        "blob": ciphertext,
        "metadata": {
            "nonce": base64.b64encode(nonce).decode(),
            "keys": encrypted_keys,
        },
    }


def decrypt_file_bytes(
    ciphertext: bytes,
    metadata: Dict[str, Any],
    key_index: str,
    private_key: RSAPrivateKey,
) -> bytes:
    """Decrypt a file blob using the metadata from Firebase DB.

    Parameters
    ----------
    ciphertext : bytes
        Encrypted file bytes downloaded from Firebase Storage.
    metadata : Dict[str, Any]
        ``{"nonce": ..., "keys": {...}}``
    key_index : str
    private_key : RSAPrivateKey

    Returns
    -------
    bytes
        Decrypted file content.
    """
    nonce: bytes = base64.b64decode(metadata["nonce"])
    wrapped_key: bytes = base64.b64decode(metadata["keys"][key_index])
    aes_key: bytes = rsa_decrypt_aes_key(wrapped_key, private_key)
    return aes_decrypt(aes_key, nonce, ciphertext)
