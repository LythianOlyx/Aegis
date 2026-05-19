# Aegis – Deployment Guide

> **Version:** 1.0.0  
> **Last Updated:** 2026-05-13  

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. Desktop Builds](#2-desktop-builds)
  - [2.1 macOS (.app / .dmg)](#21-macos-app--dmg)
  - [2.2 Windows (.exe)](#22-windows-exe)
  - [2.3 Linux (.AppImage / .deb)](#23-linux-appimage--deb)
- [3. Mobile Builds](#3-mobile-builds)
  - [3.1 Android (.apk / .aab)](#31-android-apk--aab)
  - [3.2 iOS (.ipa)](#32-ios-ipa)
- [4. Using compile.py](#4-using-compilepy)
- [5. Environment Variables](#5-environment-variables)
- [6. CI/CD Pipeline](#6-cicd-pipeline)
- [7. Code Signing](#7-code-signing)
- [8. Troubleshooting](#8-troubleshooting)

---

## 1. Overview

Aegis uses **build-time UI separation** with two entry points:

| Target | Entry Point | Build Tool | Excludes |
|--------|------------|------------|----------|
| Desktop | `main_desktop.py` | PyInstaller | `ui/mobile/*` |
| Mobile | `main_mobile.py` | Buildozer | `ui/desktop/*` |

The unified `compile.py` script automates both pipelines.

---

## 2. Desktop Builds

### Prerequisites (All Platforms)

```bash
pip install pyinstaller>=6.10.0
```

### 2.1 macOS (.app / .dmg)

```bash
# Option A: Using compile.py
python compile.py
# Select: [1] Desktop UI → [1] .app

# Option B: Manual PyInstaller
pyinstaller aegis_desktop.spec --clean

# Output: dist/Aegis.app
```

**Creating a DMG:**

```bash
# Install create-dmg
brew install create-dmg

# Create DMG
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
# On Windows:
python compile.py
# Select: [1] Desktop UI → [1] .exe

# Output: dist/Aegis.exe
```

**Requirements:**
- Python 3.10+ (64-bit recommended)
- Visual C++ Redistributable 2015-2022
- Run from a normal Command Prompt (not PowerShell ISE)

### 2.3 Linux (.AppImage / .deb)

```bash
# AppImage
python compile.py
# Select: [1] Desktop UI → [1] .AppImage

# Make executable
chmod +x dist/Aegis.AppImage
./dist/Aegis.AppImage
```

**System Dependencies (Debian/Ubuntu):**

```bash
sudo apt-get install -y \
    build-essential python3-dev \
    libgl1-mesa-dev libgles2-mesa-dev \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libffi-dev libssl-dev
```

---

## 3. Mobile Builds

### 3.1 Android (.apk / .aab)

**Requirements:**
- Linux or macOS host (Buildozer does not support Windows natively)
- Java JDK 17
- Android SDK and NDK (auto-installed by Buildozer)

**System Setup (Ubuntu/Debian):**

```bash
# System dependencies
sudo apt-get install -y \
    python3-pip python3-setuptools \
    build-essential git zip unzip \
    openjdk-17-jdk autoconf libtool \
    libffi-dev libssl-dev zlib1g-dev \
    liblzma-dev

# Install Buildozer
pip install buildozer cython

# Initialize Android SDK (first run only)
buildozer android debug
# This auto-downloads SDK, NDK, and platform tools
```

**Building:**

```bash
# Using compile.py
python compile.py
# Select: [2] Mobile UI → [1] .apk

# Or directly
buildozer android debug

# Release build
buildozer android release

# Output: bin/aegis-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
```

**Important:** `compile.py` automatically copies `main_mobile.py` → `main.py` before invoking Buildozer, and restores the original after the build.

**Testing on Device:**

```bash
# Install via USB
adb install bin/aegis-*.apk

# With live log
buildozer android deploy logcat
```

### 3.2 iOS (.ipa)

**Requirements:**
- macOS host with Xcode 15+
- Apple Developer Account
- kivy-ios toolchain

```bash
# Install kivy-ios
pip install kivy-ios

# Build toolchain
toolchain build python3 kivy pillow

# Create Xcode project
toolchain create Aegis /path/to/aegis/main_mobile.py

# Open in Xcode
open aegis-ios/Aegis.xcodeproj
# Configure signing → Build → Run on device
```

---

## 4. Using compile.py

The interactive CLI guides you through the build process:

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

## 5. Environment Variables

Firebase credentials must be set before building or running:

| Variable | Description | Example |
|----------|-------------|---------|
| `FIREBASE_API_KEY` | Web API key from Firebase Console | `AIzaSyB1234...` |
| `FIREBASE_PROJECT_ID` | Firebase project identifier | `aegis-msg-12345` |
| `FIREBASE_DB_URL` | Realtime Database URL | `https://aegis-msg-12345-default-rtdb.firebaseio.com` |
| `FIREBASE_STORAGE_BUCKET` | Cloud Storage bucket | `aegis-msg-12345.appspot.com` |

**For production builds**, embed these in the source or use a config file instead of environment variables.

---

## 6. CI/CD Pipeline

### GitHub Actions Example

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

## 7. Code Signing

### macOS (Notarization)

```bash
# Sign the app
codesign --deep --force --sign "Developer ID Application: Your Name" dist/Aegis.app

# Create DMG
create-dmg --volname "Aegis" dist/Aegis.dmg dist/Aegis.app

# Submit for notarization
xcrun notarytool submit dist/Aegis.dmg \
    --apple-id your@email.com \
    --team-id TEAMID \
    --password @keychain:notary

# Staple the ticket
xcrun stapler staple dist/Aegis.dmg
```

### Android (Release Signing)

```bash
# Generate keystore (one-time)
keytool -genkey -v -keystore aegis-release.keystore \
    -alias aegis -keyalg RSA -keysize 2048 -validity 10000

# Add to buildozer.spec
# android.keystore = aegis-release.keystore
# android.keyalias = aegis

# Build signed release
buildozer android release
```

---

## 8. Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: kivymd` | Run `pip install kivymd==2.0.1` |
| `SDL2 not found` (Linux) | `sudo apt-get install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev` |
| PyInstaller `RecursionError` | Add `sys.setrecursionlimit(5000)` to the top of the .spec file |
| Buildozer `gradle` failure | Ensure Java 17: `java -version` |
| `FIREBASE_API_KEY not set` | Export env vars or update `main_desktop.py` / `main_mobile.py` directly |
| macOS `"cannot be opened"` | Right-click → Open, or sign the app with `codesign` |
| Android `INSTALL_FAILED_` | Check `android.api` and `android.minapi` in `buildozer.spec` |
| Firebase 401 errors | Token expired; app should auto-refresh via `refresh_id_token()` |
