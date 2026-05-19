# Aegis – Firebase Setup Guide

> **Version:** 1.0.0  
> **Last Updated:** 2026-05-13  

---

## Table of Contents

- [1. Create Firebase Project](#1-create-firebase-project)
- [2. Enable Authentication](#2-enable-authentication)
- [3. Set Up Realtime Database](#3-set-up-realtime-database)
- [4. Configure Security Rules](#4-configure-security-rules)
- [5. Enable Cloud Storage](#5-enable-cloud-storage)
- [6. Get Configuration Keys](#6-get-configuration-keys)
- [7. Set Environment Variables](#7-set-environment-variables)
- [8. Database Indexing](#8-database-indexing)
- [9. Storage Rules](#9-storage-rules)
- [10. Billing & Quotas](#10-billing--quotas)

---

## 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Create a project"**
3. Enter project name: `aegis-messenger` (or your preferred name)
4. Enable or disable Google Analytics (optional for Aegis)
5. Click **"Create project"**
6. Wait for provisioning to complete

---

## 2. Enable Authentication

1. In the Firebase Console, go to **Build → Authentication**
2. Click **"Get started"**
3. Go to the **"Sign-in method"** tab
4. Enable **"Email/Password"** provider
   - Toggle **"Email/Password"** to Enabled
   - (Optional) Toggle **"Email link (passwordless sign-in)"** — Aegis uses password-based auth
5. Click **"Save"**

### Optional: Set Password Requirements

- Go to **Authentication → Settings → User account linking**
- Under **Password policy**, set minimum length to 8 characters
- Enable requirements: uppercase, lowercase, numeric, special character

---

## 3. Set Up Realtime Database

1. Go to **Build → Realtime Database**
2. Click **"Create Database"**
3. Select a location closest to your users (e.g., `us-central1`, `asia-southeast1`)
4. Start in **"Test mode"** for development (we'll lock down in step 4)
5. Click **"Enable"**

Your database URL will look like:
```
https://aegis-messenger-xxxxx-default-rtdb.firebaseio.com
```

---

## 4. Configure Security Rules

Go to **Realtime Database → Rules** and replace the default rules with:

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

### Rules Explanation

| Path | Read | Write | Purpose |
|------|------|-------|---------|
| `/usernames` | Public | Any authenticated user | Checking username availability |
| `/users/$uid` | Any authenticated user | Only the user themselves | Public profiles (name, pubkey) |
| `/chats/$chatId` | Chat participants only | Any authenticated user | Chat metadata |
| `/messages/$chatId` | Chat participants only | Chat participants only | E2EE messages |
| `/user_chats/$uid` | Only the user | Any authenticated user | Chat index per user |

Click **"Publish"** to apply the rules.

---

## 5. Enable Cloud Storage

1. Go to **Build → Storage**
2. Click **"Get started"**
3. Start in **"Test mode"** for development
4. Select a location (same as your database)
5. Click **"Done"**

Your storage bucket will look like:
```
aegis-messenger-xxxxx.appspot.com
```

---

## 6. Get Configuration Keys

1. Go to **Project Settings** (gear icon at top-left)
2. Scroll down to **"Your apps"**
3. If no web app exists, click **"Add app"** → **Web** (</> icon)
4. Register with nickname `aegis-web` (no hosting needed)
5. Copy the configuration values:

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

## 7. Set Environment Variables

### macOS / Linux

Add to `~/.zshrc` or `~/.bashrc`:

```bash
export FIREBASE_API_KEY="AIzaSyB..."
export FIREBASE_PROJECT_ID="aegis-messenger-xxxxx"
export FIREBASE_DB_URL="https://aegis-messenger-xxxxx-default-rtdb.firebaseio.com"
export FIREBASE_STORAGE_BUCKET="aegis-messenger-xxxxx.appspot.com"
```

Reload:
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

### Verification

```bash
python -c "import os; print(os.environ.get('FIREBASE_API_KEY', 'NOT SET'))"
```

---

## 8. Database Indexing

For efficient user search and message queries, add these indexes:

Go to **Realtime Database → Rules** and ensure these `.indexOn` rules exist:

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

Without indexes, Firebase will log warnings and queries will be slow on large datasets.

---

## 9. Storage Rules

Go to **Storage → Rules** and set:

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

This ensures:
- Only authenticated users can read/write files
- Maximum upload size is 100 MiB (matches `file_manager.MAX_FILE_SIZE`)

---

## 10. Billing & Quotas

### Spark Plan (Free)

| Resource | Limit |
|----------|-------|
| Authentication | 50,000 monthly active users |
| Realtime Database | 1 GB stored, 10 GB/month download |
| Cloud Storage | 5 GB stored, 1 GB/day download |
| Simultaneous connections | 100 |

### Blaze Plan (Pay-as-you-go)

Recommended for production. Enables:
- Unlimited authentication users
- Auto-scaling database and storage
- Cloud Functions (for future features like push notifications)

### Estimated Costs (Blaze)

| 1,000 daily active users | ~Cost/month |
|--------------------------|-------------|
| Authentication | Free |
| Database reads | ~$0.50 |
| Database storage | ~$1.00 |
| Storage (1 GB files/day) | ~$0.30 |
| **Total estimate** | **~$2-5/month** |

> **Tip:** Enable budget alerts in Google Cloud Console to avoid unexpected charges.
