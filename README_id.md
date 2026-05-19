<p align="center">
  <img src="assets/logo.png" alt="Logo Aegis" width="160" />
</p>

<h1 align="center">Aegis – End-to-End Encrypted Messenger</h1>

<p align="center">
  <strong>Aman. Privat. Lintas Platform.</strong><br/>
  Aplikasi perpesanan E2EE kelas profesional yang dibangun dengan Python, Kivy & KivyMD.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/kivy-2.3.1-green?style=flat-square" alt="Kivy 2.3.1" />
  <img src="https://img.shields.io/badge/kivymd-2.0.1-teal?style=flat-square" alt="KivyMD 2.0.1" />
  <img src="https://img.shields.io/badge/encryption-RSA%202048%20%2B%20AES--GCM%20256-red?style=flat-square&logo=letsencrypt" alt="RSA + AES" />
  <img src="https://img.shields.io/badge/license-MIT-orange?style=flat-square" alt="Lisensi MIT" />
</p>

---

[Baca dalam Bahasa Inggris (Read in English)](README.md)

## 📋 Daftar Isi

- [Gambaran Umum](#-gambaran-umum)
- [Fitur](#-fitur)
- [Arsitektur](#-arsitektur)
- [Struktur Proyek](#-struktur-proyek)
- [Prasyarat](#-prasyarat)
- [Instalasi](#-instalasi)
- [Pengaturan Firebase](#-pengaturan-firebase)
- [Menjalankan Aplikasi](#-menjalankan-aplikasi)
- [Membangun untuk Produksi](#-membangun-untuk-produksi)
- [Model Keamanan](#-model-keamanan)
- [Dokumentasi](#-dokumentasi)
- [Berkontribusi](#-berkontribusi)
- [Lisensi](#-lisensi)

---

## 🛡️ Gambaran Umum

**Aegis** adalah aplikasi perpesanan terenkripsi end-to-end (E2EE) lintas platform yang menjamin privasi mutlak untuk komunikasi teks dan file. Dibangun dengan fokus pada keamanan, Aegis menggunakan protokol enkripsi **hybrid RSA-2048 / AES-256-GCM** di mana data *plaintext* **tidak pernah** meninggalkan perangkat pengguna dalam keadaan tidak terenkripsi.

Aplikasi ini menargetkan **Windows, macOS, Linux, Android, dan iOS** dari satu basis kode Python, dengan **pemisahan UI pada saat kompilasi (build-time)** untuk mengoptimalkan ukuran biner dan performa untuk masing-masing platform.

### Mengapa "Aegis"?

Dalam mitologi Yunani, *Aegis* (Αἰγίς) adalah perisai legendaris milik Zeus — pertahanan yang tak tertembus. Aplikasi kami mewujudkan konsep ini: perisai yang tak terpatahkan untuk melindungi komunikasi pribadi Anda.

---

## ✨ Fitur

### 🔐 Keamanan
- Enkripsi asimetris **RSA-2048 (OAEP/SHA-256)** untuk pertukaran kunci
- Enkripsi simetris **AES-256-GCM** dengan kunci & *nonce* per-pesan
- **PBKDF2-HMAC-SHA256** (600.000 iterasi) untuk perlindungan *private key* berbasis kata sandi
- *Private key* tidak pernah meninggalkan perangkat; *public key* disimpan di Firebase
- Arsitektur *Zero-knowledge* — server **tidak bisa** membaca pesan

### 💬 Perpesanan
- Obrolan langsung 1-on-1 dengan E2EE penuh
- Obrolan grup dengan pembungkusan kunci multi-penerima (*multi-recipient key wrapping*)
- Transfer file terenkripsi (gambar, dokumen, media)
- Penarikan pesan (*polling*) real-time dengan dekripsi otomatis

### 🔐 Pemulihan & Penyimpanan (Custody)
- Sistem pemulihan akun menggunakan **24-Word Seed Phrase (BIP39)**
- Enkripsi *private key* dua lapis (Kata Sandi Lokal + *Backup* Seed Phrase di Cloud)
- Pemulihan kunci *Zero-knowledge* tanpa mengorbankan E2EE

### 🎨 Antarmuka Pengguna (UI)
- Material Design 3 dengan KivyMD 2.0.1
- Tema gelap *cybersecurity* (palet navy/cyan/hijau)
- Layar *splash* animasi dengan efek *scale/fade-in*
- Transisi layar dan mikro-animasi yang mulus
- Tata letak responsif untuk desktop maupun seluler

### 🏗️ Arsitektur
- Pemisahan UI pada saat kompilasi (Desktop vs Seluler)
- Arsitektur bersih terinspirasi dari MVVM
- Operasi latar belakang *threaded* untuk kriptografi & jaringan
- Skrip otomatisasi *build* terpadu (`compile.py`)
- Firebase REST API — tanpa SDK berat

---

## 🏛️ Arsitektur

Aegis mengikuti arsitektur berlapis dengan pemisahan tugas yang ketat:

```
┌────────────────────────────────────────────────────────┐
│                    ENTRY POINTS                        │
│   main_desktop.py          main_mobile.py              │
├────────────────────────────────────────────────────────┤
│                    UI LAYER                            │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐     │
│  │ Desktop  │  │  Mobile  │  │  Shared Widgets   │     │
│  │ Auth     │  │  Auth    │  │  SplashScreen     │     │
│  │ Main     │  │  ChatList│  │  MessageBubble    │     │
│  │(split)   │  │  ChatRoom│  │  ChatListItem     │     │
│  └──────────┘  └──────────┘  └───────────────────┘     │
├────────────────────────────────────────────────────────┤
│                    CORE LAYER                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │CryptoEngine  │ │FirebaseClient│ │ FileManager  │    │
│  │RSA + AES-GCM │ │Auth, DB, Stor│ │Chunk, MIME   │    │
│  └──────────────┘ └──────────────┘ └──────────────┘    │
├────────────────────────────────────────────────────────┤
│                    BUILD LAYER                         │
│  compile.py  ──►  PyInstaller (Desktop)                │
│              ──►  Buildozer   (Mobile)                 │
└────────────────────────────────────────────────────────┘
```

> **Build-Time Separation:** UI Desktop dan Seluler dipisahkan secara **fisik** pada saat kompilasi — bukan dipilih saat aplikasi berjalan (*runtime*). Hal ini mengurangi ukuran biner dan mengeliminasi kode yang tidak terpakai dari paket akhir.

---

## 📁 Struktur Proyek

```
Aegis/
├── assets/
│   └── logo.png                    # Ikon aplikasi & logo splash
│
├── core/                           # Logika bisnis (lintas platform)
│   ├── __init__.py
│   ├── crypto_engine.py            # Enkripsi RSA-2048 / AES-256-GCM
│   ├── firebase_client.py          # Wrapper Firebase REST API
│   └── file_manager.py             # File I/O, validasi, MIME
│
├── ui/                             # Modul antarmuka pengguna
│   ├── __init__.py
│   ├── theme.kv                    # Token & gaya warna KV global
│   ├── desktop/                    # Layar khusus Desktop
│   │   ├── __init__.py
│   │   ├── desktop_auth.py         # Login/Daftar dengan keygen RSA
│   │   └── desktop_main.py         # Layar terbelah (sidebar + ruang obrolan)
│   ├── mobile/                     # Layar khusus Seluler
│   │   ├── __init__.py
│   │   ├── mobile_auth.py          # Login/Daftar layar penuh
│   │   ├── mobile_chatlist.py      # Daftar obrolan dengan overlay pencarian
│   │   └── mobile_chatroom.py      # Ruang obrolan layar penuh
│   └── shared/                     # Widget yang dapat digunakan ulang
│       ├── __init__.py
│       └── widgets.py              # SplashScreen, Bubbles, ListItems
│
├── docs/                           # Dokumentasi Lanjutan
│   ├── ARCHITECTURE_id.md
│   ├── SECURITY_id.md
│   ├── API_REFERENCE_id.md
│   ├── DEPLOYMENT_id.md
│   ├── FIREBASE_SETUP_id.md
│   └── CONTRIBUTING_id.md
│
├── main_desktop.py                 # 🖥️  Titik masuk Desktop
├── main_mobile.py                  # 📱 Titik masuk Seluler
├── compile.py                      # 🔨 Otomatisasi build terpadu
├── buildozer.spec                  # Konfigurasi build Android/iOS
├── requirements.txt                # Dependensi Python
└── README.md                       # File ini
```

---

## 📦 Prasyarat

| Kebutuhan | Versi | Tujuan |
|-------------|---------|---------|
| Python | 3.10+ | Runtime |
| pip | Terbaru | Manajer paket |
| Git | Apapun | Kontrol versi |
| Kivy | 2.3.1 | Kerangka UI |
| KivyMD | 2.0.1 | Widget Material Design |
| cryptography | 43.0+ | Operasi E2EE |
| requests | 2.32+ | Panggilan REST Firebase |
| PyInstaller | 6.10+ | Build Desktop |
| Buildozer | 1.5+ | Build Seluler (hanya Linux/macOS) |

**Khusus Platform:**
- **macOS:** Alat Baris Perintah Xcode (`xcode-select --install`)
- **Linux:** `build-essential`, `libffi-dev`, `libssl-dev`
- **Build Android:** Java JDK 17, Android SDK/NDK (dikelola otomatis oleh Buildozer)

---

## 🚀 Instalasi

### 1. Klon Repositori

```bash
git clone https://github.com/your-username/aegis-messenger.git
cd aegis-messenger
```

### 2. Buat Lingkungan Virtual (Virtual Environment)

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows
```

### 3. Instal Dependensi

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verifikasi Instalasi

```bash
python -c "import kivy; print(f'Kivy {kivy.__version__}')"
python -c "import kivymd; print(f'KivyMD {kivymd.__version__}')"
python -c "from core.crypto_engine import generate_rsa_keypair; print('Crypto ✓')"
```

---

## 🔥 Pengaturan Firebase

Aegis memerlukan proyek Firebase dengan **Authentication**, **Realtime Database**, dan **Cloud Storage** diaktifkan. Lihat [`docs/FIREBASE_SETUP_id.md`](docs/FIREBASE_SETUP_id.md) untuk panduan langkah demi langkah secara mendetail.

### Mulai Cepat

1. Buat proyek di [Firebase Console](https://console.firebase.google.com/)
2. Aktifkan autentikasi **Email/Password**
3. Buat **Realtime Database** (mulai dalam test mode)
4. Aktifkan **Cloud Storage**
5. Atur variabel lingkungan (environment variables):

```bash
export FIREBASE_API_KEY="AIzaSy..."
export FIREBASE_PROJECT_ID="aegis-messenger-xxxxx"
export FIREBASE_DB_URL="https://aegis-messenger-xxxxx-default-rtdb.firebaseio.com"
export FIREBASE_STORAGE_BUCKET="aegis-messenger-xxxxx.appspot.com"
```

---

## ▶️ Menjalankan Aplikasi

### Mode Desktop

```bash
python main_desktop.py
```

Jendela akan terbuka pada resolusi **1280×800** dengan antarmuka terbelah:
- Bilah samping (kiri): Daftar obrolan, pencarian pengguna, obrolan baru
- Panel kanan: Ruang obrolan aktif dengan perpesanan E2EE

### Mode Seluler (Pengembangan)

```bash
python main_mobile.py
```

Meluncurkan UI seluler di jendela desktop untuk pengembangan/pengujian. Menggunakan navigasi layar bertumpuk (Auth → ChatList → ChatRoom).

---

## 🔨 Membangun untuk Produksi

### Alat Build Interaktif

```bash
python compile.py
```

Alat build ini akan:
1. Mendeteksi OS *host* Anda (Linux / macOS / Windows)
2. Meminta Anda memilih: target **Desktop** atau **Mobile**
3. Menampilkan format *output* yang valid untuk OS Anda
4. Menjalankan alur *build* yang sesuai

### Desktop (PyInstaller)

| OS Host | Format Output |
|---------|---------------|
| macOS | `.app`, `.dmg` |
| Windows | `.exe` |
| Linux | `.AppImage`, `.deb`, Direktori |

```bash
# Build PyInstaller langsung (tanpa compile.py)
pyinstaller aegis_desktop.spec --clean
```

### Seluler (Buildozer)

```bash
# APK Android (memerlukan Linux atau macOS)
buildozer android debug

# iOS (memerlukan macOS + Xcode)
buildozer ios debug
```

> Lihat [`docs/DEPLOYMENT_id.md`](docs/DEPLOYMENT_id.md) untuk instruksi *build* khusus platform, *code signing*, dan *pipeline* CI/CD.

---

## 🔐 Model Keamanan

### Protokok Enkripsi

```
┌─────────────────────────────────────────────────────────┐
│                    ENKRIPSI PESAN                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Buat kunci AES-256 acak (32 byte)                   │
│  2. Buat nonce acak (12 byte)                           │
│  3. Enkripsi AES-GCM-256(plaintext) → ciphertext + tag  │
│  4. Untuk SETIAP penerima:                              │
│     Enkripsi RSA-OAEP(SHA-256)(kunci AES, pub_key)      │
│  5. Kirim ke Firebase:                                  │
│     { ciphertext, nonce, encrypted_keys[] }             │
│                                                         │
│  ⚠ Plaintext dan kunci AES mentah TIDAK PERNAH          │
│    menyentuh jaringan                                   │
└─────────────────────────────────────────────────────────┘
```

### Perlindungan Private Key

```
Kata Sandi Pengguna                        BIP39 Seed Phrase (24 Kata)
      │                                          │
      ▼                                          ▼
PBKDF2-HMAC-SHA256                           PBKDF2-HMAC-SHA256
(600,000 iterasi)                            (100,000 iterasi)
      │                                          │
      ▼                                          ▼
Kunci Turunan AES-256                        Kunci Turunan AES-256
      │                                          │
      ▼                                          ▼
AES-GCM encrypt(RSA private key)             AES-GCM encrypt(RSA private key)
      │                                          │
      ▼                                          ▼
Tersimpan lokal:                             Tersimpan di Firebase:
{ salt, nonce, ciphertxt }                   recovery_blob
```

> **Mekanisme Pemulihan:** *Private key* dienkripsi dua kali. Salinan lokal diamankan oleh kata sandi pengguna. Cadangan sekunder (`recovery_blob`) dienkripsi dengan 24 kata *seed phrase* yang dibuat secara acak dan disimpan di Firebase.
>
> **Alur Pemulihan Otomatis:** Jika pengguna lupa kata sandi mereka, mereka dapat meresetnya via email. Saat mereka masuk (*login*) dengan kata sandi *baru*, Aegis otomatis mendeteksi bahwa *private key* lokal tidak dapat didekripsi. Aplikasi akan beralih dengan mulus ke **Layar Pemulihan (Recovery Screen)**, meminta 24 kata *seed phrase* untuk mendekripsi `recovery_blob` dari Firebase dan mengembalikan *private key*.
>
> **Kehilangan Data & Regenerasi Kunci (Skip):** Jika pengguna benar-benar kehilangan *seed phrase* mereka, mereka dapat memilih opsi **"Skip"** (Lewati) pada layar pemulihan. Hal ini akan membuang identitas kriptografi yang lama secara permanen, membuat pasangan kunci RSA yang baru secara otomatis, dan mengarahkan pengguna kembali ke tahap *setup* untuk membuat 24 kata *seed phrase* yang baru. **Semua riwayat pesan sebelumnya akan menjadi tidak dapat dibaca secara permanen**, sebagai konsekuensi logis dari desain *E2EE Zero-Knowledge*.

> Lihat [`docs/SECURITY_id.md`](docs/SECURITY_id.md) untuk spesifikasi kriptografi penuh, model ancaman, dan daftar periksa audit keamanan.

---

## 📚 Dokumentasi

| Dokumen | Deskripsi |
|----------|-------------|
| [`docs/ARCHITECTURE_id.md`](docs/ARCHITECTURE_id.md) | Arsitektur sistem, pola desain, alur data |
| [`docs/SECURITY_id.md`](docs/SECURITY_id.md) | Protokol kriptografi, model ancaman, manajemen kunci |
| [`docs/API_REFERENCE_id.md`](docs/API_REFERENCE_id.md) | Dokumentasi API modul-ke-modul |
| [`docs/DEPLOYMENT_id.md`](docs/DEPLOYMENT_id.md) | Panduan build, CI/CD, code signing |
| [`docs/FIREBASE_SETUP_id.md`](docs/FIREBASE_SETUP_id.md) | Konfigurasi proyek Firebase |
| [`docs/CONTRIBUTING_id.md`](docs/CONTRIBUTING_id.md) | Panduan kontribusi, gaya kode |

---

## 🤝 Berkontribusi

Kami menyambut kontribusi Anda! Silakan baca [`docs/CONTRIBUTING_id.md`](docs/CONTRIBUTING_id.md) untuk:
- Panduan gaya kode (PEP 8, type hints, docstrings)
- Konvensi penamaan cabang (branch)
- Proses Pull Request
- Pelaporan kerentanan keamanan

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah **Lisensi MIT** — lihat file [LICENSE](LICENSE) untuk detailnya.

---

<p align="center">
  <img src="assets/logo.png" alt="Aegis" width="48" /><br/>
  <em>Dibangun dengan 🔒 oleh Tim Aegis</em>
</p>
