"""
Aegis – Desktop Main Screen (Split-Pane Layout)
================================================
Left sidebar: Chat list + search + new chat.
Right pane: Active chat room with message input.
"""

from __future__ import annotations

import hashlib
import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import (
    BooleanProperty, ListProperty, NumericProperty,
    ObjectProperty, StringProperty,
)
from kivy.uix.screenmanager import Screen

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText

from ui.shared.widgets import (
    ChatListItem, E2EEMessageBubble, FileMessageBubble,
    UserSearchResult, ACCENT_CYAN, BG_PRIMARY, BG_SURFACE,
    TEXT_PRIMARY, TEXT_SECONDARY, EmojiPicker
)
from core.crypto_engine import (
    decrypt_message, deserialize_public_key, encrypt_message,
)
from core.firebase_client import FirebaseClient

Builder.load_string("""
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp

<DesktopMainScreen>:
    name: "main"
    md_bg_color: 0.039, 0.086, 0.157, 1

    MDBoxLayout:
        orientation: "horizontal"
        md_bg_color: 0.039, 0.086, 0.157, 1

        # ═══ LEFT SIDEBAR ═══════════════════════════════
        MDBoxLayout:
            orientation: "vertical"
            size_hint_x: None
            width: dp(340)
            md_bg_color: 0.053, 0.110, 0.204, 1
            padding: [dp(0), dp(0)]

            # ── Header ──
            MDBoxLayout:
                orientation: "horizontal"
                size_hint_y: None
                height: dp(64)
                padding: [dp(16), dp(10)]
                spacing: dp(8)
                md_bg_color: 0.053, 0.110, 0.204, 1

                Image:
                    source: root.logo_path
                    size_hint: None, None
                    size: dp(36), dp(36)
                    pos_hint: {"center_y": 0.5}
                    allow_stretch: True

                MDLabel:
                    text: "Aegis"
                    font_style: "Title"
                    role: "large"
                    theme_text_color: "Custom"
                    text_color: 0.000, 0.898, 0.800, 1
                    bold: True
                    adaptive_width: True

                Widget:

                MDIconButton:
                    icon: "magnify"
                    theme_icon_color: "Custom"
                    icon_color: 0.502, 0.796, 0.769, 1
                    on_release: root.toggle_search()


                MDIconButton:
                    icon: "cog"
                    theme_icon_color: "Custom"
                    icon_color: 0.502, 0.796, 0.769, 1
                    on_release: root.open_settings()

            # ── Search Bar ──
            ScrollView:
                id: search_box
                size_hint_y: None
                height: dp(0)
                do_scroll_x: False
                do_scroll_y: False

                MDBoxLayout:
                    orientation: "vertical"
                    adaptive_height: True
                    padding: [dp(12), dp(4)]

                    MDTextField:
                        id: search_field
                        mode: "outlined"
                        size_hint_y: None
                        height: dp(60)
                        on_text: root.on_search_text(self.text)
                        on_text_validate: root.on_search_text(self.text)

                        MDTextFieldHintText:
                            text: "Search by name or @username..."

            # ── Search Results ──
            ScrollView:
                id: search_results_scroll
                size_hint_y: None
                height: dp(0)

                MDBoxLayout:
                    id: search_results_container
                    orientation: "vertical"
                    adaptive_height: True
                    spacing: dp(4)
                    padding: [dp(8), dp(4)]

            # ── Chat List ──
            ScrollView:
                MDBoxLayout:
                    id: chat_list_container
                    orientation: "vertical"
                    adaptive_height: True
                    spacing: dp(2)
                    padding: [dp(8), dp(8)]

        # ── Sidebar divider ──
        Widget:
            size_hint_x: None
            width: dp(1)
            canvas:
                Color:
                    rgba: 0.102, 0.200, 0.333, 0.6
                Rectangle:
                    pos: self.pos
                    size: self.size

        # ═══ RIGHT PANE (Chat Room) ═════════════════════
        MDBoxLayout:
            orientation: "vertical"
            md_bg_color: 0.039, 0.086, 0.157, 1

            # ── Chat Header ──
            MDBoxLayout:
                id: chat_header
                orientation: "horizontal"
                size_hint_y: None
                height: dp(64)
                padding: [dp(20), dp(10)]
                spacing: dp(12)
                md_bg_color: 0.053, 0.110, 0.204, 1

                MDLabel:
                    id: header_avatar
                    text: ""
                    halign: "center"
                    valign: "middle"
                    font_style: "Title"
                    role: "medium"
                    theme_text_color: "Custom"
                    text_color: 0.039, 0.086, 0.157, 1
                    size_hint: None, None
                    size: dp(40), dp(40)
                    pos_hint: {"center_y": 0.5}
                    canvas.before:
                        Color:
                            rgba: 0.000, 0.898, 0.800, 1
                        Ellipse:
                            pos: self.pos
                            size: self.size

                MDBoxLayout:
                    orientation: "vertical"
                    spacing: dp(2)
                    padding: [0, dp(6)]

                    MDLabel:
                        id: chat_title
                        text: "Select a chat"
                        font_style: "Title"
                        role: "medium"
                        theme_text_color: "Custom"
                        text_color: 0.878, 0.969, 0.980, 1

                    MDLabel:
                        id: chat_subtitle
                        text: "End-to-End Encrypted"
                        font_style: "Label"
                        role: "medium"
                        theme_text_color: "Custom"
                        text_color: 0.000, 0.898, 0.800, 0.7

                Widget:


            # ── Messages Area ──
            ScrollView:
                id: messages_scroll
                do_scroll_x: False

                MDBoxLayout:
                    id: messages_container
                    orientation: "vertical"
                    adaptive_height: True
                    spacing: dp(8)
                    padding: [dp(16), dp(16)]

            # ── Message Input Bar ──
            MDBoxLayout:
                orientation: "horizontal"
                size_hint_y: None
                height: dp(68)
                padding: [dp(12), dp(10)]
                spacing: dp(10)
                md_bg_color: 0.053, 0.110, 0.204, 1

                MDIconButton:
                    icon: "emoticon-outline"
                    theme_icon_color: "Custom"
                    icon_color: 0.502, 0.796, 0.769, 1
                    pos_hint: {"center_y": 0.5}
                    on_release: root.show_emoji_picker()

                MDTextField:
                    id: message_input
                    mode: "outlined"
                    size_hint_x: 1
                    multiline: False
                    on_text_validate: root.send_text_message()

                    MDTextFieldHintText:
                        text: "Type a message..."

                MDIconButton:
                    icon: "send"
                    style: "filled"
                    theme_bg_color: "Custom"
                    md_bg_color: 0.000, 0.898, 0.800, 1
                    theme_icon_color: "Custom"
                    icon_color: 0.039, 0.086, 0.157, 1
                    pos_hint: {"center_y": 0.5}
                    on_release: root.send_text_message()
""")


