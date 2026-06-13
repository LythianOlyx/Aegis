"""
Aegis – Desktop Entry Point
============================
Launches the Desktop UI build with split-pane layout.
Only imports Desktop-specific modules. Mobile UI is excluded.
"""

from __future__ import annotations

import os
import sys

# Ensure project root is on sys.path
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from kivy.config import Config

# Desktop window defaults
Config.set("graphics", "width", "1280")
Config.set("graphics", "height", "800")
Config.set("graphics", "minimum_width", "900")
Config.set("graphics", "minimum_height", "600")
Config.set("graphics", "resizable", "1")

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, FadeTransition

from kivymd.app import MDApp

# ── Desktop-only imports (no mobile modules) ──
from ui.shared.widgets import SplashScreen
from ui.shared.email_verify_screen import EmailVerifyScreen
from ui.shared.recovery_setup_screen import RecoverySetupScreen
from ui.shared.recovery_verify_screen import RecoveryVerifyScreen
from ui.shared.recovery_input_screen import RecoveryInputScreen
from ui.desktop.desktop_auth import DesktopAuthScreen
from ui.desktop.desktop_main import DesktopMainScreen
from ui.desktop.desktop_settings import DesktopSettingsScreen
from core.firebase_client import FirebaseClient


class AegisDesktopApp(MDApp):
    """Aegis Desktop Application (KivyMD MDApp)."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.private_key = None  # RSA private key (set after auth)
        self.firebase: FirebaseClient = FirebaseClient({
            "api_key": "AIzaSyDk8fV0Kqo3JXNcXd_4a3EYBgk3DWtalUc",
            "project_id": "aegis-b6f5a",
            "db_url": "https://aegis-b6f5a-default-rtdb.asia-southeast1.firebasedatabase.app",
            "storage_bucket": "aegis-b6f5a.firebasestorage.app",
        })

    def build(self) -> ScreenManager:
        # ── Theme ──
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"

        # ── Window ──
        self.title = "Aegis – Secure Messenger"
        logo = os.path.join(_ROOT, "assets", "logo.png")
        if os.path.exists(logo):
            self.icon = logo
            Window.set_icon(logo)

        # ── Load global theme KV ──
        theme_kv = os.path.join(_ROOT, "ui", "theme.kv")
        if os.path.exists(theme_kv):
            Builder.load_file(theme_kv)

        # ── Screen Manager ──
        sm = ScreenManager(transition=FadeTransition(duration=0.35))

        splash = SplashScreen(name="splash", next_screen="auth")
        auth = DesktopAuthScreen(name="auth")
        auth.firebase = self.firebase
        verify = EmailVerifyScreen(name="verify")
        verify.firebase = self.firebase
        verify.next_screen = "main"
        rec_setup = RecoverySetupScreen(name="recovery_setup")
        rec_verify = RecoveryVerifyScreen(name="recovery_verify")
        rec_input = RecoveryInputScreen(name="recovery_input")
        main = DesktopMainScreen(name="main")
        main.firebase = self.firebase

        sm.add_widget(splash)
        sm.add_widget(auth)
        sm.add_widget(verify)
        sm.add_widget(rec_setup)
        sm.add_widget(rec_verify)
        sm.add_widget(rec_input)
        sm.add_widget(main)

        settings = DesktopSettingsScreen(name="settings")
        settings.firebase = self.firebase
        sm.add_widget(settings)

        return sm


def main() -> None:
    """Launch Aegis Desktop."""
    AegisDesktopApp().run()


if __name__ == "__main__":
    main()
