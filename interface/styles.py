"""Centralized modern styling for the TrueVAR application.

Import COLORS for one-off inline styles and APP_STYLESHEET to apply the
global look (dark theme, rounded cards, flat accent buttons) once on the
QMainWindow.
"""

COLORS = {
    "bg_primary": "#121417",
    "bg_secondary": "#1B1F24",
    "bg_card": "#20242B",
    "border": "#2A2F37",
    "text_primary": "#F5F6F7",
    "text_secondary": "#9AA3AE",
    "accent": "#3D8BFF",
    "accent_hover": "#5C9CFF",
    "success": "#33C481",
    "danger": "#E5484D",
    "blue": "#2F6FE4",
    "red": "#E5484D",
    "warning": "#F2A93B",
}

APP_STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Inter', 'Helvetica Neue', Arial, sans-serif;
    font-size: 14px;
}}

QFrame#card {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
}}

QPushButton {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {COLORS['accent']};
    border-color: {COLORS['accent']};
    color: white;
}}
QPushButton:pressed {{
    background-color: {COLORS['accent_hover']};
}}
QPushButton:disabled {{
    color: {COLORS['text_secondary']};
    background-color: {COLORS['bg_secondary']};
    border-color: {COLORS['border']};
}}

QPushButton#dangerButton:hover {{
    background-color: {COLORS['danger']};
    border-color: {COLORS['danger']};
}}
QPushButton#successButton:hover {{
    background-color: {COLORS['success']};
    border-color: {COLORS['success']};
}}

QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    background-color: {COLORS['bg_secondary']};
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {COLORS['text_secondary']};
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
}}
QTabBar::tab:selected {{
    color: {COLORS['text_primary']};
    background-color: {COLORS['bg_secondary']};
    border-bottom: 2px solid {COLORS['accent']};
}}
QTabBar::tab:hover {{
    color: {COLORS['text_primary']};
}}

QLineEdit, QSpinBox, QKeySequenceEdit {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 8px;
    color: {COLORS['text_primary']};
}}
QLineEdit:focus, QSpinBox:focus, QKeySequenceEdit:focus {{
    border-color: {COLORS['accent']};
}}

QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid {COLORS['border']};
    background: {COLORS['bg_secondary']};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['accent']};
    border-color: {COLORS['accent']};
}}

QSlider::groove:horizontal {{
    height: 6px;
    background: {COLORS['bg_secondary']};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {COLORS['accent']};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}
QSlider::sub-page:horizontal {{
    background: {COLORS['accent']};
    border-radius: 3px;
}}

QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QLabel#sectionTitle {{
    color: {COLORS['text_secondary']};
    font-weight: 800;
    font-size: 12px;
    letter-spacing: 2px;
}}

QLabel#statusOk {{
    color: {COLORS['success']};
    font-weight: 800;
    font-size: 32px;
}}
QLabel#statusBad {{
    color: {COLORS['danger']};
    font-weight: 800;
    font-size: 32px;
}}
"""