"""
Aegis – Mobile Authentication Screen
=====================================
Modern full-screen login/register for Mobile builds.
Features a hero logo section with glow effects, gradient background,
animated form card, and smooth transitions between login/register modes.
"""

from __future__ import annotations

import os
import re
import threading
from typing import Optional

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.screenmanager import Screen

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText

from core.crypto_engine import decrypt_private_key
from core.firebase_client import FirebaseClient, FirebaseAuthError

Builder.load_string("""
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp
#:import Animation kivy.animation.Animation

<MobileAuthScreen>:
    name: "auth"
    md_bg_color: 0.039, 0.086, 0.157, 1

    # Background canvas effects
    canvas.before:
        # Base
        Color:
            rgba: 0.039, 0.086, 0.157, 1
        Rectangle:
            pos: self.pos
            size: self.size
        # Top radial glow (cyan)
        Color:
            rgba: 0.000, 0.898, 0.800, 0.06
        Ellipse:
            pos: self.center_x - dp(200), self.top - dp(300)
            size: dp(400), dp(400)
        # Bottom-left glow (green)
        Color:
            rgba: 0.000, 1.000, 0.639, 0.03
        Ellipse:
            pos: self.x - dp(80), self.y - dp(80)
            size: dp(300), dp(300)

    ScrollView:
        do_scroll_x: False
        bar_width: 0

        MDBoxLayout:
            orientation: "vertical"
            adaptive_height: True
            padding: [dp(28), dp(24), dp(28), dp(20)]
            spacing: dp(0)
            md_bg_color: 0, 0, 0, 0

            Widget:
                size_hint_y: None
                height: dp(28)

            # ═══════════════════════════════════════════════
            #  HERO SECTION – Logo + Branding
            # ═══════════════════════════════════════════════
            FloatLayout:
                size_hint: None, None
                size: dp(110), dp(110)
                pos_hint: {"center_x": 0.5}

                # Glow aura
                Widget:
                    id: hero_glow
                    size_hint: None, None
                    size: dp(140), dp(140)
                    pos_hint: {"center_x": 0.5, "center_y": 0.5}
                    opacity: 0
                    canvas:
                        Color:
                            rgba: 0.000, 0.898, 0.800, 0.12
                        Ellipse:
                            pos: self.x, self.y
                            size: self.size

                # Logo with rounded corners
                Widget:
                    id: hero_logo
                    size_hint: None, None
                    size: dp(90), dp(90)
                    pos_hint: {"center_x": 0.5, "center_y": 0.5}
                    opacity: 0
                    canvas.before:
                        StencilPush
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(20)]
                        StencilUse
                    canvas:
                        Color:
                            rgba: 1, 1, 1, 1
                        Rectangle:
                            pos: self.pos
                            size: self.size
                            source: root.logo_path
                    canvas.after:
                        StencilUnUse
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(20)]
                        StencilPop

                # Subtle border
                Widget:
                    size_hint: None, None
                    size: dp(94), dp(94)
                    pos_hint: {"center_x": 0.5, "center_y": 0.5}
                    canvas:
                        Color:
                            rgba: 0.000, 0.898, 0.800, 0.25
                        Line:
                            rounded_rectangle: self.x, self.y, self.width, self.height, dp(21)
                            width: dp(1.2)

            Widget:
                size_hint_y: None
                height: dp(16)

            # ── App title ──
            MDLabel:
                id: hero_title
                text: "A E G I S"
                halign: "center"
                font_style: "Headline"
                role: "medium"
                theme_text_color: "Custom"
                text_color: 0.000, 0.898, 0.800, 1
                opacity: 0
                bold: True
                adaptive_height: True

            Widget:
                size_hint_y: None
                height: dp(4)

            MDLabel:
                id: hero_subtitle
                text: "Secure Messaging"
                halign: "center"
                font_style: "Body"
                role: "medium"
                theme_text_color: "Custom"
                text_color: 0.502, 0.796, 0.769, 0.8
                opacity: 0
                adaptive_height: True

            Widget:
                size_hint_y: None
                height: dp(24)

            # ═══════════════════════════════════════════════
            #  AUTH FORM CARD
            # ═══════════════════════════════════════════════
            MDBoxLayout:
                id: auth_card
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: [dp(22), dp(24), dp(22), dp(20)]
                spacing: dp(12)
                opacity: 0

                # Card background
                canvas.before:
                    Color:
                        rgba: 0.067, 0.133, 0.251, 0.75
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(22)]
                    # Card top accent line
                    Color:
                        rgba: 0.000, 0.898, 0.800, 0.25
                    RoundedRectangle:
                        pos: self.x + dp(36), self.top - dp(1.5)
                        size: self.width - dp(72), dp(1.5)
                        radius: [dp(1)]

                # ── Form Header ──
                MDLabel:
                    id: auth_title
                    text: "Welcome Back"
                    halign: "center"
                    font_style: "Title"
                    role: "large"
                    theme_text_color: "Custom"
                    text_color: 0.878, 0.969, 0.980, 1
                    bold: True
                    adaptive_height: True

                MDLabel:
                    id: auth_description
                    text: "Sign in to your encrypted world"
                    halign: "center"
                    font_style: "Body"
                    role: "small"
                    theme_text_color: "Custom"
                    text_color: 0.502, 0.796, 0.769, 0.7
                    adaptive_height: True

                Widget:
                    size_hint_y: None
                    height: dp(6)

                # ── Display Name (Register only) ──
                MDTextField:
                    id: field_name
                    mode: "outlined"
                    opacity: 0
                    disabled: True
                    size_hint_y: None
                    height: dp(0)
                    MDTextFieldHintText:
                        text: "Display Name"

                # ── Username (Register only) ──
                MDTextField:
                    id: field_username
                    mode: "outlined"
                    opacity: 0
                    disabled: True
                    size_hint_y: None
                    height: dp(0)
                    MDTextFieldHintText:
                        text: "@username"

                # ── Email ──
                MDTextField:
                    id: field_email
                    mode: "outlined"
                    MDTextFieldHintText:
                        text: "Email Address"

                # ── Password ──
                MDTextField:
                    id: field_password
                    mode: "outlined"
                    size_hint_y: None
                    height: dp(56)
                    password: True
                    MDTextFieldHintText:
                        text: "Password"

                # ── Forgot Password Button ──
                MDBoxLayout:
                    id: forgot_password_box
                    orientation: "horizontal"
                    adaptive_height: True
                    size_hint_y: None
                    height: dp(32)

                    Widget:

                    MDButton:
                        id: btn_forgot_password
                        style: "text"
                        on_release: root.toggle_reset_mode()
                        theme_width: "Custom"
                        size_hint_x: None
                        width: dp(140)
                        
                        MDButtonText:
                            text: "Forgot Password?"
                            theme_text_color: "Custom"
                            text_color: 0.000, 0.898, 0.800, 0.8
                            font_size: sp(12)

                Widget:
                    size_hint_y: None
                    height: dp(4)

                # ── Primary Action Button ──
                MDButton:
                    id: btn_primary
                    style: "filled"
                    theme_bg_color: "Custom"
                    md_bg_color: 0.000, 0.898, 0.800, 1
                    size_hint_x: 1
                    on_release: root.on_primary_action()

                    MDButtonText:
                        id: btn_primary_text
                        text: "Sign In"
                        theme_text_color: "Custom"
                        text_color: 0.039, 0.086, 0.157, 1
                        bold: True
                        font_size: sp(15)

                # ── Divider ──
                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: dp(18)
                    spacing: dp(10)
                    padding: [dp(2), dp(4)]

                    Widget:
                        canvas:
                            Color:
                                rgba: 0.102, 0.200, 0.333, 0.5
                            Rectangle:
                                pos: self.x, self.center_y
                                size: self.width, dp(1)

                    MDLabel:
                        text: "or"
                        halign: "center"
                        font_style: "Body"
                        role: "small"
                        theme_text_color: "Custom"
                        text_color: 0.502, 0.796, 0.769, 0.4
                        size_hint_x: None
                        width: dp(28)

                    Widget:
                        canvas:
                            Color:
                                rgba: 0.102, 0.200, 0.333, 0.5
                            Rectangle:
                                pos: self.x, self.center_y
                                size: self.width, dp(1)

                # ── Toggle Button ──
                MDButton:
                    style: "outlined"
                    size_hint_x: 1
                    theme_line_color: "Custom"
                    line_color: 0.000, 0.898, 0.800, 0.25
                    on_release: root.toggle_mode()
                    MDButtonText:
                        id: btn_toggle_text
                        text: "Create a new account"
                        theme_text_color: "Custom"
                        text_color: 0.000, 0.898, 0.800, 0.85
                        font_size: sp(13)

                # ── Status Label ──
                MDLabel:
                    id: status_label
                    text: ""
                    halign: "center"
                    font_style: "Label"
                    role: "large"
                    theme_text_color: "Custom"
                    text_color: 1.0, 0.322, 0.322, 1
                    adaptive_height: True

            Widget:
                size_hint_y: None
                height: dp(20)

            # ── Footer ──
            MDLabel:
                id: footer_label
                text: "🔒  Protected by end-to-end encryption"
                halign: "center"
                font_style: "Label"
                role: "small"
                theme_text_color: "Custom"
                text_color: 0.502, 0.796, 0.769, 0.3
                adaptive_height: True
                opacity: 0

            Widget:
                size_hint_y: None
                height: dp(12)
""")


