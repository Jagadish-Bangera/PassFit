"""
ui/theme.py

Stylesheet definitions and theme state. Spec ref: Section 3.9.

Some widgets (StrengthMeter, CrackTimeGrid, TickCheckBox) set colors
dynamically in Python rather than pure QSS, because they change based on
live data (strength bucket, missing character classes, etc.). Those
widgets import COLORS/CURRENT_MODE from here directly so they stay in
sync with the toggle instead of hardcoding neutral colors themselves.

Semantic/status colors (red=weak, green=strong, model card accents) are
intentionally the SAME in both themes — they carry meaning, not just
decoration, and should stay recognizable either way. Only neutral chrome
(backgrounds, borders, muted text) actually flips.
"""

CURRENT_MODE = "dark"  # "dark" | "light" — in-memory only, per Section 3.9 (no disk write)

COLORS = {
    "dark": {
        "window_bg": "#0f1115",
        "card_bg": "#171a21",
        "card_border": "#262b36",
        "text": "#e6e8eb",
        "text_strong": "#ffffff",
        "muted": "#8b92a5",
        "section_label": "#6b7280",
        "input_bg": "#0f1115",
        "input_border": "#2b3140",
        "input_text": "#f2f3f5",
        "chip_neutral_bg": "rgba(139, 146, 165, 0.10)",
        "chip_neutral_text": "#8b92a5",
        "chip_active_bg": "rgba(79, 140, 255, 0.14)",
        "chip_active_text": "#8fb8ff",
        "button_bg": "#1c212b",
        "button_border": "#2b3140",
        "button_hover": "#232935",
        "button_disabled_bg": "#14171e",
        "button_disabled_text": "#565d6b",
        "checkbox_unchecked_bg": "#1a1e27",
        "checkbox_unchecked_border": "#3a4152",
        "checkbox_text": "#b7bdc9",
        "crack_card_bg": "#12151b",
        "slider_groove": "#262b36",
    },
    "light": {
        "window_bg": "#f4f5f7",
        "card_bg": "#ffffff",
        "card_border": "#e1e4e9",
        "text": "#20242c",
        "text_strong": "#0f1115",
        "muted": "#5b6472",
        "section_label": "#7a8291",
        "input_bg": "#f7f8fa",
        "input_border": "#d3d7de",
        "input_text": "#1a1d23",
        "chip_neutral_bg": "rgba(91, 100, 114, 0.08)",
        "chip_neutral_text": "#5b6472",
        "chip_active_bg": "rgba(47, 107, 237, 0.10)",
        "chip_active_text": "#2f6bed",
        "button_bg": "#eef0f3",
        "button_border": "#d3d7de",
        "button_hover": "#e3e6eb",
        "button_disabled_bg": "#f1f2f4",
        "button_disabled_text": "#a8adb6",
        "checkbox_unchecked_bg": "#ffffff",
        "checkbox_unchecked_border": "#c3c8d1",
        "checkbox_text": "#3d4451",
        "crack_card_bg": "#f7f8fa",
        "slider_groove": "#dde1e7",
    },
}

# Colors that stay constant across both themes (semantic meaning, not chrome)
ACCENT_BLUE = "#4f8cff"
STATUS_RED = "#e5484d"
STATUS_ORANGE = "#f5a524"
STATUS_YELLOW = "#e8d44d"
STATUS_GREEN = "#3dd68c"


def current_colors() -> dict:
    return COLORS[CURRENT_MODE]


def toggle_theme():
    global CURRENT_MODE
    CURRENT_MODE = "light" if CURRENT_MODE == "dark" else "dark"


def get_stylesheet() -> str:
    c = current_colors()
    return f"""
QMainWindow {{
    background-color: {c['window_bg']};
}}

QWidget {{
    color: {c['text']};
    font-family: 'Segoe UI', sans-serif;
    background-color: transparent;
}}

QFrame#card {{
    background-color: {c['card_bg']};
    border: 1px solid {c['card_border']};
    border-radius: 12px;
}}

QLabel#appTitle {{
    font-size: 21px;
    font-weight: 600;
    color: {c['text_strong']};
}}

QLabel#appSubtitle {{
    font-size: 12px;
    color: {c['muted']};
}}

QLabel#sectionLabel {{
    font-size: 10px;
    font-weight: 600;
    color: {c['section_label']};
    letter-spacing: 1px;
}}

QLineEdit {{
    background-color: {c['input_bg']};
    border: 1px solid {c['input_border']};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 14px;
    color: {c['input_text']};
    selection-background-color: {ACCENT_BLUE};
}}

QLineEdit:focus {{
    border: 1px solid {ACCENT_BLUE};
}}

QProgressBar {{
    border: 1px solid {c['card_border']};
    border-radius: 6px;
    background-color: {c['input_bg']};
    height: 10px;
}}

QProgressBar::chunk {{
    border-radius: 5px;
}}

QPushButton {{
    background-color: {c['button_bg']};
    color: {c['text']};
    border: 1px solid {c['button_border']};
    border-radius: 7px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {c['button_hover']};
}}

QPushButton:disabled {{
    color: {c['button_disabled_text']};
    background-color: {c['button_disabled_bg']};
}}

QPushButton#primaryButton {{
    background-color: {ACCENT_BLUE};
    border: 1px solid {ACCENT_BLUE};
    color: #ffffff;
}}

QPushButton#primaryButton:hover {{
    background-color: #6f9fff;
}}

QSpinBox {{
    background-color: {c['input_bg']};
    border: 1px solid {c['input_border']};
    border-radius: 6px;
    padding: 3px 6px;
    color: {c['input_text']};
    font-size: 12px;
    min-width: 46px;
}}

QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {c['button_bg']};
    border: none;
    width: 18px;
}}

QSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    border-top-right-radius: 6px;
    border-bottom: 1px solid {c['input_border']};
}}

QSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    border-bottom-right-radius: 6px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {c['button_hover']};
}}

QSpinBox::up-arrow, QSpinBox::down-arrow {{
    image: none;
    width: 0;
    height: 0;
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {c['slider_groove']};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {ACCENT_BLUE};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}

QSlider::sub-page:horizontal {{
    background: {ACCENT_BLUE};
    border-radius: 2px;
}}
"""


# Backwards-compatible constant some modules may still import directly.
DARK_THEME = get_stylesheet() if CURRENT_MODE == "dark" else None