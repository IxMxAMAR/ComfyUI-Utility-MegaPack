"""Cryptographic operations: hashes, HMAC, AES-GCM."""

import base64
import hashlib
import hmac as _hmac
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .. import op


# PBKDF2 work factor — 600k iterations is the OWASP 2023 recommendation for
# SHA-256-based password derivation. Increases the cost of a dictionary
# attack against user-entered passwords substantially.
# v0.1.2 (Gemini review #5) replaces the old HKDF-with-static-salt approach,
# which had no work factor and was vulnerable to brute-force on weak keys.
_PBKDF2_ITERATIONS = 600_000
_SALT_BYTES = 16


def _derive_aes_key(key_str: str, salt: bytes) -> bytes:
    """Derive a 32-byte AES key from an arbitrary-length string via PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_PBKDF2_ITERATIONS,
    )
    return kdf.derive(key_str.encode("utf-8"))


def _hash_hex(text: str, name: str) -> str:
    h = hashlib.new(name)
    h.update(text.encode("utf-8"))
    return h.hexdigest()


@op(
    op_id="hash_sha256",
    display_name="Hash SHA-256",
    category="Crypto",
    input_schema={"required": {"text": ("STRING", {"default": ""})}},
    output_indices=(0,),
)
def hash_sha256(self, text):
    return (_hash_hex(text, "sha256"),)


@op(
    op_id="hash_sha512",
    display_name="Hash SHA-512",
    category="Crypto",
    input_schema={"required": {"text": ("STRING", {"default": ""})}},
    output_indices=(0,),
)
def hash_sha512(self, text):
    return (_hash_hex(text, "sha512"),)


@op(
    op_id="hash_md5",
    display_name="Hash MD5 (legacy)",
    category="Crypto",
    input_schema={"required": {"text": ("STRING", {"default": ""})}},
    output_indices=(0,),
    description="Legacy / non-cryptographic. Use SHA-256 for security-relevant work.",
)
def hash_md5(self, text):
    return (_hash_hex(text, "md5"),)


@op(
    op_id="hash_blake2b",
    display_name="Hash BLAKE2b",
    category="Crypto",
    input_schema={"required": {"text": ("STRING", {"default": ""})}},
    output_indices=(0,),
)
def hash_blake2b(self, text):
    return (_hash_hex(text, "blake2b"),)


@op(
    op_id="hmac_sign",
    display_name="HMAC Sign (SHA-256)",
    category="Crypto",
    input_schema={"required": {
        "text": ("STRING", {"default": ""}),
        "key": ("STRING", {"default": ""}),
    }},
    output_indices=(0,),
)
def hmac_sign(self, text, key):
    sig = _hmac.new(key.encode("utf-8"), text.encode("utf-8"), hashlib.sha256).hexdigest()
    return (sig,)


@op(
    op_id="hmac_verify",
    display_name="HMAC Verify",
    category="Crypto",
    input_schema={"required": {
        "text": ("STRING", {"default": ""}),
        "key": ("STRING", {"default": ""}),
        "expected_hex": ("STRING", {"default": ""}),
    }},
    output_indices=(3,),
    description="Constant-time compare of HMAC-SHA256(text, key) vs expected_hex.",
)
def hmac_verify(self, text, key, expected_hex):
    actual = _hmac.new(key.encode("utf-8"), text.encode("utf-8"), hashlib.sha256).hexdigest()
    return (_hmac.compare_digest(actual, expected_hex),)


@op(
    op_id="aes_encrypt",
    display_name="AES-GCM Encrypt",
    category="Crypto",
    input_schema={"required": {
        "plaintext": ("STRING", {"default": ""}),
        "key": ("STRING", {"default": ""}),
    }},
    output_indices=(0,),
    description=(
        "AES-256-GCM with PBKDF2-HMAC-SHA256 key derivation (600k iters). "
        "Returns base64(salt[16] || nonce[12] || ciphertext_with_tag). "
        "NOTE: ciphertexts from v0.1.0/0.1.1 (HKDF-based) cannot be decrypted by v0.1.2+."
    ),
)
def aes_encrypt(self, plaintext, key):
    salt = os.urandom(_SALT_BYTES)
    aes = AESGCM(_derive_aes_key(key, salt))
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext.encode("utf-8"), None)
    return (base64.b64encode(salt + nonce + ct).decode("ascii"),)


@op(
    op_id="aes_decrypt",
    display_name="AES-GCM Decrypt",
    category="Crypto",
    input_schema={"required": {
        "ciphertext_b64": ("STRING", {"default": ""}),
        "key": ("STRING", {"default": ""}),
    }},
    output_indices=(0,),
    description="Inverse of aes_encrypt. Raises on tag mismatch or malformed input.",
)
def aes_decrypt(self, ciphertext_b64, key):
    blob = base64.b64decode(ciphertext_b64)
    min_len = _SALT_BYTES + 12 + 16  # salt + nonce + GCM tag minimum
    if len(blob) < min_len:
        raise ValueError(
            f"ciphertext too short for AES-GCM with PBKDF2 (need >= {min_len} bytes, got {len(blob)})"
        )
    salt = blob[:_SALT_BYTES]
    nonce = blob[_SALT_BYTES:_SALT_BYTES + 12]
    ct = blob[_SALT_BYTES + 12:]
    aes = AESGCM(_derive_aes_key(key, salt))
    return (aes.decrypt(nonce, ct, None).decode("utf-8"),)
