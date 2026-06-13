# Aegis – Panduan Penyiapan Firebase

> **Versi:** 1.1.0  
> **Terakhir Diperbarui:** 2026-06-13  

---

## Daftar Isi

- [1. Buat Proyek Firebase](#1-buat-proyek-firebase)
- [2. Aktifkan Autentikasi (Authentication)](#2-aktifkan-autentikasi-authentication)
- [3. Siapkan Realtime Database](#3-siapkan-realtime-database)
- [4. Konfigurasi Aturan Keamanan (Security Rules)](#4-konfigurasi-aturan-keamanan-security-rules)
- [5. Dapatkan Kunci Konfigurasi](#5-dapatkan-kunci-konfigurasi)
- [6. Konfigurasi Aplikasi](#6-konfigurasi-aplikasi)
- [7. Pengindeksan Database](#7-pengindeksan-database)
- [8. Tagihan & Kuota (Billing & Quotas)](#8-tagihan--kuota-billing--quotas)

---

## 1. Buat Proyek Firebase

1. Buka [Konsol Firebase](https://console.firebase.google.com/)
2. Klik **"Create a project"** (Buat proyek)
3. Masukkan nama proyek (misalnya, `aegis-messenger`)
4. Aktifkan atau nonaktifkan Google Analytics (opsional)
5. Klik **"Create project"** dan tunggu hingga selesai

---

## 2. Aktifkan Autentikasi (Authentication)

1. Di Konsol Firebase, buka menu **Build → Authentication**
2. Klik **"Get started"** (Mulai)
3. Buka tab **"Sign-in method"** (Metode login)
4. Aktifkan penyedia **"Email/Password"**
5. Klik **"Save"** (Simpan)

### Opsional: Tetapkan Persyaratan Kata Sandi

- Buka **Authentication → Settings → Password policy**
- Atur panjang minimum menjadi 8 karakter
- Aktifkan: huruf besar, huruf kecil, angka, karakter khusus

---

## 3. Siapkan Realtime Database

1. Buka menu **Build → Realtime Database**
2. Klik **"Create Database"** (Buat Database)
3. Pilih region yang paling dekat dengan pengguna Anda  
   > Untuk Indonesia/Asia Tenggara: pilih `asia-southeast1`
4. Mulai dalam **"Test mode"** (Mode pengujian) untuk tahap pengembangan
5. Klik **"Enable"** (Aktifkan)

URL database Anda akan terlihat seperti ini:
```
https://<project-id>-default-rtdb.asia-southeast1.firebasedatabase.app
```

> ☁️ **Cloud Storage TIDAK diperlukan.** Aegis hanya mendukung pesan teks dan emoji — tidak ada unggahan file.

---

## 4. Konfigurasi Aturan Keamanan (Security Rules)

Buka **Realtime Database → Rules** dan ganti dengan aturan berikut. Ini adalah **aturan lengkap siap produksi** yang sudah mencakup indeks:

```json
{
  "rules": {
    "usernames": {
      ".read": true,
      "$username": {
        ".write": "auth != null && (!data.exists() || data.val() == auth.uid)"
      }
    },

    "users": {
      ".read": "auth != null",
      ".indexOn": ["display_name", "username"],
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

Klik **"Publish"** untuk menerapkan aturan.

### Penjelasan Aturan

| Path (Jalur) | Baca (Read) | Tulis (Write) | Tujuan |
|------|------|-------|---------|
| `/usernames/$username` | Publik | Pemilik atau jika baru | Cek ketersediaan & reservasi username |
| `/users/$uid` | Pengguna terautentikasi | Hanya pemilik | Profil publik (nama, public key) |
| `/chats/$chatId` | Peserta obrolan | Pengguna terautentikasi | Metadata obrolan |
| `/messages/$chatId` | Peserta obrolan | Peserta obrolan | Pesan teks/emoji E2EE |
| `/user_chats/$uid` | Hanya pemilik | Pengguna terautentikasi | Indeks obrolan per pengguna |

---

## 5. Dapatkan Kunci Konfigurasi

1. Buka **Project Settings** (ikon roda gigi di kiri atas)
2. Gulir ke bawah ke bagian **"Your apps"** (Aplikasi Anda)
3. Klik **"Add app"** → **Web** (ikon `</>`) jika belum ada aplikasi
4. Daftarkan dengan nama panggilan `aegis-web` (tidak perlu Firebase Hosting)
5. Salin nilai yang dibutuhkan:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSy...",            // ← diperlukan
  projectId: "your-project-id",   // ← diperlukan
  databaseURL: "https://...",     // ← diperlukan
  storageBucket: "...",           // ← TIDAK diperlukan (tidak ada unggahan file)
  authDomain: "...",              // ← TIDAK diperlukan
  messagingSenderId: "...",       // ← TIDAK diperlukan
  appId: "...",                   // ← TIDAK diperlukan
};
```

Hanya `apiKey`, `projectId`, dan `databaseURL` yang dibutuhkan oleh Aegis.

---

## 6. Konfigurasi Aplikasi

Buka `main_desktop.py` dan `main_mobile.py`, lalu perbarui dict konfigurasi `FirebaseClient`:

```python
self.firebase = FirebaseClient({
    "api_key":        "AIzaSyDk8fV0Kqo3JXNcXd_4a3EYBgk3DWtalUc",
    "project_id":     "aegis-b6f5a",
    "db_url":         "https://aegis-b6f5a-default-rtdb.asia-southeast1.firebasedatabase.app",
    "storage_bucket": "",   # Tidak digunakan — biarkan kosong
})
```

Ganti nilai-nilai ini dengan kredensial proyek Firebase Anda sendiri.

---

## 7. Pengindeksan Database

Aturan keamanan di langkah 4 sudah mencakup semua direktif `.indexOn` yang diperlukan:

| Indeks | Path | Tujuan |
|-------|------|---------|
| `display_name` | `/users` | Pencarian pengguna berdasarkan nama tampilan |
| `username` | `/users` | Pencarian pengguna berdasarkan @username |
| `timestamp` | `/messages/$chatId` | Pengurutan pesan secara kronologis |

Tanpa indeks ini, Firebase akan mencatat peringatan dan kueri akan menjadi lambat pada data besar.

---

## 8. Tagihan & Kuota (Billing & Quotas)

### Paket Spark (Gratis)

| Sumber Daya | Batas |
|----------|-------|
| Autentikasi | 50.000 pengguna aktif bulanan |
| Realtime Database | 1 GB tersimpan, 10 GB/bulan unduhan |
| Koneksi bersamaan | 100 |

> Karena Aegis **tidak** menggunakan Cloud Storage, tidak ada biaya penyimpanan file.

### Paket Blaze (Bayar sesuai penggunaan)

Direkomendasikan untuk produksi. Mengaktifkan:
- Pengguna autentikasi tak terbatas
- Database berskala otomatis
- Cloud Functions (untuk fitur masa depan seperti notifikasi push)

### Perkiraan Biaya (Blaze)

| 1.000 pengguna aktif harian | ~Biaya/bulan |
|--------------------------|-------------|
| Autentikasi | Gratis |
| Baca (reads) Database | ~$0.50 |
| Penyimpanan Database | ~$1.00 |
| **Total perkiraan** | **~$1-2/bulan** |

> **Tip:** Aktifkan peringatan anggaran (budget alerts) di Google Cloud Console untuk menghindari tagihan yang tidak terduga.
