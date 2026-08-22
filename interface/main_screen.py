from app.injector import Injector
from app.camera_manager import CameraManager
from app.main_manager import MainManager

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QHBoxLayout,
    QFrame, QSizePolicy, QScrollArea, QPushButton, QLineEdit
)
from PyQt5.QtCore import Qt

from interface.styles import COLORS


class MainScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.camera_manager: CameraManager = Injector.find(CameraManager)
        self.blink_timers = {}
        self.video_widgets = []
        self.init_ui()
        self.start()

    def init_ui(self):
        vertical = QVBoxLayout()
        vertical.setContentsMargins(24, 24, 24, 24)

        # --- Centered status card ---
        card = QFrame()
        card.setObjectName("card")
        card.setMaximumWidth(560)
        card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(48, 48, 48, 48)
        card_layout.setSpacing(14)
        card_layout.setAlignment(Qt.AlignCenter)

        self.dot = QLabel()
        self.dot.setFixedSize(16, 16)
        card_layout.addWidget(self.dot, alignment=Qt.AlignHCenter)

        self.status_label = QLabel("TrueVAR is not recording")
        self.status_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.status_label)

        self.subtitle_label = QLabel("Press the record key to start capturing")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        card_layout.addWidget(self.subtitle_label)

        vertical.addStretch(1)
        vertical.addWidget(card, alignment=Qt.AlignCenter)
        vertical.addStretch(1)

        self.setLayout(vertical)

        # connect recording status
        self.camera_manager.is_recording_stream.connect(self.update_status)
        self.update_status(False)

    def update_status(self, is_recording):
        if is_recording:
            self.status_label.setStyleSheet(
                f"color: {COLORS['success']}; font-weight: 800; font-size: 32px;"
            )
            self.status_label.setText("TrueVAR is recording")
            self.subtitle_label.setText("Capture in progress")
            self.dot.setStyleSheet(f"background-color: {COLORS['success']}; border-radius: 8px;")
        else:
            self.status_label.setStyleSheet(
                f"color: {COLORS['danger']}; font-weight: 800; font-size: 32px;"
            )
            self.status_label.setText("TrueVAR is not recording")
            self.subtitle_label.setText("Press the record key to start capturing")
            self.dot.setStyleSheet(f"background-color: {COLORS['danger']}; border-radius: 8px;")

    def start(self):
        for widget in self.video_widgets:
            widget.start()

    def stop(self):
        for widget in self.video_widgets:
            widget.stop()