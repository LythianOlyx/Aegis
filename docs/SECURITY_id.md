# Aegis – Spesifikasi Keamanan

> **Versi:** 1.0.0  
> **Terakhir Diperbarui:** 2026-05-13  
> **Klasifikasi:** Publik  

---

## Daftar Isi

- [1. Ringkasan Eksekutif](#1-ringkasan-eksekutif)
- [2. Primitif Kriptografi](#2-primitif-kriptografi)
- [3. Manajemen Kunci](#3-manajemen-kunci)
- [4. Protokol Enkripsi Pesan](#4-protokol-enkripsi-pesan)
- [5. Model Ancaman](#5-model-ancaman)
- [6. Properti Keamanan](#6-properti-keamanan)
- [7. Pendaftaran & Verifikasi Akun](#7-pendaftaran--verifikasi-akun)
- [8. Keterbatasan yang Diketahui](#8-keterbatasan-yang-diketahui)
- [9. Daftar Periksa Audit Keamanan](#9-daftar-periksa-audit-keamanan)

---

## 1. Ringkasan Eksekutif

Aegis mengimplementasikan **protokol enkripsi hybrid** yang menggabungkan kriptografi asimetris (RSA-2048) dan simetris (AES-256-GCM) untuk menyediakan enkripsi end-to-end (E2EE) pada semua pesan. Server (Firebase) berfungsi secara eksklusif sebagai **relai ciphertext** — server tidak pernah memiliki akses ke konten plaintext atau kunci simetris yang diperlukan untuk mendekripsinya.

**Jaminan Kunci:**
- ✅ Pesan dienkripsi di perangkat pengirim sebelum transmisi
- ✅ Hanya penerima yang dituju yang dapat mendekripsi pesan
- ✅ Server tidak dapat membaca konten pesan
- ✅ *Private key* tidak pernah meninggalkan perangkat pengguna
- ✅ Setiap pesan menggunakan kunci AES dan *nonce* yang unik (tanpa penggunaan ulang kunci)

---

## 2. Primitif Kriptografi

| Primitif | Algoritma | Parameter | Pustaka (Library) |
|-----------|-----------|------------|---------|
| Enkripsi Asimetris | RSA-OAEP | 2048-bit, SHA-256, MGF1-SHA-256 | `cryptography` |
| Enkripsi Simetris | AES-GCM | kunci 256-bit, nonce 96-bit (12 byte) | `cryptography` |
| Derivasi Kunci | PBKDF2-HMAC | SHA-256, 600.000 iterasi, salt 128-bit | `cryptography` |
| Pembangkitan Acak | OS CSPRNG | Melalui `secrets.token_bytes()` dan `AESGCM.generate_key()` | Python `secrets` |

### Mengapa Pilihan Ini?

| Pilihan | Alasan |
|--------|-----------|
| **RSA-2048** | Didukung secara luas, cukup memadai untuk pertukaran kunci. 2048-bit memberikan tingkat keamanan sekitar 112-bit. |
| **OAEP dengan SHA-256** | Skema *padding* aman IND-CCA2; tahan terhadap serangan *chosen-ciphertext*. |
| **AES-256-GCM** | Enkripsi terautentikasi (AEAD); memberikan kerahasiaan dan integritas sekaligus. Mendeteksi jika data diubah. |
| **Nonce 96-bit** | Panjang *nonce* yang direkomendasikan NIST untuk AES-GCM. *Nonce* acak dengan kunci 256-bit memiliki probabilitas tabrakan (collision) yang dapat diabaikan. |
| **PBKDF2 600K** | Iterasi minimum yang direkomendasikan OWASP 2024 untuk SHA-256. Memberikan ketahanan *brute-force* untuk derivasi kunci berbasis kata sandi. |

---

## 3. Manajemen Kunci

### 3.1 Pembuatan Kunci

```text
Pendaftaran Pengguna
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
       │         └──► Simpan lokal: { salt, nonce, ciphertext }
       │              Path: ~/.aegis/keys/<uid>.key
       │
       │    encrypt_private_key_with_phrase(24_words)
       │         │
       │         ├──► PBKDF2(seed_phrase, random_salt) → derived_recovery_key
       │         ├──► AES-GCM(derived_recovery_key, random_nonce, privkey_pem) → recovery_blob
       │         └──► Simpan di Firebase: /users/<uid>/recovery_blob
       │
       └──► RSA Public Key
                 │
                 ▼
            serialize_public_key() → Base64 PEM
                 │
                 ▼
            Firebase RTDB: /users/<uid>/public_key
```

### 3.2 Lokasi Penyimpanan Kunci

| Kunci | Penyimpanan | Dienkripsi? | Akses |
|-----|---------|------------|--------|
| RSA Public Key | Firebase RTDB | Tidak (publik) | Semua pengguna yang terautentikasi |
| RSA Private Key (Lokal) | Sistem file lokal `~/.aegis/keys/` | Ya (AES-GCM + PBKDF2 via Kata Sandi) | Hanya pemilik perangkat |
| RSA Private Key (Backup) | Firebase RTDB `recovery_blob` | Ya (AES-GCM + PBKDF2 via 24 Kata Seed) | Hanya pengguna terautentikasi |
| AES Session Keys | Hanya RAM (sementara) | N/A | Dibuat per-pesan, tidak pernah disimpan |
| PBKDF2 Salt | Di dalam file kunci terenkripsi | Tidak | Dibutuhkan untuk derivasi kunci |

### 3.3 Siklus Hidup Kunci

```text
Pendaftaran ──► Private key dibuat ──► Dienkripsi dengan kata sandi ──► Disimpan di disk
                Private key        ──► Dienkripsi dengan 24 kata  ──► Disimpan di Firebase (recovery_blob)
                Public key dibuat  ──► Disimpan di Firebase

Masuk (Login) ──► Muat private key terenkripsi ──► PBKDF2(password) ──► Dekripsi AES-GCM
              ──► Private key disimpan di RAM (app.private_key) selama sesi

Keluar (Logout) ──► app.private_key = None ──► Private key dihapus dari RAM

Pesan ──► Kunci AES baru dibuat ──► Digunakan sekali ──► Dibungkus RSA ──► Dibuang
```

### 3.4 Pemulihan Kunci & Regenerasi Kunci

Karena Aegis menggunakan arsitektur *Zero-Knowledge*, server tidak dapat membantu pengaturan ulang kata sandi tanpa merusak akses ke data terenkripsi yang sudah ada.

1. **Pemulihan Otomatis:** Jika pengguna mereset kata sandi via email, kata sandi baru mereka akan berhasil masuk (autentikasi) ke Firebase, tetapi akan gagal mendekripsi file lokal `~/.aegis/keys/<uid>.key`. Aegis akan mendeteksi kesalahan `InvalidTag` AES-GCM ini dan otomatis meminta pengguna memasukkan 24 kata *seed phrase* mereka untuk mengunduh dan mendekripsi `recovery_blob`.
2. **Regenerasi Kunci (Lewati/Skip):** Jika pengguna kehilangan kata sandi *dan* *seed phrase* mereka, mereka dapat memilih untuk **"Skip"** (Melewati) pemulihan. Tindakan ini memicu proses regenerasi kunci yang tidak dapat dibatalkan:
   - Pasangan kunci RSA baru dibuat secara lokal.
   - Pengguna dipaksa untuk membuat dan menyimpan 24 kata *seed phrase* yang *baru*.
   - *Public key* baru dan `recovery_blob` baru akan menimpa data yang lama di Firebase.
   - **Hasil:** Pengguna mendapatkan kembali akses ke akun mereka untuk mengirim/menerima pesan *baru*, tetapi semua pesan *sebelumnya* akan tetap tidak dapat dibaca secara permanen karena hilangnya *private key* asli. Ini adalah perilaku kriptografi yang memang disengaja.

---

## 4. Protokol Enkripsi Pesan

### 4.1 Enkripsi (Pengirim)

```python
# Langkah 1: Buat kunci simetris per-pesan
aes_key = AESGCM.generate_key(256)      # 32 byte acak
nonce = secrets.token_bytes(12)           # 12 byte acak

# Langkah 2: Enkripsi konten pesan
aesgcm = AESGCM(aes_key)
ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
# ciphertext mencakup 16-byte tag autentikasi GCM

# Langkah 3: Bungkus kunci AES untuk setiap penerima
for recipient in recipients:
    encrypted_key = recipient.public_key.encrypt(
        aes_key,
        OAEP(mgf=MGF1(SHA256()), algorithm=SHA256(), label=None)
    )

# Langkah 4: Kirim ke Firebase
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

### 4.2 Dekripsi (Penerima)

```python
# Langkah 1: Ambil kunci AES terenkripsi milik sendiri
my_index = participants.index(my_uid)
encrypted_key = base64_decode(payload["keys"][str(my_index)])

# Langkah 2: Buka bungkus kunci AES dengan private key RSA
aes_key = private_key.decrypt(
    encrypted_key,
    OAEP(mgf=MGF1(SHA256()), algorithm=SHA256(), label=None)
)

# Langkah 3: Dekripsi pesan
nonce = base64_decode(payload["nonce"])
ciphertext = base64_decode(payload["ciphertext"])
plaintext = AESGCM(aes_key).decrypt(nonce, ciphertext, None)
# Tag GCM diverifikasi secara otomatis; InvalidTag dinaikkan jika ada perubahan data
```

### 4.3 Distribusi Kunci Obrolan Grup

Untuk obrolan grup dengan N peserta, kunci AES dienkripsi sebanyak **N kali** — satu kali untuk setiap *public key* penerima. Ini berarti:

- Semua peserta dapat mendekripsi ciphertext yang sama
- Menambah/mengeluarkan anggota hanya memerlukan proses re-enkripsi pada pesan-pesan yang baru ke depannya
- Tidak diperlukan kunci grup bersama (*shared group key*) (tiap anggota menggunakan pasangan kunci RSA masing-masing)

---

## 5. Model Ancaman

### 5.1 Kemampuan Musuh (Adversary Capabilities)

| Musuh | Kemampuan | Dimitigasi? |
|-----------|-------------|------------|
| **Penyadap jaringan (Network eavesdropper)** | Dapat mencegat seluruh lalu lintas (traffic) antara klien dan Firebase | ✅ HTTPS + E2EE: bahkan jika TLS ditembus, *payload* tetap terenkripsi |
| **Server diretas (Compromised server)** | Akses baca penuh ke Firebase RTDB | ✅ Server hanya melihat ciphertext, *nonce*, dan kunci-kunci yang sudah terenkripsi |
| **Peserta berniat jahat (Malicious participant)** | Akses ke kunci mereka sendiri dan pesan-pesan yang telah didekripsi | ⚠️ Tidak dapat dicegah; peserta dapat melakukan tangkapan layar (screenshot) |
| **Pencurian perangkat (terkunci)** | Akses fisik ke perangkat, tanpa kata sandi | ✅ File *private key* dienkripsi secara AES-GCM dengan PBKDF2 |
| **Pencurian perangkat (tidak terkunci)** | Akses penuh ke sistem file selama sesi aktif | ⚠️ *Private key* ada di RAM; penyerang dengan akses pembuangan memori (memory dump) dapat mengekstraknya |
| **Brute-force kata sandi** | Serangan offline terhadap file *private key* terenkripsi | ✅ PBKDF2 dengan iterasi 600K membuat serangan *brute-force* menjadi sangat lambat dan mahal |
| **Brute-force recovery blob** | Serangan offline terhadap cadangan Firebase | ✅ 24 kata BIP39 memberikan entropi 256 bit (mustahil untuk di-*brute-force*) |

### 5.2 Hal yang TIDAK Dilindungi Oleh Aegis

| Ancaman | Status | Catatan |
|--------|--------|-------|
| Analisis metadata | ❌ | Firebase mengetahui siapa berbicara dengan siapa, kapan, dan ukuran pesan |
| Forward secrecy | ❌ | Tidak ada pertukaran kunci efemeral (contoh: *Diffie-Hellman ratchet*) |
| Verifikasi kunci | ❌ | Belum ada antarmuka verifikasi *fingerprint* kunci secara *out-of-band* |
| Malware pada perangkat | ❌ | *Keylogger* / penangkap layar dapat membobol enkripsi tingkat aplikasi mana pun |
| Komputasi kuantum | ❌ | RSA-2048 tidak aman terhadap serangan pasca-kuantum (*post-quantum secure*) |

---

## 6. Properti Keamanan

| Properti | Diberikan? | Mekanisme |
|----------|-----------|-----------|
| **Kerahasiaan (Confidentiality)** | ✅ | Enkripsi AES-256-GCM |
| **Integritas (Integrity)** | ✅ | Tag autentikasi GCM (128-bit) |
| **Autentikasi** | ✅ | RSA-OAEP; hanya pemegang *private key* yang dapat membuka bungkus kunci |
| **Non-penolakan (Non-repudiation)**| ❌ | Pengirim diidentifikasi berdasarkan UID, namun pesan tidak ditandatangani secara digital (digital signature) |
| **Forward secrecy** | ❌ | Kunci RSA statis; jika kunci dikompromikan, pesan-pesan lalu akan terbongkar |
| **Replay protection** | Sebagian | Timestamp server; tidak ada nomor urut (sequence numbers) |
| **Penyangkalan (Deniability)** | ❌ | Pesan dapat ditelusuri kembali ke pengirim melalui UID |

---

## 7. Pendaftaran & Verifikasi Akun

Untuk mencegah penyalahgunaan dan tautan verifikasi kedaluwarsa, Aegis menerapkan batas waktu (timeout) verifikasi email kustom yang sangat ketat:

1. **Timeout Kustom 10 Menit:** Tautan verifikasi email default Firebase berlaku selama 3 hari. Aegis mengesampingkan perilaku ini di sisi klien dengan mencatat *timestamp* UNIX (`verification_sent_at`) secara presisi pada saat email verifikasi diminta.
2. **Penolakan Tautan Kedaluwarsa (Stale Links):** Saat siklus (looping) verifikasi berjalan, jika pengguna berhasil mengklik tautan tetapi waktu yang berlalu sejak permintaan melebihi 10 menit (600 detik), Aegis akan menolak verifikasi tersebut, segera mengeluarkan (*sign out*) pengguna, dan mengharuskan mereka meminta tautan baru.
3. **Manfaat Keamanan:** Meminimalkan celah waktu di mana tautan verifikasi email yang disadap atau bocor dapat digunakan untuk membajak akun yang baru dibuat, sebelum pengguna tersebut sempat membuat kunci kriptografi mereka.

---

## 8. Keterbatasan yang Diketahui

1. **Tanpa Forward Secrecy:** Jika *private key* RSA pengguna berhasil dikompromikan, musuh yang telah mengarsipkan *ciphertext* di masa lalu dapat mendekripsi semua pesan riwayat. Versi masa depan harus menerapkan protokol **Double Ratchet** (Protokol Signal) menggunakan kunci efemeral X25519.

2. **Tanpa Verifikasi Kunci:** Pengguna tidak dapat saling memverifikasi *fingerprint* dari *public key* satu sama lain melalui *out-of-band* (contoh: memindai kode QR). Hal ini membuat sistem rentan terhadap serangan Man-in-the-Middle (MITM) di mana server menukar *public key*.

3. **Paparan Metadata:** Firebase mengetahui UID pengirim/penerima, *timestamp*, ukuran pesan, dan alamat IP. Untuk perlindungan metadata yang lebih kuat, pertimbangkan *onion routing* atau protokol terdesentralisasi.

4. **Perlindungan Kunci Berbasis Kata Sandi:** Keamanan file *private key* sangat bergantung pada kekuatan kata sandi. Kata sandi yang lemah dapat di-*brute-force* meskipun PBKDF2 sudah diulang 600.000 kali. Pertimbangkan penambahan pembuka kunci biometrik atau dukungan kunci fisik (hardware key).

---

## 9. Daftar Periksa Audit Keamanan

Gunakan daftar periksa (checklist) ini saat mengaudit basis kode Aegis:

- [ ] **Pembuatan Kunci:** Kunci RSA menggunakan `rsa.generate_private_key()` dengan `public_exponent=65537` dan `key_size=2048`
- [ ] **Tanpa Penggunaan Ulang Kunci:** Tiap pesan menghasilkan kunci AES yang benar-benar baru melalui `AESGCM.generate_key()`
- [ ] **Keunikan Nonce:** Tiap pesan menghasilkan 12-byte *nonce* yang benar-benar baru melalui `secrets.token_bytes(12)`
- [ ] **Padding OAEP:** Operasi RSA menggunakan `OAEP(mgf=MGF1(SHA256()), algorithm=SHA256())`
- [ ] **Tag Auth GCM:** AES-GCM secara otomatis menambahkan dan memverifikasi 128-bit tag autentikasi
- [ ] **Iterasi PBKDF2:** Perlindungan *private key* menggunakan 600.000 iterasi
- [ ] **Tanpa Plaintext dalam Transmisi:** Pastikan Firebase tidak pernah menerima konten pesan tanpa dienkripsi
- [ ] **Pembersihan Memori:** `app.private_key` diatur menjadi `None` saat *sign-out*
- [ ] **Penanganan Error:** Eksepsi (pengecualian) `InvalidTag` ditangkap dengan baik tanpa membocorkan informasi
- [ ] **Versi Dependensi:** Pustaka `cryptography` terus diperbarui dengan *patch* keamanan terbaru
- [ ] **TLS Pinning:** Pertimbangkan menambahkan *certificate pinning* untuk panggilan API Firebase
- [ ] **Pembatasan Laju (Rate Limiting):** Aturan Firebase seharusnya dapat mencegah terjadinya spam/penyalahgunaan
