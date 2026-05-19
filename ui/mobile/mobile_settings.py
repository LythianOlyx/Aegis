"""
Aegis – Mobile Settings Screen
==============================
Settings to edit account information: Display Name, Username, Email, Password.
"""

from __future__ import annotations

import threading
from typing import Optional

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen

from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogSupportingText, MDDialogButtonContainer
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
from kivymd.uix.boxlayout import MDBoxLayout

from core.firebase_client import FirebaseClient, FirebaseAuthError, FirebaseDBError

Builder.load_string("""
#:import dp kivy.metrics.dp

<MobileSettingsScreen>:
    name: "settings"
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
                text: "Settings"
                font_style: "Title"
                role: "large"
                theme_text_color: "Custom"
                text_color: 0.000, 0.898, 0.800, 1
                bold: True

            Widget:

        ScrollView:
            MDBoxLayout:
                orientation: "vertical"
                adaptive_height: True
                padding: dp(24)
                spacing: dp(24)

                MDLabel:
                    text: "Account Information"
                    font_style: "Title"
                    role: "medium"
                    theme_text_color: "Custom"
                    text_color: 0.878, 0.969, 0.980, 1

                AegisTextField:
                    id: field_display_name
                    MDTextFieldHintText:
                        text: "Display Name"

                AegisTextField:
                    id: field_username
                    MDTextFieldHintText:
                        text: "Username"

                AegisTextField:
                    id: field_email
                    MDTextFieldHintText:
                        text: "Email"

                AegisTextField:
                    id: field_password
                    password: True
                    MDTextFieldHintText:
                        text: "New Password (Optional)"

                Widget:
                    size_hint_y: None
                    height: dp(16)

                MDButton:
                    style: "filled"
                    theme_bg_color: "Custom"
                    md_bg_color: 0.000, 0.898, 0.800, 1
                    size_hint_x: 1
                    on_release: root.save_settings()

                    MDButtonText:
                        text: "Save Changes"
                        theme_text_color: "Custom"
                        text_color: 0.039, 0.086, 0.157, 1
                        pos_hint: {"center_x": 0.5, "center_y": 0.5}

""")


class MobileSettingsScreen(Screen):
    """Mobile settings screen."""

    firebase = ObjectProperty(None, allownone=True)
    _current_username: str = ""

    def on_enter(self, *args) -> None:
        self._load_data()

    def go_back(self) -> None:
        if self.manager:
            self.manager.current = "chatlist"

    def _load_data(self) -> None:
        if not self.firebase or not self.firebase.local_id:
            return

        def _fetch():
            try:
                ud = self.firebase.db_get(f"users/{self.firebase.local_id}")
                if isinstance(ud, dict):
                    dn = ud.get("display_name", "")
                    un = ud.get("username", "")
                    Clock.schedule_once(lambda dt: self._populate(dn, un, self.firebase.email or ""), 0)
            except Exception:
                pass

        threading.Thread(target=_fetch, daemon=True).start()

    def _populate(self, display_name: str, username: str, email: str) -> None:
        self.ids.field_display_name.text = display_name
        self.ids.field_username.text = username
        self.ids.field_email.text = email
        self._current_username = username

    def save_settings(self) -> None:
        dn = self.ids.field_display_name.text.strip()
        un = self.ids.field_username.text.strip()
        em = self.ids.field_email.text.strip()
        pw = self.ids.field_password.text.strip()

        if not dn or not un or not em:
            self.show_error("Display name, username, and email are required.")
            return

        threading.Thread(target=self._do_save, args=(dn, un, em, pw), daemon=True).start()

    def _do_save(self, dn: str, un: str, em: str, pw: str) -> None:
        try:
            if not self.firebase or not self.firebase.local_id:
                return

            uid = self.firebase.local_id

            # 1. Update Display Name
            self.firebase.update_user_display_name(uid, dn)

            # 2. Update Username
            if un != self._current_username:
                self.firebase.update_username(uid, self._current_username, un)
                self._current_username = un

            # 3. Update Email
            if em != self.firebase.email:
                self.firebase.update_email(em)

            # 4. Update Password
            if pw:
                self.firebase.update_password(pw)
                Clock.schedule_once(lambda dt: setattr(self.ids.field_password, "text", ""), 0)

            Clock.schedule_once(lambda dt: self.show_success("Settings saved successfully."), 0)

        except (FirebaseAuthError, FirebaseDBError) as e:
            Clock.schedule_once(lambda dt: self.show_error(str(e)), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_error(f"Failed to save settings: {e}"), 0)

    def show_error(self, message: str) -> None:
        self._show_dialog("Error", message)

    def show_success(self, message: str) -> None:
        self._show_dialog("Success", message)

    def _show_dialog(self, title: str, text: str) -> None:
        dialog = MDDialog(
            MDDialogHeadlineText(text=title),
            MDDialogSupportingText(text=text),
            MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(text="OK"),
                    style="text",
                    on_release=lambda x: dialog.dismiss()
                ),
                spacing=dp(8)
            )
        )
        dialog.open()

# We need Widget import for dialog
from kivy.uix.widget import Widget
