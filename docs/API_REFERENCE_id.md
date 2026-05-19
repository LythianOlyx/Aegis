# Aegis – Referensi API

> **Versi:** 1.0.0  
> **Terakhir Diperbarui:** 2026-05-13  

---

## Daftar Isi

- [1. core.crypto\_engine](#1-corecrypto_engine)
- [2. core.firebase\_client](#2-corefirebase_client)
- [3. core.file\_manager](#3-corefile_manager)
- [4. ui.shared.widgets](#4-uisharedwidgets)

---

## 1. core.crypto_engine

Mesin enkripsi hybrid RSA-2048 / AES-256-GCM untuk perpesanan terenkripsi *end-to-end* (E2EE).

### Konstanta

| Konstanta | Nilai | Deskripsi |
|----------|-------|-------------|
| `RSA_KEY_SIZE` | `2048` | Panjang kunci RSA dalam bit |
| `AES_KEY_BYTES` | `32` | Panjang kunci AES-256 (byte) |
| `AES_NONCE_BYTES` | `12` | Panjang nonce AES-GCM (byte) |
| `PBKDF2_ITERATIONS` | `600_000` | Jumlah iterasi PBKDF2 |
| `PBKDF2_SALT_BYTES` | `16` | Panjang salt PBKDF2 (byte) |

### Pembuatan Kunci

#### `generate_rsa_keypair() → Tuple[RSAPrivateKey, RSAPublicKey]`

Membuat pasangan kunci RSA-2048 yang baru.

```python
from core.crypto_engine import generate_rsa_keypair

private_key, public_key = generate_rsa_keypair()
```

#### `generate_aes_key() → bytes`

Mengembalikan kunci AES 256-bit acak yang aman secara kriptografi.

#### `generate_nonce() → bytes`

Mengembalikan *nonce* 96-bit acak untuk AES-GCM yang aman secara kriptografi.

### Serialisasi RSA

#### `serialize_public_key(public_key: RSAPublicKey) → str`

Menserialisasi *public key* RSA menjadi string PEM berenkode Base64 (aman untuk disimpan di Firebase).

#### `deserialize_public_key(b64_pem: str) → RSAPublicKey`

Merekonstruksi *public key* RSA dari string PEM berenkode Base64.

### Perlindungan Private Key

#### `encrypt_private_key(private_key: RSAPrivateKey, password: str) → str`

Mengenkripsi *private key* RSA menggunakan kunci AES-GCM yang diturunkan dari kata sandi. Mengembalikan string JSON `{"salt": ..., "nonce": ..., "ct": ...}`.

#### `decrypt_private_key(encrypted_json: str, password: str) → RSAPrivateKey`

Mendekripsi *private key* RSA dari amplop JSON yang terenkripsi.

**Eksepsi (Raises):** `cryptography.exceptions.InvalidTag` jika kata sandi salah.

### Enkripsi Simetris

#### `aes_encrypt(plaintext: bytes) → Tuple[bytes, bytes, bytes]`

Mengenkripsi plaintext dengan kunci AES-256-GCM baru. Mengembalikan `(aes_key, nonce, ciphertext_with_tag)`.

#### `aes_decrypt(aes_key: bytes, nonce: bytes, ciphertext: bytes) → bytes`

Mendekripsi ciphertext AES-256-GCM. **Eksepsi (Raises):** `InvalidTag` jika data telah diubah (tampered).

### Pembungkusan Kunci RSA (Key Wrapping)

#### `rsa_encrypt_aes_key(aes_key: bytes, recipient_pub: RSAPublicKey) → bytes`

Mengenkripsi kunci AES menggunakan *public key* RSA penerima (OAEP/SHA-256). Mengembalikan 256 byte.

#### `rsa_decrypt_aes_key(encrypted_key: bytes, private_key: RSAPrivateKey) → bytes`

Mendekripsi kunci AES yang dibungkus RSA menggunakan *private key* lokal.

### Pembantu Tingkat Tinggi (High-Level Helpers)

#### `encrypt_message(plaintext: str, recipient_public_keys: List[RSAPublicKey]) → Dict[str, Any]`

Mengenkripsi pesan teks untuk satu atau lebih penerima.

**Mengembalikan:**
```json
{
    "nonce": "<base64>",
    "ciphertext": "<base64>",
    "keys": {
        "0": "<kunci AES terenkripsi RSA dalam base64>",
        "1": "<kunci AES terenkripsi RSA dalam base64>"
    }
}
```

#### `decrypt_message(payload: Dict, key_index: str, private_key: RSAPrivateKey) → str`

Mendekripsi payload pesan E2EE. Mengembalikan string *plaintext*.

#### `encrypt_file_bytes(raw_data: bytes, recipient_public_keys: List[RSAPublicKey]) → Dict`

Mengenkripsi byte file mentah. Mengembalikan `{"blob": bytes, "metadata": {"nonce": ..., "keys": {...}}}`.

#### `decrypt_file_bytes(ciphertext: bytes, metadata: Dict, key_index: str, private_key: RSAPrivateKey) → bytes`

Mendekripsi blob file menggunakan metadata dari Firebase DB.

---

## 2. core.firebase_client

Wrapper REST API Firebase yang ringan hanya menggunakan pustaka `requests`.

### Eksepsi (Exceptions)

| Eksepsi | Deskripsi |
|-----------|-------------|
| `FirebaseAuthError` | Kegagalan autentikasi (kredensial salah, token kedaluwarsa, dll.) |
| `FirebaseDBError` | Kegagalan operasi Realtime Database |
| `FirebaseStorageError` | Kegagalan unggah/unduh Cloud Storage |

### Kelas: `FirebaseClient`

#### Konstruktor

```python
client = FirebaseClient({
    "api_key": "AIzaSy...",
    "project_id": "my-project",
    "db_url": "https://my-project-default-rtdb.firebaseio.com",
    "storage_bucket": "my-project.appspot.com",
})
```

### Properti Instansiasi

| Properti | Tipe | Deskripsi |
|----------|------|-------------|
| `id_token` | `Optional[str]` | Token ID Firebase saat ini |
| `refresh_token` | `Optional[str]` | Refresh token saat ini |
| `local_id` | `Optional[str]` | UID Firebase |
| `email` | `Optional[str]` | Email pengguna |
| `display_name` | `Optional[str]` | Nama tampilan (display name) pengguna |

### Metode Autentikasi

| Metode | Parameter | Kembali (Returns) | Deskripsi |
|--------|-----------|---------|-------------|
| `sign_up(email, password, display_name="")` | `str, str, str` | `Dict[str, Any]` | Mendaftarkan pengguna baru |
| `sign_in(email, password)` | `str, str` | `Dict[str, Any]` | Masuk sebagai pengguna lama |
| `sign_out()` | — | `None` | Menghapus status autentikasi lokal |
| `refresh_id_token()` | — | `None` | Menukar refresh token dengan ID token baru |
| `update_profile(display_name=None, photo_url=None)` | `Optional[str], Optional[str]` | `Dict` | Memperbarui profil pengguna |
| `get_user_data()` | — | `Dict[str, Any]` | Mengambil profil pengguna saat ini |

### Metode Database

| Metode | Parameter | Kembali | Deskripsi |
|--------|-----------|---------|-------------|
| `db_get(path)` | `str` | `Any` | Membaca data di path (jalur) tertentu |
| `db_put(path, data)` | `str, Any` | `Any` | Menulis (menimpa) di path |
| `db_patch(path, data)` | `str, Dict` | `Any` | Memperbarui sebagian (partial update) di path |
| `db_post(path, data)` | `str, Any` | `Dict[str, str]` | Menambahkan (*push*) dengan kunci otomatis |
| `db_delete(path)` | `str` | `None` | Menghapus data di path |
| `db_query(path, order_by, ...)` | Beragam | `Any` | Permintaan (query) terindeks dengan filter |

### Metode Penyimpanan (Storage)

| Metode | Parameter | Kembali | Deskripsi |
|--------|-----------|---------|-------------|
| `storage_upload(remote_path, data, content_type)` | `str, bytes, str` | `str` | Mengunggah byte, mengembalikan URL unduhan |
| `storage_download(download_url)` | `str` | `bytes` | Mengunduh byte dari URL |

### Metode Pengguna & Obrolan

| Metode | Parameter | Kembali | Deskripsi |
|--------|-----------|---------|-------------|
| `search_users(query)` | `str` | `List[Dict]` | Mencari berdasarkan awalan nama tampilan |
| `register_user_profile(uid, email, display_name, public_key_b64)` | `str ×4` | `None` | Menulis profil publik |
| `get_public_key(uid)` | `str` | `Optional[str]` | Mendapatkan kunci publik RSA pengguna |
| `send_message(chat_id, sender_uid, encrypted_payload, msg_type)` | `str ×3, str` | `str` | Mengirim pesan terenkripsi |
| `get_messages(chat_id, limit=50)` | `str, int` | `List[Dict]` | Mengambil pesan-pesan terbaru |
| `create_chat(chat_id, participants, chat_type, group_name)` | `str, List[str], str, str` | `None` | Membuat ruang obrolan |
| `get_user_chats(uid)` | `str` | `List[str]` | Daftar ID obrolan untuk pengguna |
| `get_chat_info(chat_id)` | `str` | `Optional[Dict]` | Metadata obrolan |

---

## 3. core.file_manager

Utilitas I/O file untuk transfer file terenkripsi.

### Konstanta

| Konstanta | Nilai | Deskripsi |
|----------|-------|-------------|
| `DEFAULT_CHUNK_SIZE` | `4 * 1024 * 1024` | 4 MiB per potongan (chunk) |
| `MAX_FILE_SIZE` | `100 * 1024 * 1024` | Batas keras (hard limit) 100 MiB |
| `ALLOWED_MIME_TYPES` | `frozenset` | 15 tipe MIME yang diizinkan |

### Eksepsi

| Eksepsi | Deskripsi |
|-----------|-------------|
| `FileTooLargeError` | File melebihi batas `MAX_FILE_SIZE` |
| `UnsupportedFileTypeError` | Tipe MIME tidak ada dalam daftar yang diizinkan |

### Fungsi

| Fungsi | Tanda Tangan (Signature) | Kembali | Deskripsi |
|----------|-----------|---------|-------------|
| `validate_file` | `(file_path, max_size, check_mime)` | `Tuple[int, str]` | Validasi ukuran & MIME |
| `read_file_bytes` | `(file_path)` | `bytes` | Membaca seluruh file |
| `read_file_chunks` | `(file_path, chunk_size)` | `Generator[bytes]` | Menghasilkan potongan berukuran tetap |
| `write_file_bytes` | `(file_path, data)` | `None` | Menulis dengan pembuatan direktori otomatis (auto-mkdir) |
| `detect_mime_type` | `(file_path)` | `str` | Ekstensi MIME berbasis jenis file |
| `format_file_size` | `(size_bytes)` | `str` | Ukuran yang dapat dibaca manusia |
| `safe_filename` | `(original_name)` | `str` | Menghapus karakter berbahaya |
| `get_file_name` | `(file_path)` | `str` | Mengekstrak nama dasar (basename) |
| `get_downloads_dir` | `()` | `str` | Direktori `~/Downloads/Aegis/` |

---

## 4. ui.shared.widgets

Widget yang dapat digunakan ulang untuk UI Desktop dan Seluler.

### Konstanta Warna

| Konstanta | RGBA | Hex |
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

### Kelas Widget

#### `SplashScreen(Screen)`

| Properti | Tipe | Default | Deskripsi |
|----------|------|---------|-------------|
| `logo_path` | `StringProperty` | Auto-resolved | Path ke `assets/logo.png` |
| `next_screen` | `StringProperty` | `"auth"` | Layar yang akan dituju setelah 2.5 detik |

**Urutan Animasi:** Skala+pudar logo (0.8s, out_back) → Pudar judul (0.6s) → Pudar sub-judul (0.6s) → Navigasi

#### `E2EEMessageBubble(MDBoxLayout)`

| Properti | Tipe | Default | Deskripsi |
|----------|------|---------|-------------|
| `message_text` | `StringProperty` | `""` | Konten pesan |
| `timestamp_str` | `StringProperty` | `""` | Tampilan waktu (contoh: "14:30") |
| `is_sent` | `BooleanProperty` | `False` | Gaya (styling) antara terkirim dan diterima |
| `encryption_icon` | `StringProperty` | `"🔒"` | Indikator gembok |
| `bubble_color` | `ColorProperty` | `BUBBLE_RECV` | Diperbarui secara otomatis berdasarkan `is_sent` |

#### `FileMessageBubble(MDBoxLayout)`

| Properti | Tipe | Deskripsi |
|----------|------|-------------|
| `file_name` | `StringProperty` | Tampilan nama file |
| `file_size_str` | `StringProperty` | String ukuran |
| `timestamp_str` | `StringProperty` | Tampilan waktu |
| `is_sent` | `BooleanProperty` | Terkirim atau diterima |
| `download_url` | `StringProperty` | URL Firebase Storage |

#### `ChatListItem(MDBoxLayout)`

| Properti | Tipe | Deskripsi |
|----------|------|-------------|
| `chat_id` | `StringProperty` | Pengidentifikasi (ID) obrolan |
| `chat_name` | `StringProperty` | Nama tampilan |
| `last_message` | `StringProperty` | Teks pratinjau |
| `time_str` | `StringProperty` | Timestamp |
| `avatar_letter` | `StringProperty` | Huruf pertama untuk avatar |
| `on_chat_selected` | `ObjectProperty` | Fungsi Callback `(chat_id: str)` |

#### `UserSearchResult(MDBoxLayout)`

| Properti | Tipe | Deskripsi |
|----------|------|-------------|
| `uid` | `StringProperty` | UID Firebase pengguna |
| `display_name` | `StringProperty` | Nama pengguna |
| `email` | `StringProperty` | Email pengguna |
| `avatar_letter` | `StringProperty` | Huruf pertama untuk avatar |
| `on_user_selected` | `ObjectProperty` | Fungsi Callback `(uid: str)` |
