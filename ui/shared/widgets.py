"""
Aegis – Shared UI Widgets
=========================
Reusable widgets for both Desktop and Mobile UIs:
- E2EEMessageBubble    – Encrypted message display with sender/time
- AegisTextField       – Themed text input
- ChatListItem         – Chat preview row
- SplashScreen         – Animated logo splash
- UserSearchResult     – User search result card
"""

from __future__ import annotations

import os
from typing import Optional

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
from kivy.uix.behaviors import ButtonBehavior

# ─────────────────── Colour Constants ────────────────────
BG_PRIMARY    = (0.039, 0.086, 0.157, 1)
BG_SURFACE    = (0.067, 0.133, 0.251, 1)
BG_ELEVATED   = (0.102, 0.200, 0.333, 1)
ACCENT_CYAN   = (0.000, 0.898, 0.800, 1)
ACCENT_GREEN  = (0.000, 1.000, 0.639, 1)
ACCENT_BLUE   = (0.000, 0.706, 0.847, 1)
TEXT_PRIMARY   = (0.878, 0.969, 0.980, 1)
TEXT_SECONDARY = (0.502, 0.796, 0.769, 1)
DANGER_RED     = (1.000, 0.322, 0.322, 1)

BUBBLE_SENT   = (0.000, 0.898, 0.800, 0.18)
BUBBLE_RECV   = (0.067, 0.133, 0.251, 0.95)


# ═══════════════════════════════════════════════════════════
#  KV DEFINITIONS
# ═══════════════════════════════════════════════════════════

