"""
Aegis – Recovery Setup Screen
=============================
Displays the 24-word recovery seed phrase to the user after registration.
Allows saving the phrase to a text file.
"""

from __future__ import annotations

import os
from typing import List

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

from core.crypto_engine import encrypt_private_key_with_phrase

Builder.load_string("""
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp
#:import Animation kivy.animation.Animation

<RecoverySetupScreen>:
    name: "recovery_setup"
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
        spacing: dp(24)

        MDLabel:
            text: "Recovery Seed Phrase"
            halign: "center"
            font_style: "Headline"
            role: "small"
            theme_text_color: "Custom"
            text_color: 0.000, 0.898, 0.800, 1
            bold: True
            adaptive_height: True

        MDLabel:
            text: "Write down or save these 24 words in the exact order.\\nYou will need them to recover your account if you forget your password."
            halign: "center"
            font_style: "Body"
            role: "medium"
            theme_text_color: "Custom"
            text_color: 1.0, 0.322, 0.322, 1
            adaptive_height: True

        # Container for the words
        MDBoxLayout:
            orientation: "vertical"
            md_bg_color: 0.053, 0.110, 0.204, 1
            radius: [dp(16)]
            padding: [dp(16), dp(16), dp(16), dp(16)]

            ScrollView:
                do_scroll_x: False
                bar_width: dp(4)
                
                MDGridLayout:
                    id: words_grid
                    cols: 2
                    adaptive_height: True
                    spacing: dp(12), dp(12)

        MDBoxLayout:
            orientation: "horizontal"
            adaptive_height: True
            spacing: dp(16)

            MDButton:
                style: "outlined"
                size_hint_x: 0.5
                theme_line_color: "Custom"
                line_color: 0.000, 0.898, 0.800, 0.5
                on_release: root.show_save_dialog()

                MDButtonText:
                    text: "Save as .txt"
                    theme_text_color: "Custom"
                    text_color: 0.000, 0.898, 0.800, 1

            MDButton:
                style: "filled"
                size_hint_x: 0.5
                theme_bg_color: "Custom"
                md_bg_color: 0.000, 0.898, 0.800, 1
                on_release: root.on_next()

                MDButtonText:
                    text: "Next"
                    theme_text_color: "Custom"
                    text_color: 0.039, 0.086, 0.157, 1
                    bold: True

<SaveFileDialog>:
    title: "Save Recovery Phrase"
    size_hint: 0.9, 0.9
    
    BoxLayout:
        orientation: 'vertical'
        FileChooserListView:
            id: filechooser
            path: root.default_path
            filters: ['']
            dirselect: True
        
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            padding: dp(10)
            spacing: dp(10)
            
            Button:
                text: "Cancel"
                on_release: root.dismiss()
            Button:
                text: "Save Here"
                on_release: root.save(filechooser.path)
""")

class SaveFileDialog(Popup):
    default_path = StringProperty(os.path.expanduser("~"))
    
    def __init__(self, content_to_save: str, **kwargs):
        super().__init__(**kwargs)
        self.content_to_save = content_to_save

    def save(self, path: str):
        filepath = os.path.join(path, "aegis_recovery_phrase.txt")
        try:
            with open(filepath, 'w') as f:
                f.write(self.content_to_save)
            self.dismiss()
            from kivy.app import App
            app = App.get_running_app()
            MDSnackbar(
                MDSnackbarText(text=f"Saved to {filepath}"),
                y=dp(24),
                pos_hint={"center_x": 0.5},
            ).open()
        except Exception as e:
            MDSnackbar(
                MDSnackbarText(text=f"Failed to save: {e}"),
                y=dp(24),
                pos_hint={"center_x": 0.5},
            ).open()

class RecoverySetupScreen(Screen):
    firebase = ObjectProperty(None, allownone=True)
    recovery_phrase = ListProperty([])
    
    pending_email = StringProperty("")
    pending_password = StringProperty("")
    pending_name = StringProperty("")
    pending_username = StringProperty("")
    private_key = ObjectProperty(None, allownone=True)
    public_key_b64 = StringProperty("")

    def on_enter(self, *args):
        self.populate_words()

    def populate_words(self):
        self.ids.words_grid.clear_widgets()
        for i, word in enumerate(self.recovery_phrase):
            box = MDBoxLayout(
                orientation="horizontal", 
                adaptive_height=True, 
                md_bg_color=(0.039, 0.086, 0.157, 1), 
                radius=[dp(8)], 
                padding=[dp(12), dp(8)]
            )
            
            lbl = MDLabel(
                text=f"[color=#00e5cc]{i+1:02d}.[/color] {word}",
                markup=True,
                font_style="Title", role="medium",
                theme_text_color="Custom", text_color=(0.878, 0.969, 0.980, 1),
                adaptive_height=True
            )
            box.add_widget(lbl)
            self.ids.words_grid.add_widget(box)

    def show_save_dialog(self):
        content = "AEGIS RECOVERY SEED PHRASE\n\n"
        content += "WARNING: Never share this with anyone. If you lose this, you lose access to your encrypted messages if you forget your password.\n\n"
        for i, word in enumerate(self.recovery_phrase):
            content += f"{i+1}. {word}\n"
            
        dialog = SaveFileDialog(content_to_save=content)
        dialog.open()

    def on_next(self):
        verify_screen = self.manager.get_screen("recovery_verify")
        verify_screen.firebase = self.firebase
        verify_screen.recovery_phrase = self.recovery_phrase
        verify_screen.pending_email = self.pending_email
        verify_screen.pending_password = self.pending_password
        verify_screen.pending_name = self.pending_name
        verify_screen.pending_username = self.pending_username
        verify_screen.private_key = self.private_key
        verify_screen.public_key_b64 = self.public_key_b64
        
        self.manager.current = "recovery_verify"
