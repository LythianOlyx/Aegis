"""
Aegis – Mobile Chat Room Screen
================================
Full-screen chat view with E2EE message display and input.
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Dict, List

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.screenmanager import Screen

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

from ui.shared.widgets import E2EEMessageBubble, FileMessageBubble, EmojiPicker
from core.crypto_engine import (
    decrypt_message, deserialize_public_key, encrypt_message,
)
from core.firebase_client import FirebaseClient

Builder.load_string("""
#:import dp kivy.metrics.dp

<MobileChatRoomScreen>:
    name: "chatroom"
    md_bg_color: 0.039, 0.086, 0.157, 1

    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.039, 0.086, 0.157, 1

        # ── Header ──
        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: dp(56)
            padding: [dp(8), dp(8)]
            spacing: dp(8)
            md_bg_color: 0.053, 0.110, 0.204, 1

            MDIconButton:
                icon: "arrow-left"
                theme_icon_color: "Custom"
                icon_color: 0.878, 0.969, 0.980, 1
                on_release: root.go_back()

            MDLabel:
                id: avatar_label
                text: "?"
                halign: "center"
                valign: "middle"
                font_style: "Title"
                role: "medium"
                theme_text_color: "Custom"
                text_color: 0.039, 0.086, 0.157, 1
                size_hint: None, None
                size: dp(36), dp(36)
                pos_hint: {"center_y": 0.5}
                canvas.before:
                    Color:
                        rgba: 0.000, 0.898, 0.800, 1
                    Ellipse:
                        pos: self.pos
                        size: self.size

            MDBoxLayout:
                orientation: "vertical"
                spacing: dp(1)
                padding: [0, dp(6)]

                MDLabel:
                    id: header_name
                    text: "Chat"
                    font_style: "Title"
                    role: "medium"
                    theme_text_color: "Custom"
                    text_color: 0.878, 0.969, 0.980, 1

                MDLabel:
                    text: "🔒 E2E Encrypted"
                    font_style: "Label"
                    role: "small"
                    theme_text_color: "Custom"
                    text_color: 0.000, 0.898, 0.800, 0.7

            Widget:

        # ── Messages ──
        ScrollView:
            id: msg_scroll
            do_scroll_x: False

            MDBoxLayout:
                id: msg_container
                orientation: "vertical"
                adaptive_height: True
                spacing: dp(6)
                padding: [dp(10), dp(10)]

        # ── Input ──
        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: dp(60)
            padding: [dp(8), dp(8)]
            spacing: dp(8)
            md_bg_color: 0.053, 0.110, 0.204, 1

            MDIconButton:
                icon: "emoticon-outline"
                theme_icon_color: "Custom"
                icon_color: 0.502, 0.796, 0.769, 1
                on_release: root.show_emoji_picker()

            MDTextField:
                id: msg_input
                mode: "outlined"
                size_hint_x: 1
                multiline: False
                on_text_validate: root.send_message()
                MDTextFieldHintText:
                    text: "Message..."

            MDIconButton:
                icon: "send"
                style: "filled"
                theme_bg_color: "Custom"
                md_bg_color: 0.000, 0.898, 0.800, 1
                theme_icon_color: "Custom"
                icon_color: 0.039, 0.086, 0.157, 1
                on_release: root.send_message()
