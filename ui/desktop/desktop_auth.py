"""
Aegis – Desktop Authentication Screen
======================================
Premium split-panel Login & Registration for the Desktop build.
Left panel:  Branding – logo, tagline, feature highlights.
Right panel: Auth form – login / register fields.
Uses KivyMD 2.0 Material Design 3 components with
the Aegis dark cybersecurity theme.
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
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText

from core.crypto_engine import decrypt_private_key
from core.firebase_client import FirebaseClient, FirebaseAuthError

# ═══════════════════════════════════════════════════════════
#  KV LAYOUT
# ═══════════════════════════════════════════════════════════

Builder.load_string("""
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp
#:import Animation kivy.animation.Animation

<DesktopAuthScreen>:
    name: "auth"
    md_bg_color: 0.039, 0.086, 0.157, 1

    MDBoxLayout:
        orientation: "horizontal"
        md_bg_color: 0, 0, 0, 0

        # ═══════════════════════════════════════════════════
        #  LEFT PANEL – Branding
        # ═══════════════════════════════════════════════════
        MDBoxLayout:
            orientation: "vertical"
            size_hint_x: 0.45
            md_bg_color: 0, 0, 0, 0
            padding: [dp(48), dp(48), dp(48), dp(48)]

            # Background with subtle gradient
            canvas.before:
                # Base dark navy
                Color:
                    rgba: 0.027, 0.063, 0.118, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [0, 0, 0, 0]
                # Large radial glow (cyan)
                Color:
                    rgba: 0.000, 0.898, 0.800, 0.05
                Ellipse:
                    pos: self.center_x - dp(250), self.center_y - dp(100)
                    size: dp(500), dp(500)
                # Secondary glow (green)
                Color:
                    rgba: 0.000, 1.000, 0.639, 0.04
                Ellipse:
                    pos: self.x + dp(20), self.y + dp(20)
                    size: dp(300), dp(400)
                # Decorative thin line on right edge
                Color:
                    rgba: 0.000, 0.898, 0.800, 0.15
                Rectangle:
                    pos: self.right - dp(1), self.y + dp(40)
                    size: dp(1), self.height - dp(80)

            Widget:
                size_hint_y: 0.18

            # ── Logo with rounded corners ──
            FloatLayout:
                size_hint: None, None
                size: dp(140), dp(140)
                pos_hint: {"center_x": 0.5}

                # Outer glow aura
                Widget:
                    id: brand_glow
                    size_hint: None, None
                    size: dp(170), dp(170)
                    pos_hint: {"center_x": 0.5, "center_y": 0.5}
                    opacity: 0
                    canvas:
                        Color:
                            rgba: 0.000, 0.898, 0.800, 0.10
                        Ellipse:
                            pos: self.x, self.y
                            size: self.size

                # Clipped logo
                Widget:
                    id: brand_logo
                    size_hint: None, None
                    size: dp(120), dp(120)
                    pos_hint: {"center_x": 0.5, "center_y": 0.5}
                    opacity: 0
                    canvas.before:
                        StencilPush
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(24)]
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
                            radius: [dp(24)]
                        StencilPop

                # Border
                Widget:
                    size_hint: None, None
                    size: dp(124), dp(124)
                    pos_hint: {"center_x": 0.5, "center_y": 0.5}
                    canvas:
                        Color:
                            rgba: 0.000, 0.898, 0.800, 0.3
                        Line:
                            rounded_rectangle: self.x, self.y, self.width, self.height, dp(25)
                            width: dp(1.5)

            Widget:
                size_hint_y: None
                height: dp(28)

            # ── App Title ──
            MDLabel:
                id: brand_title
                text: "A E G I S"
                halign: "center"
                font_style: "Display"
                role: "small"
                theme_text_color: "Custom"
                text_color: 0.000, 0.898, 0.800, 1
                opacity: 0
                bold: True

            Widget:
                size_hint_y: None
                height: dp(8)

            # ── Tagline ──
            MDLabel:
                id: brand_tagline
                text: "End-to-End Encrypted Messaging"
                halign: "center"
                font_style: "Body"
                role: "large"
                theme_text_color: "Custom"
                text_color: 0.502, 0.796, 0.769, 1
                opacity: 0

            Widget:
                size_hint_y: None
                height: dp(36)

            # ── Feature Highlights ──
            MDBoxLayout:
                id: features_box
                orientation: "vertical"
                spacing: dp(18)
                padding: [dp(20), 0]
                adaptive_height: True
                pos_hint: {"center_x": 0.5}
                opacity: 0

                # Feature 1
                MDBoxLayout:
                    orientation: "horizontal"
                    adaptive_height: True
                    spacing: dp(12)

                    MDLabel:
                        text: "🔐"
                        font_style: "Title"
                        role: "large"
                        size_hint_x: None
                        width: dp(32)
                        halign: "center"

                    MDBoxLayout:
                        orientation: "vertical"
                        adaptive_height: True
                        spacing: dp(2)

                        MDLabel:
                            text: "RSA-2048 + AES-256-GCM"
                            font_style: "Body"
                            role: "medium"
                            theme_text_color: "Custom"
                            text_color: 0.878, 0.969, 0.980, 1
                            adaptive_height: True

                        MDLabel:
                            text: "Military-grade encryption for every message"
                            font_style: "Body"
                            role: "small"
                            theme_text_color: "Custom"
                            text_color: 0.502, 0.796, 0.769, 0.7
                            adaptive_height: True

                # Feature 2
                MDBoxLayout:
                    orientation: "horizontal"
                    adaptive_height: True
                    spacing: dp(12)

                    MDLabel:
                        text: "🛡️"
                        font_style: "Title"
                        role: "large"
                        size_hint_x: None
                        width: dp(32)
                        halign: "center"

                    MDBoxLayout:
                        orientation: "vertical"
                        adaptive_height: True
                        spacing: dp(2)

                        MDLabel:
                            text: "Zero Knowledge Architecture"
                            font_style: "Body"
                            role: "medium"
                            theme_text_color: "Custom"
                            text_color: 0.878, 0.969, 0.980, 1
                            adaptive_height: True

                        MDLabel:
                            text: "Your keys never leave your device"
                            font_style: "Body"
                            role: "small"
                            theme_text_color: "Custom"
                            text_color: 0.502, 0.796, 0.769, 0.7
                            adaptive_height: True

                # Feature 3
                MDBoxLayout:
                    orientation: "horizontal"
                    adaptive_height: True
                    spacing: dp(12)

                    MDLabel:
                        text: "📱"
                        font_style: "Title"
                        role: "large"
                        size_hint_x: None
                        width: dp(32)
                        halign: "center"

                    MDBoxLayout:
                        orientation: "vertical"
                        adaptive_height: True
                        spacing: dp(2)

                        MDLabel:
                            text: "Cross-Platform Sync"
                            font_style: "Body"
                            role: "medium"
                            theme_text_color: "Custom"
                            text_color: 0.878, 0.969, 0.980, 1
                            adaptive_height: True

                        MDLabel:
                            text: "Seamless on desktop and mobile"
                            font_style: "Body"
                            role: "small"
                            theme_text_color: "Custom"
                            text_color: 0.502, 0.796, 0.769, 0.7
                            adaptive_height: True

            Widget:
                size_hint_y: 0.15

        # ═══════════════════════════════════════════════════
        #  RIGHT PANEL – Auth Form (vertically centred)
        # ═══════════════════════════════════════════════════
        FloatLayout:
            size_hint_x: 0.55

            # Background canvas
            canvas.before:
                Color:
                    rgba: 0.039, 0.086, 0.157, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
                # Subtle centred glow
                Color:
                    rgba: 0.000, 0.706, 0.847, 0.03
                Ellipse:
                    pos: self.center_x - dp(180), self.center_y - dp(180)
                    size: dp(360), dp(360)

            # ── Auth Card (centred via AnchorLayout) ──
            AnchorLayout:
                anchor_x: "center"
                anchor_y: "center"
                size: self.parent.size
                pos: self.parent.pos
                padding: [dp(48), dp(48), dp(48), dp(48)]

                MDBoxLayout:
                    id: auth_card
                    orientation: "vertical"
                    size_hint: 0.88, None
                    height: self.minimum_height
                    padding: [dp(36), dp(32), dp(36), dp(28)]
                    spacing: dp(14)
                    opacity: 0

                    # Card background
                    canvas.before:
                        Color:
                            rgba: 0.067, 0.133, 0.251, 0.85
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(24)]

                    # ── Form Header ──
                    MDLabel:
                        id: auth_title
                        text: "Welcome Back"
                        halign: "left"
                        font_style: "Headline"
                        role: "small"
                        theme_text_color: "Custom"
                        text_color: 0.878, 0.969, 0.980, 1
                        bold: True
                        adaptive_height: True

                    MDLabel:
                        id: auth_description
                        text: "Sign in to continue your secure conversations"
                        halign: "left"
                        font_style: "Body"
                        role: "medium"
                        theme_text_color: "Custom"
                        text_color: 0.502, 0.796, 0.769, 0.8
                        adaptive_height: True

                    Widget:
                        size_hint_y: None
                        height: dp(10)

                    # ── Display Name (Register only) ──
                    MDTextField:
                        id: field_name
                        mode: "outlined"
                        size_hint_x: 1
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
                        size_hint_x: 1
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
                        size_hint_x: 1

                        MDTextFieldHintText:
                            text: "Email Address"

                    # ── Password ──
                    MDTextField:
                        id: field_password
                        mode: "outlined"
                        size_hint_x: 1
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
                        pos_hint: {"center_x": 0.5}
                        on_release: root.on_primary_action()

                        MDButtonText:
                            id: btn_primary_text
                            text: "Sign In"
                            theme_text_color: "Custom"
                            text_color: 0.039, 0.086, 0.157, 1
                            font_size: sp(16)
                            bold: True

                    # ── Divider ──
                    MDBoxLayout:
                        orientation: "horizontal"
                        size_hint_y: None
                        height: dp(20)
                        spacing: dp(12)
                        padding: [dp(4), dp(6)]

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

                    # ── Toggle link ──
                    MDButton:
                        id: btn_toggle
                        style: "outlined"
                        size_hint_x: 1
                        pos_hint: {"center_x": 0.5}
                        theme_line_color: "Custom"
                        line_color: 0.000, 0.898, 0.800, 0.25
                        on_release: root.toggle_mode()

                        MDButtonText:
                            id: btn_toggle_text
                            text: "Create a new account"
                            theme_text_color: "Custom"
                            text_color: 0.000, 0.898, 0.800, 0.85
                            font_size: sp(14)

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

            # ── Footer (anchored to bottom) ──
            MDLabel:
                text: "🔒  Protected by end-to-end encryption"
                halign: "center"
                font_style: "Label"
                role: "small"
                theme_text_color: "Custom"
                text_color: 0.502, 0.796, 0.769, 0.25
                size_hint: 1, None
                height: dp(20)
                pos_hint: {"center_x": 0.5, "y": 0.02}
