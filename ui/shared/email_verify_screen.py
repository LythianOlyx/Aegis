"""
Aegis – Email Verification Screen
===================================
Shared verification screen shown after registration.
Features:
- Custom 10-minute link expiry enforcement (app-side)
- 2-minute resend cooldown
- Max 3 resends per 12-hour window
- Auto-polling for emailVerified status
"""

from __future__ import annotations

import os
import time
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

from core.firebase_client import FirebaseClient, FirebaseAuthError
from core.crypto_engine import (
    decrypt_private_key, encrypt_private_key,
    generate_rsa_keypair, serialize_public_key,
    generate_recovery_phrase
)

# ── Constants ──
LINK_EXPIRY = 600           # 10 minutes in seconds
RESEND_COOLDOWN = 120       # 2 minutes
MAX_RESENDS = 3             # Max 3 resends
RESEND_WINDOW = 43200       # 12 hours in seconds

Builder.load_string("""
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp
#:import Animation kivy.animation.Animation

<EmailVerifyScreen>:
    name: "verify"
    md_bg_color: 0.039, 0.086, 0.157, 1

    canvas.before:
        Color:
            rgba: 0.039, 0.086, 0.157, 1
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 0.000, 0.898, 0.800, 0.05
        Ellipse:
            pos: self.center_x - dp(200), self.center_y + dp(50)
            size: dp(400), dp(400)
        Color:
            rgba: 0.000, 1.000, 0.639, 0.03
        Ellipse:
            pos: self.center_x - dp(150), self.y - dp(50)
            size: dp(300), dp(300)

    ScrollView:
        do_scroll_x: False
        bar_width: 0

        MDBoxLayout:
            orientation: "vertical"
            adaptive_height: True
            padding: [dp(32), dp(40), dp(32), dp(24)]
            spacing: dp(0)
            md_bg_color: 0, 0, 0, 0

            Widget:
                size_hint_y: None
                height: dp(40)

            # ── Mail Icon with Glow ──
            FloatLayout:
                size_hint: None, None
                size: dp(120), dp(120)
                pos_hint: {"center_x": 0.5}

                Widget:
                    id: icon_glow
                    size_hint: None, None
                    size: dp(140), dp(140)
                    pos_hint: {"center_x": 0.5, "center_y": 0.5}
                    opacity: 0
                    canvas:
                        Color:
                            rgba: 0.000, 0.898, 0.800, 0.10
                        Ellipse:
                            pos: self.x, self.y
                            size: self.size

                MDLabel:
                    id: mail_icon
                    text: "📧"
                    halign: "center"
                    valign: "middle"
                    font_style: "Display"
                    role: "large"
                    size_hint: None, None
                    size: dp(100), dp(100)
                    pos_hint: {"center_x": 0.5, "center_y": 0.5}
                    opacity: 0

            Widget:
                size_hint_y: None
                height: dp(20)

            # ── Heading ──
            MDLabel:
                id: verify_title
                text: "Verify Your Email"
                halign: "center"
                font_style: "Headline"
                role: "small"
                theme_text_color: "Custom"
                text_color: 0.878, 0.969, 0.980, 1
                bold: True
                adaptive_height: True
                opacity: 0

            Widget:
                size_hint_y: None
                height: dp(8)

            MDLabel:
                id: verify_subtitle
                text: "We sent a verification link to your email"
                halign: "center"
                font_style: "Body"
                role: "medium"
                theme_text_color: "Custom"
                text_color: 0.502, 0.796, 0.769, 0.8
                adaptive_height: True
                opacity: 0

            Widget:
                size_hint_y: None
                height: dp(6)

            # ── Email Display ──
            MDLabel:
                id: email_display
                text: ""
                halign: "center"
                font_style: "Title"
                role: "medium"
                theme_text_color: "Custom"
                text_color: 0.000, 0.898, 0.800, 1
                adaptive_height: True
                opacity: 0

            Widget:
                size_hint_y: None
                height: dp(28)

            # ── Card Container ──
            MDBoxLayout:
                id: verify_card
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: [dp(24), dp(24), dp(24), dp(20)]
                spacing: dp(12)
                opacity: 0

                canvas.before:
                    Color:
                        rgba: 0.067, 0.133, 0.251, 0.75
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(22)]
                    Color:
                        rgba: 0.000, 0.898, 0.800, 0.20
                    RoundedRectangle:
                        pos: self.x + dp(36), self.top - dp(1.5)
                        size: self.width - dp(72), dp(1.5)
                        radius: [dp(1)]

                # ── Link Expiry Timer (10 min) ──
                MDBoxLayout:
                    orientation: "vertical"
                    adaptive_height: True
                    padding: [dp(16), dp(12), dp(16), dp(12)]
                    spacing: dp(4)
                    md_bg_color: 0.039, 0.086, 0.157, 1
                    radius: [dp(16)]
                    
                    MDLabel:
                        id: expiry_heading
                        text: "Link expires in"
                        halign: "center"
                        font_style: "Label"
                        role: "large"
                        theme_text_color: "Custom"
                        text_color: 0.502, 0.796, 0.769, 0.7
                        adaptive_height: True

                    MDLabel:
                        id: expiry_timer
                        text: "10:00"
                        halign: "center"
                        font_style: "Display"
                        role: "small"
                        theme_text_color: "Custom"
                        text_color: 0.000, 0.898, 0.800, 1
                        adaptive_height: True
                        bold: True

                # ── Resend Cooldown Hint ──
                MDLabel:
                    id: cooldown_hint
                    text: "Resend available in 02:00"
                    halign: "center"
                    font_style: "Label"
                    role: "small"
                    theme_text_color: "Custom"
                    text_color: 0.502, 0.796, 0.769, 0.5
                    adaptive_height: True

                # ── Resend Button ──
                MDButton:
                    id: btn_resend
                    style: "outlined"
                    size_hint_x: 1
                    theme_line_color: "Custom"
                    line_color: 0.000, 0.898, 0.800, 0.25
                    disabled: True
                    on_release: root.on_resend()

                    MDButtonText:
                        id: btn_resend_text
                        text: "Resend Verification Link"
                        theme_text_color: "Custom"
                        text_color: 0.000, 0.898, 0.800, 0.85
                        font_size: sp(14)

                # ── Resend Counter ──
                MDLabel:
                    id: resend_counter
                    text: "0/3 resends used"
                    halign: "center"
                    font_style: "Label"
                    role: "small"
                    theme_text_color: "Custom"
                    text_color: 0.502, 0.796, 0.769, 0.5
                    adaptive_height: True

                Widget:
                    size_hint_y: None
                    height: dp(4)

                # ── Verify Button ──
                MDButton:
                    id: btn_verify
                    style: "filled"
                    theme_bg_color: "Custom"
                    md_bg_color: 0.000, 0.898, 0.800, 1
                    size_hint_x: 1
                    on_release: root.on_check_verified()

                    MDButtonText:
                        id: btn_verify_text
                        text: "I've Verified My Email"
                        theme_text_color: "Custom"
                        text_color: 0.039, 0.086, 0.157, 1
                        bold: True
                        font_size: sp(15)

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
                height: dp(16)

            # ── Back Button ──
            MDButton:
                style: "text"
                size_hint_x: None
                pos_hint: {"center_x": 0.5}
                on_release: root.on_back()

                MDButtonText:
                    text: "← Back to Sign In"
                    theme_text_color: "Custom"
                    text_color: 0.502, 0.796, 0.769, 0.7
                    font_size: sp(13)

            Widget:
                size_hint_y: None
                height: dp(16)

            # ── Footer ──
            MDLabel:
                text: "🔒  Verification link valid for 10 minutes"
                halign: "center"
                font_style: "Label"
                role: "small"
                theme_text_color: "Custom"
                text_color: 0.502, 0.796, 0.769, 0.3
                adaptive_height: True

            Widget:
                size_hint_y: None
                height: dp(12)
""")


