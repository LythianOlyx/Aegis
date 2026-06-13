# Aegis – System Architecture

> **Version:** 1.0.0  
> **Last Updated:** 2026-05-13  
> **Author:** Aegis Development Team

---

## Table of Contents

- [1. High-Level Overview](#1-high-level-overview)
- [2. Design Principles](#2-design-principles)
- [3. Layer Breakdown](#3-layer-breakdown)
- [4. Data Flow Diagrams](#4-data-flow-diagrams)
- [5. Build-Time UI Separation](#5-build-time-ui-separation)
- [6. Threading Model](#6-threading-model)
- [7. State Management](#7-state-management)
- [8. Firebase Data Schema](#8-firebase-data-schema)
- [9. Module Dependency Graph](#9-module-dependency-graph)

---

## 1. High-Level Overview

Aegis is structured as a **three-layer application** with strict separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                      │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │  Desktop UI │  │  Mobile UI   │  │   Shared Widgets   │  │
│  │             │  │              │  │                    │  │
│  │ Split-Pane  │  │ Stacked Nav  │  │  SplashScreen      │  │
│  │ Sidebar +   │  │ Auth →       │  │  E2EEMessageBubble │  │
│  │ ChatRoom    │  │ ChatList →   │  │  ChatListItem      │  │
│  │             │  │ ChatRoom     │  │  UserSearchResult  │  │
│  └─────────────┘  └──────────────┘  └────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│                      BUSINESS LOGIC LAYER                    │
│                                                              │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  │
│  │      CryptoEngine       │  │     FirebaseClient      │  │
│  │                         │  │                         │  │
│  │  RSA-2048 OAEP          │  │  Auth REST API          │  │
│  │  AES-256-GCM            │  │  RTDB CRUD              │  │
│  │  PBKDF2 KDF             │  │  User Search            │  │
│  │  Key Serialize          │  │                         │  │
│  └─────────────────────────┘  └─────────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│                      INFRASTRUCTURE LAYER                    │
│                                                              │
│           Firebase Auth ◄──► Firebase RTDB                   │
│            (REST API)         (REST API)                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Design Principles

| # | Principle | Implementation |
|---|-----------|----------------|
| 1 | **Zero Trust** | All payloads encrypted before leaving the device. Firebase stores only ciphertext. |
| 2 | **Build-Time Separation** | Desktop and Mobile UIs are separate codepaths, selected at compile time — not runtime. |
| 3 | **Non-Blocking UI** | All crypto and network operations run in `threading.Thread`; results dispatched to UI via `Clock.schedule_once`. |
| 4 | **SDK-Free Backend** | Firebase interactions use raw REST APIs via `requests` — no heavyweight SDKs that bloat the binary. |
| 5 | **Type Safety** | Strict Python type hints throughout with comprehensive docstrings. |
| 6 | **Single Responsibility** | Each module has exactly one job: crypto, network, or UI rendering. |

---

## 3. Layer Breakdown

### 3.1 Core Layer (`core/`)

#### `crypto_engine.py`

| Function | Purpose | Algorithm |
|----------|---------|-----------|
| `generate_rsa_keypair()` | Create 2048-bit key pair | RSA, e=65537 |
| `generate_aes_key()` | Random 256-bit symmetric key | CSPRNG |
| `generate_nonce()` | Random 96-bit nonce | CSPRNG |
| `serialize_public_key()` | RSA pubkey → Base64 PEM | PEM/DER |
| `deserialize_public_key()` | Base64 PEM → RSA pubkey | PEM/DER |
| `encrypt_private_key()` | Password-protect RSA privkey | PBKDF2 + AES-GCM |
| `decrypt_private_key()` | Unlock RSA privkey from password | PBKDF2 + AES-GCM |
| `aes_encrypt()` | Encrypt raw bytes | AES-256-GCM |
| `aes_decrypt()` | Decrypt raw bytes | AES-256-GCM |
| `rsa_encrypt_aes_key()` | Wrap AES key with RSA pubkey | RSA-OAEP/SHA-256 |
| `rsa_decrypt_aes_key()` | Unwrap AES key with RSA privkey | RSA-OAEP/SHA-256 |
| `encrypt_message()` | High-level text E2EE | AES-GCM + RSA-OAEP |
| `decrypt_message()` | High-level text decryption | RSA-OAEP + AES-GCM |

#### `firebase_client.py`

| Method Category | Methods | Firebase Service |
|----------------|---------|-----------------|
| Authentication | `sign_up`, `sign_in`, `sign_out`, `refresh_id_token`, `update_profile`, `get_user_data` | Identity Toolkit |
| Database CRUD | `db_get`, `db_put`, `db_patch`, `db_post`, `db_delete`, `db_query` | Realtime Database |
| Users | `search_users`, `register_user_profile`, `get_public_key` | RTDB |
| Messaging | `send_message`, `get_messages`, `create_chat`, `get_user_chats`, `get_chat_info` | RTDB |

### 3.2 UI Layer (`ui/`)

#### Shared Widgets (`ui/shared/widgets.py`)

| Widget | Type | Description |
|--------|------|-------------|
| `SplashScreen` | `Screen` | Animated logo with scale/fade-in, auto-navigates after 2.5s |
| `E2EEMessageBubble` | `MDBoxLayout` | Text message bubble with sent/received styling, lock icon |
| `ChatListItem` | `MDBoxLayout` | Chat preview with avatar, name, last message, timestamp |
| `UserSearchResult` | `MDBoxLayout` | Search result with avatar, name, email |
| `AegisTextField` | `MDTextField` | Pre-themed text input |

#### Desktop UI (`ui/desktop/`)

- **`desktop_auth.py`** — `DesktopAuthScreen`: Centred card layout, login/register toggle with slide animation, background RSA key generation on registration
- **`desktop_main.py`** — `DesktopMainScreen`: 340dp sidebar with chat list + search + new chat button; right pane with chat header, scrollable message area, and message input bar

#### Mobile UI (`ui/mobile/`)

- **`mobile_auth.py`** — `MobileAuthScreen`: Full-screen scrollable form
- **`mobile_chatlist.py`** — `MobileChatListScreen`: Top bar + search overlay + vertical chat list
- **`mobile_chatroom.py`** — `MobileChatRoomScreen`: Back button, chat header, message area, input bar

---

## 4. Data Flow Diagrams

### 4.1 Message Send Flow

```
User types message
       │
       ▼
┌──────────────────┐
│  UI Thread       │
│  send_message()  │───► threading.Thread()
└──────────────────┘           │
                               ▼
                    ┌────────────────────┐
                    │  Background Thread │
                    ├────────────────────┤
                    │ 1. Fetch recipient │
                    │    public keys     │
                    │    (Firebase GET)  │
                    │                    │
                    │ 2. encrypt_message │
                    │    AES-GCM +       │
                    │    RSA-OAEP wrap   │
                    │                    │
                    │ 3. send_message    │
                    │    (Firebase POST) │
                    └────────┬───────────┘
                             │
                             ▼
                    Clock.schedule_once()
                             │
                             ▼
                    ┌────────────────────┐
                    │  UI Thread         │
                    │  _render_messages() │
                    │  Update ScrollView │
                    └────────────────────┘
```

### 4.2 User Registration Flow

```
User fills form → [Register]
       │
       ▼
  Background Thread:
  ┌───────────────────────────────────┐
  │ 1. Firebase Auth signUp()         │
  │ 2. generate_rsa_keypair()         │
  │ 3. encrypt_private_key(password)  │
  │ 4. Store pubkey → Firebase DB     │
  │ 5. Store encrypted privkey → disk │
  │    ~/.aegis/keys/<uid>.key        │
  └───────────────────────────────────┘
       │
       ▼
  UI Thread: Navigate to Main Screen
  (private key held in app.private_key RAM)
```

---

## 5. Build-Time UI Separation

```
          Source Code
               │
     ┌─────────┴─────────┐
     ▼                    ▼
main_desktop.py      main_mobile.py
     │                    │
     ▼                    ▼
┌─────────┐         ┌─────────┐
│ imports  │         │ imports  │
│ ui/desk/ │         │ ui/mob/ │
│ ui/shar/ │         │ ui/shar/│
│ core/*   │         │ core/*  │
└────┬─────┘         └────┬────┘
     │                    │
     ▼                    ▼
PyInstaller          Buildozer
excludes:            excludes:
  ui.mobile            ui/desktop
     │                    │
     ▼                    ▼
 Desktop.app          Mobile.apk
 (no mobile           (no desktop
  code inside)         code inside)
```

---

## 6. Threading Model

All heavy operations run in daemon threads to keep the UI responsive:

| Operation | Thread | UI Callback |
|-----------|--------|-------------|
| Sign In / Register | `threading.Thread(daemon=True)` | `Clock.schedule_once(_on_auth_success)` |
| Load Chat List | `threading.Thread(daemon=True)` | `Clock.schedule_once(_render_chat_list)` |
| Load Messages | `threading.Thread(daemon=True)` | `Clock.schedule_once(_render_messages)` |
| Send Message | `threading.Thread(daemon=True)` | `Clock.schedule_once(_load_messages)` |
| Search Users | `threading.Thread(daemon=True)` | `Clock.schedule_once(_display_search_results)` |
| Message Polling | `Clock.schedule_interval(5.0)` | Triggers threaded `_load_messages` |

**Rule:** Never call `requests.*` or `crypto_engine.*` from the main thread.

---

## 7. State Management

| State | Location | Scope |
|-------|----------|-------|
| Firebase tokens | `FirebaseClient` instance | Session |
| RSA private key | `app.private_key` (RAM) | Session |
| Encrypted private key | `~/.aegis/keys/<uid>.key` | Persistent |
| RSA public keys | Firebase RTDB `/users/<uid>/public_key` | Persistent |
| Current chat ID | `app.active_chat_id` (mobile) / `screen.current_chat_id` (desktop) | Session |
| Chat participants | `screen._chat_participants` dict | Session |

---

## 8. Firebase Data Schema

```
firebase-rtdb/
├── users/
│   └── <uid>/
│       ├── email: string
│       ├── display_name: string
│       ├── public_key: string (Base64 PEM)
│       └── created_at: number (timestamp)
│
├── chats/
│   └── <chat_id>/
│       ├── type: "direct" | "group"
│       ├── name: string (groups only)
│       ├── participants/
│       │   ├── <uid_1>: true
│       │   └── <uid_2>: true
│       └── created_at: number (server timestamp)
│
├── messages/
│   └── <chat_id>/
│       └── <message_id>/
│           ├── sender: string (uid)
│           ├── type: "text"
│           ├── timestamp: number (server timestamp)
│           └── payload/
│               ├── nonce: string (Base64)
│               ├── ciphertext: string (Base64)
│               └── keys/
│                   ├── "0": string (Base64 RSA-encrypted AES key)
│                   └── "1": string (for 2nd participant)
│
├── user_chats/
│   └── <uid>/
│       ├── <chat_id_1>: true
│       └── <chat_id_2>: true
```

### Realtime Database Rules (Recommended)

```json
{
  "rules": {
    "users": {
      "$uid": {
        ".read": "auth != null",
        ".write": "auth != null && auth.uid == $uid"
      }
    },
    "chats": {
      "$chatId": {
        ".read": "auth != null && data.child('participants').child(auth.uid).exists()",
        ".write": "auth != null"
      }
    },
    "messages": {
      "$chatId": {
        ".read": "auth != null && root.child('chats').child($chatId).child('participants').child(auth.uid).exists()",
        ".write": "auth != null && root.child('chats').child($chatId).child('participants').child(auth.uid).exists()"
      }
    },
    "user_chats": {
      "$uid": {
        ".read": "auth != null && auth.uid == $uid",
        ".write": "auth != null"
      }
    }
  }
}
```

---

## 9. Module Dependency Graph

```
main_desktop.py ──┬──► ui/desktop/desktop_auth.py ──┬──► core/crypto_engine.py
                  │                                  └──► core/firebase_client.py
                  ├──► ui/desktop/desktop_main.py ──┬──► core/crypto_engine.py
                  │                                 ├──► core/firebase_client.py
                  │                                 └──► ui/shared/widgets.py
                  └──► ui/shared/widgets.py

main_mobile.py ───┬──► ui/mobile/mobile_auth.py ───┬──► core/crypto_engine.py
                  │                                 └──► core/firebase_client.py
                  ├──► ui/mobile/mobile_chatlist.py ┬──► core/firebase_client.py
                  │                                 └──► ui/shared/widgets.py
                  ├──► ui/mobile/mobile_chatroom.py ┬──► core/crypto_engine.py
                  │                                 ├──► core/firebase_client.py
                  │                                 └──► ui/shared/widgets.py
                  └──► ui/shared/widgets.py

core/crypto_engine.py ──► cryptography (stdlib)
core/firebase_client.py ──► requests
```
