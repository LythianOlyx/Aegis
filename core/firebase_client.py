"""
Aegis – Firebase REST Client
=============================
Handles Authentication, Realtime Database, and Cloud Storage operations
via Firebase REST APIs.  No heavyweight SDKs – only ``requests``.

Configuration
-------------
Set environment variables or pass a config dict at initialization:
    FIREBASE_API_KEY, FIREBASE_PROJECT_ID, FIREBASE_DB_URL, FIREBASE_STORAGE_BUCKET

All network calls are designed to be invoked from background threads
(via ``threading.Thread`` or Kivy ``Clock.schedule_once``) to avoid UI freezes.
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable, Dict, List, Optional

import requests

# ─────────────────── Default Config ─────────────────────
_DEFAULT_CONFIG: Dict[str, str] = {
    "api_key": "",
    "project_id": "",
    "db_url": "",           # e.g. "https://<project>.firebaseio.com"
    "storage_bucket": "",   # e.g. "<project>.appspot.com"
}


class FirebaseAuthError(Exception):
    """Raised when Firebase authentication fails."""


class FirebaseDBError(Exception):
    """Raised when a Realtime Database operation fails."""


class FirebaseStorageError(Exception):
    """Raised when a Storage upload/download fails."""


class FirebaseClient:
    """Lightweight Firebase REST API wrapper.

    Parameters
    ----------
    config : Dict[str, str]
        Must include ``api_key``, ``project_id``, ``db_url``,
        ``storage_bucket``.
    """

    # ────────── Auth endpoints ──────────
    _SIGN_UP_URL = (
        "https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={key}"
    )
    _SIGN_IN_URL = (
        "https://identitytoolkit.googleapis.com/v1/accounts:"
        "signInWithPassword?key={key}"
    )
    _REFRESH_URL = (
        "https://securetoken.googleapis.com/v1/token?key={key}"
    )
    _USER_DATA_URL = (
        "https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={key}"
    )
    _SEND_OOB_CODE_URL = (
        "https://identitytoolkit.googleapis.com/v1/"
        "accounts:sendOobCode?key={key}"
    )

    def __init__(self, config: Dict[str, str]) -> None:
        self._api_key: str = config["api_key"]
        self._project_id: str = config["project_id"]
        self._db_url: str = config["db_url"].rstrip("/")
        self._storage_bucket: str = config["storage_bucket"]

        # Auth state
        self.id_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.local_id: Optional[str] = None        # Firebase UID
        self.email: Optional[str] = None
        self.display_name: Optional[str] = None
        self._token_expiry: float = 0.0

    # ═══════════════════════════════════════════════════════
    #  AUTHENTICATION
    # ═══════════════════════════════════════════════════════

    def sign_up(
        self,
        email: str,
        password: str,
        display_name: str = "",
    ) -> Dict[str, Any]:
        """Register a new user with email/password.

        Parameters
        ----------
        email : str
        password : str
        display_name : str, optional

        Returns
        -------
        Dict[str, Any]
            Firebase response with ``idToken``, ``localId``, etc.

        Raises
        ------
        FirebaseAuthError
        """
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        }
        url = self._SIGN_UP_URL.format(key=self._api_key)
        resp = requests.post(url, json=payload, timeout=15)
        data: Dict[str, Any] = resp.json()

        if resp.status_code != 200:
            msg = data.get("error", {}).get("message", "Unknown error")
            raise FirebaseAuthError(f"Sign-up failed: {msg}")

        self._cache_auth(data)

        # Set display name if provided
        if display_name:
            self.update_profile(display_name=display_name)

        return data

    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate an existing user with email/password.

        Parameters
        ----------
        email : str
        password : str

        Returns
        -------
        Dict[str, Any]

        Raises
        ------
        FirebaseAuthError
        """
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        }
        url = self._SIGN_IN_URL.format(key=self._api_key)
        resp = requests.post(url, json=payload, timeout=15)
        data: Dict[str, Any] = resp.json()

        if resp.status_code != 200:
            msg = data.get("error", {}).get("message", "Unknown error")
            raise FirebaseAuthError(f"Sign-in failed: {msg}")

        self._cache_auth(data)
        return data

    def update_profile(
        self,
        display_name: Optional[str] = None,
        photo_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update the authenticated user's profile.

        Parameters
        ----------
        display_name : str, optional
        photo_url : str, optional

        Returns
        -------
        Dict[str, Any]
        """
        self._ensure_token()
        url = (
            "https://identitytoolkit.googleapis.com/v1/"
            f"accounts:update?key={self._api_key}"
        )
        payload: Dict[str, Any] = {"idToken": self.id_token}
        if display_name is not None:
            payload["displayName"] = display_name
        if photo_url is not None:
            payload["photoUrl"] = photo_url

        resp = requests.post(url, json=payload, timeout=15)
        data = resp.json()
        if resp.status_code != 200:
            raise FirebaseAuthError(
                data.get("error", {}).get("message", "Profile update failed")
            )
        if display_name:
            self.display_name = display_name
        return data

    def update_email(self, new_email: str) -> Dict[str, Any]:
        """Update the authenticated user's email address.

        Parameters
        ----------
        new_email : str

        Returns
        -------
        Dict[str, Any]
        """
        self._ensure_token()
        url = (
            "https://identitytoolkit.googleapis.com/v1/"
            f"accounts:update?key={self._api_key}"
        )
        payload = {
            "idToken": self.id_token,
            "email": new_email,
            "returnSecureToken": True,
        }
        resp = requests.post(url, json=payload, timeout=15)
        data = resp.json()
        if resp.status_code != 200:
            raise FirebaseAuthError(
                data.get("error", {}).get("message", "Email update failed")
            )
        self.email = new_email
        self._cache_auth(data) # updating the token
        return data

    def update_password(self, new_password: str) -> Dict[str, Any]:
        """Update the authenticated user's password.

        Parameters
        ----------
        new_password : str

        Returns
        -------
        Dict[str, Any]
        """
        self._ensure_token()
        url = (
            "https://identitytoolkit.googleapis.com/v1/"
            f"accounts:update?key={self._api_key}"
        )
        payload = {
            "idToken": self.id_token,
            "password": new_password,
            "returnSecureToken": True,
        }
        resp = requests.post(url, json=payload, timeout=15)
        data = resp.json()
        if resp.status_code != 200:
            raise FirebaseAuthError(
                data.get("error", {}).get("message", "Password update failed")
            )
        self._cache_auth(data) # updating the token
        return data

    def refresh_id_token(self) -> None:
        """Exchange the refresh token for a new ID token."""
        if not self.refresh_token:
            raise FirebaseAuthError("No refresh token available.")
        url = self._REFRESH_URL.format(key=self._api_key)
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        resp = requests.post(url, data=payload, timeout=15)
        data = resp.json()
        if resp.status_code != 200:
            raise FirebaseAuthError("Token refresh failed.")
        self.id_token = data.get("id_token")
        self.refresh_token = data.get("refresh_token")
        expires_in = int(data.get("expires_in", 3600))
        self._token_expiry = time.time() + expires_in - 60

    def get_user_data(self) -> Dict[str, Any]:
        """Fetch the current user's profile from Firebase Auth.

        Returns
        -------
        Dict[str, Any]
        """
        self._ensure_token()
        url = self._USER_DATA_URL.format(key=self._api_key)
        resp = requests.post(
            url, json={"idToken": self.id_token}, timeout=15
        )
        data = resp.json()
        users = data.get("users", [])
        return users[0] if users else {}

    def send_email_verification(self) -> Dict[str, Any]:
        """Send an email verification link to the authenticated user.

        Uses Firebase's built-in email verification system.
        The verification link has a fixed 3-day expiry set by Firebase
        and cannot be customized.

        Returns
        -------
        Dict[str, Any]
            Firebase response containing ``email`` and ``kind``.

        Raises
        ------
        FirebaseAuthError
        """
        self._ensure_token()
        url = self._SEND_OOB_CODE_URL.format(key=self._api_key)
        payload = {
            "requestType": "VERIFY_EMAIL",
            "idToken": self.id_token,
        }
        resp = requests.post(url, json=payload, timeout=15)
        data: Dict[str, Any] = resp.json()
        if resp.status_code != 200:
            msg = data.get("error", {}).get(
                "message", "Failed to send verification email"
            )
            raise FirebaseAuthError(f"Email verification failed: {msg}")
        return data

    def send_password_reset_email(self, email: str) -> Dict[str, Any]:
        """Send a password reset email to the specified address.

        Parameters
        ----------
        email : str
            The user's registered email address.

        Returns
        -------
        Dict[str, Any]
            Firebase response containing ``email``.

        Raises
        ------
        FirebaseAuthError
        """
        url = self._SEND_OOB_CODE_URL.format(key=self._api_key)
        payload = {
            "requestType": "PASSWORD_RESET",
            "email": email,
        }
        resp = requests.post(url, json=payload, timeout=15)
        data: Dict[str, Any] = resp.json()
        if resp.status_code != 200:
            msg = data.get("error", {}).get(
                "message", "Failed to send password reset email"
            )
            raise FirebaseAuthError(f"Password reset failed: {msg}")
        return data

    def is_email_verified(self) -> bool:
        """Check whether the current user's email has been verified.

        Returns
        -------
        bool
            ``True`` if the email is verified.
        """
        user_data = self.get_user_data()
        return bool(user_data.get("emailVerified", False))

    def sign_out(self) -> None:
        """Clear local auth state."""
        self.id_token = None
        self.refresh_token = None
        self.local_id = None
        self.email = None
        self.display_name = None
        self._token_expiry = 0.0

    # ═══════════════════════════════════════════════════════
    #  REALTIME DATABASE – CRUD
    # ═══════════════════════════════════════════════════════

    def db_get(self, path: str) -> Any:
        """Read data at *path*.

        Parameters
        ----------
        path : str
            Firebase path, e.g. ``"users/abc123"``.

        Returns
        -------
        Any
            Parsed JSON (dict, list, str, int, None).
        """
        self._ensure_token()
        url = f"{self._db_url}/{path}.json?auth={self.id_token}"
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            raise FirebaseDBError(f"DB GET {path} failed: {resp.text}")
        return resp.json()

    def db_put(self, path: str, data: Any) -> Any:
        """Write (overwrite) data at *path*.

        Parameters
        ----------
        path : str
        data : Any
            JSON-serializable value.

        Returns
        -------
        Any
            Written data echoed back.
        """
        self._ensure_token()
        url = f"{self._db_url}/{path}.json?auth={self.id_token}"
        resp = requests.put(url, json=data, timeout=15)
        if resp.status_code != 200:
            raise FirebaseDBError(f"DB PUT {path} failed: {resp.text}")
        return resp.json()

    def db_patch(self, path: str, data: Dict[str, Any]) -> Any:
        """Merge data at *path* (partial update).

        Parameters
        ----------
        path : str
        data : Dict[str, Any]
        """
        self._ensure_token()
        url = f"{self._db_url}/{path}.json?auth={self.id_token}"
        resp = requests.patch(url, json=data, timeout=15)
        if resp.status_code != 200:
            raise FirebaseDBError(f"DB PATCH {path} failed: {resp.text}")
        return resp.json()

    def db_post(self, path: str, data: Any) -> Dict[str, str]:
        """Push data with an auto-generated key.

        Parameters
        ----------
        path : str
        data : Any

        Returns
        -------
        Dict[str, str]
            ``{"name": "<generated_key>"}``
        """
        self._ensure_token()
        url = f"{self._db_url}/{path}.json?auth={self.id_token}"
        resp = requests.post(url, json=data, timeout=15)
        if resp.status_code != 200:
            raise FirebaseDBError(f"DB POST {path} failed: {resp.text}")
        return resp.json()

    def db_delete(self, path: str) -> None:
        """Delete data at *path*."""
        self._ensure_token()
        url = f"{self._db_url}/{path}.json?auth={self.id_token}"
        resp = requests.delete(url, timeout=15)
        if resp.status_code != 200:
            raise FirebaseDBError(f"DB DELETE {path} failed: {resp.text}")

    def db_query(
        self,
        path: str,
        order_by: str,
        equal_to: Optional[Any] = None,
        start_at: Optional[Any] = None,
        end_at: Optional[Any] = None,
        limit_to_first: Optional[int] = None,
        limit_to_last: Optional[int] = None,
    ) -> Any:
        """Perform an indexed query on the Realtime Database.

        Parameters
        ----------
        path : str
        order_by : str
            Field name, ``"$key"``, or ``"$value"``.
        equal_to, start_at, end_at : Any, optional
        limit_to_first, limit_to_last : int, optional

        Returns
        -------
        Any
        """
        self._ensure_token()
        params: Dict[str, str] = {
            "auth": self.id_token,
            "orderBy": json.dumps(order_by),
        }
        if equal_to is not None:
            params["equalTo"] = json.dumps(equal_to)
        if start_at is not None:
            params["startAt"] = json.dumps(start_at)
        if end_at is not None:
            params["endAt"] = json.dumps(end_at)
        if limit_to_first is not None:
            params["limitToFirst"] = str(limit_to_first)
        if limit_to_last is not None:
            params["limitToLast"] = str(limit_to_last)

        url = f"{self._db_url}/{path}.json"
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            raise FirebaseDBError(f"DB QUERY {path} failed: {resp.text}")
        return resp.json()

    # ═══════════════════════════════════════════════════════
    #  CLOUD STORAGE
    # ═══════════════════════════════════════════════════════

    def storage_upload(
        self,
        remote_path: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload bytes to Firebase Cloud Storage.

        Parameters
        ----------
        remote_path : str
            Object path inside the bucket.
        data : bytes
        content_type : str

        Returns
        -------
        str
            Public download URL (with token).
        """
        self._ensure_token()
        url = (
            f"https://firebasestorage.googleapis.com/v0/b/"
            f"{self._storage_bucket}/o?uploadType=media"
            f"&name={requests.utils.quote(remote_path, safe='')}"
        )
        headers = {
            "Authorization": f"Bearer {self.id_token}",
            "Content-Type": content_type,
        }
        resp = requests.post(url, headers=headers, data=data, timeout=60)
        if resp.status_code != 200:
            raise FirebaseStorageError(
                f"Storage upload failed: {resp.text}"
            )
        result = resp.json()
        token = result.get("downloadTokens", "")
        download_url = (
            f"https://firebasestorage.googleapis.com/v0/b/"
            f"{self._storage_bucket}/o/"
            f"{requests.utils.quote(remote_path, safe='')}?alt=media"
            f"&token={token}"
        )
        return download_url

    def storage_download(self, download_url: str) -> bytes:
        """Download bytes from a Firebase Storage URL.

        Parameters
        ----------
        download_url : str
            Full download URL (with token) from ``storage_upload``.

        Returns
        -------
        bytes
        """
        resp = requests.get(download_url, timeout=60)
        if resp.status_code != 200:
            raise FirebaseStorageError(
                f"Storage download failed: {resp.status_code}"
            )
        return resp.content

    # ═══════════════════════════════════════════════════════
    #  USER SEARCH & CONTACTS
    # ═══════════════════════════════════════════════════════

    def search_users(self, query: str) -> List[Dict[str, Any]]:
        """Search users by display name or username.

        Returns a combined list of matching records.
        """
        # Strip @ if present to treat it as a raw search term
        if query.startswith("@"):
            query = query[1:]
            
        results_dict: Dict[str, Dict[str, Any]] = {}

        # 1. Search by username (lowercase)
        username_query = query.lower()
        try:
            raw_usernames = self.db_query(
                path="users",
                order_by="username",
                start_at=username_query,
                end_at=username_query + "\uf8ff",
                limit_to_first=20,
            )
            if raw_usernames:
                for uid, info in raw_usernames.items():
                    if isinstance(info, dict):
                        results_dict[uid] = {"uid": uid, **info}
        except Exception as e:
            print(f"[Search] Username index query failed: {e}")

        # 2. Search by display_name (exact case)
        try:
            raw_display = self.db_query(
                path="users",
                order_by="display_name",
                start_at=query,
                end_at=query + "\uf8ff",
                limit_to_first=20,
            )
            if raw_display:
                for uid, info in raw_display.items():
                    if isinstance(info, dict):
                        results_dict[uid] = {"uid": uid, **info}
        except Exception as e:
            print(f"[Search] Display name index query failed: {e}")
            
        # 3. Search by display_name (Title Case, useful for uncapitalized input)
        title_query = query.title()
        if title_query != query:
            try:
                raw_title = self.db_query(
                    path="users",
                    order_by="display_name",
                    start_at=title_query,
                    end_at=title_query + "\uf8ff",
                    limit_to_first=20,
                )
                if raw_title:
                    for uid, info in raw_title.items():
                        if isinstance(info, dict):
                            results_dict[uid] = {"uid": uid, **info}
            except Exception as e:
                print(f"[Search] Title case index query failed: {e}")

        # 4. FALLBACK: If results are empty (e.g. missing Firebase indexes), do client-side filter
        if not results_dict:
            try:
                all_users = self.db_query(
                    path="users",
                    order_by="$key",
                    limit_to_first=100
                )
                if all_users:
                    q_low = query.lower()
                    for uid, info in all_users.items():
                        if isinstance(info, dict):
                            uname = info.get("username", "").lower()
                            dname = info.get("display_name", "").lower()
                            # True case-insensitive substring search!
                            if q_low in uname or q_low in dname:
                                results_dict[uid] = {"uid": uid, **info}
            except Exception as e:
                print(f"[Search] Fallback query failed: {e}")

        return list(results_dict.values())

    def check_username_available(self, username: str) -> bool:
        """Check whether a username is available.

        Looks up the ``/usernames/<username>`` index node.

        Parameters
        ----------
        username : str
            Username to check (without ``@`` prefix).

        Returns
        -------
        bool
            ``True`` if the username is not taken.
        """
        url = f"{self._db_url}/usernames/{username}.json"
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            raise FirebaseDBError(f"DB GET usernames/{username} failed: {resp.text}. Make sure your Firebase Realtime Database rules allow public read access to /usernames.")
        return resp.json() is None

    def update_username(self, uid: str, old_username: str, new_username: str) -> None:
        """Update the user's username. Validates availability and updates indices.
        
        Parameters
        ----------
        uid : str
        old_username : str
        new_username : str
        """
        if not self.check_username_available(new_username):
            raise FirebaseDBError("Username is already taken.")
            
        # Write to usernames index and delete old
        self.db_put(f"usernames/{new_username}", uid)
        if old_username:
            try:
                self.db_delete(f"usernames/{old_username}")
            except Exception:
                pass
                
        # Update user profile
        self.db_patch(f"users/{uid}", {"username": new_username})

    def update_user_display_name(self, uid: str, new_name: str) -> None:
        """Update the user's display name in the realtime database."""
        self.db_patch(f"users/{uid}", {"display_name": new_name})

    def register_user_profile(
        self,
        uid: str,
        email: str,
        display_name: str,
        public_key_b64: str,
        username: str = "",
        recovery_blob: str = "",
    ) -> None:
        """Write the user's public profile to the Realtime Database.

        Parameters
        ----------
        uid : str
        email : str
        display_name : str
        public_key_b64 : str
            Base64-encoded PEM RSA public key.
        username : str, optional
            Unique username (without ``@`` prefix).
        recovery_blob : str, optional
            Encrypted private key blob for seed phrase recovery.
        """
        profile: Dict[str, Any] = {
            "email": email,
            "display_name": display_name,
            "public_key": public_key_b64,
            "created_at": int(time.time() * 1000),
        }
        if username:
            profile["username"] = username
        if recovery_blob:
            profile["recovery_blob"] = recovery_blob
            
        self.db_put(f"users/{uid}", profile)

        # Write username → uid index for uniqueness enforcement
        if username:
            self.db_put(f"usernames/{username}", uid)

    def get_public_key(self, uid: str) -> Optional[str]:
        """Retrieve a user's public key from the database.

        Parameters
        ----------
        uid : str

        Returns
        -------
        Optional[str]
            Base64-encoded PEM public key, or None.
        """
        data = self.db_get(f"users/{uid}/public_key")
        return data if isinstance(data, str) else None

    def get_recovery_blob(self, uid: str) -> Optional[str]:
        """Retrieve a user's recovery blob (encrypted private key) from the database."""
        data = self.db_get(f"users/{uid}/recovery_blob")
        return data if isinstance(data, str) else None

    # ═══════════════════════════════════════════════════════
    #  MESSAGING
    # ═══════════════════════════════════════════════════════

    def send_message(
        self,
        chat_id: str,
        sender_uid: str,
        encrypted_payload: Dict[str, Any],
        msg_type: str = "text",
    ) -> str:
        """Push an encrypted message to a chat.

        Parameters
        ----------
        chat_id : str
            Chat room identifier.
        sender_uid : str
        encrypted_payload : Dict[str, Any]
            Output of ``crypto_engine.encrypt_message``.
        msg_type : str
            ``"text"`` or ``"file"``.

        Returns
        -------
        str
            Firebase-generated message key.
        """
        message_data = {
            "sender": sender_uid,
            "type": msg_type,
            "payload": encrypted_payload,
            "timestamp": {".sv": "timestamp"},
        }
        result = self.db_post(f"messages/{chat_id}", message_data)
        return result.get("name", "")

    def get_messages(
        self,
        chat_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Fetch the latest messages from a chat.

        Parameters
        ----------
        chat_id : str
        limit : int

        Returns
        -------
        List[Dict[str, Any]]
            Ordered list of message dicts.
        """
        raw = self.db_query(
            path=f"messages/{chat_id}",
            order_by="timestamp",
            limit_to_last=limit,
        )
        if not raw:
            return []
        messages = []
        for key, val in raw.items():
            if isinstance(val, dict):
                val["_key"] = key
                messages.append(val)
        messages.sort(key=lambda m: m.get("timestamp", 0))
        return messages

    def create_chat(
        self,
        chat_id: str,
        participants: List[str],
        chat_type: str = "direct",
        group_name: str = "",
    ) -> None:
        """Create a chat room entry in the database.

        Parameters
        ----------
        chat_id : str
        participants : List[str]
            List of UIDs.
        chat_type : str
            ``"direct"`` or ``"group"``.
        group_name : str
            Name for group chats.
        """
        chat_data: Dict[str, Any] = {
            "type": chat_type,
            "participants": {uid: True for uid in participants},
            "created_at": {".sv": "timestamp"},
        }
        if group_name:
            chat_data["name"] = group_name

        self.db_put(f"chats/{chat_id}", chat_data)

        # Index chat for each participant
        for uid in participants:
            self.db_put(f"user_chats/{uid}/{chat_id}", True)

    def get_user_chats(self, uid: str) -> List[str]:
        """List chat IDs for a user.

        Parameters
        ----------
        uid : str

        Returns
        -------
        List[str]
            Chat IDs.
        """
        data = self.db_get(f"user_chats/{uid}")
        if not data or not isinstance(data, dict):
            return []
        return list(data.keys())

    def get_chat_info(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve metadata for a chat.

        Parameters
        ----------
        chat_id : str

        Returns
        -------
        Optional[Dict[str, Any]]
        """
        data = self.db_get(f"chats/{chat_id}")
        return data if isinstance(data, dict) else None

    # ═══════════════════════════════════════════════════════
    #  INTERNAL HELPERS
    # ═══════════════════════════════════════════════════════

    def _cache_auth(self, data: Dict[str, Any]) -> None:
        """Cache tokens and user info from a sign-in/sign-up response."""
        self.id_token = data.get("idToken")
        self.refresh_token = data.get("refreshToken")
        self.local_id = data.get("localId")
        self.email = data.get("email")
        self.display_name = data.get("displayName", "")
        expires_in = int(data.get("expiresIn", 3600))
        self._token_expiry = time.time() + expires_in - 60

    def _ensure_token(self) -> None:
        """Refresh the ID token if expired."""
        if not self.id_token:
            raise FirebaseAuthError("Not authenticated.")
        if time.time() >= self._token_expiry:
            self.refresh_id_token()
