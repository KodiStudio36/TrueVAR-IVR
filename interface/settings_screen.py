from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTabWidget, QFrame, QCheckBox,
    QSizePolicy, QKeySequenceEdit, QFormLayout, QSpinBox, QScrollArea
)
import gi
from PyQt5.QtCore import Qt, pyqtSlot
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

from PyQt5.QtWidgets import (
    QVBoxLayout, QLabel, QPushButton
)
from interface.video_stream_widget import VideoStreamWidget
from interface.styles import COLORS

from app.injector import Injector
from app.key_bind_manager import KeyBindManager
from app.main_manager import MainManager
from app.camera_manager import CameraManager

class SettingsScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.key_bind_manager: KeyBindManager = Injector.find(KeyBindManager)
        self.camera_manager: CameraManager = Injector.find(CameraManager)
        self.hub: MainManager = Injector.find(MainManager)
        self.video_widgets = []
        self.is_update = False
        self.init_ui()

    def init_ui(self):
        # Main layout with tabs
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.tabs = QTabWidget()
        self.tabs.setContentsMargins(0, 0, 0, 0)

        # Camera Settings Tab
        self.init_tabs()
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def init_tabs(self):
        self.camera_settings_tab = QWidget()
        self.init_camera_settings_tab()
        self.tabs.addTab(self.camera_settings_tab, "Video Replay")

        self.key_bind_settings_tab = QWidget()
        self.init_key_binding_tab()
        self.tabs.addTab(self.key_bind_settings_tab, "Key Binds")

    def init_key_binding_tab(self):
        outer_layout = QVBoxLayout(self.key_bind_settings_tab)
        outer_layout.setContentsMargins(16, 16, 16, 16)

        card = QFrame()
        card.setObjectName("card")
        self.key_bind_layout = QFormLayout(card)
        self.key_bind_layout.setContentsMargins(24, 24, 24, 24)
        self.key_bind_layout.setSpacing(14)
        self.key_bind_layout.setLabelAlignment(Qt.AlignRight)

        self.key_bind_widgets = {}

        for field_name in self.key_bind_manager._settings_fields:
            seq_edit = QKeySequenceEdit()
            seq_edit.setKeySequence(getattr(self.key_bind_manager, field_name))
            seq_edit.editingFinished.connect(
            lambda fn_captured=field_name, widget=seq_edit: self.update_key_bind(
                    fn_captured, 
                    widget.keySequence().toString(), 
                    widget
                )
            )
            self.key_bind_widgets[field_name] = seq_edit
            label = QLabel(field_name.replace("_", " ").title() + ":")
            label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")
            self.key_bind_layout.addRow(label, seq_edit)

        outer_layout.addWidget(card)
        outer_layout.addStretch(1)

    def update_key_bind(self, fn, key, widget):
        if key != "":
            setattr(self.key_bind_manager, fn, key)
        widget.clearFocus()

    def init_camera_settings_tab(self):
        # 1. Main layout for the tab itself
        tab_layout = QVBoxLayout(self.camera_settings_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)

        # 2. Create Scroll Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # 3. Create a container widget for all the content
        container = QWidget()
        # AlignTop is the secret sauce—it prevents widgets from stretching to fill height
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setAlignment(Qt.AlignTop) 
        layout.setSpacing(16)

        # --- TOP SETTINGS SECTION ---
        start_frame = QFrame()
        start_frame.setObjectName("card")
        start_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        form_layout = QFormLayout(start_frame)
        form_layout.setContentsMargins(20, 18, 20, 18)
        form_layout.setSpacing(10)

        release_label = QLabel("Release Records:")
        release_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")

        delete_toggle = QCheckBox()
        delete_toggle.setChecked(self.camera_manager.delete_records)
        delete_toggle.clicked.connect(lambda x: self.set_release_records(x))

        form_layout.addRow(release_label, delete_toggle)

        layout.addWidget(start_frame)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(12)

        add_button = QPushButton("+  Add New Camera")
        add_button.setObjectName("successButton")
        add_button.setFixedHeight(46)
        add_button.clicked.connect(self.add_camera)
        buttons_row.addWidget(add_button)

        remove_button = QPushButton("\u2013  Remove Camera")
        remove_button.setObjectName("dangerButton")
        remove_button.setFixedHeight(46)
        remove_button.clicked.connect(self.remove_camera)
        buttons_row.addWidget(remove_button)

        layout.addLayout(buttons_row)

        # --- NEW VERTICAL LAYOUT LOGIC ---
        for idx in range(int(not self.camera_manager.is_scoreboard), self.camera_manager.camera_count + 1):
            cam_frame = QFrame()
            cam_frame.setObjectName("card")
            cam_frame.setFixedHeight(190) # Keep height consistent
            cam_row_layout = QHBoxLayout(cam_frame)
            cam_row_layout.setContentsMargins(16, 16, 16, 16)
            cam_row_layout.setSpacing(16)

            # Left side: Video Stream
            stream_pipe = f"{self.camera_manager._shmsrc(idx)} ! video/x-raw,width={'1280' if idx == 0 else self.camera_manager.res_width},height={'720' if idx == 0 else self.camera_manager.res_height},framerate={self.camera_manager.fps}/1,format=NV12 ! videoconvert ! videoscale ! video/x-raw,format=RGB,width=272,height=153 ! queue ! appsink name=sink emit-signals=True sync=True drop=False"
            preview_label = VideoStreamWidget(stream_pipe, 272, 153)
            self.video_widgets.append(preview_label)
            cam_row_layout.addWidget(preview_label)

            # Right side: Controls
            details_layout = QVBoxLayout()
            details_layout.setAlignment(Qt.AlignTop)
            details_layout.setSpacing(6)
            
            cam_name = "Scoreboard" if idx == 0 else (f"Camera {idx}")
            name_label = QLabel(cam_name)
            name_label.setStyleSheet("font-weight: 800; font-size: 16px;")
            details_layout.addWidget(name_label)

            status_label = QLabel("Live preview")
            status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
            details_layout.addWidget(status_label)

            cam_row_layout.addLayout(details_layout, stretch=1)
            layout.addWidget(cam_frame)

        # 4. Finalizing the ScrollView
        scroll_area.setWidget(container)
        tab_layout.addWidget(scroll_area)

    def add_camera(self):
        self.camera_manager.add_camera()
        self.update_camera_list()

    def remove_camera(self):
        self.camera_manager.remove_camera()
        self.update_camera_list()

    def update_camera_list(self):
        self.clear_layout()
        self.stop()
        self.video_widgets.clear()
        self.init_tabs()
        self.start()

    def set_release_records(self, delete_records):
        self.camera_manager.delete_records = delete_records

    def refresh_camera_list(self):
        self.update_camera_list()

    def clear_layout(self):
        while self.tabs.count() > 0:
            self.tabs.removeTab(0)

    def start(self):
        for widget in self.video_widgets:
            widget.start()
    
    def stop(self):
        for widget in self.video_widgets:
            widget.stop()