Builder.load_string("""
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp
#:import Animation kivy.animation.Animation

# ──── Splash Screen ────────────────────────────────────
<SplashScreen>:
    name: "splash"
    md_bg_color: 0.039, 0.086, 0.157, 1

    # ── Background gradient canvas ──
    canvas.before:
        # Deep navy base
        Color:
            rgba: 0.039, 0.086, 0.157, 1
        Rectangle:
            pos: self.pos
            size: self.size
        # Subtle radial glow at center (large soft circle)
        Color:
            rgba: 0.000, 0.898, 0.800, 0.04
        Ellipse:
            pos: self.center_x - dp(300), self.center_y - dp(100)
            size: dp(600), dp(600)
        # Secondary glow (green tint, offset)
        Color:
            rgba: 0.000, 1.000, 0.639, 0.03
        Ellipse:
            pos: self.center_x - dp(200), self.center_y - dp(250)
            size: dp(400), dp(500)

    MDBoxLayout:
        orientation: "vertical"
        spacing: dp(0)
        padding: [dp(40), dp(40), dp(40), dp(30)]
        md_bg_color: 0, 0, 0, 0

        Widget:
            size_hint_y: 0.22

        # ── Glow ring behind logo ──
        FloatLayout:
            size_hint: None, None
            size: dp(220), dp(220)
            pos_hint: {"center_x": 0.5}

            # Outer glow aura
            Widget:
                id: splash_glow_outer
                size_hint: None, None
                size: dp(240), dp(240)
                pos_hint: {"center_x": 0.5, "center_y": 0.5}
                opacity: 0
                canvas:
                    Color:
                        rgba: 0.000, 0.898, 0.800, 0.12
                    Ellipse:
                        pos: self.x, self.y
                        size: self.size
                    Color:
                        rgba: 0.000, 1.000, 0.639, 0.06
                    Ellipse:
                        pos: self.x + dp(15), self.y + dp(15)
                        size: self.width - dp(30), self.height - dp(30)

            # Inner glow ring
            Widget:
                id: splash_glow_inner
                size_hint: None, None
                size: dp(200), dp(200)
                pos_hint: {"center_x": 0.5, "center_y": 0.5}
                opacity: 0
                canvas:
                    Color:
                        rgba: 0.000, 0.898, 0.800, 0.25
                    Line:
                        ellipse: self.x, self.y, self.width, self.height
                        width: dp(1.5)

            # ── Logo with rounded corners (Stencil clipping) ──
            Widget:
                id: splash_stencil
                size_hint: None, None
                size: dp(180), dp(180)
                pos_hint: {"center_x": 0.5, "center_y": 0.5}
                opacity: 0

                canvas.before:
                    StencilPush
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(32), dp(32), dp(32), dp(32)]
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
                        radius: [dp(32), dp(32), dp(32), dp(32)]
                    StencilPop

            # Border ring around logo
            Widget:
                id: splash_logo_border
                size_hint: None, None
                size: dp(184), dp(184)
                pos_hint: {"center_x": 0.5, "center_y": 0.5}
                opacity: 0
                canvas:
                    Color:
                        rgba: 0.000, 0.898, 0.800, 0.5
                    Line:
                        rounded_rectangle: self.x, self.y, self.width, self.height, dp(33)
                        width: dp(2)

        Widget:
            size_hint_y: None
            height: dp(28)

        # ── Title ──
        MDLabel:
            id: splash_title
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
            height: dp(4)

        # ── Subtitle ──
        MDLabel:
            id: splash_subtitle
            text: "End-to-End Encrypted Messaging"
            halign: "center"
            font_style: "Body"
            role: "large"
            theme_text_color: "Custom"
            text_color: 0.502, 0.796, 0.769, 1
            opacity: 0

        Widget:
            size_hint_y: None
            height: dp(6)

        # ── Tagline ──
        MDLabel:
            id: splash_tagline
            text: "Your privacy. Our priority."
            halign: "center"
            font_style: "Body"
            role: "medium"
            theme_text_color: "Custom"
            text_color: 0.502, 0.796, 0.769, 0.5
            opacity: 0

        Widget:
            size_hint_y: 0.25

        # ── Loading bar container ──
        FloatLayout:
            size_hint_y: None
            height: dp(30)

            # Track
            Widget:
                id: splash_track
                size_hint: None, None
                size: dp(200), dp(3)
                pos_hint: {"center_x": 0.5, "center_y": 0.6}
                opacity: 0
                canvas:
                    Color:
                        rgba: 0.102, 0.200, 0.333, 0.6
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(2)]

            # Progress fill
            Widget:
                id: splash_progress
                size_hint: None, None
                size: 0, dp(3)
                pos: splash_track.pos
                opacity: 0
                canvas:
                    Color:
                        rgba: 0.000, 0.898, 0.800, 0.9
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(2)]

        # ── Version text ──
        MDLabel:
            id: splash_version
            text: "v1.0.0"
            halign: "center"
            font_style: "Label"
            role: "small"
            theme_text_color: "Custom"
            text_color: 0.502, 0.796, 0.769, 0.3
            opacity: 0

        Widget:
            size_hint_y: None
            height: dp(8)

# ──── Message Bubble ───────────────────────────────────
<E2EEMessageBubble>:
    orientation: "vertical"
    size_hint_y: None
    height: self.minimum_height
    padding: [dp(14), dp(10), dp(14), dp(8)]
    spacing: dp(4)
    pos_hint: {"right": 1} if root.is_sent else {"x": 0}
    size_hint_x: 0.72

    canvas.before:
        Color:
            rgba: root.bubble_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(16), dp(16), dp(4) if root.is_sent else dp(16), dp(16) if root.is_sent else dp(4)]

    MDLabel:
        text: root.message_text
        font_style: "Body"
        role: "large"
        theme_text_color: "Custom"
        text_color: 0.878, 0.969, 0.980, 1
        adaptive_height: True
        size_hint_x: 1

    MDBoxLayout:
        orientation: "horizontal"
        adaptive_height: True
        spacing: dp(8)

        Widget:

        MDLabel:
            text: root.timestamp_str
            font_style: "Label"
            role: "small"
            theme_text_color: "Custom"
            text_color: 0.502, 0.796, 0.769, 0.7
            adaptive_size: True

        MDLabel:
            text: root.encryption_icon
            font_style: "Label"
            role: "small"
            theme_text_color: "Custom"
            text_color: 0.000, 0.898, 0.800, 0.8
            adaptive_size: True

# ──── Chat List Item ───────────────────────────────────
<ChatListItem>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(72)
    padding: [dp(16), dp(8)]
    spacing: dp(12)
    md_bg_color: 0, 0, 0, 0

    canvas.before:
        Color:
            rgba: (0.102, 0.200, 0.333, 0.5) if root._hovered else (0, 0, 0, 0)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]

    MDBoxLayout:
        orientation: "vertical"
        size_hint_x: None
        width: dp(48)
        padding: [0, dp(4)]

        MDLabel:
            text: root.avatar_letter
            halign: "center"
            valign: "middle"
            font_style: "Title"
            role: "large"
            theme_text_color: "Custom"
            text_color: 0.039, 0.086, 0.157, 1
            size_hint: None, None
            size: dp(44), dp(44)
            pos_hint: {"center_x": 0.5, "center_y": 0.5}

            canvas.before:
                Color:
                    rgba: 0.000, 0.898, 0.800, 1
                Ellipse:
                    pos: self.pos
                    size: self.size

    MDBoxLayout:
        orientation: "vertical"
        spacing: dp(2)
        padding: [0, dp(6)]

        MDLabel:
            text: root.chat_name
            font_style: "Title"
            role: "medium"
            theme_text_color: "Custom"
            text_color: 0.878, 0.969, 0.980, 1
            shorten: True
            shorten_from: "right"

        MDLabel:
            text: root.last_message
            font_style: "Body"
            role: "small"
            theme_text_color: "Custom"
            text_color: 0.502, 0.796, 0.769, 0.8
            shorten: True
            shorten_from: "right"

    MDLabel:
        text: root.time_str
        font_style: "Label"
        role: "small"
        theme_text_color: "Custom"
        text_color: 0.502, 0.796, 0.769, 0.6
        size_hint_x: None
        width: dp(48)
        halign: "right"
        valign: "top"
        padding: [0, dp(10)]

# ──── User Search Result ──────────────────────────────
<UserSearchResult>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(64)
    padding: [dp(16), dp(8)]
    spacing: dp(12)

    canvas.before:
        Color:
            rgba: 0.067, 0.133, 0.251, 0.7
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]

    MDLabel:
        text: root.avatar_letter
        halign: "center"
        valign: "middle"
        font_style: "Title"
        role: "medium"
        theme_text_color: "Custom"
        text_color: 0.039, 0.086, 0.157, 1
        size_hint: None, None
        size: dp(40), dp(40)
        pos_hint: {"center_y": 0.5}

        canvas.before:
            Color:
                rgba: 0.000, 1.000, 0.639, 1
            Ellipse:
                pos: self.pos
                size: self.size

    MDBoxLayout:
        orientation: "vertical"
        spacing: dp(2)
        padding: [0, dp(6)]

        MDLabel:
            text: root.display_name
            font_style: "Title"
            role: "medium"
            theme_text_color: "Custom"
            text_color: 0.878, 0.969, 0.980, 1

        MDLabel:
            text: ("@" + root.username) if root.username else root.email
            font_style: "Body"
            role: "small"
            theme_text_color: "Custom"
            text_color: [0.000, 0.898, 0.800, 0.7] if root.username else [0.502, 0.796, 0.769, 0.7]

# ──── Themed TextField ────────────────────────────────
<AegisTextField>:
    mode: "outlined"
    size_hint_x: 1
    theme_line_color: "Custom"
    line_color_normal: 0.102, 0.200, 0.333, 1
    line_color_focus: 0.000, 0.898, 0.800, 1

# ──── File Attachment Bubble ──────────────────────────
<FileMessageBubble>:
    orientation: "vertical"
    size_hint_y: None
    height: self.minimum_height
    padding: [dp(14), dp(10)]
    spacing: dp(6)
    pos_hint: {"right": 1} if root.is_sent else {"x": 0}
    size_hint_x: 0.72

    canvas.before:
        Color:
            rgba: root.bubble_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(16), dp(16), dp(4) if root.is_sent else dp(16), dp(16) if root.is_sent else dp(4)]

    MDBoxLayout:
        orientation: "horizontal"
        adaptive_height: True
        spacing: dp(10)

        MDIconButton:
            icon: "file-document-outline"
            theme_icon_color: "Custom"
            icon_color: 0.000, 0.898, 0.800, 1

        MDBoxLayout:
            orientation: "vertical"
            adaptive_height: True
            spacing: dp(2)

            MDLabel:
                text: root.file_name
                font_style: "Body"
                role: "medium"
                theme_text_color: "Custom"
                text_color: 0.878, 0.969, 0.980, 1
                adaptive_height: True
                shorten: True

            MDLabel:
                text: root.file_size_str
                font_style: "Label"
                role: "small"
                theme_text_color: "Custom"
                text_color: 0.502, 0.796, 0.769, 0.7
                adaptive_height: True

    MDBoxLayout:
        orientation: "horizontal"
        adaptive_height: True

        Widget:

        MDLabel:
            text: root.timestamp_str
            font_style: "Label"
            role: "small"
            theme_text_color: "Custom"
            text_color: 0.502, 0.796, 0.769, 0.7
            adaptive_size: True

        MDLabel:
            text: "🔒"
            font_style: "Label"
            role: "small"
            adaptive_size: True

# ──── Emoji Picker ──────────────────────────────────────
<EmojiPicker>:
    size_hint: (0.9, 0.45) if root.width < dp(600) else (None, None)
    size: (dp(360), dp(280)) if root.width >= dp(600) else (0, 0)
    background_color: 0, 0, 0, 0
    auto_dismiss: True

    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.053, 0.110, 0.204, 1
        radius: [dp(16)]
        padding: dp(8)
        
        ScrollView:
            MDGridLayout:
                id: emoji_grid
                cols: 8 if root.width >= dp(600) else 6
                adaptive_height: True
                spacing: dp(4)
""")


