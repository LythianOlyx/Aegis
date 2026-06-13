# Aegis – Arsitektur Sistem

> **Versi:** 1.0.0  
> **Terakhir Diperbarui:** 2026-05-13  
> **Penulis:** Tim Pengembang Aegis

---

## Daftar Isi

- [1. Gambaran Tingkat Tinggi](#1-gambaran-tingkat-tinggi)
- [2. Prinsip Desain](#2-prinsip-desain)
- [3. Rincian Lapisan (Layer Breakdown)](#3-rincian-lapisan-layer-breakdown)
- [4. Diagram Aliran Data (Data Flow Diagrams)](#4-diagram-aliran-data-data-flow-diagrams)
- [5. Pemisahan UI pada saat Kompilasi (Build-Time UI Separation)](#5-pemisahan-ui-pada-saat-kompilasi-build-time-ui-separation)
- [6. Model Threading](#6-model-threading)
- [7. Manajemen State](#7-manajemen-state)
- [8. Skema Data Firebase](#8-skema-data-firebase)
- [9. Grafik Ketergantungan Modul](#9-grafik-ketergantungan-modul)

---

## 1. Gambaran Tingkat Tinggi

Aegis disusun sebagai **aplikasi tiga lapis** dengan pemisahan tugas yang ketat:

```text
┌─────────────────────────────────────────────────────────────┐
│                       LAPISAN PRESENTASI                     │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │  UI Desktop │  │  UI Seluler  │  │ Widget Bersama     │   │
│  │             │  │              │  │                    │   │
│  │ Split-Pane  │  │ Stacked Nav  │  │  SplashScreen      │   │
│  │ Sidebar +   │  │ Auth →       │  │  E2EEMessageBubble │   │
│  │ ChatRoom    │  │ ChatList →   │  │  ChatListItem      │   │
│  │             │  │ ChatRoom     │  │  UserSearchResult  │   │
│  └─────────────┘  └──────────────┘  └────────────────────┘   │
├──────────────────────────────────────────────────────────────┤
│                       LAPISAN LOGIKA BISNIS                  │
│                                                              │
│  ┌─────────────────────────┐  ┌─────────────────────────┐   │
│  │      CryptoEngine       │  │     FirebaseClient      │   │
│  │                         │  │                         │   │
│  │  RSA-2048 OAEP          │  │  Auth REST API          │   │
│  │  AES-256-GCM            │  │  RTDB CRUD              │   │
│  │  PBKDF2 KDF             │  │  Pencarian User         │   │
│  │  Serialisasi Kunci      │  │                         │   │
│  └─────────────────────────┘  └─────────────────────────┘   │
├──────────────────────────────────────────────────────────────┤
│                       LAPISAN INFRASTRUKTUR                  │
│                                                              │
│           Firebase Auth ◄──► Firebase RTDB                   │
│            (REST API)         (REST API)                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Prinsip Desain

| # | Prinsip | Implementasi |
|---|-----------|----------------|
| 1 | **Zero Trust** | Semua payload dienkripsi sebelum meninggalkan perangkat. Firebase hanya menyimpan ciphertext. |
| 2 | **Pemisahan Build-Time** | UI Desktop dan Seluler adalah codepath yang berbeda, dipilih saat kompilasi — bukan runtime. |
| 3 | **UI Non-Blocking** | Semua operasi kripto dan jaringan berjalan di `threading.Thread`; hasil dikirim ke UI via `Clock.schedule_once`. |
| 4 | **Backend Tanpa SDK** | Interaksi Firebase menggunakan REST API mentah via `requests` — tidak ada SDK berat yang membuat ukuran biner membengkak. |
| 5 | **Keamanan Tipe (Type Safety)** | Petunjuk tipe Python (type hints) yang ketat di seluruh bagian dengan docstrings yang komprehensif. |
| 6 | **Tanggung Jawab Tunggal** | Setiap modul memiliki tepat satu pekerjaan: kripto, jaringan, I/O file, atau rendering UI. |

---

## 3. Rincian Lapisan (Layer Breakdown)

### 3.1 Lapisan Inti (`core/`)

#### `crypto_engine.py`

| Fungsi | Tujuan | Algoritma |
|----------|---------|-----------|
| `generate_rsa_keypair()` | Membuat pasangan kunci 2048-bit | RSA, e=65537 |
| `generate_aes_key()` | Kunci simetris 256-bit acak | CSPRNG |
| `generate_nonce()` | Nonce 96-bit acak | CSPRNG |
| `serialize_public_key()` | RSA pubkey → Base64 PEM | PEM/DER |
| `deserialize_public_key()` | Base64 PEM → RSA pubkey | PEM/DER |
| `encrypt_private_key()` | Melindungi RSA privkey dengan kata sandi | PBKDF2 + AES-GCM |
| `decrypt_private_key()` | Membuka RSA privkey dari kata sandi | PBKDF2 + AES-GCM |
| `aes_encrypt()` | Mengenkripsi byte mentah | AES-256-GCM |
| `aes_decrypt()` | Mendekripsi byte mentah | AES-256-GCM |
| `rsa_encrypt_aes_key()` | Membungkus kunci AES dengan RSA pubkey | RSA-OAEP/SHA-256 |
| `rsa_decrypt_aes_key()` | Membuka bungkus kunci AES dengan RSA privkey | RSA-OAEP/SHA-256 |
| `encrypt_message()` | E2EE teks tingkat tinggi | AES-GCM + RSA-OAEP |
| `decrypt_message()` | Dekripsi teks tingkat tinggi | RSA-OAEP + AES-GCM |

#### `firebase_client.py`

| Kategori Metode | Metode | Layanan Firebase |
|----------------|---------|-----------------|
| Autentikasi | `sign_up`, `sign_in`, `sign_out`, `refresh_id_token`, `update_profile`, `get_user_data` | Identity Toolkit |
| Database CRUD | `db_get`, `db_put`, `db_patch`, `db_post`, `db_delete`, `db_query` | Realtime Database |
| Pengguna | `search_users`, `register_user_profile`, `get_public_key` | RTDB |
| Perpesanan | `send_message`, `get_messages`, `create_chat`, `get_user_chats`, `get_chat_info` | RTDB |

### 3.2 Lapisan Antarmuka Pengguna (`ui/`)

#### Widget Bersama (`ui/shared/widgets.py`)

| Widget | Tipe | Deskripsi |
|--------|------|-------------|
| `SplashScreen` | `Screen` | Logo animasi dengan efek scale/fade-in, auto-navigasi setelah 2.5s |
| `E2EEMessageBubble` | `MDBoxLayout` | Gelembung pesan teks dengan gaya terkirim/diterima, ikon gembok |
| `ChatListItem` | `MDBoxLayout` | Pratinjau obrolan dengan avatar, nama, pesan terakhir, timestamp |
| `UserSearchResult` | `MDBoxLayout` | Hasil pencarian dengan avatar, nama, email |
| `AegisTextField` | `MDTextField` | Input teks yang sudah disesuaikan temanya |

#### UI Desktop (`ui/desktop/`)

- **`desktop_auth.py`** — `DesktopAuthScreen`: Tata letak kartu di tengah, toggle login/daftar dengan animasi geser, pembuatan kunci RSA latar belakang saat pendaftaran
- **`desktop_main.py`** — `DesktopMainScreen`: Sidebar 340dp dengan daftar obrolan + pencarian + tombol obrolan baru; panel kanan dengan header obrolan, area pesan yang dapat di-scroll, dan bar input pesan

#### UI Seluler (`ui/mobile/`)

- **`mobile_auth.py`** — `MobileAuthScreen`: Formulir layar penuh yang dapat di-scroll
- **`mobile_chatlist.py`** — `MobileChatListScreen`: Bilah atas + overlay pencarian + daftar obrolan vertikal
- **`mobile_chatroom.py`** — `MobileChatRoomScreen`: Tombol kembali, header obrolan, area pesan, bar input

---

## 4. Diagram Aliran Data (Data Flow Diagrams)

### 4.1 Aliran Pengiriman Pesan

```
Pengguna mengetik pesan
       │
       ▼
┌──────────────────┐
│  UI Thread       │
│  send_message()  │───► threading.Thread()
└──────────────────┘           │
                               ▼
                    ┌────────────────────┐
                    │ Background Thread  │
                    ├────────────────────┤
                    │ 1. Ambil public key│
                    │    penerima        │
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
                    │  _render_messages()│
                    │  Perbarui ListView │
                    └────────────────────┘
```

### 4.2 Aliran Pendaftaran Pengguna

```
Pengguna mengisi form → [Register]
       │
       ▼
  Background Thread:
  ┌───────────────────────────────────┐
  │ 1. Firebase Auth signUp()         │
  │ 2. generate_rsa_keypair()         │
  │ 3. encrypt_private_key(password)  │
  │ 4. Simpan pubkey → Firebase DB    │
  │ 5. Simpan privkey terenkripsi →   │
  │    ~/.aegis/keys/<uid>.key        │
  └───────────────────────────────────┘
       │
       ▼
  UI Thread: Navigasi ke Layar Utama
  (private key disimpan di app.private_key RAM)
```

---

## 5. Pemisahan UI pada saat Kompilasi (Build-Time UI Separation)

```
           Kode Sumber
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
  (tanpa kode          (tanpa kode
   seluler di           desktop di
   dalamnya)            dalamnya)
```

---

## 6. Model Threading

Semua operasi berat berjalan di *daemon threads* agar UI tetap responsif:

| Operasi | Thread | Callback UI |
|-----------|--------|-------------|
| Masuk / Daftar | `threading.Thread(daemon=True)` | `Clock.schedule_once(_on_auth_success)` |
| Muat Daftar Obrolan | `threading.Thread(daemon=True)` | `Clock.schedule_once(_render_chat_list)` |
| Muat Pesan | `threading.Thread(daemon=True)` | `Clock.schedule_once(_render_messages)` |
| Kirim Pesan | `threading.Thread(daemon=True)` | `Clock.schedule_once(_load_messages)` |
| Cari Pengguna | `threading.Thread(daemon=True)` | `Clock.schedule_once(_display_search_results)` |
| Polling Pesan | `Clock.schedule_interval(5.0)` | Memicu thread `_load_messages` |

**Aturan:** Jangan pernah memanggil `requests.*` atau `crypto_engine.*` dari *main thread*.

---

## 7. Manajemen State

| State | Lokasi | Cakupan |
|-------|----------|-------|
| Token Firebase | `FirebaseClient` instance | Sesi |
| RSA private key | `app.private_key` (RAM) | Sesi |
| Encrypted private key | `~/.aegis/keys/<uid>.key` | Persisten |
| RSA public keys | Firebase RTDB `/users/<uid>/public_key` | Persisten |
| ID obrolan saat ini | `app.active_chat_id` (seluler) / `screen.current_chat_id` (desktop) | Sesi |
| Peserta obrolan | Dict `screen._chat_participants` | Sesi |

---

## 8. Skema Data Firebase

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
│       ├── name: string (khusus grup)
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
│                   └── "1": string (untuk peserta ke-2)
│
├── user_chats/
│   └── <uid>/
│       ├── <chat_id_1>: true
│       └── <chat_id_2>: true
```

### Aturan Realtime Database (Disarankan)

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

## 9. Grafik Ketergantungan Modul

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
