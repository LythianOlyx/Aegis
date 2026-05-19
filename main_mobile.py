"""
Aegis – Mobile Entry Point
============================
Launches the Mobile UI build with stacked screens.
Only imports Mobile-specific modules. Desktop UI is excluded.
"""

from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, SlideTransition

from kivymd.app import MDApp

# ── Mobile-only imports (no desktop modules) ──
from ui.shared.widgets import SplashScreen
from ui.shared.email_verify_screen import EmailVerifyScreen
from ui.shared.recovery_setup_screen import RecoverySetupScreen
from ui.shared.recovery_verify_screen import RecoveryVerifyScreen
from ui.shared.recovery_input_screen import RecoveryInputScreen
from ui.mobile.mobile_auth import MobileAuthScreen
from ui.mobile.mobile_chatlist import MobileChatListScreen
from ui.mobile.mobile_chatroom import MobileChatRoomScreen
from ui.mobile.mobile_settings import MobileSettingsScreen
from core.firebase_client import FirebaseClient


class AegisMobileApp(MDApp):
    """Aegis Mobile Application (KivyMD MDApp)."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.private_key = None
        self.active_chat_id: str = ""
        self.firebase: FirebaseClient = FirebaseClient({
            "api_key": "AIzaSyCC11W5hX7rTwna38sTx9RHV_gX9Z8rQOI",
            "project_id": "aegis-14d99",
            "db_url": "https://aegis-14d99-default-rtdb.firebaseio.com",
            "storage_bucket": "aegis-14d99.firebasestorage.app",
        })

    def build(self) -> ScreenManager:
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        self.title = "Aegis"

        logo = os.path.join(_ROOT, "assets", "logo.png")
        if os.path.exists(logo):
            self.icon = logo

        theme_kv = os.path.join(_ROOT, "ui", "theme.kv")
        if os.path.exists(theme_kv):
            Builder.load_file(theme_kv)

        sm = ScreenManager(transition=SlideTransition(duration=0.3))

        splash = SplashScreen(name="splash", next_screen="auth")
        auth = MobileAuthScreen(name="auth")
        auth.firebase = self.firebase
        verify = EmailVerifyScreen(name="verify")
        verify.firebase = self.firebase
        verify.next_screen = "chatlist"
        rec_setup = RecoverySetupScreen(name="recovery_setup")
        rec_verify = RecoveryVerifyScreen(name="recovery_verify")
        rec_input = RecoveryInputScreen(name="recovery_input")
        chatlist = MobileChatListScreen(name="chatlist")
        chatlist.firebase = self.firebase
        chatroom = MobileChatRoomScreen(name="chatroom")
        chatroom.firebase = self.firebase

        sm.add_widget(splash)
        sm.add_widget(auth)
        sm.add_widget(verify)
        sm.add_widget(rec_setup)
        sm.add_widget(rec_verify)
        sm.add_widget(rec_input)
        sm.add_widget(chatlist)
        sm.add_widget(chatroom)

        settings = MobileSettingsScreen(name="settings")
        settings.firebase = self.firebase
        sm.add_widget(settings)

        return sm


def main() -> None:
    """Launch Aegis Mobile."""
    AegisMobileApp().run()


if __name__ == "__main__":
    main()