# ═══════════════════════════════════════════════════════════
#  PYTHON WIDGET CLASSES
# ═══════════════════════════════════════════════════════════

class SplashScreen(Screen):
    """Premium animated splash screen with glow effects and progress bar.

    Features:
    - Logo with rounded corners via StencilView clipping
    - Animated glowing aura behind the logo
    - Multi-stage staggered animation sequence
    - Loading progress bar
    - Pulsing glow loop
    - Auto-navigates to auth after 3.5 seconds
    """

    logo_path: str = StringProperty("")
    next_screen: str = StringProperty("auth")
    _glow_event = None

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Resolve logo path relative to project root
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)
        )))
        self.logo_path = os.path.join(base_dir, "assets", "logo.png")

    def on_enter(self, *args) -> None:
        """Start the premium splash animation sequence."""
        stencil = self.ids.splash_stencil
        glow_outer = self.ids.splash_glow_outer
        glow_inner = self.ids.splash_glow_inner
        logo_border = self.ids.splash_logo_border
        title = self.ids.splash_title
        subtitle = self.ids.splash_subtitle
        tagline = self.ids.splash_tagline
        track = self.ids.splash_track
        progress = self.ids.splash_progress
        version = self.ids.splash_version

        # ── Reset all elements ──
        for widget in [stencil, glow_outer, glow_inner, logo_border,
                       title, subtitle, tagline, track, progress, version]:
            widget.opacity = 0

        # ── Stage 1: Outer glow aura fades in (0.0s) ──
        anim_glow_outer = Animation(opacity=1, duration=0.6, t="out_cubic")
        anim_glow_outer.start(glow_outer)

        # ── Stage 2: Inner glow ring appears (0.2s) ──
        Clock.schedule_once(
            lambda dt: Animation(
                opacity=1, duration=0.5, t="out_cubic"
            ).start(glow_inner),
            0.2,
        )

        # ── Stage 3: Logo scales up with fade (0.3s) ──
        Clock.schedule_once(
            lambda dt: Animation(
                opacity=1, duration=0.7, t="out_back"
            ).start(stencil),
            0.3,
        )

        # ── Stage 4: Border ring appears (0.6s) ──
        Clock.schedule_once(
            lambda dt: Animation(
                opacity=1, duration=0.4, t="out_cubic"
            ).start(logo_border),
            0.6,
        )

        # ── Stage 5: Title fade in (0.8s) ──
        Clock.schedule_once(
            lambda dt: Animation(
                opacity=1, duration=0.5, t="out_cubic"
            ).start(title),
            0.8,
        )

        # ── Stage 6: Subtitle fade in (1.1s) ──
        Clock.schedule_once(
            lambda dt: Animation(
                opacity=1, duration=0.5, t="out_cubic"
            ).start(subtitle),
            1.1,
        )

        # ── Stage 7: Tagline fade in (1.4s) ──
        Clock.schedule_once(
            lambda dt: Animation(
                opacity=1, duration=0.5, t="out_cubic"
            ).start(tagline),
            1.4,
        )

        # ── Stage 8: Loading bar appears and fills (1.6s) ──
        Clock.schedule_once(self._start_loading_bar, 1.6)

        # ── Stage 9: Version text (1.8s) ──
        Clock.schedule_once(
            lambda dt: Animation(
                opacity=1, duration=0.4, t="out_cubic"
            ).start(version),
            1.8,
        )

        # ── Start pulsing glow loop (1.0s) ──
        Clock.schedule_once(self._start_glow_pulse, 1.0)

        # ── Navigate to auth after 3.5s ──
        Clock.schedule_once(self._go_to_auth, 3.5)

    def _start_loading_bar(self, dt: float) -> None:
        """Animate the loading progress bar."""
        track = self.ids.splash_track
        progress = self.ids.splash_progress

        # Show track
        Animation(opacity=1, duration=0.3).start(track)

        # Show and fill progress
        progress.opacity = 1
        anim = Animation(
            width=dp(200),
            duration=1.6,
            t="in_out_cubic",
        )
        anim.start(progress)

    def _start_glow_pulse(self, dt: float) -> None:
        """Start a subtle pulsing animation on the outer glow."""
        glow = self.ids.splash_glow_outer
        pulse_up = Animation(opacity=0.7, duration=1.2, t="in_out_sine")
        pulse_down = Animation(opacity=0.35, duration=1.2, t="in_out_sine")
        pulse_seq = pulse_up + pulse_down
        pulse_seq.repeat = True
        pulse_seq.start(glow)

    def on_leave(self, *args) -> None:
        """Clean up animations when leaving the screen."""
        Animation.cancel_all(self.ids.splash_glow_outer)

    def _go_to_auth(self, dt: float) -> None:
        """Transition to the authentication screen."""
        if self.manager:
            self.manager.current = self.next_screen