class MobileAuthScreen(Screen):
    """Mobile login/registration screen with modern design.

    Features:
    - Hero section with glowing logo and brand
    - Frosted glass-style form card
    - Smooth staggered entry animations
    - Animated mode switching (login/register)
    """

    logo_path: str = StringProperty("")
    firebase = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._is_register: bool = False
        self._is_reset_mode: bool = False
        base = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)
        )))
        self.logo_path = os.path.join(base, "assets", "logo.png")

    def on_enter(self, *args) -> None:
        """Animate screen elements on entry."""
        hero_glow = self.ids.hero_glow
        hero_logo = self.ids.hero_logo
        hero_title = self.ids.hero_title
        hero_subtitle = self.ids.hero_subtitle
        auth_card = self.ids.auth_card
        footer = self.ids.footer_label

        # Reset
        for w in [hero_glow, hero_logo, hero_title, hero_subtitle,
                  auth_card, footer]:
            w.opacity = 0

        # Staggered reveal
        Animation(opacity=1, duration=0.4, t="out_cubic").start(hero_glow)
        Clock.schedule_once(
            lambda dt: Animation(opacity=1, duration=0.5, t="out_back").start(hero_logo), 0.1
        )
        Clock.schedule_once(
            lambda dt: Animation(opacity=1, duration=0.4, t="out_cubic").start(hero_title), 0.3
        )
        Clock.schedule_once(
            lambda dt: Animation(opacity=1, duration=0.4, t="out_cubic").start(hero_subtitle), 0.45
        )
        Clock.schedule_once(
            lambda dt: Animation(opacity=1, duration=0.5, t="out_cubic").start(auth_card), 0.55
        )
        Clock.schedule_once(
            lambda dt: Animation(opacity=1, duration=0.4, t="out_cubic").start(footer), 0.8
        )

    def toggle_mode(self) -> None:
        """Switch between Login and Register modes with animation."""
        if self._is_reset_mode:
            self.toggle_reset_mode()
            return
            
        self._is_register = not self._is_register
        fn = self.ids.field_name
        fu = self.ids.field_username
        self.ids.status_label.text = ""
        forgot_box = self.ids.forgot_password_box

        if self._is_register:
            self.ids.auth_title.text = "Create Account"
            self.ids.auth_description.text = "Set up your secure identity"
            self.ids.btn_primary_text.text = "Create Account"
            self.ids.btn_toggle_text.text = "Already have an account? Sign In"
            fn.disabled = False
            Animation(opacity=1, height=dp(56), d=0.3, t="out_cubic").start(fn)
            fu.disabled = False
            Animation(opacity=1, height=dp(56), d=0.3, t="out_cubic").start(fu)
            Animation(opacity=0, height=dp(0), d=0.3, t="out_cubic").start(forgot_box)
        else:
            self.ids.auth_title.text = "Welcome Back"
            self.ids.auth_description.text = "Sign in to your encrypted world"
            self.ids.btn_primary_text.text = "Sign In"
            self.ids.btn_toggle_text.text = "Create a new account"
            fn.disabled = True
            Animation(opacity=0, height=dp(0), d=0.3, t="out_cubic").start(fn)
            fu.disabled = True
            Animation(opacity=0, height=dp(0), d=0.3, t="out_cubic").start(fu)
            Animation(opacity=1, height=dp(32), d=0.3, t="out_cubic").start(forgot_box)

    def toggle_reset_mode(self) -> None:
        """Switch to Password Reset mode."""
        self._is_reset_mode = not self._is_reset_mode
        self.ids.status_label.text = ""
        fn = self.ids.field_name
        fu = self.ids.field_username
        pwd = self.ids.field_password
        forgot_box = self.ids.forgot_password_box

        if self._is_reset_mode:
            self._is_register = False
            self.ids.auth_title.text = "Reset Password"
            self.ids.auth_description.text = "WARNING: Resetting your password will result in the loss of all previous E2EE messages.\nProceed only if necessary."
            self.ids.auth_description.text_color = (1.0, 0.322, 0.322, 1)
            self.ids.btn_primary_text.text = "Send Reset Link"
            self.ids.btn_toggle_text.text = "Back to Sign In"
            
            pwd.disabled = True
            Animation(opacity=0, height=dp(0), d=0.3, t="out_cubic").start(pwd)
            Animation(opacity=0, height=dp(0), d=0.3, t="out_cubic").start(forgot_box)
            
            fn.disabled = True
            fu.disabled = True
            fn.opacity = 0
            fn.height = 0
            fu.opacity = 0
            fu.height = 0
        else:
            self.ids.auth_title.text = "Welcome Back"
            self.ids.auth_description.text = "Sign in to your encrypted world"
            self.ids.auth_description.text_color = (0.502, 0.796, 0.769, 0.7)
            self.ids.btn_primary_text.text = "Sign In"
            self.ids.btn_toggle_text.text = "Create a new account"
            
            pwd.disabled = False
            Animation(opacity=1, height=dp(56), d=0.3, t="out_cubic").start(pwd)
            Animation(opacity=1, height=dp(32), d=0.3, t="out_cubic").start(forgot_box)

    def on_primary_action(self) -> None:
        """Handle Sign In, Register, or Reset Password button press."""
        email = self.ids.field_email.text.strip()
        password = self.ids.field_password.text.strip()
        status = self.ids.status_label
        
        if not email:
            status.text = "Please enter your email address."
            return

        if self._is_reset_mode:
            status.text = "Sending reset link..."
            status.text_color = (0, 0.898, 0.8, 1)
            threading.Thread(target=self._do_reset_password, args=(email,), daemon=True).start()
            return

        if not password:
            status.text = "Please fill in all fields."
            return
        if self._is_register:
            name = self.ids.field_name.text.strip()
            if not name:
                status.text = "Please enter a display name."
                return
            # Validate username
            raw_username = self.ids.field_username.text.strip()
            username = raw_username.lstrip("@").lower()
            if not username:
                status.text = "Please enter a username."
                return
            if len(username) < 3 or len(username) > 20:
                status.text = "Username must be 3–20 characters."
                return
            if not re.match(r'^[a-z0-9_.]+$', username):
                status.text = "Username: only lowercase, numbers, _ and ."
                return
            status.text = "Creating account..."
            status.text_color = (0, 0.898, 0.8, 1)
            threading.Thread(target=self._do_register, args=(email, password, name, username), daemon=True).start()
        else:
            status.text = "Signing in..."
            status.text_color = (0, 0.898, 0.8, 1)
            threading.Thread(target=self._do_sign_in, args=(email, password), daemon=True).start()

    def _do_reset_password(self, email: str) -> None:
        """Send password reset email via Firebase."""
        try:
            if not self.firebase:
                raise FirebaseAuthError("Firebase not configured.")
            self.firebase.send_password_reset_email(email)
            Clock.schedule_once(
                lambda dt: self._on_success_message(
                    "Reset link sent! Your old messages will require a Seed Phrase to read."
                ), 0
            )
        except Exception as e:
            Clock.schedule_once(lambda dt, err=str(e): self._on_error(err), 0)

    def _do_register(self, email: str, password: str, name: str, username: str) -> None:
        """Register and send email verification link."""
        try:
            if not self.firebase:
                raise FirebaseAuthError("Firebase not configured.")

            # Check username availability
            if not self.firebase.check_username_available(username):
                Clock.schedule_once(
                    lambda dt: self._on_error(
                        f"Username @{username} is already taken."
                    ), 0
                )
                return

            self.firebase.sign_up(email, password, display_name=name)
            self.firebase.send_email_verification()
            Clock.schedule_once(
                lambda dt: self._go_to_verify(
                    email, password, name, username
                ), 0
            )
        except Exception as e:
            Clock.schedule_once(lambda dt, err=str(e): self._on_error(err), 0)

    def _do_sign_in(self, email: str, password: str) -> None:
        """Sign in, check email verification, then decrypt private key."""
        try:
            if not self.firebase:
                raise FirebaseAuthError("Firebase not configured.")
            self.firebase.sign_in(email, password)

            # Check email verification status
            if not self.firebase.is_email_verified():
                # Re-send verification and redirect
                try:
                    self.firebase.send_email_verification()
                except Exception:
                    pass  # May fail if recently sent
                Clock.schedule_once(
                    lambda dt: self._go_to_verify(email, password, "", ""),
                    0,
                )
                return

            uid = self.firebase.local_id or ""
            kp = os.path.join(
                os.path.expanduser("~"), ".aegis", "keys", f"{uid}.key"
            )
            if not os.path.exists(kp):
                raise FileNotFoundError("Private key not found.")
            with open(kp) as f:
                enc = f.read()
            priv = decrypt_private_key(enc, password)
            Clock.schedule_once(lambda dt: self._on_success(priv), 0)
        except Exception as e:
            if "InvalidTag" in str(type(e)) or isinstance(e, FileNotFoundError):
                Clock.schedule_once(
                    lambda dt: self._go_to_seed_recovery(uid, password), 0
                )
            else:
                Clock.schedule_once(lambda dt, err=str(e): self._on_error(err), 0)

    def _go_to_seed_recovery(self, uid: str, password: str) -> None:
        """Navigate to the seed phrase recovery screen."""
        if not self.manager:
            return
        rec_screen = self.manager.get_screen("recovery_input")
        rec_screen.firebase = self.firebase
        rec_screen.pending_uid = uid
        rec_screen.pending_password = password
        rec_screen.next_screen = "chatlist"
        self.manager.current = "recovery_input"

    def _go_to_verify(
        self, email: str, password: str, name: str, username: str,
    ) -> None:
        """Navigate to the email verification screen."""
        if not self.manager:
            return
        verify_screen = self.manager.get_screen("verify")
        verify_screen.firebase = self.firebase
        verify_screen.pending_email = email
        verify_screen.pending_password = password
        verify_screen.pending_name = name
        verify_screen.pending_username = username
        verify_screen.next_screen = "chatlist"
        self.manager.current = "verify"

    def _on_success(self, private_key) -> None:
        """Navigate to chat list after successful auth."""
        from kivy.app import App
        app = App.get_running_app()
        if app:
            app.private_key = private_key
        if self.manager:
            self.manager.current = "chatlist"

    def _on_error(self, msg: str) -> None:
        """Display error message."""
        self.ids.status_label.text_color = (1, 0.322, 0.322, 1)
        self.ids.status_label.text = msg

    def _on_success_message(self, message: str) -> None:
        """Display success message."""
        self.ids.status_label.text_color = (0, 0.898, 0.8, 1)
        self.ids.status_label.text = message
        self.ids.field_password.text = ""