""")


# ═══════════════════════════════════════════════════════════
#  PYTHON CLASS
# ═══════════════════════════════════════════════════════════

class DesktopAuthScreen(Screen):
    """Desktop login / registration screen with E2EE key generation.

    Split-panel layout:
    - Left panel:  Branding (logo, tagline, features)
    - Right panel: Auth form (login / register)

    Attributes
    ----------
    firebase : FirebaseClient
        Injected Firebase client instance.
    is_register_mode : bool
        Whether the form is in registration mode.
    """

    logo_path: str = StringProperty("")
    firebase = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._is_register: bool = False
        self._is_reset_mode: bool = False
        self.pending_uid_for_recovery: str = ""
        self.pending_password_for_recovery: str = ""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)
        )))
        self.logo_path = os.path.join(base_dir, "assets", "logo.png")

    def on_enter(self, *args) -> None:
        """Animate the auth screen elements on entry."""
        card = self.ids.auth_card
        brand_logo = self.ids.brand_logo
        brand_glow = self.ids.brand_glow
        brand_title = self.ids.brand_title
        brand_tagline = self.ids.brand_tagline
        features = self.ids.features_box

        # Reset
        for w in [card, brand_logo, brand_glow, brand_title,
                  brand_tagline, features]:
            w.opacity = 0

        # Left panel animations (staggered)
        Animation(opacity=1, duration=0.5, t="out_cubic").start(brand_glow)
        Clock.schedule_once(
            lambda dt: Animation(opacity=1, duration=0.6, t="out_back").start(brand_logo), 0.15
        )
        Clock.schedule_once(
            lambda dt: Animation(opacity=1, duration=0.5, t="out_cubic").start(brand_title), 0.35
        )
        Clock.schedule_once(
            lambda dt: Animation(opacity=1, duration=0.5, t="out_cubic").start(brand_tagline), 0.5
        )
        Clock.schedule_once(
            lambda dt: Animation(opacity=1, duration=0.6, t="out_cubic").start(features), 0.7
        )

        # Right panel: auth card slides in
        Clock.schedule_once(
            lambda dt: Animation(opacity=1, duration=0.6, t="out_cubic").start(card), 0.3
        )

    def toggle_mode(self) -> None:
        """Switch between Login and Register modes with animation."""
        if self._is_reset_mode:
            self.toggle_reset_mode()
            return
            
        self._is_register = not self._is_register
        field_name = self.ids.field_name
        title = self.ids.auth_title
        desc = self.ids.auth_description
        btn_text = self.ids.btn_primary_text
        toggle_text = self.ids.btn_toggle_text
        status = self.ids.status_label
        forgot_box = self.ids.forgot_password_box

        status.text = ""

        if self._is_register:
            title.text = "Create Account"
            desc.text = "Set up your secure identity to start messaging"
            btn_text.text = "Create Account"
            toggle_text.text = "Already have an account? Sign In"
            field_name.disabled = False
            Animation(opacity=1, height=dp(56), duration=0.3, t="out_cubic").start(field_name)
            # Show username field
            field_username = self.ids.field_username
            field_username.disabled = False
            Animation(opacity=1, height=dp(56), duration=0.3, t="out_cubic").start(field_username)
            # Hide forgot password
            Animation(opacity=0, height=dp(0), duration=0.3, t="out_cubic").start(forgot_box)
        else:
            title.text = "Welcome Back"
            desc.text = "Sign in to continue your secure conversations"
            btn_text.text = "Sign In"
            toggle_text.text = "Create a new account"
            field_name.disabled = True
            Animation(opacity=0, height=dp(0), duration=0.3, t="out_cubic").start(field_name)
            # Hide username field
            field_username = self.ids.field_username
            field_username.disabled = True
            Animation(opacity=0, height=dp(0), duration=0.3, t="out_cubic").start(field_username)
            # Show forgot password
            Animation(opacity=1, height=dp(32), duration=0.3, t="out_cubic").start(forgot_box)

    def toggle_reset_mode(self) -> None:
        """Switch to Password Reset mode."""
        self._is_reset_mode = not self._is_reset_mode
        title = self.ids.auth_title
        desc = self.ids.auth_description
        btn_text = self.ids.btn_primary_text
        toggle_text = self.ids.btn_toggle_text
        status = self.ids.status_label
        pwd = self.ids.field_password
        forgot_box = self.ids.forgot_password_box

        status.text = ""

        if self._is_reset_mode:
            self._is_register = False
            title.text = "Reset Password"
            desc.text = "WARNING: Resetting your password will result in the loss of all previously encrypted messages due to E2EE. Proceed only if necessary."
            desc.text_color = (1.0, 0.322, 0.322, 1)
            btn_text.text = "Send Reset Link"
            toggle_text.text = "Back to Sign In"
            
            pwd.disabled = True
            Animation(opacity=0, height=dp(0), duration=0.3, t="out_cubic").start(pwd)
            Animation(opacity=0, height=dp(0), duration=0.3, t="out_cubic").start(forgot_box)
            
            fn = self.ids.field_name
            fu = self.ids.field_username
            fn.disabled = True
            fu.disabled = True
            fn.opacity = 0
            fn.height = 0
            fu.opacity = 0
            fu.height = 0
        else:
            title.text = "Welcome Back"
            desc.text = "Sign in to continue your secure conversations"
            desc.text_color = (0.502, 0.796, 0.769, 0.8)
            btn_text.text = "Sign In"
            toggle_text.text = "Create a new account"
            
            pwd.disabled = False
            Animation(opacity=1, height=dp(56), duration=0.3, t="out_cubic").start(pwd)
            Animation(opacity=1, height=dp(32), duration=0.3, t="out_cubic").start(forgot_box)

    def on_primary_action(self) -> None:
        """Handle Sign In, Register, or Reset Password button press."""
        email: str = self.ids.field_email.text.strip()
        password: str = self.ids.field_password.text.strip()
        status: MDLabel = self.ids.status_label

        if not email:
            status.text = "Please enter your email address."
            return

        if self._is_reset_mode:
            status.text = "Sending reset link..."
            status.text_color = ACCENT_CYAN_COLOR
            threading.Thread(
                target=self._do_reset_password,
                args=(email,),
                daemon=True,
            ).start()
            return

        if not password:
            status.text = "Please fill in all fields."
            return

        if self._is_register:
            display_name: str = self.ids.field_name.text.strip()
            if not display_name:
                status.text = "Please enter a display name."
                return
            # Validate username
            raw_username: str = self.ids.field_username.text.strip()
            # Strip leading @ if user typed it
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
            status.text = "Creating account & generating keys..."
            status.text_color = ACCENT_CYAN_COLOR
            threading.Thread(
                target=self._do_register,
                args=(email, password, display_name, username),
                daemon=True,
            ).start()
        else:
            status.text = "Signing in..."
            status.text_color = ACCENT_CYAN_COLOR
            threading.Thread(
                target=self._do_sign_in,
                args=(email, password),
                daemon=True,
            ).start()

    # ──── Background Auth Tasks ────────────────────────
    def _do_reset_password(self, email: str) -> None:
        """Send password reset email via Firebase."""
        try:
            if not self.firebase:
                raise FirebaseAuthError("Firebase not configured.")
            self.firebase.send_password_reset_email(email)
            Clock.schedule_once(
                lambda dt: self._on_auth_success_message(
                    "Reset link sent! Your old messages will require a Seed Phrase to read."
                ), 0
            )
        except Exception as e:
            Clock.schedule_once(
                lambda dt, err=str(e): self._on_auth_error(err), 0
            )

    def _do_register(self, email: str, password: str, name: str, username: str) -> None:
        """Register and send email verification link."""
        try:
            if not self.firebase:
                raise FirebaseAuthError("Firebase not configured.")

            # 0. Check username availability
            if not self.firebase.check_username_available(username):
                Clock.schedule_once(
                    lambda dt: self._on_auth_error(
                        f"Username @{username} is already taken."
                    ), 0
                )
                return

            # 1. Firebase Auth registration
            self.firebase.sign_up(email, password, display_name=name)

            # 2. Send email verification
            self.firebase.send_email_verification()

            # 3. Navigate to verify screen
            Clock.schedule_once(
                lambda dt: self._go_to_verify(
                    email, password, name, username
                ), 0
            )

        except Exception as e:
            Clock.schedule_once(
                lambda dt, err=str(e): self._on_auth_error(err), 0
            )

    def _do_sign_in(self, email: str, password: str) -> None:
        """Sign in, check email verification, then decrypt private key."""
        try:
            if not self.firebase:
                raise FirebaseAuthError("Firebase not configured.")

            self.firebase.sign_in(email, password)

            # Check email verification status
            if not self.firebase.is_email_verified():
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

            # Load and decrypt private key
            key_path = os.path.join(
                os.path.expanduser("~"), ".aegis", "keys", f"{uid}.key"
            )
            if not os.path.exists(key_path):
                raise FileNotFoundError(
                    "Private key not found. Register on this device first."
                )

            with open(key_path, "r") as f:
                encrypted_priv = f.read()

            private_key = decrypt_private_key(encrypted_priv, password)

            Clock.schedule_once(
                lambda dt: self._on_auth_success(private_key), 0
            )

        except Exception as e:
            if "InvalidTag" in str(type(e)) or isinstance(e, FileNotFoundError):
                # Transition to RecoveryInputScreen
                Clock.schedule_once(
                    lambda dt: self._go_to_seed_recovery(uid, password), 0
                )
            else:
                Clock.schedule_once(
                    lambda dt, err=str(e): self._on_auth_error(err), 0
                )

    def _go_to_seed_recovery(self, uid: str, password: str) -> None:
        """Navigate to the seed phrase recovery screen."""
        if not self.manager:
            return
        rec_screen = self.manager.get_screen("recovery_input")
        rec_screen.firebase = self.firebase
        rec_screen.pending_uid = uid
        rec_screen.pending_password = password
        rec_screen.next_screen = "main"
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
        verify_screen.next_screen = "main"
        self.manager.current = "verify"

    def _on_auth_success(self, private_key) -> None:
        """Navigate to main chat screen after successful auth."""
        from kivy.app import App
        app = App.get_running_app()
        if app:
            app.private_key = private_key
        if self.manager:
            self.manager.current = "main"

    def _on_auth_error(self, message: str) -> None:
        """Display error message."""
        status: MDLabel = self.ids.status_label
        status.text_color = (1.0, 0.322, 0.322, 1)
        status.text = message

    def _on_auth_success_message(self, message: str) -> None:
        """Display success message for actions like password reset."""
        status: MDLabel = self.ids.status_label
        status.text_color = ACCENT_CYAN_COLOR
        status.text = message
        self.ids.field_password.text = ""


# Colour tuple for use in code
ACCENT_CYAN_COLOR = (0.000, 0.898, 0.800, 1)