class E2EEMessageBubble(MDBoxLayout):
    """Encrypted message bubble widget.

    Attributes
    ----------
    message_text : str
    timestamp_str : str
    is_sent : bool
    encryption_icon : str
    """

    message_text: str = StringProperty("")
    timestamp_str: str = StringProperty("")
    is_sent: bool = BooleanProperty(False)
    encryption_icon: str = StringProperty("🔒")
    bubble_color = ColorProperty(BUBBLE_RECV)

    def on_is_sent(self, instance, value: bool) -> None:
        """Update bubble colour based on sent/received status."""
        self.bubble_color = BUBBLE_SENT if value else BUBBLE_RECV


class FileMessageBubble(MDBoxLayout):
    """File attachment message bubble widget.

    Attributes
    ----------
    file_name : str
    file_size_str : str
    timestamp_str : str
    is_sent : bool
    download_url : str
    """

    file_name: str = StringProperty("")
    file_size_str: str = StringProperty("")
    timestamp_str: str = StringProperty("")
    is_sent: bool = BooleanProperty(False)
    download_url: str = StringProperty("")
    bubble_color = ColorProperty(BUBBLE_RECV)

    def on_is_sent(self, instance, value: bool) -> None:
        self.bubble_color = BUBBLE_SENT if value else BUBBLE_RECV


