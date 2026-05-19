# Aegis – Security Specification

> **Version:** 1.0.0  
> **Last Updated:** 2026-05-13  
> **Classification:** Public  

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. Cryptographic Primitives](#2-cryptographic-primitives)
- [3. Key Management](#3-key-management)
- [4. Message Encryption Protocol](#4-message-encryption-protocol)
- [5. File Encryption Protocol](#5-file-encryption-protocol)
- [6. Threat Model](#6-threat-model)
- [7. Security Properties](#7-security-properties)
- [8. Known Limitations](#8-known-limitations)
- [9. Security Audit Checklist](#9-security-audit-checklist)

---

## 1. Executive Summary

Aegis implements a **hybrid encryption protocol** combining asymmetric (RSA-2048) and symmetric (AES-256-GCM) cryptography to provide end-to-end encryption for all messages and files. The server (Firebase) functions exclusively as a **ciphertext relay** — it never has access to plaintext content or the symmetric keys needed to decrypt it.

**Key guarantees:**
- ✅ Messages are encrypted on the sender's device before transmission
- ✅ Only intended recipients can decrypt messages
- ✅ The server cannot read message content
- ✅ Private keys never leave the user's device
- ✅ Each message uses a unique AES key and nonce (no key reuse)

---

## 2. Cryptographic Primitives

| Primitive | Algorithm | Parameters | Library |
|-----------|-----------|------------|---------|
| Asymmetric Encryption | RSA-OAEP | 2048-bit, SHA-256, MGF1-SHA-256 | `cryptography` |
| Symmetric Encryption | AES-GCM | 256-bit key, 96-bit nonce (12 bytes) | `cryptography` |
| Key Derivation | PBKDF2-HMAC | SHA-256, 600,000 iterations, 128-bit salt | `cryptography` |
| Random Generation | OS CSPRNG | Via `secrets.token_bytes()` and `AESGCM.generate_key()` | Python `secrets` |

### Why These Choices?

| Choice | Rationale |
|--------|-----------|
| **RSA-2048** | Widely supported, sufficient for key exchange. 2048-bit provides ~112-bit security level. |
| **OAEP with SHA-256** | IND-CCA2 secure padding scheme; resistant to chosen-ciphertext attacks. |
| **AES-256-GCM** | Authenticated encryption (AEAD); provides both confidentiality and integrity. Detects tampering. |
| **96-bit nonce** | NIST-recommended nonce length for AES-GCM. Random nonces with 256-bit keys have negligible collision probability. |
| **PBKDF2 600K** | OWASP 2024 recommended minimum for SHA-256. Provides brute-force resistance for password-based key derivation. |

---

## 3. Key Management

### 3.1 Key Generation

```
User Registration
       │
       ▼
generate_rsa_keypair()
       │
       ├──► RSA Private Key (2048-bit)
       │         │
       │         ▼
       │    encrypt_private_key(password)
       │         │
       │         ├──► PBKDF2(password, random_salt) → derived_key
       │         ├──► AES-GCM(derived_key, random_nonce, privkey_pem) → ciphertext
       │         └──► Store locally: { salt, nonce, ciphertext }
       │              Path: ~/.aegis/keys/<uid>.key
       │
       │    encrypt_private_key_with_phrase(24_words)
       │         │
       │         ├──► PBKDF2(seed_phrase, random_salt) → derived_recovery_key
       │         ├──► AES-GCM(derived_recovery_key, random_nonce, privkey_pem) → recovery_blob
       │         └──► Store on Firebase: /users/<uid>/recovery_blob
       │
       └──► RSA Public Key
                 │
                 ▼
            serialize_public_key() → Base64 PEM
                 │
                 ▼
            Firebase RTDB: /users/<uid>/public_key
```

### 3.2 Key Storage Locations

| Key | Storage | Encrypted? | Access |
|-----|---------|------------|--------|
| RSA Public Key | Firebase RTDB | No (public) | Any authenticated user |
| RSA Private Key (Local) | Local filesystem `~/.aegis/keys/` | Yes (AES-GCM + PBKDF2 via Password) | Device owner only |
| RSA Private Key (Backup) | Firebase RTDB `recovery_blob` | Yes (AES-GCM + PBKDF2 via 24-word Seed) | Authenticated user only |
| AES Session Keys | RAM only (ephemeral) | N/A | Generated per-message, never stored |
| PBKDF2 Salt | Inside encrypted key file | No | Needed for key derivation |

### 3.3 Key Lifecycle

```
Registration ──► Private key generated ──► Encrypted with password ──► Stored on disk
                 Private key           ──► Encrypted with 24-words ──► Stored on Firebase (recovery_blob)
                 Public key generated  ──► Stored on Firebase

Login ──► Load encrypted private key ──► PBKDF2(password) ──► AES-GCM decrypt
          ──► Private key held in RAM (app.private_key) for session

Recovery ──► Firebase Login (New Password) ──► Download `recovery_blob` ──► PBKDF2(seed_phrase)
           ──► AES-GCM decrypt ──► Re-encrypt with New Password ──► Store locally

Logout ──► app.private_key = None ──► Private key cleared from RAM

Message ──► Fresh AES key generated ──► Used once ──► Wrapped with RSA ──► Discarded
```

### 3.4 Key Recovery & Key Regeneration

Because Aegis uses a Zero-Knowledge architecture, the server cannot assist in password resets without destroying access to existing encrypted data.

1. **Automatic Recovery:** If a user resets their password via email, their new password will successfully authenticate with Firebase but will fail to decrypt the local `~/.aegis/keys/<uid>.key` file. Aegis detects this `InvalidTag` AES-GCM error and automatically prompts the user for their 24-word seed phrase to download and decrypt the `recovery_blob`.
2. **Key Regeneration (Skip):** If the user has lost both their password *and* their seed phrase, they can opt to **"Skip"** recovery. This invokes an irreversible key regeneration process:
   - A new RSA keypair is generated locally.
   - The user is forced to generate and save a *new* 24-word seed phrase.
   - The new public key and new `recovery_blob` overwrite the old ones on Firebase.
   - **Result:** The user regains access to their account to send/receive *new* messages, but all *previous* messages remain permanently unreadable due to the loss of the original private key. This is the intended cryptographic behavior.

---

## 4. Message Encryption Protocol

### 4.1 Encryption (Sender)

```python
# Step 1: Generate per-message symmetric key
aes_key = AESGCM.generate_key(256)      # 32 random bytes
nonce = secrets.token_bytes(12)           # 12 random bytes

# Step 2: Encrypt message content
aesgcm = AESGCM(aes_key)
ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
# ciphertext includes 16-byte GCM authentication tag

# Step 3: Wrap AES key for each recipient
for recipient in recipients:
    encrypted_key = recipient.public_key.encrypt(
        aes_key,
        OAEP(mgf=MGF1(SHA256()), algorithm=SHA256(), label=None)
    )

# Step 4: Transmit to Firebase
payload = {
    "nonce": base64(nonce),
    "ciphertext": base64(ciphertext),
    "keys": {
        "0": base64(encrypted_key_for_recipient_0),
        "1": base64(encrypted_key_for_recipient_1),
        ...
    }
}
```

### 4.2 Decryption (Recipient)

```python
# Step 1: Retrieve own encrypted AES key
my_index = participants.index(my_uid)
encrypted_key = base64_decode(payload["keys"][str(my_index)])

# Step 2: Unwrap AES key with RSA private key
aes_key = private_key.decrypt(
    encrypted_key,
    OAEP(mgf=MGF1(SHA256()), algorithm=SHA256(), label=None)
)

# Step 3: Decrypt message
nonce = base64_decode(payload["nonce"])
ciphertext = base64_decode(payload["ciphertext"])
plaintext = AESGCM(aes_key).decrypt(nonce, ciphertext, None)
# GCM tag is verified automatically; InvalidTag raised if tampered
```

### 4.3 Group Chat Key Distribution

For group chats with N participants, the AES key is encrypted **N times** — once per recipient's public key. This means:

- All participants can decrypt the same ciphertext
- Adding/removing members requires re-encrypting future messages only
- No shared group key needed (each member uses their own RSA key pair)

---

## 5. File Encryption Protocol

```
Sender Device                    Firebase                    Recipient Device
     │                              │                              │
     ├─ Read file bytes             │                              │
     ├─ Generate AES key + nonce    │                              │
     ├─ AES-GCM encrypt(file)       │                              │
     │  → encrypted_blob            │                              │
     ├─ RSA wrap AES key ×N         │                              │
     │                              │                              │
     ├─ Upload encrypted_blob ────► │ Storage: files/<chat>/<ts>   │
     ├─ Send message metadata ────► │ RTDB: messages/<chat>/<id>   │
     │  { nonce, keys, file_url,    │  { payload: {...} }          │
     │    file_name, file_size }    │                              │
     │                              │                              │
     │                              │ ◄──── Download blob ─────────┤
     │                              │ ◄──── Read message metadata ─┤
     │                              │                              │
     │                              │                    RSA unwrap AES key
     │                              │                    AES-GCM decrypt(blob)
     │                              │                    → original file ✓
```

---

## 6. Threat Model

### 6.1 Adversary Capabilities

| Adversary | Capabilities | Mitigated? |
|-----------|-------------|------------|
| **Network eavesdropper** | Can intercept all traffic between client and Firebase | ✅ HTTPS + E2EE: even if TLS is broken, payload is encrypted |
| **Compromised server** | Full read access to Firebase RTDB and Storage | ✅ Server only sees ciphertext, nonces, and encrypted keys |
| **Malicious participant** | Access to their own keys and decrypted messages | ⚠️ Cannot be prevented; participants can screenshot |
| **Device theft (locked)** | Physical access to device, no password | ✅ Private key file is AES-GCM encrypted with PBKDF2 |
| **Device theft (unlocked)** | Full filesystem access during active session | ⚠️ Private key is in RAM; attacker with memory dump access can extract |
| **Brute-force password** | Offline attack on encrypted private key file | ✅ PBKDF2 with 600K iterations makes brute-force costly |
| **Brute-force recovery blob** | Offline attack on Firebase backup | ✅ 24-word BIP39 phrase provides 256 bits of entropy (impossible to brute-force) |

### 6.2 What Aegis Does NOT Protect Against

| Threat | Status | Notes |
|--------|--------|-------|
| Metadata analysis | ❌ | Firebase knows who talks to whom, when, and message sizes |
| Forward secrecy | ❌ | No ephemeral key exchange (e.g., Diffie-Hellman ratchet) |
| Key verification | ❌ | No out-of-band key fingerprint verification UI yet |
| Compromised device malware | ❌ | Keyloggers/screen capture can bypass any app-level encryption |
| Quantum computing | ❌ | RSA-2048 is not post-quantum secure |

---

## 7. Security Properties

| Property | Provided? | Mechanism |
|----------|-----------|-----------|
| **Confidentiality** | ✅ | AES-256-GCM encryption |
| **Integrity** | ✅ | GCM authentication tag (128-bit) |
| **Authentication** | ✅ | RSA-OAEP; only holder of private key can unwrap |
| **Non-repudiation** | ❌ | Sender is identified by UID, but messages are not digitally signed |
| **Forward secrecy** | ❌ | Static RSA keys; compromised key reveals past messages |
| **Replay protection** | Partial | Server timestamps; no sequence numbers |
| **Deniability** | ❌ | Messages are attributable to sender via UID |

---

## 8. Account Registration & Verification

To prevent abuse and stale verification links, Aegis enforces a strict custom email verification timeout:

1. **Custom 10-Minute Timeout:** Firebase's default email verification link is valid for 3 days. Aegis overrides this behavior client-side by recording the exact UNIX timestamp (`verification_sent_at`) when the verification email is requested.
2. **Rejection of Stale Links:** During the verification loop, if the user successfully clicks the link but the time elapsed since the request exceeds 10 minutes (600 seconds), Aegis will reject the verification, immediately sign the user out, and require them to request a fresh link.
3. **Security Benefit:** This minimizes the window in which an intercepted or leaked email verification link can be used to hijack a newly created account before the user has generated their cryptographic keys.

---

## 9. Known Limitations

1. **No Forward Secrecy:** If a user's RSA private key is ever compromised, an adversary who has archived past ciphertext can decrypt all historical messages. A future version should implement a **Double Ratchet** protocol (Signal Protocol) using X25519 ephemeral keys.

2. **No Key Verification:** Users cannot verify each other's public key fingerprints out-of-band (e.g., QR code scanning). This leaves the system vulnerable to a MITM attack where the server substitutes public keys.

3. **Metadata Exposure:** Firebase knows sender/receiver UIDs, timestamps, message sizes, and IP addresses. For stronger metadata protection, consider onion routing or a decentralised protocol.

4. **Password-Based Key Protection:** The security of the private key file depends on password strength. Weak passwords can be brute-forced despite 600K PBKDF2 iterations. Consider adding biometric unlock or hardware key support.

---

## 10. Security Audit Checklist

Use this checklist when auditing the Aegis codebase:

- [ ] **Key Generation:** RSA keys use `rsa.generate_private_key()` with `public_exponent=65537` and `key_size=2048`
- [ ] **No Key Reuse:** Each message generates a fresh AES key via `AESGCM.generate_key()`
- [ ] **Nonce Uniqueness:** Each message generates a fresh 12-byte nonce via `secrets.token_bytes(12)`
- [ ] **OAEP Padding:** RSA operations use `OAEP(mgf=MGF1(SHA256()), algorithm=SHA256())`
- [ ] **GCM Auth Tag:** AES-GCM automatically appends and verifies 128-bit authentication tag
- [ ] **PBKDF2 Iterations:** Private key protection uses 600,000 iterations
- [ ] **No Plaintext in Transit:** Verify Firebase never receives unencrypted message content
- [ ] **No Plaintext in Storage:** Verify Firebase Storage contains only encrypted blobs
- [ ] **Memory Cleanup:** `app.private_key` is set to `None` on sign-out
- [ ] **Error Handling:** `InvalidTag` exceptions are caught gracefully without leaking information
- [ ] **Dependency Versions:** `cryptography` package is up-to-date with latest security patches
- [ ] **TLS Pinning:** Consider adding certificate pinning for Firebase API calls
- [ ] **Rate Limiting:** Firebase rules should prevent abuse
