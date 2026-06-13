<p align="center">
  <img src="assets/logo.png" alt="Aegis Logo" width="160" />
</p>

<h1 align="center">Aegis – End-to-End Encrypted Messenger</h1>

<p align="center">
  <strong>Secure. Private. Cross-Platform.</strong><br/>
  A professional-grade E2EE messaging application built with Python, Kivy & KivyMD.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/kivy-2.3.1-green?style=flat-square" alt="Kivy 2.3.1" />
  <img src="https://img.shields.io/badge/kivymd-2.0.1-teal?style=flat-square" alt="KivyMD 2.0.1" />
  <img src="https://img.shields.io/badge/encryption-RSA%202048%20%2B%20AES--GCM%20256-red?style=flat-square&logo=letsencrypt" alt="RSA + AES" />
  <img src="https://img.shields.io/badge/license-MIT-orange?style=flat-square" alt="License MIT" />
</p>

---

[Baca dalam Bahasa Indonesia (Read in Indonesian)](README_id.md)

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Firebase Setup](#-firebase-setup)
- [Running the App](#-running-the-app)
- [Building for Production](#-building-for-production)
- [Security Model](#-security-model)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🛡️ Overview

**Aegis** is a cross-platform end-to-end encrypted messaging application that ensures absolute privacy for text and emoji communications. Built with a focus on security, Aegis uses a **hybrid RSA-2048 / AES-256-GCM** encryption protocol where plaintext data **never** leaves the user's device unencrypted.

The application targets **Windows, macOS, Linux, Android, and iOS** from a single Python codebase, with **build-time UI separation** to optimize binary size and performance for each platform.

### Why "Aegis"?

In Greek mythology, the *Aegis* (Αἰγίς) was Zeus's legendary shield — an impenetrable defense. Our application embodies this concept: an unbreakable shield protecting your private communications.

---

## ✨ Features

### 🔐 Security
- **RSA-2048 (OAEP/SHA-256)** asymmetric encryption for key exchange
- **AES-256-GCM** symmetric encryption with per-message key & nonce
- **PBKDF2-HMAC-SHA256** (600,000 iterations) for password-based private key protection
- Private keys never leave the device; public keys stored on Firebase
- Zero-knowledge architecture — the server **cannot** read messages

### 💬 Messaging
- 1-on-1 direct chats with full E2EE
- Group chats with multi-recipient key wrapping
- Emoji picker with 400+ emojis organized by 8 categories
- Real-time message polling with automatic decryption

### 🔐 Recovery & Custody
- **24-Word Seed Phrase (BIP39)** account recovery system
- Dual-layer private key encryption (Local Password + Cloud Seed Phrase Backup)
- Zero-knowledge key recovery without compromising E2EE

### 🎨 User Interface
- Material Design 3 with KivyMD 2.0.1
- Dark cybersecurity theme (navy/cyan/green palette)
- Animated splash screen with scale/fade-in effects
- Smooth screen transitions and micro-animations
- Responsive layouts for both desktop and mobile

### 🏗️ Architecture
- Build-time UI separation (Desktop vs Mobile)
- MVVM-inspired clean architecture
- Threaded background operations for crypto & network
- Unified build automation script (`compile.py`)
- Firebase REST API — no heavy SDKs

---

## 🏛️ Architecture

Aegis follows a layered architecture with strict separation of concerns:

```
┌────────────────────────────────────────────────────────┐
│                    ENTRY POINTS                        │
│   main_desktop.py          main_mobile.py              │
├────────────────────────────────────────────────────────┤
│                    UI LAYER                             │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐    │
│  │ Desktop  │  │  Mobile  │  │  Shared Widgets   │    │
│  │ Auth     │  │  Auth    │  │  SplashScreen     │    │
│  │ Main     │  │  ChatList│  │  MessageBubble    │    │
│  │(split)   │  │  ChatRoom│  │  ChatListItem     │    │
│  └──────────┘  └──────────┘  └───────────────────┘    │
├────────────────────────────────────────────────────────┤
│                    CORE LAYER                          │
│  ┌──────────────┐ ┌──────────────┐                   │
│  │CryptoEngine  │ │FirebaseClient│                   │
│  │RSA + AES-GCM │ │Auth, DB      │                   │
│  └──────────────┘ └──────────────┘                   │
├────────────────────────────────────────────────────────┤
│                    BUILD LAYER                         │
│  compile.py  ──►  PyInstaller (Desktop)                │
│              ──►  Buildozer   (Mobile)                 │
└────────────────────────────────────────────────────────┘
```

> **Build-Time Separation:** Desktop and Mobile UIs are **physically separated** at compile time — not selected at runtime. This reduces binary size and eliminates unused code from the final package.

---

## 📁 Project Structure

```
Aegis/
├── assets/
│   └── logo.png                    # App icon & splash logo
│
├── core/                           # Business logic (platform-agnostic)
│   ├── __init__.py
│   ├── crypto_engine.py            # RSA-2048 / AES-256-GCM encryption
│   ├── firebase_client.py          # Firebase REST API wrapper

│
├── ui/                             # User interface modules
│   ├── __init__.py
│   ├── theme.kv                    # Global KV colour tokens & styles
│   ├── desktop/                    # Desktop-only screens
│   │   ├── __init__.py
│   │   ├── desktop_auth.py         # Login/Register with RSA keygen
│   │   └── desktop_main.py         # Split-pane (sidebar + chat room)
│   ├── mobile/                     # Mobile-only screens
│   │   ├── __init__.py
│   │   ├── mobile_auth.py          # Full-screen login/register
│   │   ├── mobile_chatlist.py      # Chat list with search overlay
│   │   └── mobile_chatroom.py      # Full-screen chat room
│   └── shared/                     # Reusable widgets (both platforms)
│       ├── __init__.py
│       └── widgets.py              # SplashScreen, Bubbles, ListItems
│
├── docs/                           # Extended documentation
│   ├── ARCHITECTURE.md
│   ├── SECURITY.md
│   ├── API_REFERENCE.md
│   ├── DEPLOYMENT.md
│   ├── FIREBASE_SETUP.md
│   └── CONTRIBUTING.md
│
├── main_desktop.py                 # 🖥️  Desktop entry point
├── main_mobile.py                  # 📱 Mobile entry point
├── compile.py                      # 🔨 Unified build automation
├── buildozer.spec                  # Android/iOS build config
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

---

## 📦 Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.10+ | Runtime |
| pip | Latest | Package manager |
| Git | Any | Version control |
| Kivy | 2.3.1 | UI framework |
| KivyMD | 2.0.1 | Material Design widgets |
| cryptography | 43.0+ | E2EE operations |
| requests | 2.32+ | Firebase REST calls |
| PyInstaller | 6.10+ | Desktop builds |
| Buildozer | 1.5+ | Mobile builds (Linux/macOS only) |

**Platform-specific:**
- **macOS:** Xcode Command Line Tools (`xcode-select --install`)
- **Linux:** `build-essential`, `libffi-dev`, `libssl-dev`
- **Android builds:** Java JDK 17, Android SDK/NDK (auto-managed by Buildozer)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/LythianOlyx/Aegis.git
cd Aegis
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python -c "import kivy; print(f'Kivy {kivy.__version__}')"
python -c "import kivymd; print(f'KivyMD {kivymd.__version__}')"
python -c "from core.crypto_engine import generate_rsa_keypair; print('Crypto ✓')"
```

---

## 🔥 Firebase Setup

Aegis requires a Firebase project with **Authentication** and **Realtime Database** enabled. Cloud Storage is not required. See [`docs/FIREBASE_SETUP.md`](docs/FIREBASE_SETUP.md) for a detailed step-by-step guide.

### Quick Start

1. Create a project at [Firebase Console](https://console.firebase.google.com/)
2. Enable **Email/Password** authentication
3. Create a **Realtime Database** (start in test mode)
4. Configure security rules and indexes

```bash
export FIREBASE_API_KEY="AIzaSyDk8fV0Kqo3JXNcXd_4a3EYBgk3DWtalUc"
export FIREBASE_PROJECT_ID="aegis-b6f5a"
export FIREBASE_DB_URL="https://aegis-b6f5a-default-rtdb.asia-southeast1.firebasedatabase.app"
```

---

## ▶️ Running the App

### Desktop Mode

```bash
python main_desktop.py
```

Window opens at **1280×800** with the split-pane interface:
- Left sidebar: Chat list, user search, new chat
- Right pane: Active chat room with E2EE messaging

### Mobile Mode (Development)

```bash
python main_mobile.py
```

Launches the mobile UI in a desktop window for development/testing. Uses stacked screen navigation (Auth → ChatList → ChatRoom).

---

## 🔨 Building for Production

### Interactive Build Tool

```bash
python compile.py
```

The build tool will:
1. Detect your host OS (Linux / macOS / Windows)
2. Ask you to choose: **Desktop** or **Mobile** target
3. Show valid output formats for your OS
4. Execute the appropriate build pipeline

### Desktop (PyInstaller)

| Host OS | Output Formats |
|---------|---------------|
| macOS | `.app`, `.dmg` |
| Windows | `.exe` |
| Linux | `.AppImage`, `.deb`, Directory |

```bash
# Direct PyInstaller build (without compile.py)
pyinstaller aegis_desktop.spec --clean
```

### Mobile (Buildozer)

```bash
# Android APK (requires Linux or macOS)
buildozer android debug

# iOS (requires macOS + Xcode)
buildozer ios debug
```

> See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for platform-specific build instructions, code signing, and CI/CD pipelines.

---

## 🔐 Security Model

### Encryption Protocol

```
┌─────────────────────────────────────────────────────────┐
│                    MESSAGE ENCRYPTION                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Generate random AES-256 key (32 bytes)              │
│  2. Generate random nonce (12 bytes)                    │
│  3. AES-GCM-256 encrypt(plaintext) → ciphertext + tag  │
│  4. For EACH recipient:                                 │
│     RSA-OAEP(SHA-256) encrypt(AES key, pub_key)         │
│  5. Send to Firebase:                                   │
│     { ciphertext, nonce, encrypted_keys[] }             │
│                                                         │
│  ⚠ Plaintext and raw AES keys NEVER touch the network  │
└─────────────────────────────────────────────────────────┘
```

### Private Key Protection

```
User Password                              BIP39 Seed Phrase (24 Words)
     │                                           │
     ▼                                           ▼
PBKDF2-HMAC-SHA256                           PBKDF2-HMAC-SHA256
(600,000 iterations)                         (100,000 iterations)
     │                                           │
     ▼                                           ▼
Derived AES-256 Key                          Derived AES-256 Key
     │                                           │
     ▼                                           ▼
AES-GCM encrypt(RSA private key)             AES-GCM encrypt(RSA private key)
     │                                           │
     ▼                                           ▼
Stored locally: { salt, nonce, ciphertxt }   Stored in Firebase: recovery_blob
```

> **Recovery Mechanism:** The private key is encrypted twice. The local copy is secured by the user's password. A secondary backup (`recovery_blob`) is encrypted with a randomly generated 24-word seed phrase and stored on Firebase.
> 
> **Automatic Recovery Flow:** If the user forgets their password, they can reset it via email. When they log in with the *new* password, Aegis automatically detects that the local private key cannot be decrypted. The application will seamlessly transition to the **Recovery Screen**, prompting for the 24-word seed phrase to decrypt the `recovery_blob` from Firebase and restore the private key.
> 
> **Data Loss & Key Regeneration:** If the user completely loses their seed phrase, they can choose to **"Skip"** recovery. This permanently discards the old cryptographic identity, generates a fresh RSA keypair, and loops them back to the setup phase to create a new 24-word seed phrase. **All previous message history will be permanently unreadable** as a deliberate consequence of the E2EE Zero-Knowledge design.

> See [`docs/SECURITY.md`](docs/SECURITY.md) for the full cryptographic specification, threat model, and security audit checklist.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System architecture, design patterns, data flow |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Cryptographic protocol, threat model, key management |
| [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) | Module-by-module API documentation |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Build guides, CI/CD, code signing |
| [`docs/FIREBASE_SETUP.md`](docs/FIREBASE_SETUP.md) | Firebase project configuration |
| [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) | Contribution guidelines, code style |

---

## 🤝 Contributing

We welcome contributions! Please read [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) for:
- Code style guidelines (PEP 8, type hints, docstrings)
- Branch naming conventions
- Pull request process
- Security vulnerability reporting

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <img src="assets/logo.png" alt="Aegis" width="48" /><br/>
  <em>Built with 🔒 by the Aegis Team</em>
</p>