class ChatListItem(ButtonBehavior, MDBoxLayout):
    """Clickable chat preview item for the sidebar/chat list.

    Attributes
    ----------
    chat_id : str
    chat_name : str
    last_message : str
    time_str : str
    avatar_letter : str
    on_chat_selected : callable
    """

    chat_id: str = StringProperty("")
    chat_name: str = StringProperty("")
    last_message: str = StringProperty("")
    time_str: str = StringProperty("")
    avatar_letter: str = StringProperty("?")
    on_chat_selected = ObjectProperty(None)
    _hovered: bool = BooleanProperty(False)

    def on_release(self):
        if self.on_chat_selected:
            self.on_chat_selected(self.chat_id)


class UserSearchResult(ButtonBehavior, MDBoxLayout):
    """User search result row.

    Attributes
    ----------
    uid : str
    display_name : str
    email : str
    username : str
    avatar_letter : str
    on_user_selected : callable
    """

    uid: str = StringProperty("")
    display_name: str = StringProperty("")
    email: str = StringProperty("")
    username: str = StringProperty("")
    avatar_letter: str = StringProperty("?")
    on_user_selected = ObjectProperty(None)

    def on_release(self):
        if self.on_user_selected:
            self.on_user_selected(self.uid)


class AegisTextField(MDTextField):
    """Pre-themed text field with Aegis styling."""
    pass

