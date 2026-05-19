"""
Aegis – Mobile Chat List Screen
================================
Displays all chats with search and new-chat functionality.
"""

from __future__ import annotations

import hashlib
import os
import threading
from typing import Any, Dict, List

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.screenmanager import Screen

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText

from ui.shared.widgets import ChatListItem, UserSearchResult
from core.firebase_client import FirebaseClient

Builder.load_string("""
#:import dp kivy.metrics.dp

<MobileChatListScreen>:
    name: "chatlist"
    md_bg_color: 0.039, 0.086, 0.157, 1

    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.039, 0.086, 0.157, 1

        # ── Top Bar ──
        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: dp(56)
            padding: [dp(16), dp(8)]
            spacing: dp(10)
            md_bg_color: 0.053, 0.110, 0.204, 1

            Image:
                source: root.logo_path
                size_hint: None, None
                size: dp(32), dp(32)
                pos_hint: {"center_y": 0.5}
                allow_stretch: True

            MDLabel:
                text: "Aegis"
                font_style: "Title"
                role: "large"
                theme_text_color: "Custom"
                text_color: 0.000, 0.898, 0.800, 1
                bold: True

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

        # ── Search ──
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
                    height: dp(56)
                    on_text: root.on_search(self.text)
                    on_text_validate: root.on_search(self.text)
                    MDTextFieldHintText:
                        text: "Search by name or @username..."

        ScrollView:
            id: search_scroll
            size_hint_y: None
            height: dp(0)
            MDBoxLayout:
                id: search_container
                orientation: "vertical"
                adaptive_height: True
                spacing: dp(4)
                padding: [dp(8), dp(4)]

        # ── Chat List ──
        ScrollView:
            MDBoxLayout:
                id: chat_container
                orientation: "vertical"
                adaptive_height: True
                spacing: dp(2)
                padding: [dp(8), dp(8)]
""")


class MobileChatListScreen(Screen):
    """Mobile chat list with search overlay."""

    logo_path: str = StringProperty("")
    firebase = ObjectProperty(None, allownone=True)
    _search_open: bool = False

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        base = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)
        )))
        self.logo_path = os.path.join(base, "assets", "logo.png")

    def on_enter(self, *args) -> None:
        self._load_chats()

    def toggle_search(self) -> None:
        self._search_open = not self._search_open
        box = self.ids.search_box
        sc = self.ids.search_scroll
        if self._search_open:
            box.height = dp(68)
            sc.height = dp(180)
            self.ids.search_field.focus = True
        else:
            box.height = dp(0)
            sc.height = dp(0)
            self.ids.search_container.clear_widgets()
            self.ids.search_field.text = ""
            self.ids.search_field.focus = False

    def open_settings(self) -> None:
        if self.manager:
            self.manager.current = "settings"

    def on_search(self, text: str) -> None:
        if len(text) < 2:
            return
        if hasattr(self, '_search_timer') and self._search_timer:
            self._search_timer.cancel()
        self._search_timer = Clock.schedule_once(lambda dt: self._start_search_thread(text), 0.5)

    def _start_search_thread(self, text: str) -> None:
        threading.Thread(target=self._search, args=(text,), daemon=True).start()

    def _search(self, q: str) -> None:
        try:
            if not self.firebase:
                return
            results = self.firebase.search_users(q)
            Clock.schedule_once(lambda dt: self._show_results(results), 0)
        except Exception:
            pass

    def _show_results(self, results: List[Dict[str, Any]]) -> None:
        c = self.ids.search_container
        c.clear_widgets()
        uid = self.firebase.local_id if self.firebase else ""
        for u in results:
            n = u.get("display_name", "?")
            is_me = (u.get("uid") == uid)
            display_name = n + " (You)" if is_me else n
            item = UserSearchResult(
                uid=u.get("uid", ""),
                display_name=display_name,
                email=u.get("email", ""),
                username=u.get("username", ""),
                avatar_letter=n[0].upper() if n else "?",
            )
            item.bind(on_release=lambda instance, target=u.get("uid", ""): self._start_chat(target))
            c.add_widget(item)

    def _start_chat(self, target: str) -> None:
        if not self.firebase or not self.firebase.local_id:
            return
        my = self.firebase.local_id
        parts = sorted([my, target])
        cid = hashlib.sha256(f"{parts[0]}_{parts[1]}".encode()).hexdigest()[:24]
        threading.Thread(target=self._open_chat, args=(cid, [my, target]), daemon=True).start()
        if self._search_open:
            self.toggle_search()

    def _open_chat(self, cid: str, parts: List[str]) -> None:
        if not getattr(self, 'firebase', None):
            return
            
        try:
            info = self.firebase.get_chat_info(cid)
        except Exception:
            info = None
            
        if not info:
            try:
                self.firebase.create_chat(cid, parts, "direct")
            except Exception as e:
                print(f"[Chat] Failed to create chat {cid}: {e}")
                
        Clock.schedule_once(lambda dt: self._go_chat(cid), 0)

    def _go_chat(self, cid: str) -> None:
        from kivy.app import App
        app = App.get_running_app()
        if app:
            app.active_chat_id = cid
        if self.manager:
            self.manager.current = "chatroom"

    def _load_chats(self) -> None:
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self) -> None:
        try:
            if not self.firebase or not self.firebase.local_id:
                return
            ids = self.firebase.get_user_chats(self.firebase.local_id)
            data = []
            for cid in ids:
                info = self.firebase.get_chat_info(cid)
                if info:
                    info["_id"] = cid
                    data.append(info)
            Clock.schedule_once(lambda dt: self._render(data), 0)
        except Exception:
            pass

    def _render(self, chats: List[Dict]) -> None:
        c = self.ids.chat_container
        c.clear_widgets()
        my = self.firebase.local_id if self.firebase else ""
        for ch in chats:
            cid = ch.get("_id", "")
            ps = ch.get("participants", {})
            others = [u for u in ps if u != my]
            name = ch.get("name", "")
            if not name and others and self.firebase:
                try:
                    ud = self.firebase.db_get(f"users/{others[0]}")
                    if isinstance(ud, dict):
                        name = ud.get("display_name", "Chat")
                except Exception:
                    name = "Chat"
            name = name or "Chat"
            item = ChatListItem(
                chat_id=cid,
                chat_name=name,
                last_message="Encrypted message",
                time_str="",
                avatar_letter=name[0].upper() if name else "?",
            )
            item.bind(on_release=lambda instance, target=cid: self._go_chat(target))
            c.add_widget(item)
