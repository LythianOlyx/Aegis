# Aegis – API Reference

> **Version:** 1.0.0  
> **Last Updated:** 2026-05-13  

---

## Table of Contents

- [1. core.crypto\_engine](#1-corecrypto_engine)
- [2. core.firebase\_client](#2-corefirebase_client)
- [3. core.file\_manager (Deprecated)](#3-corefile_manager-deprecated)
- [4. ui.shared.widgets](#4-uisharedwidgets)

---

## 1. core.crypto_engine

Hybrid RSA-2048 / AES-256-GCM encryption engine for end-to-end encrypted messaging.

### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `RSA_KEY_SIZE` | `2048` | RSA key length in bits |
| `AES_KEY_BYTES` | `32` | AES-256 key length (bytes) |
| `AES_NONCE_BYTES` | `12` | AES-GCM nonce length (bytes) |
| `PBKDF2_ITERATIONS` | `600_000` | PBKDF2 iteration count |
| `PBKDF2_SALT_BYTES` | `16` | PBKDF2 salt length (bytes) |

### Key Generation

#### `generate_rsa_keypair() → Tuple[RSAPrivateKey, RSAPublicKey]`

Generate a fresh RSA-2048 key pair.

```python
from core.crypto_engine import generate_rsa_keypair

private_key, public_key = generate_rsa_keypair()
```

#### `generate_aes_key() → bytes`

Return a cryptographically random 256-bit AES key.

#### `generate_nonce() → bytes`

Return a cryptographically random 96-bit nonce for AES-GCM.

### RSA Serialization

#### `serialize_public_key(public_key: RSAPublicKey) → str`

Serialize an RSA public key to a Base64-encoded PEM string (safe for Firebase).

#### `deserialize_public_key(b64_pem: str) → RSAPublicKey`

Reconstruct an RSA public key from a Base64-encoded PEM string.

### Private Key Protection

#### `encrypt_private_key(private_key: RSAPrivateKey, password: str) → str`

Encrypt the RSA private key with a password-derived AES-GCM key. Returns a JSON string `{"salt": ..., "nonce": ..., "ct": ...}`.

#### `decrypt_private_key(encrypted_json: str, password: str) → RSAPrivateKey`

Decrypt the RSA private key from the encrypted JSON envelope.

**Raises:** `cryptography.exceptions.InvalidTag` if the password is wrong.

### Symmetric Encryption

#### `aes_encrypt(plaintext: bytes) → Tuple[bytes, bytes, bytes]`

Encrypt plaintext with a fresh AES-256-GCM key. Returns `(aes_key, nonce, ciphertext_with_tag)`.

#### `aes_decrypt(aes_key: bytes, nonce: bytes, ciphertext: bytes) → bytes`

Decrypt AES-256-GCM ciphertext. **Raises:** `InvalidTag` if tampered.

### RSA Key Wrapping

#### `rsa_encrypt_aes_key(aes_key: bytes, recipient_pub: RSAPublicKey) → bytes`

Encrypt an AES key using the recipient's RSA public key (OAEP/SHA-256). Returns 256 bytes.

#### `rsa_decrypt_aes_key(encrypted_key: bytes, private_key: RSAPrivateKey) → bytes`

Decrypt an RSA-wrapped AES key using the local private key.

### High-Level Helpers

#### `encrypt_message(plaintext: str, recipient_public_keys: List[RSAPublicKey]) → Dict[str, Any]`

Encrypt a text message for one or more recipients.

**Returns:**
```json
{
    "nonce": "<base64>",
    "ciphertext": "<base64>",
    "keys": {
        "0": "<base64 RSA-encrypted AES key>",
        "1": "<base64 RSA-encrypted AES key>"
    }
}
```

#### `decrypt_message(payload: Dict, key_index: str, private_key: RSAPrivateKey) → str`

Decrypt an E2EE message payload. Returns the plaintext string.

#### `encrypt_file_bytes(raw_data: bytes, recipient_public_keys: List[RSAPublicKey]) → Dict` (Deprecated)

> [!WARNING]
> This method is deprecated and no longer used by Aegis.

Encrypt raw file bytes. Returns `{"blob": bytes, "metadata": {"nonce": ..., "keys": {...}}}`.

#### `decrypt_file_bytes(ciphertext: bytes, metadata: Dict, key_index: str, private_key: RSAPrivateKey) → bytes` (Deprecated)

> [!WARNING]
> This method is deprecated and no longer used by Aegis.

Decrypt a file blob using metadata from Firebase DB.

---

## 2. core.firebase_client

Lightweight Firebase REST API wrapper using only the `requests` library.

### Exceptions

| Exception | Description |
|-----------|-------------|
| `FirebaseAuthError` | Authentication failure (wrong credentials, expired token, etc.) |
| `FirebaseDBError` | Realtime Database operation failure |
| `FirebaseStorageError` (Deprecated) | Cloud Storage upload/download failure (No longer used) |

### Class: `FirebaseClient`

#### Constructor

```python
client = FirebaseClient({
    "api_key": "AIzaSy...",
    "project_id": "my-project",
    "db_url": "https://my-project-default-rtdb.firebaseio.com",
    "storage_bucket": "",  # Unused — leave empty
})
```

### Instance Properties

| Property | Type | Description |
|----------|------|-------------|
| `id_token` | `Optional[str]` | Current Firebase ID token |
| `refresh_token` | `Optional[str]` | Current refresh token |
| `local_id` | `Optional[str]` | Firebase UID |
| `email` | `Optional[str]` | User's email |
| `display_name` | `Optional[str]` | User's display name |

### Authentication Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `sign_up(email, password, display_name="")` | `str, str, str` | `Dict[str, Any]` | Register new user |
| `sign_in(email, password)` | `str, str` | `Dict[str, Any]` | Sign in existing user |
| `sign_out()` | — | `None` | Clear local auth state |
| `refresh_id_token()` | — | `None` | Exchange refresh token for new ID token |
| `update_profile(display_name=None, photo_url=None)` | `Optional[str], Optional[str]` | `Dict` | Update user profile |
| `get_user_data()` | — | `Dict[str, Any]` | Fetch current user's profile |

### Database Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `db_get(path)` | `str` | `Any` | Read data at path |
| `db_put(path, data)` | `str, Any` | `Any` | Write (overwrite) at path |
| `db_patch(path, data)` | `str, Dict` | `Any` | Partial update at path |
| `db_post(path, data)` | `str, Any` | `Dict[str, str]` | Push with auto-generated key |
| `db_delete(path)` | `str` | `None` | Delete data at path |
| `db_query(path, order_by, ...)` | Multiple | `Any` | Indexed query with filters |

### Storage Methods (Deprecated)

> [!WARNING]
> The following storage methods are deprecated and no longer used by Aegis.

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `storage_upload(remote_path, data, content_type)` | `str, bytes, str` | `str` | Upload bytes, returns download URL |
| `storage_download(download_url)` | `str` | `bytes` | Download bytes from URL |

### User & Chat Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `search_users(query)` | `str` | `List[Dict]` | Search by display name prefix |
| `register_user_profile(uid, email, display_name, public_key_b64)` | `str ×4` | `None` | Write public profile |
| `get_public_key(uid)` | `str` | `Optional[str]` | Get user's RSA public key |
| `send_message(chat_id, sender_uid, encrypted_payload, msg_type)` | `str ×3, str` | `str` | Push encrypted message |
| `get_messages(chat_id, limit=50)` | `str, int` | `List[Dict]` | Fetch latest messages |
| `create_chat(chat_id, participants, chat_type, group_name)` | `str, List[str], str, str` | `None` | Create chat room |
| `get_user_chats(uid)` | `str` | `List[str]` | List chat IDs for user |
| `get_chat_info(chat_id)` | `str` | `Optional[Dict]` | Chat metadata |

---

## 3. core.file_manager (Deprecated)

> [!WARNING]
> This module is deprecated and no longer used by Aegis since file transfers have been disabled.

File I/O utilities for encrypted file transfers.

### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `DEFAULT_CHUNK_SIZE` | `4 * 1024 * 1024` | 4 MiB per chunk |
| `MAX_FILE_SIZE` | `100 * 1024 * 1024` | 100 MiB hard limit |
| `ALLOWED_MIME_TYPES` | `frozenset` | 15 allowlisted MIME types |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `FileTooLargeError` | File exceeds `MAX_FILE_SIZE` |
| `UnsupportedFileTypeError` | MIME type not in allowlist |

### Functions

| Function | Signature | Returns | Description |
|----------|-----------|---------|-------------|
| `validate_file` | `(file_path, max_size, check_mime)` | `Tuple[int, str]` | Validate size & MIME |
| `read_file_bytes` | `(file_path)` | `bytes` | Read entire file |
| `read_file_chunks` | `(file_path, chunk_size)` | `Generator[bytes]` | Yield fixed-size chunks |
| `write_file_bytes` | `(file_path, data)` | `None` | Write with auto-mkdir |
| `detect_mime_type` | `(file_path)` | `str` | Extension-based MIME |
| `format_file_size` | `(size_bytes)` | `str` | Human-readable size |
| `safe_filename` | `(original_name)` | `str` | Remove dangerous chars |
| `get_file_name` | `(file_path)` | `str` | Extract basename |
| `get_downloads_dir` | `()` | `str` | `~/Downloads/Aegis/` |

---

## 4. ui.shared.widgets

Reusable widgets for both Desktop and Mobile UIs.

### Colour Constants

| Constant | RGBA | Hex |
|----------|------|-----|
| `BG_PRIMARY` | `(0.039, 0.086, 0.157, 1)` | `#0A1628` |
| `BG_SURFACE` | `(0.067, 0.133, 0.251, 1)` | `#112240` |
| `BG_ELEVATED` | `(0.102, 0.200, 0.333, 1)` | `#1A3355` |
| `ACCENT_CYAN` | `(0.000, 0.898, 0.800, 1)` | `#00E5CC` |
| `ACCENT_GREEN` | `(0.000, 1.000, 0.639, 1)` | `#00FFA3` |
| `ACCENT_BLUE` | `(0.000, 0.706, 0.847, 1)` | `#00B4D8` |
| `TEXT_PRIMARY` | `(0.878, 0.969, 0.980, 1)` | `#E0F7FA` |
| `TEXT_SECONDARY` | `(0.502, 0.796, 0.769, 1)` | `#80CBC4` |
| `DANGER_RED` | `(1.000, 0.322, 0.322, 1)` | `#FF5252` |

### Widget Classes

#### `SplashScreen(Screen)`

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `logo_path` | `StringProperty` | Auto-resolved | Path to `assets/logo.png` |
| `next_screen` | `StringProperty` | `"auth"` | Screen to navigate to after 2.5s |

**Animation sequence:** Logo scale+fade (0.8s, out_back) → Title fade (0.6s) → Subtitle fade (0.6s) → Navigate

#### `E2EEMessageBubble(MDBoxLayout)`

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `message_text` | `StringProperty` | `""` | Message content |
| `timestamp_str` | `StringProperty` | `""` | Time display (e.g. "14:30") |
| `is_sent` | `BooleanProperty` | `False` | Sent vs received styling |
| `encryption_icon` | `StringProperty` | `"🔒"` | Lock indicator |
| `bubble_color` | `ColorProperty` | `BUBBLE_RECV` | Auto-updates based on `is_sent` |

#### `FileMessageBubble(MDBoxLayout)` (Deprecated)

> [!WARNING]
> This widget is deprecated and no longer used for sending new files. It is kept only for rendering legacy file messages.

| Property | Type | Description |
|----------|------|-------------|
| `file_name` | `StringProperty` | Filename display |
| `file_size_str` | `StringProperty` | Size string |
| `timestamp_str` | `StringProperty` | Time display |
| `is_sent` | `BooleanProperty` | Sent vs received |
| `download_url` | `StringProperty` | Firebase Storage URL |

#### `ChatListItem(MDBoxLayout)`

| Property | Type | Description |
|----------|------|-------------|
| `chat_id` | `StringProperty` | Chat identifier |
| `chat_name` | `StringProperty` | Display name |
| `last_message` | `StringProperty` | Preview text |
| `time_str` | `StringProperty` | Timestamp |
| `avatar_letter` | `StringProperty` | First letter for avatar |
| `on_chat_selected` | `ObjectProperty` | Callback `(chat_id: str)` |

#### `UserSearchResult(MDBoxLayout)`

| Property | Type | Description |
|----------|------|-------------|
| `uid` | `StringProperty` | User's Firebase UID |
| `display_name` | `StringProperty` | User's name |
| `email` | `StringProperty` | User's email |
| `avatar_letter` | `StringProperty` | First letter for avatar |
| `on_user_selected` | `ObjectProperty` | Callback `(uid: str)` |