""")


class MobileChatRoomScreen(Screen):
    """Mobile full-screen chat room with E2EE."""

    firebase = ObjectProperty(None, allownone=True)
    _poll = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._chat_id: str = ""
        self._participants: List[str] = []

    def on_enter(self, *args) -> None:
        from kivy.app import App
        app = App.get_running_app()
        self._chat_id = getattr(app, "active_chat_id", "") if app else ""
        self._current_msg_count = 0
        if self._chat_id:
            self._load_header()
            self._load_msgs()
            self._poll = Clock.schedule_interval(self._poll_msgs, 5.0)

    def on_leave(self, *args) -> None:
        if self._poll:
            self._poll.cancel()
            self._poll = None

    def go_back(self) -> None:
        if self.manager:
            self.manager.current = "chatlist"

    def _load_header(self) -> None:
        def _f():
            try:
                if not self.firebase:
                    return
                info = self.firebase.get_chat_info(self._chat_id)
                if not info:
                    return
                ps = info.get("participants", {})
                self._participants = list(ps.keys())
                my = self.firebase.local_id or ""
                others = [u for u in ps if u != my]
                name = info.get("name", "")
                if not name and others:
                    ud = self.firebase.db_get(f"users/{others[0]}")
                    if isinstance(ud, dict):
                        name = ud.get("display_name", "Chat")
                name = name or "Chat"
                Clock.schedule_once(lambda dt: self._set_hdr(name), 0)
            except Exception:
                pass
        threading.Thread(target=_f, daemon=True).start()

    def _set_hdr(self, name: str) -> None:
        self.ids.header_name.text = name
        self.ids.avatar_label.text = name[0].upper() if name else "?"

    def _load_msgs(self) -> None:
        threading.Thread(target=self._fetch_msgs, daemon=True).start()

    def _fetch_msgs(self) -> None:
        try:
            if not self.firebase:
                return
            msgs = self.firebase.get_messages(self._chat_id, 50)
            Clock.schedule_once(lambda dt: self._render(msgs), 0)
        except Exception:
            pass

    def _render(self, msgs: List[Dict]) -> None:
        c = self.ids.msg_container
        
        current_count = getattr(self, '_current_msg_count', 0)
        if len(msgs) == current_count:
            return
            
        if len(msgs) < current_count:
            c.clear_widgets()
            current_count = 0
            
        new_msgs = msgs[current_count:]
        self._current_msg_count = len(msgs)

        from kivy.app import App
        app = App.get_running_app()
        pk = getattr(app, "private_key", None) if app else None
        my = self.firebase.local_id if self.firebase else ""

        for m in new_msgs:
            sender = m.get("sender", "")
            sent = sender == my
            ts = m.get("timestamp", 0)
            tstr = datetime.fromtimestamp(ts / 1000).strftime("%H:%M") if isinstance(ts, (int, float)) and ts > 0 else ""
            payload = m.get("payload", {})
            msg_type = m.get("type", "text")
            text = "[Encrypted]"
            if pk and isinstance(payload, dict) and "keys" in payload:
                try:
                    if my in payload.get("keys", {}):
                        text = decrypt_message(payload, my, pk)
                except Exception:
                    text = "[Decryption failed]"
            
            if msg_type == "file":
                c.add_widget(FileMessageBubble(
                    file_name=text[:40],
                    file_size_str="Encrypted file",
                    timestamp_str=tstr,
                    is_sent=sent,
                ))
            else:
                c.add_widget(E2EEMessageBubble(
                    message_text=text, timestamp_str=tstr, is_sent=sent,
                ))

        if current_count == 0:
            Clock.schedule_once(lambda dt: setattr(self.ids.msg_scroll, "scroll_y", 0), 0.1)
        else:
            sv = self.ids.msg_scroll
            if sv.scroll_y < 0.05:
                Clock.schedule_once(lambda dt: setattr(self.ids.msg_scroll, "scroll_y", 0), 0.1)

    def send_message(self) -> None:
        text = self.ids.msg_input.text.strip()
        if not text or not self._chat_id:
            return
        self.ids.msg_input.text = ""
        threading.Thread(target=self._do_send, args=(text,), daemon=True).start()

    def _do_send(self, text: str) -> None:
        try:
            if not self.firebase or not self.firebase.local_id:
                return
            pks = {}
            for uid in self._participants:
                b64 = self.firebase.get_public_key(uid)
                if b64:
                    pks[uid] = deserialize_public_key(b64)
            if not pks:
                return
            payload = encrypt_message(text, pks)
            self.firebase.send_message(self._chat_id, self.firebase.local_id, payload, "text")
            Clock.schedule_once(lambda dt: self._load_msgs(), 0.1)
        except Exception:
            pass

    def show_emoji_picker(self) -> None:
        picker = EmojiPicker(on_emoji_selected=self._insert_emoji)
        picker.open()

    def _insert_emoji(self, emoji: str) -> None:
        """Insert emoji at the current cursor position in the message input."""
        ti = self.ids.msg_input
        try:
            idx = ti.cursor_index()
            ti.text = ti.text[:idx] + emoji + ti.text[idx:]
            ti.cursor = ti.get_cursor_from_index(idx + len(emoji))
        except Exception:
            ti.text += emoji
        # Restore focus so the user can keep typing
        Clock.schedule_once(lambda dt: setattr(ti, 'focus', True), 0.05)

    def _poll_msgs(self, dt: float) -> None:
        if self._chat_id:
            self._load_msgs()