class EmailVerifyScreen(Screen):
    """Email verification screen with custom 10-minute link expiry.

    Firebase's built-in verification link has a fixed 3-day expiry
    that cannot be customized. This screen enforces a stricter
    10-minute window on the application side: even if Firebase marks
    ``emailVerified`` as True, the app will reject the verification
    if the 10-minute window has elapsed since the link was sent.

    Features
    --------
    - **10-minute link expiry**: Countdown timer; verification only
      accepted within the window.
    - **2-minute resend cooldown**: Prevents spamming.
    - **3 resends per 12 hours**: Rate limiting.
    - **Auto-poll every 5s**: Checks emailVerified silently.
    - **Manual verify button**: User can trigger a check.
    - **On success**: Generates RSA-2048 keys and proceeds.

    Attributes
    ----------
    firebase : FirebaseClient
    next_screen : str
    pending_email, pending_password, pending_name, pending_username : str
    """

    firebase = ObjectProperty(None, allownone=True)
    next_screen: str = StringProperty("chatlist")

    # Pending registration data (set by auth screen before navigating)
    pending_email: str = StringProperty("")
    pending_password: str = StringProperty("")
    pending_name: str = StringProperty("")
    pending_username: str = StringProperty("")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Rate limiting state
        self._resend_count: int = 0
        self._resend_window_start: float = 0.0
        # Cooldown state
        self._cooldown_remaining: int = 0
        # Link expiry state
        self._link_expires_at: float = 0.0
        self._link_expired: bool = False
        # Clock events
        self._tick_event = None
        self._poll_event = None

    def on_enter(self, *args) -> None:
        """Animate elements and start all timers."""
        email = self.pending_email or (
            self.firebase.email if self.firebase else ""
        )
        self.ids.email_display.text = self._mask_email(email)
        self.ids.status_label.text = ""

        # Initialize link expiry (10 minutes from now)
        self._link_expires_at = time.time() + LINK_EXPIRY
        self._link_expired = False

        # Start resend cooldown
        self._cooldown_remaining = RESEND_COOLDOWN
        self.ids.btn_resend.disabled = True
        self.ids.btn_verify.disabled = False

        # Start unified tick (drives both expiry and cooldown)
        if self._tick_event:
            self._tick_event.cancel()
        self._tick_event = Clock.schedule_interval(self._tick, 1.0)
        self._update_displays()

        # Start auto-poll for verification
        if self._poll_event:
            self._poll_event.cancel()
        self._poll_event = Clock.schedule_interval(
            self._auto_check_verified, 5.0
        )

        self._animate_entry()

    def on_leave(self, *args) -> None:
        """Clean up all timers when leaving."""
        if self._tick_event:
            self._tick_event.cancel()
            self._tick_event = None
        if self._poll_event:
            self._poll_event.cancel()
            self._poll_event = None

    # ──── Unified Tick (1 Hz) ─────────────────────────────

    def _tick(self, dt: float) -> None:
        """Called every second. Updates both expiry and cooldown."""
        now = time.time()

        # ── Link expiry ──
        expiry_left = max(0, int(self._link_expires_at - now))
        if expiry_left <= 0 and not self._link_expired:
            self._on_link_expired()

        # ── Resend cooldown ──
        if self._cooldown_remaining > 0:
            self._cooldown_remaining -= 1
            if self._cooldown_remaining <= 0:
                self._cooldown_remaining = 0
                # Enable resend only if not at rate limit
                if self._resend_count < MAX_RESENDS or (
                    time.time() - self._resend_window_start >= RESEND_WINDOW
                ):
                    self.ids.btn_resend.disabled = False

        self._update_displays()

    def _update_displays(self) -> None:
        """Refresh the expiry timer and cooldown hint text."""
        now = time.time()

        # ── Expiry timer ──
        expiry_left = max(0, int(self._link_expires_at - now))
        e_min = expiry_left // 60
        e_sec = expiry_left % 60

        if self._link_expired:
            self.ids.expiry_timer.text = "EXPIRED"
            self.ids.expiry_timer.text_color = (1.0, 0.322, 0.322, 1)
            self.ids.expiry_heading.text = "Verification link has"
        elif expiry_left <= 60:
            # Last minute — warning colour (amber)
            self.ids.expiry_timer.text = f"{e_min:02d}:{e_sec:02d}"
            self.ids.expiry_timer.text_color = (1.0, 0.757, 0.027, 1)
            self.ids.expiry_heading.text = "Link expires in"
        else:
            self.ids.expiry_timer.text = f"{e_min:02d}:{e_sec:02d}"
            self.ids.expiry_timer.text_color = (0.0, 0.898, 0.800, 1)
            self.ids.expiry_heading.text = "Link expires in"

        # ── Cooldown hint ──
        if self._cooldown_remaining > 0:
            c_min = self._cooldown_remaining // 60
            c_sec = self._cooldown_remaining % 60
            self.ids.cooldown_hint.text = (
                f"Resend available in {c_min:02d}:{c_sec:02d}"
            )
        elif self._link_expired:
            self.ids.cooldown_hint.text = (
                "Please resend to get a new link"
            )
        else:
            self.ids.cooldown_hint.text = "Resend is available"

    def _on_link_expired(self) -> None:
        """Handle link expiry — disable verify, prompt resend."""
        self._link_expired = True
        self.ids.btn_verify.disabled = True
        self._show_error(
            "Verification link has expired. "
            "Please resend to get a new link."
        )
        # Force-enable resend if cooldown is done
        if self._cooldown_remaining <= 0:
            if self._resend_count < MAX_RESENDS or (
                time.time() - self._resend_window_start >= RESEND_WINDOW
            ):
                self.ids.btn_resend.disabled = False

    # ──── Animations ──────────────────────────────────────

    def _animate_entry(self) -> None:
        """Staggered reveal animation."""
        glow = self.ids.icon_glow
        icon = self.ids.mail_icon
        title = self.ids.verify_title
        subtitle = self.ids.verify_subtitle
        email_lbl = self.ids.email_display
        card = self.ids.verify_card

        for w in [glow, icon, title, subtitle, email_lbl, card]:
            w.opacity = 0

        Animation(opacity=1, d=0.4, t="out_cubic").start(glow)
        Clock.schedule_once(
            lambda dt: Animation(
                opacity=1, d=0.5, t="out_back"
            ).start(icon), 0.1,
        )
        Clock.schedule_once(
            lambda dt: Animation(
                opacity=1, d=0.4, t="out_cubic"
            ).start(title), 0.3,
        )
        Clock.schedule_once(
            lambda dt: Animation(
                opacity=1, d=0.4, t="out_cubic"
            ).start(subtitle), 0.4,
        )
        Clock.schedule_once(
            lambda dt: Animation(
                opacity=1, d=0.4, t="out_cubic"
            ).start(email_lbl), 0.5,
        )
        Clock.schedule_once(
            lambda dt: Animation(
                opacity=1, d=0.5, t="out_cubic"
            ).start(card), 0.6,
        )

    # ──── Resend Logic ────────────────────────────────────

    def on_resend(self) -> None:
        """Handle resend button press with rate limiting."""
        now = time.time()

        # Check 12-hour window
        if self._resend_count >= MAX_RESENDS:
            elapsed = now - self._resend_window_start
            if elapsed < RESEND_WINDOW:
                remaining_h = int((RESEND_WINDOW - elapsed) / 3600)
                remaining_m = int(
                    ((RESEND_WINDOW - elapsed) % 3600) / 60
                )
                self._show_error(
                    f"Resend limit reached. Try again in "
                    f"{remaining_h}h {remaining_m}m."
                )
                return
            else:
                # Reset after 12 hours
                self._resend_count = 0
                self._resend_window_start = 0.0

        # Initialize window on first resend
        if self._resend_count == 0:
            self._resend_window_start = now

        self.ids.btn_resend.disabled = True
        self._show_status("Sending verification link...")
        threading.Thread(
            target=self._do_resend, daemon=True
        ).start()

    def _do_resend(self) -> None:
        """Send verification email in background thread."""
        try:
            if not self.firebase:
                raise FirebaseAuthError("Firebase not configured.")
            self.firebase.send_email_verification()
            self._resend_count += 1
            Clock.schedule_once(lambda dt: self._on_resend_success(), 0)
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._show_error(str(e)), 0
            )

    def _on_resend_success(self) -> None:
        """Update UI after successful resend — reset expiry & cooldown."""
        self.ids.resend_counter.text = (
            f"{self._resend_count}/{MAX_RESENDS} resends used"
        )
        self._show_status("New verification link sent! ✓")

        # Reset 10-minute expiry window
        self._link_expires_at = time.time() + LINK_EXPIRY
        self._link_expired = False
        self.ids.btn_verify.disabled = False

        # Reset 2-minute resend cooldown
        self._cooldown_remaining = RESEND_COOLDOWN
        self.ids.btn_resend.disabled = True
        self._update_displays()

    # ──── Verification Check ──────────────────────────────

    def on_check_verified(self) -> None:
        """Manual check: user claims they verified."""
        if self._link_expired:
            self._show_error(
                "Link has expired. Please resend to get a new link."
            )
            return
        self._show_status("Checking verification status...")
        threading.Thread(
            target=self._do_check_verified, daemon=True
        ).start()

    def _auto_check_verified(self, dt: float) -> None:
        """Auto-poll: check verification status every 5s."""
        if self._link_expired:
            return  # Don't poll if link expired
        threading.Thread(
            target=self._do_check_verified,
            kwargs={"silent": True},
            daemon=True,
        ).start()

    def _do_check_verified(self, silent: bool = False) -> None:
        """Check emailVerified status + enforce 10-minute expiry."""
        try:
            if not self.firebase:
                return
            verified = self.firebase.is_email_verified()
            if verified:
                # ── Custom expiry enforcement ──
                now = time.time()
                if now > self._link_expires_at:
                    # Verified AFTER the 10-minute window — reject
                    if not silent:
                        Clock.schedule_once(
                            lambda dt: self._show_error(
                                "Verification was too late. "
                                "The link has expired. Please resend."
                            ), 0,
                        )
                    Clock.schedule_once(
                        lambda dt: self._on_link_expired(), 0
                    )
                    return
                # Verified WITHIN the window — accept!
                Clock.schedule_once(
                    lambda dt: self._on_verified(), 0
                )
            elif not silent:
                Clock.schedule_once(
                    lambda dt: self._show_error(
                        "Email not verified yet. "
                        "Please check your inbox."
                    ), 0,
                )
        except Exception as e:
            if not silent:
                Clock.schedule_once(
                    lambda dt: self._show_error(str(e)), 0
                )

    def _on_verified(self) -> None:
        """Email verified within time — generate keys and proceed."""
        self._show_status(
            "Email verified! Generating encryption keys..."
        )

        # Stop all polling/timers
        if self._poll_event:
            self._poll_event.cancel()
            self._poll_event = None
        if self._tick_event:
            self._tick_event.cancel()
            self._tick_event = None

        threading.Thread(
            target=self._do_generate_keys, daemon=True
        ).start()

    def _do_generate_keys(self) -> None:
        """Generate RSA keys and prepare for recovery phrase setup."""
        try:
            if not self.firebase:
                raise FirebaseAuthError("Firebase not configured.")

            # Generate RSA key pair
            private_key, public_key = generate_rsa_keypair()
            pub_b64 = serialize_public_key(public_key)
            
            # Generate 24-word recovery phrase
            recovery_phrase = generate_recovery_phrase()

            Clock.schedule_once(
                lambda dt: self._go_to_recovery_setup(private_key, pub_b64, recovery_phrase), 0
            )
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._show_error(str(e)), 0
            )

    def _go_to_recovery_setup(self, private_key, pub_b64, recovery_phrase) -> None:
        """Navigate to the recovery setup screen."""
        if not self.manager:
            return
            
        setup_screen = self.manager.get_screen("recovery_setup")
        setup_screen.firebase = self.firebase
        setup_screen.recovery_phrase = recovery_phrase
        setup_screen.pending_email = self.pending_email
        setup_screen.pending_password = self.pending_password
        setup_screen.pending_name = self.pending_name
        setup_screen.pending_username = self.pending_username
        setup_screen.private_key = private_key
        setup_screen.public_key_b64 = pub_b64
        
        self.manager.current = "recovery_setup"

    # ──── Navigation ──────────────────────────────────────

    def on_back(self) -> None:
        """Go back to auth screen."""
        if self.firebase:
            self.firebase.sign_out()
        if self.manager:
            self.manager.current = "auth"

    # ──── UI Helpers ──────────────────────────────────────

    def _mask_email(self, email: str) -> str:
        """Partially mask email: a***@domain.com"""
        if not email or "@" not in email:
            return email
        local, domain = email.split("@", 1)
        if len(local) <= 2:
            masked = local[0] + "***"
        else:
            masked = local[0] + "***" + local[-1]
        return f"{masked}@{domain}"

    def _show_error(self, msg: str) -> None:
        """Display error message."""
        lbl = self.ids.status_label
        lbl.text_color = (1.0, 0.322, 0.322, 1)
        lbl.text = msg

    def _show_status(self, msg: str) -> None:
        """Display info/success message."""
        lbl = self.ids.status_label
        lbl.text_color = (0.000, 0.898, 0.800, 1)
        lbl.text = msg
