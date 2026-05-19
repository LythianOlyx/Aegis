# Aegis – Panduan Deployment

> **Versi:** 1.0.0  
> **Terakhir Diperbarui:** 2026-05-13  

---

## Daftar Isi

- [1. Gambaran Umum](#1-gambaran-umum)
- [2. Build Desktop](#2-build-desktop)
  - [2.1 macOS (.app / .dmg)](#21-macos-app--dmg)
  - [2.2 Windows (.exe)](#22-windows-exe)
  - [2.3 Linux (.AppImage / .deb)](#23-linux-appimage--deb)
- [3. Build Seluler (Mobile)](#3-build-seluler-mobile)
  - [3.1 Android (.apk / .aab)](#31-android-apk--aab)
  - [3.2 iOS (.ipa)](#32-ios-ipa)
- [4. Menggunakan compile.py](#4-menggunakan-compilepy)
- [5. Variabel Lingkungan (Environment Variables)](#5-variabel-lingkungan-environment-variables)
- [6. Alur Kerja (Pipeline) CI/CD](#6-alur-kerja-pipeline-cicd)
- [7. Penandatanganan Kode (Code Signing)](#7-penandatanganan-kode-code-signing)
- [8. Pemecahan Masalah (Troubleshooting)](#8-pemecahan-masalah-troubleshooting)

---

## 1. Gambaran Umum

Aegis menggunakan **pemisahan UI pada saat kompilasi (build-time UI separation)** dengan dua titik masuk (entry point):

| Target | Entry Point | Alat Build | Pengecualian (Excludes) |
|--------|------------|------------|----------|
| Desktop | `main_desktop.py` | PyInstaller | `ui/mobile/*` |
| Seluler | `main_mobile.py` | Buildozer | `ui/desktop/*` |

Skrip `compile.py` gabungan mengotomatiskan kedua alur kerja tersebut.

---

## 2. Build Desktop

### Prasyarat (Semua Platform)

```bash
pip install pyinstaller>=6.10.0
```

### 2.1 macOS (.app / .dmg)

```bash
# Opsi A: Menggunakan compile.py
python compile.py
# Pilih: [1] Desktop UI → [1] .app

# Opsi B: PyInstaller Manual
pyinstaller aegis_desktop.spec --clean

# Output: dist/Aegis.app
```

**Membuat file DMG:**

```bash
# Instal create-dmg
brew install create-dmg

# Buat DMG
create-dmg \
    --volname "Aegis Installer" \
    --volicon "assets/logo.png" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "Aegis.app" 175 120 \
    --hide-extension "Aegis.app" \
    --app-drop-link 425 120 \
    "dist/Aegis-1.0.0.dmg" \
    "dist/Aegis.app"
```

### 2.2 Windows (.exe)

```bash
# Di Windows:
python compile.py
# Pilih: [1] Desktop UI → [1] .exe

# Output: dist/Aegis.exe
```

**Persyaratan:**
- Python 3.10+ (Direkomendasikan 64-bit)
- Visual C++ Redistributable 2015-2022
- Jalankan dari Command Prompt biasa (bukan PowerShell ISE)

### 2.3 Linux (.AppImage / .deb)

```bash
# AppImage
python compile.py
# Pilih: [1] Desktop UI → [1] .AppImage

# Buat agar dapat dieksekusi
chmod +x dist/Aegis.AppImage
./dist/Aegis.AppImage
```

**Dependensi Sistem (Debian/Ubuntu):**

```bash
sudo apt-get install -y \
    build-essential python3-dev \
    libgl1-mesa-dev libgles2-mesa-dev \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libffi-dev libssl-dev
```

---

## 3. Build Seluler (Mobile)

### 3.1 Android (.apk / .aab)

**Persyaratan:**
- Host Linux atau macOS (Buildozer tidak mendukung Windows secara langsung)
- Java JDK 17
- Android SDK dan NDK (diinstal otomatis oleh Buildozer)

**Pengaturan Sistem (Ubuntu/Debian):**

```bash
# Dependensi sistem
sudo apt-get install -y \
    python3-pip python3-setuptools \
    build-essential git zip unzip \
    openjdk-17-jdk autoconf libtool \
    libffi-dev libssl-dev zlib1g-dev \
    liblzma-dev

# Instal Buildozer
pip install buildozer cython

# Inisialisasi Android SDK (hanya saat pertama kali)
buildozer android debug
# Perintah ini otomatis mengunduh SDK, NDK, dan alat platform (platform tools)
```

**Proses Build:**

```bash
# Menggunakan compile.py
python compile.py
# Pilih: [2] Mobile UI → [1] .apk

# Atau secara langsung
buildozer android debug

# Build untuk rilis (Release)
buildozer android release

# Output: bin/aegis-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
```

**Penting:** `compile.py` otomatis menyalin `main_mobile.py` → `main.py` sebelum memanggil Buildozer, dan mengembalikan status awalnya setelah proses build selesai.

**Pengujian di Perangkat:**

```bash
# Instal melalui USB
adb install bin/aegis-*.apk

# Dengan log langsung (live log)
buildozer android deploy logcat
```

### 3.2 iOS (.ipa)

**Persyaratan:**
- Host macOS dengan Xcode 15+
- Akun Pengembang Apple (Apple Developer Account)
- Rantai alat (toolchain) kivy-ios

```bash
# Instal kivy-ios
pip install kivy-ios

# Build toolchain
toolchain build python3 kivy pillow

# Buat proyek Xcode
toolchain create Aegis /path/to/aegis/main_mobile.py

# Buka di Xcode
open aegis-ios/Aegis.xcodeproj
# Konfigurasikan penandatanganan (signing) → Build → Jalankan di perangkat
```

---

## 4. Menggunakan compile.py

CLI interaktif akan memandu Anda melalui proses build:

```
╔══════════════════════════════════════════════╗
║          AEGIS BUILD SYSTEM v1.0.0            ║
║      End-to-End Encrypted Messenger          ║
╚══════════════════════════════════════════════╝

  Host OS: Darwin
  Python:  3.11.5
  Project: /Users/you/Aegis

Select Target UI:
  [1] Desktop UI (PyInstaller)
  [2] Mobile UI (Buildozer)

▶ Enter choice (1-2): 1

Select Output Format:
  [1] .app (macOS Application)
  [2] .dmg (macOS Disk Image)

▶ Enter choice (1-2): 1

▶ Building Desktop: .app (macOS Application)
  ✓ Generated /Users/you/Aegis/aegis_desktop.spec
  Running: python -m PyInstaller aegis_desktop.spec --clean

  ✓ Desktop build complete!
  Output: /Users/you/Aegis/dist/Aegis
```

---

## 5. Variabel Lingkungan (Environment Variables)

Kredensial Firebase harus diatur sebelum memulai proses build atau menjalankan aplikasi:

| Variabel | Deskripsi | Contoh |
|----------|-------------|---------|
| `FIREBASE_API_KEY` | Web API key dari Konsol Firebase | `AIzaSyB1234...` |
| `FIREBASE_PROJECT_ID` | Pengidentifikasi proyek Firebase | `aegis-msg-12345` |
| `FIREBASE_DB_URL` | URL Realtime Database | `https://aegis-msg-12345-default-rtdb.firebaseio.com` |
| `FIREBASE_STORAGE_BUCKET` | Bucket Cloud Storage | `aegis-msg-12345.appspot.com` |

**Untuk build produksi**, tanamkan kredensial ini di dalam source code atau gunakan file konfigurasi sebagai pengganti variabel lingkungan.

---

## 6. Alur Kerja (Pipeline) CI/CD

### Contoh GitHub Actions

```yaml
name: Aegis Build

on:
  push:
    tags: ['v*']

jobs:
  build-desktop-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pyinstaller
      - run: python compile.py <<< $'1\n1\n'
      - uses: actions/upload-artifact@v4
        with:
          name: aegis-macos
          path: dist/Aegis.app

  build-desktop-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pyinstaller
      - run: pyinstaller aegis_desktop.spec --clean
      - uses: actions/upload-artifact@v4
        with:
          name: aegis-windows
          path: dist/Aegis.exe

  build-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'
      - run: |
          pip install buildozer cython
          cp main_mobile.py main.py
          buildozer android debug
      - uses: actions/upload-artifact@v4
        with:
          name: aegis-android
          path: bin/*.apk
```

---

## 7. Penandatanganan Kode (Code Signing)

### macOS (Notarisasi/Notarization)

```bash
# Tandatangani aplikasi
codesign --deep --force --sign "Developer ID Application: Your Name" dist/Aegis.app

# Buat DMG
create-dmg --volname "Aegis" dist/Aegis.dmg dist/Aegis.app

# Kirim untuk notarisasi
xcrun notarytool submit dist/Aegis.dmg \
    --apple-id your@email.com \
    --team-id TEAMID \
    --password @keychain:notary

# Tempelkan tiket (Staple)
xcrun stapler staple dist/Aegis.dmg
```

### Android (Penandatanganan Rilis)

```bash
# Buat keystore (satu kali)
keytool -genkey -v -keystore aegis-release.keystore \
    -alias aegis -keyalg RSA -keysize 2048 -validity 10000

# Tambahkan ke buildozer.spec
# android.keystore = aegis-release.keystore
# android.keyalias = aegis

# Build rilis yang sudah ditandatangani
buildozer android release
```

---

## 8. Pemecahan Masalah (Troubleshooting)

| Masalah (Issue) | Solusi |
|-------|----------|
| `ModuleNotFoundError: kivymd` | Jalankan `pip install kivymd==2.0.1` |
| `SDL2 not found` (Linux) | `sudo apt-get install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev` |
| PyInstaller `RecursionError` | Tambahkan `sys.setrecursionlimit(5000)` di bagian atas file `.spec` |
| Kegagalan `gradle` Buildozer | Pastikan Java 17 terinstal: `java -version` |
| `FIREBASE_API_KEY not set` | Ekspor variabel lingkungan atau perbarui `main_desktop.py` / `main_mobile.py` secara langsung |
| macOS `"cannot be opened"` | Klik Kanan → Open, atau tandatangani aplikasi dengan `codesign` |
| Android `INSTALL_FAILED_` | Periksa `android.api` dan `android.minapi` di `buildozer.spec` |
| Kesalahan Firebase 401 | Token kedaluwarsa; aplikasi seharusnya melakukan auto-refresh melalui `refresh_id_token()` |
