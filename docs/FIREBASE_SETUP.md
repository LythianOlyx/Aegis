# Aegis – Firebase Setup Guide

> **Version:** 1.1.0  
> **Last Updated:** 2026-06-13  

---

## Table of Contents

- [1. Create Firebase Project](#1-create-firebase-project)
- [2. Enable Authentication](#2-enable-authentication)
- [3. Set Up Realtime Database](#3-set-up-realtime-database)
- [4. Configure Security Rules](#4-configure-security-rules)
- [5. Get Configuration Keys](#5-get-configuration-keys)
- [6. Configure the App](#6-configure-the-app)
- [7. Database Indexing](#7-database-indexing)
- [8. Billing & Quotas](#8-billing--quotas)

---

## 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Create a project"**
3. Enter project name (e.g., `aegis-messenger`)
4. Enable or disable Google Analytics (optional)
5. Click **"Create project"** and wait for provisioning

---

## 2. Enable Authentication

1. In the Firebase Console, go to **Build → Authentication**
2. Click **"Get started"**
3. Go to the **"Sign-in method"** tab
4. Enable **"Email/Password"** provider
5. Click **"Save"**

### Optional: Set Password Requirements

- Go to **Authentication → Settings → Password policy**
- Set minimum length to 8 characters
- Enable: uppercase, lowercase, numeric, special character

---

## 3. Set Up Realtime Database

1. Go to **Build → Realtime Database**
2. Click **"Create Database"**
3. Select a region closest to your users  
   > For Indonesia/Southeast Asia: choose `asia-southeast1`
4. Start in **"Test mode"** for development
5. Click **"Enable"**

Your database URL will look like:
```
https://<project-id>-default-rtdb.asia-southeast1.firebasedatabase.app
```

> ☁️ **Cloud Storage is NOT required.** Aegis only supports text and emoji messages — no file uploads.

---

## 4. Configure Security Rules

Go to **Realtime Database → Rules** and replace with the following. This is the **complete, production-ready ruleset** including indexes:

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

Click **"Publish"** to apply.

### Rules Explanation

| Path | Read | Write | Purpose |
|------|------|-------|---------|
| `/usernames/$username` | Public | Owner or if new | Check username availability & reservation |
| `/users/$uid` | Authenticated users | Owner only | Public profiles (name, public key) |
| `/chats/$chatId` | Chat participants | Authenticated users | Chat metadata |
| `/messages/$chatId` | Chat participants | Chat participants | E2EE text/emoji messages |
| `/user_chats/$uid` | Owner only | Authenticated users | Chat index per user |

---

## 5. Get Configuration Keys

1. Go to **Project Settings** (gear icon at top-left)
2. Scroll down to **"Your apps"**
3. Click **"Add app"** → **Web** (`</>` icon) if no app exists
4. Register with nickname `aegis-web` (no hosting needed)
5. Copy the values you need:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSy...",            // ← needed
  projectId: "your-project-id",   // ← needed
  databaseURL: "https://...",     // ← needed
  storageBucket: "...",           // ← NOT needed (no file uploads)
  authDomain: "...",              // ← NOT needed
  messagingSenderId: "...",       // ← NOT needed
  appId: "...",                   // ← NOT needed
};
```

Only `apiKey`, `projectId`, and `databaseURL` are required by Aegis.

---

## 6. Configure the App

Open `main_desktop.py` and `main_mobile.py` and update the `FirebaseClient` config dict:

```python
self.firebase = FirebaseClient({
    "api_key":        "AIzaSyDk8fV0Kqo3JXNcXd_4a3EYBgk3DWtalUc",
    "project_id":     "aegis-b6f5a",
    "db_url":         "https://aegis-b6f5a-default-rtdb.asia-southeast1.firebasedatabase.app",
    "storage_bucket": "",   # Not used — leave empty
})
```

Replace these values with your own project's credentials.

---

## 7. Database Indexing

The security rules in step 4 already include all required `.indexOn` directives:

| Index | Path | Purpose |
|-------|------|---------|
| `display_name` | `/users` | User search by display name |
| `username` | `/users` | User search by @username |
| `timestamp` | `/messages/$chatId` | Chronological message ordering |

Without these indexes, Firebase will log warnings and queries will be slow on large datasets.

---

## 8. Billing & Quotas

### Spark Plan (Free)

| Resource | Limit |
|----------|-------|
| Authentication | 50,000 monthly active users |
| Realtime Database | 1 GB stored, 10 GB/month download |
| Simultaneous connections | 100 |

> Since Aegis does **not** use Cloud Storage, no storage costs apply.

### Blaze Plan (Pay-as-you-go)

Recommended for production. Enables:
- Unlimited authentication users
- Auto-scaling database
- Cloud Functions (for future features like push notifications)

### Estimated Costs (Blaze)

| 1,000 daily active users | ~Cost/month |
|--------------------------|-------------|
| Authentication | Free |
| Database reads | ~$0.50 |
| Database storage | ~$1.00 |
| **Total estimate** | **~$1-2/month** |

> **Tip:** Enable budget alerts in Google Cloud Console to avoid unexpected charges.
