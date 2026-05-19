"""
Aegis – Recovery Verify Screen
==============================
Asks the user to verify 6 random words from their 24-word seed phrase.
Upon success, completes the registration and saves the keys.
"""

from __future__ import annotations

import os
import random
import threading
from typing import List

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivy.uix.screenmanager import Screen

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText

from core.crypto_engine import encrypt_private_key, encrypt_private_key_with_phrase

Builder.load_string("""
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp

<RecoveryVerifyScreen>:
    name: "recovery_verify"
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
            text: "Verify Seed Phrase"
            halign: "center"
            font_style: "Headline"
            role: "small"
            theme_text_color: "Custom"
            text_color: 0.000, 0.898, 0.800, 1
            bold: True
            adaptive_height: True

        MDLabel:
            text: "To ensure you have saved your phrase, please enter the requested words below."
            halign: "center"
            font_style: "Body"
            role: "medium"
            theme_text_color: "Custom"
            text_color: 0.502, 0.796, 0.769, 0.8
            adaptive_height: True

        ScrollView:
            MDBoxLayout:
                id: inputs_grid
                orientation: "vertical"
                adaptive_height: True
                spacing: dp(12)
                padding: [0, dp(10)]

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
                    text: "Back"
                    theme_text_color: "Custom"
                    text_color: 0.502, 0.796, 0.769, 0.8

            MDButton:
                style: "filled"
                size_hint_x: 0.7
                theme_bg_color: "Custom"
                md_bg_color: 0.000, 0.898, 0.800, 1
                on_release: root.on_verify()

                MDButtonText:
                    text: "Verify & Finish"
                    theme_text_color: "Custom"
                    text_color: 0.039, 0.086, 0.157, 1
                    bold: True
""")

class RecoveryVerifyScreen(Screen):
    firebase = ObjectProperty(None, allownone=True)
    recovery_phrase = ListProperty([])
    
    # Registration data
    pending_email = StringProperty("")
    pending_password = StringProperty("")
    pending_name = StringProperty("")
    pending_username = StringProperty("")
    private_key = ObjectProperty(None, allownone=True)
    public_key_b64 = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.indices_to_verify = []
        self.text_fields = []

    def on_enter(self, *args):
        self.ids.status_label.text = ""
        self.setup_inputs()

    def setup_inputs(self):
        self.ids.inputs_grid.clear_widgets()
        self.text_fields.clear()
        
        # Pick 6 random indices from 0 to 23
        self.indices_to_verify = sorted(random.sample(range(24), 6))
        
        for i in self.indices_to_verify:
            tf = MDTextField(mode="outlined", size_hint_x=1)
            tf.add_widget(MDTextFieldHintText(text=f"Word #{i+1}"))
            self.ids.inputs_grid.add_widget(tf)
            self.text_fields.append((i, tf))

    def on_back(self):
        self.manager.current = "recovery_setup"

    def on_verify(self):
        # Validate inputs
        for idx, tf in self.text_fields:
            entered_word = tf.text.strip().lower()
            expected_word = self.recovery_phrase[idx].lower()
            if entered_word != expected_word:
                self.ids.status_label.text = f"Word #{idx+1} is incorrect."
                return
                
        self.ids.status_label.text = "Verification successful! Finishing setup..."
        self.ids.status_label.text_color = (0.000, 0.898, 0.800, 1)
        
        # Run final registration in background
        threading.Thread(target=self._do_finish_registration, daemon=True).start()

    def _do_finish_registration(self):
        try:
            uid = self.firebase.local_id or ""
            
            # 1. Encrypt private key with user password
            encrypted_priv_password = encrypt_private_key(self.private_key, self.pending_password)
            
            # 2. Encrypt private key with recovery phrase
            recovery_blob = encrypt_private_key_with_phrase(self.private_key, list(self.recovery_phrase))
            
            # 3. Store public profile and recovery blob in Firebase DB
            self.firebase.register_user_profile(
                uid=uid,
                email=self.pending_email,
                display_name=self.pending_name,
                public_key_b64=self.public_key_b64,
                username=self.pending_username,
                recovery_blob=recovery_blob
            )
            
            # 4. Store encrypted private key locally
            key_dir = os.path.join(os.path.expanduser("~"), ".aegis", "keys")
            os.makedirs(key_dir, exist_ok=True)
            key_path = os.path.join(key_dir, f"{uid}.key")
            with open(key_path, "w") as f:
                f.write(encrypted_priv_password)
                
            Clock.schedule_once(lambda dt: self._on_success(), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt, err=str(e): self._show_error(err), 0)

    def _on_success(self):
        from kivy.app import App
        app = App.get_running_app()
        if app:
            app.private_key = self.private_key

        # Clear memory
        self.pending_password = ""
        self.recovery_phrase = []
        
        # Navigate to main app
        # Since this is shared between desktop/mobile, check if chatlist or main exists
        if self.manager.has_screen("chatlist"):
            self.manager.current = "chatlist"
        else:
            self.manager.current = "main"

    def _show_error(self, msg: str):
        self.ids.status_label.text_color = (1.0, 0.322, 0.322, 1)
        self.ids.status_label.text = msg
