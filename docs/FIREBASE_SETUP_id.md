# Aegis – Panduan Penyiapan Firebase

> **Versi:** 1.0.0  
> **Terakhir Diperbarui:** 2026-05-13  

---

## Daftar Isi

- [1. Buat Proyek Firebase](#1-buat-proyek-firebase)
- [2. Aktifkan Autentikasi (Authentication)](#2-aktifkan-autentikasi-authentication)
- [3. Siapkan Realtime Database](#3-siapkan-realtime-database)
- [4. Konfigurasi Aturan Keamanan (Security Rules)](#4-konfigurasi-aturan-keamanan-security-rules)
- [5. Aktifkan Cloud Storage](#5-aktifkan-cloud-storage)
- [6. Dapatkan Kunci Konfigurasi](#6-dapatkan-kunci-konfigurasi)
- [7. Atur Variabel Lingkungan (Environment Variables)](#7-atur-variabel-lingkungan-environment-variables)
- [8. Pengindeksan Database](#8-pengindeksan-database)
- [9. Aturan Penyimpanan (Storage Rules)](#9-aturan-penyimpanan-storage-rules)
- [10. Tagihan & Kuota (Billing & Quotas)](#10-tagihan--kuota-billing--quotas)

---

## 1. Buat Proyek Firebase

1. Buka [Konsol Firebase](https://console.firebase.google.com/)
2. Klik **"Create a project"** (Buat proyek)
3. Masukkan nama proyek: `aegis-messenger` (atau nama pilihan Anda)
4. Aktifkan atau nonaktifkan Google Analytics (opsional untuk Aegis)
5. Klik **"Create project"** (Buat proyek)
6. Tunggu hingga proses penyediaan (provisioning) selesai

---

## 2. Aktifkan Autentikasi (Authentication)

1. Di Konsol Firebase, buka menu **Build → Authentication**
2. Klik **"Get started"** (Mulai)
3. Buka tab **"Sign-in method"** (Metode login)
4. Aktifkan penyedia **"Email/Password"**
   - Alihkan (toggle) **"Email/Password"** ke posisi Enabled (Aktif)
   - (Opsional) Alihkan **"Email link (passwordless sign-in)"** — Aegis menggunakan autentikasi berbasis kata sandi
5. Klik **"Save"** (Simpan)

### Opsional: Tetapkan Persyaratan Kata Sandi

- Buka **Authentication → Settings → User account linking** (Tautan akun pengguna)
- Di bawah **Password policy** (Kebijakan kata sandi), atur panjang minimum menjadi 8 karakter
- Aktifkan persyaratan: huruf besar, huruf kecil, angka, karakter khusus

---

## 3. Siapkan Realtime Database

1. Buka menu **Build → Realtime Database**
2. Klik **"Create Database"** (Buat Database)
3. Pilih lokasi yang paling dekat dengan pengguna Anda (misalnya, `us-central1`, `asia-southeast1`)
4. Mulai dalam **"Test mode"** (Mode pengujian) untuk tahap pengembangan (kita akan menguncinya pada langkah 4)
5. Klik **"Enable"** (Aktifkan)

URL database Anda akan terlihat seperti ini:
```
https://aegis-messenger-xxxxx-default-rtdb.firebaseio.com
```

---

## 4. Konfigurasi Aturan Keamanan (Security Rules)

Buka **Realtime Database → Rules** dan ganti aturan bawaan (default) dengan:

```json
{
  "rules": {
    "usernames": {
      ".read": true,
      ".write": "auth != null"
    },
    "users": {
      ".read": "auth != null",
      "$uid": {
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
        ".write": "auth != null && root.child('chats').child($chatId).child('participants').child(auth.uid).exists()",
        ".indexOn": ["timestamp"]
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

### Penjelasan Aturan

| Path (Jalur) | Baca (Read) | Tulis (Write) | Tujuan |
|------|------|-------|---------|
| `/usernames` | Publik | Semua pengguna yang terautentikasi | Pengecekan ketersediaan username |
| `/users/$uid` | Semua pengguna yang terautentikasi | Hanya pengguna itu sendiri | Profil publik (nama, pubkey) |
| `/chats/$chatId` | Hanya peserta obrolan | Semua pengguna yang terautentikasi | Metadata obrolan |
| `/messages/$chatId` | Hanya peserta obrolan | Hanya peserta obrolan | Pesan E2EE |
| `/user_chats/$uid` | Hanya pengguna tersebut | Semua pengguna yang terautentikasi | Indeks obrolan per pengguna |

Klik **"Publish"** (Publikasikan) untuk menerapkan aturan tersebut.

---

## 5. Aktifkan Cloud Storage

1. Buka menu **Build → Storage**
2. Klik **"Get started"** (Mulai)
3. Mulai dalam **"Test mode"** (Mode pengujian) untuk tahap pengembangan
4. Pilih lokasi (sama dengan database Anda)
5. Klik **"Done"** (Selesai)

Bucket penyimpanan Anda akan terlihat seperti ini:
```
aegis-messenger-xxxxx.appspot.com
```

---

## 6. Dapatkan Kunci Konfigurasi

1. Buka **Project Settings** (ikon roda gigi di kiri atas)
2. Gulir ke bawah ke bagian **"Your apps"** (Aplikasi Anda)
3. Jika belum ada aplikasi web, klik **"Add app"** (Tambahkan aplikasi) → **Web** (ikon </>)
4. Daftarkan dengan nama panggilan (nickname) `aegis-web` (tidak perlu Firebase Hosting)
5. Salin nilai konfigurasinya:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSyB...",            // ← FIREBASE_API_KEY
  authDomain: "aegis-messenger-xxxxx.firebaseapp.com",
  projectId: "aegis-messenger-xxxxx",  // ← FIREBASE_PROJECT_ID
  storageBucket: "aegis-messenger-xxxxx.appspot.com",  // ← FIREBASE_STORAGE_BUCKET
  databaseURL: "https://aegis-messenger-xxxxx-default-rtdb.firebaseio.com",  // ← FIREBASE_DB_URL
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123"
};
```

---

## 7. Atur Variabel Lingkungan (Environment Variables)

### macOS / Linux

Tambahkan ke file `~/.zshrc` atau `~/.bashrc`:

```bash
export FIREBASE_API_KEY="AIzaSyB..."
export FIREBASE_PROJECT_ID="aegis-messenger-xxxxx"
export FIREBASE_DB_URL="https://aegis-messenger-xxxxx-default-rtdb.firebaseio.com"
export FIREBASE_STORAGE_BUCKET="aegis-messenger-xxxxx.appspot.com"
```

Muat ulang (Reload):
```bash
source ~/.zshrc
```

### Windows (PowerShell)

```powershell
[Environment]::SetEnvironmentVariable("FIREBASE_API_KEY", "AIzaSyB...", "User")
[Environment]::SetEnvironmentVariable("FIREBASE_PROJECT_ID", "aegis-messenger-xxxxx", "User")
[Environment]::SetEnvironmentVariable("FIREBASE_DB_URL", "https://aegis-messenger-xxxxx-default-rtdb.firebaseio.com", "User")
[Environment]::SetEnvironmentVariable("FIREBASE_STORAGE_BUCKET", "aegis-messenger-xxxxx.appspot.com", "User")
```

### Verifikasi

```bash
python -c "import os; print(os.environ.get('FIREBASE_API_KEY', 'BELUM DIATUR'))"
```

---

## 8. Pengindeksan Database

Untuk pencarian pengguna dan kueri pesan yang efisien, tambahkan indeks berikut:

Buka **Realtime Database → Rules** dan pastikan aturan `.indexOn` ini ada:

```json
{
  "rules": {
    "usernames": {
      ".read": true,
      ".write": "auth != null"
    },
    "users": {
      ".read": "auth != null",
      ".indexOn": ["display_name", "username"],
      "$uid": {
        ".write": "auth != null && auth.uid == $uid"
      }
    },
    "messages": {
      "$chatId": {
        ".indexOn": ["timestamp"],
        ".read": "...",
        ".write": "..."
      }
    }
  }
}
```

Tanpa indeks, Firebase akan mencatat peringatan dan kueri (permintaan data) akan menjadi lambat pada kumpulan data yang besar.

---

## 9. Aturan Penyimpanan (Storage Rules)

Buka **Storage → Rules** dan atur:

```
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /files/{chatId}/{fileName} {
      allow read: if request.auth != null;
      allow write: if request.auth != null
                   && request.resource.size < 100 * 1024 * 1024;
    }
  }
}
```

Hal ini memastikan:
- Hanya pengguna yang terautentikasi yang dapat membaca/menulis file
- Ukuran unggahan maksimum adalah 100 MiB (sesuai dengan `file_manager.MAX_FILE_SIZE`)

---

## 10. Tagihan & Kuota (Billing & Quotas)

### Paket Spark (Gratis)

| Sumber Daya | Batas |
|----------|-------|
| Autentikasi | 50.000 pengguna aktif bulanan |
| Realtime Database | 1 GB tersimpan, 10 GB/bulan unduhan |
| Cloud Storage | 5 GB tersimpan, 1 GB/hari unduhan |
| Koneksi bersamaan (Simultaneous) | 100 |

### Paket Blaze (Bayar sesuai penggunaan / Pay-as-you-go)

Direkomendasikan untuk produksi. Mengaktifkan:
- Pengguna autentikasi tak terbatas
- Database dan penyimpanan berskala otomatis (Auto-scaling)
- Cloud Functions (untuk fitur masa depan seperti notifikasi push)

### Perkiraan Biaya (Blaze)

| 1.000 pengguna aktif harian | ~Biaya/bulan |
|--------------------------|-------------|
| Autentikasi | Gratis |
| Baca (reads) Database | ~$0.50 |
| Penyimpanan Database | ~$1.00 |
| Penyimpanan (1 GB file/hari) | ~$0.30 |
| **Total perkiraan** | **~$2-5/bulan** |

> **Tip:** Aktifkan peringatan anggaran (budget alerts) di Google Cloud Console untuk menghindari tagihan yang tidak terduga.
