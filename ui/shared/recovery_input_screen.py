"""
Aegis – Recovery Input Screen
==============================
Handles entering the 24-word seed phrase after a password reset or on a new device.
Downloads the recovery_blob from Firebase, decrypts the private key, re-encrypts it locally, and logs in.
"""

from __future__ import annotations

import os
import threading
from typing import List

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField

from core.crypto_engine import encrypt_private_key, decrypt_private_key_with_phrase
from core.firebase_client import FirebaseAuthError

Builder.load_string("""
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp

<SkipWarningDialogContent>:
    orientation: "vertical"
    padding: dp(24)
    spacing: dp(24)
    adaptive_height: True
    
    MDLabel:
        text: "Are you sure you want to skip?\\n\\nIf you do this you will lose your message history and create new RSA keys."
        theme_text_color: "Custom"
        text_color: 1.0, 0.322, 0.322, 1
        adaptive_height: True
        font_style: "Body"
        role: "medium"
        
    MDBoxLayout:
        adaptive_height: True
        spacing: dp(16)
        
        Widget:
        
        MDButton:
            style: "text"
            on_release: root.screen._cancel_skip()
            MDButtonText:
                text: "Cancel"
                
        MDButton:
            id: btn_continue
            style: "filled"
            disabled: True
            theme_bg_color: "Custom"
            md_bg_color: 1.0, 0.322, 0.322, 1
            on_release: root.screen._execute_skip()
            MDButtonText:
                id: text_continue
                text: "Continue (10s)"
                text_color: 1, 1, 1, 1

<RecoveryInputScreen>:
    name: "recovery_input"
    md_bg_color: 0.039, 0.086, 0.157, 1

    canvas.before:
        Color:
            rgba: 0.039, 0.086, 0.157, 1
        Rectangle:
            pos: self.pos
            size: self.size

    MDBoxLayout:
        orientation: "vertical"
        padding: [dp(24), dp(40), dp(24), dp(24)]
        spacing: dp(16)

        MDLabel:
            text: "Account Recovery"
            halign: "center"
            font_style: "Headline"
            role: "small"
            theme_text_color: "Custom"
            text_color: 0.000, 0.898, 0.800, 1
            bold: True
            adaptive_height: True

        MDLabel:
            text: "Your local keys are missing or your password changed. Enter your 24-word seed phrase to recover your encrypted messages."
            halign: "center"
            font_style: "Body"
            role: "medium"
            theme_text_color: "Custom"
            text_color: 0.502, 0.796, 0.769, 0.8
            adaptive_height: True

        MDTextField:
            id: field_seed_phrase
            mode: "outlined"
            size_hint_x: 1
            size_hint_y: 1
            multiline: True
            text_color_normal: 0.878, 0.969, 0.980, 1

            MDTextFieldHintText:
                text: "Paste 24-Word Recovery Seed Phrase"

        MDLabel:
            id: status_label
            text: ""
            halign: "center"
            font_style: "Label"
            role: "large"
            theme_text_color: "Custom"
            text_color: 1.0, 0.322, 0.322, 1
            adaptive_height: True

        MDBoxLayout:
            orientation: "horizontal"
            adaptive_height: True
            spacing: dp(16)

            MDButton:
                style: "text"
                size_hint_x: 0.3
                on_release: root.on_back()

                MDButtonText:
                    text: "Cancel"
                    theme_text_color: "Custom"
                    text_color: 0.502, 0.796, 0.769, 0.8

            MDButton:
                style: "filled"
                size_hint_x: 0.7
                theme_bg_color: "Custom"
                md_bg_color: 0.000, 0.898, 0.800, 1
                on_release: root.on_recover()

                MDButtonText:
                    text: "Recover Account"
                    theme_text_color: "Custom"
                    text_color: 0.039, 0.086, 0.157, 1
                    bold: True
                    
            MDButton:
                style: "text"
                size_hint_x: 0.2
                on_release: root.on_skip()

                MDButtonText:
                    text: "Skip"
                    theme_text_color: "Custom"
                    text_color: 1.0, 0.322, 0.322, 0.8
""")

class SkipWarningDialogContent(MDBoxLayout):
    screen = ObjectProperty(None)

