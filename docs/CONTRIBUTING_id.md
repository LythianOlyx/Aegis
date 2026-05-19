# Aegis – Panduan Kontribusi

> **Versi:** 1.0.0  
> **Terakhir Diperbarui:** 2026-05-13  

---

## Daftar Isi

- [1. Selamat Datang](#1-selamat-datang)
- [2. Penyiapan Pengembangan (Development Setup)](#2-penyiapan-pengembangan-development-setup)
- [3. Gaya Kode (Code Style)](#3-gaya-kode-code-style)
- [4. Konvensi Proyek](#4-konvensi-proyek)
- [5. Alur Kerja Git (Git Workflow)](#5-alur-kerja-git-git-workflow)
- [6. Proses Pull Request](#6-proses-pull-request)
- [7. Panduan Pengujian (Testing)](#7-panduan-pengujian-testing)
- [8. Pelaporan Kerentanan Keamanan](#8-pelaporan-kerentanan-keamanan)
- [9. Aturan Arsitektur](#9-aturan-arsitektur)

---

## 1. Selamat Datang

Terima kasih telah mempertimbangkan untuk berkontribusi pada Aegis! Panduan ini akan membantu Anda memulai dengan alur kerja pengembangan, standar kode, dan proses kontribusi.

**Sebelum Anda mulai:**
- Baca [Panduan Arsitektur](ARCHITECTURE_id.md) untuk memahami desain sistem
- Baca [Spesifikasi Keamanan](SECURITY_id.md) untuk memahami protokol kriptografi
- Periksa *issues* dan PR (Pull Request) yang ada untuk menghindari pekerjaan yang duplikat

---

## 2. Penyiapan Pengembangan (Development Setup)

```bash
# Clone repositori
git clone https://github.com/username-anda/aegis-messenger.git
cd aegis-messenger

# Buat virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Instal dependensi
pip install -r requirements.txt

# Instal dependensi pengembangan (development)
pip install pytest pytest-cov flake8 mypy black isort

# Verifikasi penyiapan
python -c "from core.crypto_engine import generate_rsa_keypair; print('✓ Siap')"

# Jalankan aplikasi desktop
python main_desktop.py
```

---

## 3. Gaya Kode (Code Style)

### Standar Python

| Aturan | Standar | Alat (Tool) |
|------|----------|------|
| Format | PEP 8, panjang baris maks 99 | `black --line-length 99` |
| Urutan Import | stdlib → pihak ketiga → lokal | `isort` |
| Petunjuk Tipe (Type hints) | Wajib pada semua fungsi publik | `mypy --strict` |
| Docstrings | Gaya NumPy | Tinjauan manual |
| Penamaan | `snake_case` untuk fungsi/variabel, `PascalCase` untuk kelas | `flake8` |

### Petunjuk Tipe / Type Hints (Wajib)

Setiap fungsi publik wajib memiliki anotasi tipe yang lengkap:

```python
# ✅ Benar
def encrypt_message(
    plaintext: str,
    recipient_public_keys: List[RSAPublicKey],
) -> Dict[str, Any]:
    """Encrypt a text message for one or more recipients."""
    ...

# ❌ Salah
def encrypt_message(plaintext, keys):
    ...
```

### Docstrings (Gaya NumPy)

```python
def aes_encrypt(plaintext: bytes) -> Tuple[bytes, bytes, bytes]:
    """Mengenkripsi plaintext dengan kunci AES-256-GCM baru dan nonce.

    Parameters
    ----------
    plaintext : bytes
        Data mentah yang akan dienkripsi.

    Returns
    -------
    Tuple[bytes, bytes, bytes]
        ``(aes_key, nonce, ciphertext_with_tag)``

    Raises
    ------
    ValueError
        Jika plaintext kosong.
    """
```

### Perintah Format

```bash
# Format kode
black --line-length 99 .

# Urutkan impor
isort .

# Linting
flake8 --max-line-length 99 --exclude .venv,dist,build

# Pemeriksaan Tipe
mypy core/ --ignore-missing-imports
```

---

## 4. Konvensi Proyek

### Organisasi File

| Direktori | Konten | Aturan |
|-----------|---------|-------|
| `core/` | Logika bisnis | Tidak ada impor UI. Tidak ada impor Kivy. |
| `ui/desktop/` | Layar desktop | Impor dari `core/` dan `ui/shared/`. Tidak pernah dari `ui/mobile/`. |
| `ui/mobile/` | Layar seluler | Impor dari `core/` dan `ui/shared/`. Tidak pernah dari `ui/desktop/`. |
| `ui/shared/` | Widget yang dapat digunakan kembali | Impor hanya dari Kivy/KivyMD. Tidak pernah dari `ui/desktop/` atau `ui/mobile/`. |

### Aturan Threading

1. **Jangan pernah** memanggil `requests.*` atau `crypto_engine.*` dari thread utama Kivy
2. Gunakan `threading.Thread(target=..., daemon=True).start()` untuk pekerjaan di latar belakang
3. Gunakan `Clock.schedule_once(callback, 0)` untuk memperbarui UI dari thread latar belakang
4. Semua thread latar belakang harus berupa *daemon threads* (otomatis dihentikan saat aplikasi keluar)

### Konstanta Warna

Gunakan konstanta warna dari `ui/shared/widgets.py` — jangan pernah menggunakan nilai hex secara langsung (*hardcode*):

```python
from ui.shared.widgets import ACCENT_CYAN, BG_PRIMARY, TEXT_PRIMARY
```

### Aturan Bahasa KV

- Semua aturan widget KV ditempatkan di dalam `Builder.load_string()` pada modul yang mendefinisikan widget tersebut
- Gaya global ditempatkan di `ui/theme.kv`
- Gunakan `dp()` untuk ukuran jarak/dimensi dan `sp()` untuk ukuran font
- Selalu referensikan properti `root.*`, jangan *hardcode* nilai langsung

---

## 5. Alur Kerja Git (Git Workflow)

### Penamaan Cabang (Branch Naming)

| Awalan | Penggunaan | Contoh |
|--------|----------|---------|
| `feature/` | Fitur baru | `feature/group-chat-ui` |
| `fix/` | Perbaikan bug | `fix/message-decryption-error` |
| `security/` | Tambalan keamanan | `security/update-crypto-lib` |
| `docs/` | Dokumentasi | `docs/api-reference-update` |
| `refactor/` | Peningkatan/restrukturisasi kode | `refactor/firebase-client` |

### Pesan Komit (Commit Messages)

Ikuti standar [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <deskripsi>

[body opsional]

[footer opsional]
```

**Tipe (Types):** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `build`, `ci`, `security`

**Contoh:**

```
feat(crypto): add AES key rotation for group chats
fix(desktop): resolve message scroll position on new message
security(crypto): update PBKDF2 iterations to 600,000
docs(api): add firebase_client method documentation
```

---

## 6. Proses Pull Request

1. **Fork** repositori dan buat cabang fitur (*feature branch*) baru
2. **Terapkan (Implement)** perubahan Anda dengan mengikuti panduan gaya kode
3. **Uji (Test)** perubahan Anda secara manual (jalankan entry point desktop dan seluler)
4. **Lint** kode Anda: `black . && isort . && flake8 . && mypy core/`
5. **Kirim (Submit)** Pull Request dengan:
   - Judul yang jelas mengikuti konvensi komit
   - Deskripsi perubahan dan alasannya
   - Tangkapan layar/rekaman (*screenshots/recordings*) untuk perubahan UI
   - Implikasi keamanan dicantumkan (jika ada)

### Daftar Periksa (Checklist) Tinjauan PR

Peninjau (Reviewer) akan memverifikasi:

- [ ] Kode mengikuti PEP 8 dan konvensi proyek
- [ ] Semua fungsi publik memiliki petunjuk tipe (type hints) dan docstrings
- [ ] Tidak ada data plaintext yang dikirim ke Firebase
- [ ] Tidak ada operasi kripto di thread utama (main thread)
- [ ] Impor desktop tidak merujuk ke modul seluler (dan sebaliknya)
- [ ] Pengujian (test) yang ada berhasil (pass)
- [ ] Tidak ada kerentanan keamanan baru yang muncul

---

## 7. Panduan Pengujian (Testing)

### Menjalankan Pengujian (Tests)

```bash
# Jalankan semua pengujian
pytest tests/ -v

# Jalankan dengan cakupan (coverage)
pytest tests/ --cov=core --cov-report=html

# Jalankan file pengujian tertentu
pytest tests/test_crypto_engine.py -v
```

### Struktur Pengujian

```
tests/
├── test_crypto_engine.py     # Pengujian unit untuk enkripsi/dekripsi
├── test_firebase_client.py   # Pengujian API berbasis Mock
├── test_file_manager.py      # Pengujian I/O File
└── conftest.py               # Fixtures bersama
```

### Menulis Pengujian

```python
import pytest
from core.crypto_engine import (
    generate_rsa_keypair,
    encrypt_message,
    decrypt_message,
)

class TestMessageEncryption:
    """Pengujian untuk pipa (pipeline) enkripsi pesan."""

    def test_encrypt_decrypt_roundtrip(self) -> None:
        """Pesan yang dienkripsi untuk penerima dapat didekripsi."""
        priv, pub = generate_rsa_keypair()
        plaintext = "Halo, Aegis!"

        payload = encrypt_message(plaintext, [pub])
        decrypted = decrypt_message(payload, "0", priv)

        assert decrypted == plaintext

    def test_wrong_key_fails(self) -> None:
        """Dekripsi dengan private key yang salah akan menghasilkan InvalidTag."""
        _, pub1 = generate_rsa_keypair()
        priv2, _ = generate_rsa_keypair()

        payload = encrypt_message("rahasia", [pub1])

        with pytest.raises(Exception):
            decrypt_message(payload, "0", priv2)
```

---

## 8. Pelaporan Kerentanan Keamanan

**JANGAN** membuka *issue* publik di GitHub untuk kerentanan keamanan.

### Pengungkapan yang Bertanggung Jawab (Responsible Disclosure)

1. Email temuan keamanan ke: `security@aegis-messenger.example`
2. Sertakan:
   - Deskripsi kerentanan
   - Langkah-langkah untuk mereproduksi
   - Penilaian dampak potensial
   - Solusi perbaikan yang disarankan (jika ada)
3. Kami akan merespons dalam **48 jam** dengan:
   - Tanda terima (pengakuan)
   - Penilaian awal
   - Garis waktu (Timeline) untuk perbaikan

### Cakupan (Scope)

| Di Dalam Cakupan | Di Luar Cakupan |
|----------|-------------|
| Kelemahan kriptografi | Rekayasa sosial (Social engineering) |
| Cacat manajemen kunci | Serangan fisik ke perangkat |
| *Bypass* aturan Firebase | Serangan DoS |
| *Bypass* autentikasi | *0-days* pada pustaka pihak ketiga |
| Kebocoran data | Masalah (bug) pada Firebase itu sendiri |

---

## 9. Aturan Arsitektur

### Aturan yang Tidak Dapat Dinegosiasikan

Aturan-aturan ini **tidak boleh** dilanggar:

1. **Tidak Ada Plaintext dalam Transmisi:** Tidak ada konten pesan yang tidak dienkripsi atau kunci AES yang boleh dikirim ke Firebase
2. **Pemisahan Saat Kompilasi (Build-Time):** Modul UI Desktop dan Seluler harus tetap terpisah secara fisik tanpa adanya *cross-imports* (impor silang)
3. **UI Non-Blocking:** Semua panggilan kripto dan jaringan harus berada di thread latar belakang
4. **Tanpa Dependensi SDK:** Interaksi Firebase wajib hanya menggunakan REST API (melalui `requests`)
5. **Keamanan Tipe (Type Safety):** Semua fungsi API publik wajib memiliki anotasi tipe yang lengkap

### Aturan Batas Impor (Import Boundary Rules)

```
✅ DIIZINKAN:
  core/* → standard library, cryptography, requests
  ui/shared/* → kivy, kivymd
  ui/desktop/* → core/*, ui/shared/*
  ui/mobile/* → core/*, ui/shared/*
  main_desktop.py → ui/desktop/*, ui/shared/*, core/*
  main_mobile.py → ui/mobile/*, ui/shared/*, core/*

❌ DILARANG:
  core/* → kivy, kivymd, ui/*
  ui/desktop/* → ui/mobile/*
  ui/mobile/* → ui/desktop/*
  main_desktop.py → ui/mobile/*
  main_mobile.py → ui/desktop/*
```

Melanggar aturan ini akan menghasilkan file biner (*binary*) yang membengkak dengan kode yang tidak terpakai dan potensi masalah (*runtime errors*) di platform yang salah.