class EmojiPicker(ModalView):
    """WhatsApp-style popup grid of emojis.

    Attributes
    ----------
    on_emoji_selected : callable
        Function called with the selected emoji string when tapped.
    """

    on_emoji_selected = ObjectProperty(None)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._populate()

    def _populate(self) -> None:
        from kivy.uix.button import Button
        from kivy.metrics import sp
        import platform

        sys_os = platform.system()
        
        if sys_os == "Darwin":
            emoji_font = "Arial"
        elif sys_os == "Windows":
            emoji_font = "Segoe UI Emoji"
        else:
            emoji_font = "Roboto" # Android fallback handles it natively

        # A curated list of common emojis
        emojis = [
            "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇",
            "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚",
            "😋", "😛", "😝", "😜", "🤪", "🤨", "🧐", "🤓", "😎", "🥸",
            "🤩", "🥳", "😏", "😒", "😞", "😔", "😟", "😕", "🙁", "☹️",
            "😣", "😖", "😫", "😩", "🥺", "😢", "😭", "😤", "😠", "😡",
            "🤬", "🤯", "😳", "🥵", "🥶", "😱", "😨", "😰", "😥", "😓",
            "👍", "👎", "👏", "🙌", "👐", "🤲", "🤝", "🙏", "✌️", "🤞",
            "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔"
        ]
        
        grid = self.ids.emoji_grid
        for e in emojis:
            btn = Button(
                text=e,
                font_size=sp(24),
                font_name=emoji_font,
                background_color=(0, 0, 0, 0),
                color=(1, 1, 1, 1),
                size_hint=(None, None),
                size=(sp(40), sp(40)),
                halign="center",
                valign="middle",
            )
            btn.bind(size=btn.setter('text_size'))
            btn.bind(on_release=lambda instance, em=e: self._select(em))
            grid.add_widget(btn)

    def _select(self, emoji: str) -> None:
        if self.on_emoji_selected:
            self.on_emoji_selected(emoji)
        self.dismiss()