class RecoveryInputScreen(Screen):
    firebase = ObjectProperty(None, allownone=True)
    
    # Received from login failure
    pending_uid = StringProperty("")
    pending_password = StringProperty("")
    next_screen = StringProperty("main")

    def on_enter(self, *args):
        self.ids.status_label.text = ""
        self.ids.field_seed_phrase.text = ""

    def on_back(self):
        # Sign out since recovery failed/cancelled
        if self.firebase:
            self.firebase.sign_out()
        self.manager.current = "auth"

    def on_recover(self):
        phrase_text = self.ids.field_seed_phrase.text.strip()
        words = phrase_text.replace("\\n", " ").split()
        
        if len(words) != 24:
            self.ids.status_label.text = f"Expected 24 words, but got {len(words)}."
            self.ids.status_label.text_color = (1.0, 0.322, 0.322, 1)
            return

        self.ids.status_label.text = "Recovering keys from network..."
        self.ids.status_label.text_color = (0.000, 0.898, 0.800, 1)
        
        threading.Thread(target=self._do_recover, args=(words,), daemon=True).start()

    def _do_recover(self, words: List[str]):
        try:
            if not self.firebase:
                raise FirebaseAuthError("Firebase not configured.")
            
            # Fetch recovery blob from firebase
            blob = self.firebase.get_recovery_blob(self.pending_uid)
            if not blob:
                raise ValueError("No recovery backup found for this account on the network.")
                
            # Decrypt private key using seed phrase
            private_key = decrypt_private_key_with_phrase(blob, words)
            
            # Re-encrypt locally with the new password
            encrypted_priv = encrypt_private_key(private_key, self.pending_password)
            
            key_dir = os.path.join(os.path.expanduser("~"), ".aegis", "keys")
            os.makedirs(key_dir, exist_ok=True)
            key_path = os.path.join(key_dir, f"{self.pending_uid}.key")
            with open(key_path, "w") as f:
                f.write(encrypted_priv)
                
            Clock.schedule_once(lambda dt: self._on_success(private_key), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._show_error(str(e)), 0)

    def _on_success(self, private_key):
        from kivy.app import App
        app = App.get_running_app()
        if app:
            app.private_key = private_key
            
        self.ids.status_label.text = "Recovery successful!"
        self.ids.status_label.text_color = (0.000, 0.898, 0.800, 1)
        
        self.manager.current = self.next_screen

    def _show_error(self, msg: str):
        self.ids.status_label.text_color = (1.0, 0.322, 0.322, 1)
        self.ids.status_label.text = msg

    # --- SKIP LOGIC ---

    def on_skip(self):
        self.dialog_content = SkipWarningDialogContent(screen=self)
        self.popup = Popup(
            title="Warning: Data Loss", 
            content=self.dialog_content,
            size_hint=(0.85, None),
            height=dp(280),
            auto_dismiss=False,
            title_color=(1, 0.322, 0.322, 1),
            separator_color=(1, 0.322, 0.322, 1)
        )
        self.popup.open()
        
        self.skip_countdown = 10
        self.skip_event = Clock.schedule_interval(self._update_skip_timer, 1)

    def _cancel_skip(self):
        if hasattr(self, 'skip_event') and self.skip_event:
            self.skip_event.cancel()
        if hasattr(self, 'popup'):
            self.popup.dismiss()

    def _update_skip_timer(self, dt):
        self.skip_countdown -= 1
        btn = self.dialog_content.ids.btn_continue
        txt = self.dialog_content.ids.text_continue
        if self.skip_countdown <= 0:
            txt.text = "Continue"
            btn.disabled = False
            self.skip_event.cancel()
        else:
            txt.text = f"Continue ({self.skip_countdown}s)"

    def _execute_skip(self):
        self.popup.dismiss()
        self.ids.status_label.text = "Generating new keys..."
        self.ids.status_label.text_color = (0.000, 0.898, 0.800, 1)
        threading.Thread(target=self._do_skip_thread, daemon=True).start()

    def _do_skip_thread(self):
        try:
            if not self.firebase:
                raise ValueError("Firebase not configured.")
            
            # Fetch user profile to get email, name, username
            profile = self.firebase.db_get(f"users/{self.pending_uid}")
            if not profile:
                raise ValueError("Could not fetch user profile.")
                
            email = profile.get("email", "")
            name = profile.get("display_name", "")
            username = profile.get("username", "")
            
            from core.crypto_engine import generate_rsa_keypair
            private_key, public_key_b64 = generate_rsa_keypair()
            
            Clock.schedule_once(lambda dt: self._go_to_setup(email, name, username, private_key, public_key_b64), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._show_error(str(e)), 0)

    def _go_to_setup(self, email, name, username, private_key, public_key_b64):
        setup_screen = self.manager.get_screen("recovery_setup")
        setup_screen.firebase = self.firebase
        setup_screen.pending_email = email
        setup_screen.pending_password = self.pending_password
        setup_screen.pending_name = name
        setup_screen.pending_username = username
        setup_screen.private_key = private_key
        setup_screen.public_key_b64 = public_key_b64
        
        self.manager.current = "recovery_setup"