class DesktopMainScreen(Screen):
    """Split-pane desktop chat interface."""

    logo_path: str = StringProperty("")
    firebase = ObjectProperty(None, allownone=True)
    current_chat_id: str = StringProperty("")
    _search_visible: bool = BooleanProperty(False)
    _poll_event = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        base = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)
        )))
        self.logo_path = os.path.join(base, "assets", "logo.png")
        self._recipient_keys: Dict[str, Any] = {}
        self._chat_participants: Dict[str, List[str]] = {}

    def on_enter(self, *args) -> None:
        """Load chats when entering the main screen."""
        Animation(opacity=1, duration=0.3).start(self)
        self._load_chats()
        self._start_polling()

    def on_leave(self, *args) -> None:
        self._stop_polling()

    # ──── Search ───────────────────────────────────────
    def toggle_search(self) -> None:
        box = self.ids.search_box
        results = self.ids.search_results_scroll
        self._search_visible = not self._search_visible
        if self._search_visible:
            box.height = dp(68)
            results.height = dp(200)
            self.ids.search_field.focus = True
        else:
            box.height = dp(0)
            results.height = dp(0)
            self.ids.search_results_container.clear_widgets()
            self.ids.search_field.text = ""
            self.ids.search_field.focus = False

    def open_settings(self) -> None:
        if self.manager:
            self.manager.current = "settings"

    def on_search_text(self, text: str) -> None:
        if len(text) < 2:
            return
        if hasattr(self, '_search_timer') and self._search_timer:
            self._search_timer.cancel()
        self._search_timer = Clock.schedule_once(lambda dt: self._start_search_thread(text), 0.5)

    def _start_search_thread(self, text: str) -> None:
        threading.Thread(target=self._search_users, args=(text,), daemon=True).start()

    def _search_users(self, query: str) -> None:
        try:
            if not self.firebase:
                return
            results = self.firebase.search_users(query)
            Clock.schedule_once(lambda dt: self._display_search_results(results), 0)
        except Exception:
            pass

    def _display_search_results(self, results: List[Dict[str, Any]]) -> None:
        container = self.ids.search_results_container
        container.clear_widgets()
        uid = self.firebase.local_id if self.firebase else ""
        for user in results:
            name = user.get("display_name", "Unknown")
            is_me = (user.get("uid") == uid)
            display_name = name + " (You)" if is_me else name
            item = UserSearchResult(
                uid=user.get("uid", ""),
                display_name=display_name,
                email=user.get("email", ""),
                username=user.get("username", ""),
                avatar_letter=name[0].upper() if name else "?",
            )
            item.bind(on_release=lambda instance, target=user.get("uid", ""): self._start_chat_with_user(target))
            container.add_widget(item)

    def _start_chat_with_user(self, target_uid: str) -> None:
        if not self.firebase or not self.firebase.local_id:
            return
        my_uid = self.firebase.local_id
        parts = sorted([my_uid, target_uid])
        chat_id = hashlib.sha256(f"{parts[0]}_{parts[1]}".encode()).hexdigest()[:24]

        threading.Thread(
            target=self._create_or_open_chat,
            args=(chat_id, [my_uid, target_uid]),
            daemon=True,
        ).start()
        self.toggle_search()

    def _create_or_open_chat(self, chat_id: str, participants: List[str]) -> None:
        if not getattr(self, 'firebase', None):
            return
            
        try:
            info = self.firebase.get_chat_info(chat_id)
        except Exception:
            # Expected if chat doesn't exist (permission denied)
            info = None
            
        if not info:
            try:
                self.firebase.create_chat(chat_id, participants, "direct")
            except Exception as e:
                print(f"[Chat] Failed to create chat {chat_id}: {e}")
                
        Clock.schedule_once(lambda dt: self._select_chat(chat_id), 0)
        Clock.schedule_once(lambda dt: self._load_chats(), 0.1)

    # ──── Chat List ────────────────────────────────────
    def _load_chats(self) -> None:
        threading.Thread(target=self._fetch_chats, daemon=True).start()

    def _fetch_chats(self) -> None:
        try:
            if not self.firebase or not self.firebase.local_id:
                return
            chat_ids = self.firebase.get_user_chats(self.firebase.local_id)
            chats_data: List[Dict[str, Any]] = []
            for cid in chat_ids:
                info = self.firebase.get_chat_info(cid)
                if info:
                    info["_id"] = cid
                    chats_data.append(info)
            Clock.schedule_once(lambda dt: self._render_chat_list(chats_data), 0)
        except Exception:
            pass

    def _render_chat_list(self, chats: List[Dict[str, Any]]) -> None:
        container = self.ids.chat_list_container
        container.clear_widgets()
        my_uid = self.firebase.local_id if self.firebase else ""

        for chat in chats:
            cid = chat.get("_id", "")
            participants = chat.get("participants", {})
            self._chat_participants[cid] = list(participants.keys())
            other_uids = [u for u in participants if u != my_uid]
            name = chat.get("name", "")

            if not name and other_uids and self.firebase:
                try:
                    user_data = self.firebase.db_get(f"users/{other_uids[0]}")
                    if isinstance(user_data, dict):
                        name = user_data.get("display_name", "Chat")
                except Exception:
                    name = "Chat"

            name = name or "Chat"
            item = ChatListItem(
                chat_id=cid,
                chat_name=name,
                last_message="Encrypted message",
                time_str="",
                avatar_letter=name[0].upper(),
            )
            item.bind(on_release=lambda instance, target=cid: self._select_chat(target))
            container.add_widget(item)

    # ──── Chat Room ────────────────────────────────────
    def _select_chat(self, chat_id: str) -> None:
        self.current_chat_id = chat_id
        self._current_msg_count = 0
        self.ids.chat_title.text = "Loading..."
        self.ids.messages_container.clear_widgets()
        threading.Thread(
            target=self._load_messages, args=(chat_id,), daemon=True
        ).start()
        self._load_chat_header(chat_id)

    def _load_chat_header(self, chat_id: str) -> None:
        def _fetch():
            try:
                if not self.firebase:
                    return
                info = self.firebase.get_chat_info(chat_id)
                if not info:
                    return
                participants = info.get("participants", {})
                my_uid = self.firebase.local_id or ""
                others = [u for u in participants if u != my_uid]
                name = info.get("name", "")
                if not name and others:
                    ud = self.firebase.db_get(f"users/{others[0]}")
                    if isinstance(ud, dict):
                        name = ud.get("display_name", "Chat")
                name = name or "Chat"
                Clock.schedule_once(lambda dt: self._set_header(name), 0)
            except Exception:
                pass
        threading.Thread(target=_fetch, daemon=True).start()

    def _set_header(self, name: str) -> None:
        self.ids.chat_title.text = name
        self.ids.header_avatar.text = name[0].upper() if name else "?"
        self.ids.chat_subtitle.text = "🔒 End-to-End Encrypted"

    def _load_messages(self, chat_id: str) -> None:
        try:
            if not self.firebase:
                return
            messages = self.firebase.get_messages(chat_id, limit=50)
            Clock.schedule_once(
                lambda dt: self._render_messages(messages, chat_id), 0
            )
        except Exception:
            pass

    def _render_messages(self, messages: List[Dict], chat_id: str) -> None:
        if chat_id != self.current_chat_id:
            return
        container = self.ids.messages_container
        
        current_count = getattr(self, '_current_msg_count', 0)
        if len(messages) == current_count:
            return
            
        if len(messages) < current_count:
            container.clear_widgets()
            current_count = 0
            
        new_msgs = messages[current_count:]
        self._current_msg_count = len(messages)

        from kivy.app import App
        app = App.get_running_app()
        private_key = getattr(app, "private_key", None) if app else None
        my_uid = self.firebase.local_id if self.firebase else ""

        for msg in new_msgs:
            sender = msg.get("sender", "")
            is_sent = sender == my_uid
            ts = msg.get("timestamp", 0)
            time_str = ""
            if isinstance(ts, (int, float)) and ts > 0:
                time_str = datetime.fromtimestamp(ts / 1000).strftime("%H:%M")

            payload = msg.get("payload", {})
            msg_type = msg.get("type", "text")

            text = "[Encrypted]"
            if private_key and isinstance(payload, dict) and "keys" in payload:
                try:
                    if my_uid in payload.get("keys", {}):
                        text = decrypt_message(payload, my_uid, private_key)
                except Exception:
                    text = "[Decryption failed]"

            if msg_type == "file":
                bubble = FileMessageBubble(
                    file_name=text[:40],
                    file_size_str="Encrypted file",
                    timestamp_str=time_str,
                    is_sent=is_sent,
                )
            else:
                bubble = E2EEMessageBubble(
                    message_text=text,
                    timestamp_str=time_str,
                    is_sent=is_sent,
                )
            container.add_widget(bubble)

        if current_count == 0:
            Clock.schedule_once(self._scroll_to_bottom, 0.1)
        else:
            sv = self.ids.messages_scroll
            if sv.scroll_y < 0.05:
                Clock.schedule_once(self._scroll_to_bottom, 0.1)

    def _scroll_to_bottom(self, dt: float) -> None:
        sv = self.ids.messages_scroll
        sv.scroll_y = 0

    # ──── Send Messages ───────────────────────────────
    def send_text_message(self) -> None:
        text = self.ids.message_input.text.strip()
        if not text or not self.current_chat_id:
            return
        self.ids.message_input.text = ""
        threading.Thread(
            target=self._do_send_text, args=(text,), daemon=True
        ).start()

    def _do_send_text(self, text: str) -> None:
        try:
            if not self.firebase or not self.firebase.local_id:
                return
            chat_id = self.current_chat_id
            participants = self._chat_participants.get(chat_id, [])
            pub_keys = {}
            for uid in participants:
                pk_b64 = self.firebase.get_public_key(uid)
                if pk_b64:
                    pub_keys[uid] = deserialize_public_key(pk_b64)
            if not pub_keys:
                return
            payload = encrypt_message(text, pub_keys)
            self.firebase.send_message(
                chat_id, self.firebase.local_id, payload, "text"
            )
            Clock.schedule_once(
                lambda dt: self._load_messages(chat_id), 0.1
            )
        except Exception:
            pass

    def show_emoji_picker(self) -> None:
        picker = EmojiPicker(on_emoji_selected=self._insert_emoji)
        picker.open()

    def _insert_emoji(self, emoji: str) -> None:
        self.ids.message_input.text += emoji

    # ──── Polling ──────────────────────────────────────
    def _start_polling(self) -> None:
        self._poll_event = Clock.schedule_interval(self._poll_messages, 5.0)

    def _stop_polling(self) -> None:
        if self._poll_event:
            self._poll_event.cancel()
            self._poll_event = None

    def _poll_messages(self, dt: float) -> None:
        if self.current_chat_id:
            threading.Thread(
                target=self._load_messages,
                args=(self.current_chat_id,),
                daemon=True,
            ).start()
