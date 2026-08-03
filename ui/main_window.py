"""
ui/main_window.py

Main application window for PassFit.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QLabel, QFrame, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
import os

from core.entropy import raw_entropy_bits, adjusted_entropy_bits, entropy_to_score_bucket, diversity_counts
from core.pattern_detection import detect_all_patterns, pattern_penalty_chars, feedback_lines
from core.dictionary_check import check_dictionary
from core.crack_time import estimate_crack_times
from core.passphrase import passphrase_entropy_bits
from ui.widgets.strength_meter import StrengthMeter
from ui.widgets.crack_time_grid import CrackTimeGrid
from ui.widgets.generator_panel import GeneratorPanel
from ui.widgets.passphrase_panel import PassphrasePanel
from ui.widgets.tick_checkbox import TickCheckBox
from ui import theme


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PassFit")
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        
        # Locked size per user request: no resize, no maximize.
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setStyleSheet(theme.get_stylesheet())

        # Main card
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(20)

        # ============================================================
        # HEADER CONTAINER BOX
        # ============================================================
        header_container = QFrame()
        header_container.setObjectName("headerContainer")
        header_container.setStyleSheet("""
            QFrame#headerContainer {
                background-color: rgba(79, 140, 255, 0.06);
                border: 1px solid rgba(79, 140, 255, 0.12);
                border-radius: 10px;
                padding: 16px 20px;
            }
        """)
        
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        # Left side: App Icon + Title + Subtitle
        left_header = QVBoxLayout()
        left_header.setSpacing(2)

        # Title row with app icon
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title_row.setContentsMargins(0, 0, 0, 0)

        # Load app icon for header
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.png")
        if os.path.exists(icon_path):
            icon_pixmap = QPixmap(icon_path).scaled(
                28, 28, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            icon_label.setPixmap(icon_pixmap)
        else:
            # Fallback to emoji if icon not found
            icon_label.setText("🔒")
            icon_label.setStyleSheet("font-size: 22px;")

        title = QLabel("PassFit")
        title.setObjectName("appTitle")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")

        title_row.addWidget(icon_label)
        title_row.addWidget(title)
        title_row.addStretch()

        left_header.addLayout(title_row)

        subtitle = QLabel("Offline, real-time password strength analysis.           Nothing you type is ever stored or transmitted.")
        subtitle.setObjectName("appSubtitle")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 12px; color: #8b92a5;")
        left_header.addWidget(subtitle)

        # Right side: Theme toggle
        right_header = QVBoxLayout()
        right_header.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.theme_button = QPushButton("Light mode")
        self.theme_button.setFixedHeight(30)
        self.theme_button.setFixedWidth(100)
        right_header.addWidget(self.theme_button)

        header_layout.addLayout(left_header, stretch=1)
        header_layout.addLayout(right_header)

        layout.addWidget(header_container)

        # ============================================================
        # PASSWORD INPUT
        # ============================================================
        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Type a password to analyze...")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(38)
        input_row.addWidget(self.password_input)

        self.show_password_checkbox = TickCheckBox("Show")
        input_row.addWidget(self.show_password_checkbox)
        layout.addLayout(input_row)

        # ============================================================
        # STRENGTH METER
        # ============================================================
        self.strength_meter = StrengthMeter()
        layout.addWidget(self.strength_meter)

        # ============================================================
        # CRACK TIME GRID
        # ============================================================
        self.crack_time_grid = CrackTimeGrid()
        layout.addWidget(self.crack_time_grid)

        # ============================================================
        # GENERATOR PANEL
        # ============================================================
        self.generator_panel = GeneratorPanel()
        layout.addWidget(self.generator_panel)

        # ============================================================
        # PASSPHRASE PANEL
        # ============================================================
        self.passphrase_panel = PassphrasePanel()
        layout.addWidget(self.passphrase_panel)

        self.setCentralWidget(card)

        # ============================================================
        # WIRING
        # ============================================================
        self.password_input.textChanged.connect(self._on_password_changed)
        self.show_password_checkbox.toggled.connect(self._on_toggle_show_password)
        self.generator_panel.password_generated.connect(self._on_password_generated)
        self.passphrase_panel.passphrase_generated.connect(self._on_passphrase_generated)
        self.theme_button.clicked.connect(self._on_toggle_theme)

        self._pending_passphrase_word_count = None

        # ============================================================
        # SIZE CALCULATION
        # ============================================================
        self.crack_time_grid.update_estimates(estimate_crack_times(40.0))
        self.strength_meter.update_strength("yellow", 40.0)
        self.strength_meter.update_diversity({"upper": 2, "lower": 2, "digit": 2, "symbol": 2})
        self.strength_meter.update_issues([
            "Sequential run: abcd",
            "Keyboard walk: qwerty",
            "Repeated characters: aaaa",
        ])
        self.adjustSize()
        max_size = self.size()

        self._on_password_changed("")

        # Add some padding for comfort
        self.setFixedSize(max_size.width() + 70, max_size.height() + 100)

    def _on_toggle_theme(self):
        theme.toggle_theme()
        self.setStyleSheet(theme.get_stylesheet())
        self.theme_button.setText("Dark mode" if theme.CURRENT_MODE == "light" else "Light mode")

        # Update header container style based on theme
        c = theme.current_colors()
        self._update_header_style(c)

        for w in (self.show_password_checkbox, self.generator_panel.upper_check,
                  self.generator_panel.lower_check, self.generator_panel.digits_check,
                  self.generator_panel.symbols_check, self.generator_panel.length_spinbox,
                  self.passphrase_panel.word_count_spinbox):
            w.update()
        self._on_password_changed(self.password_input.text())

    def _update_header_style(self, c):
        """Update header container colors based on theme."""
        self.findChild(QFrame, "headerContainer").setStyleSheet(f"""
            QFrame#headerContainer {{
                background-color: rgba(79, 140, 255, 0.06);
                border: 1px solid rgba(79, 140, 255, 0.12);
                border-radius: 10px;
                padding: 16px 20px;
            }}
        """)

    def _on_password_generated(self, pw: str):
        self._pending_passphrase_word_count = None
        self.show_password_checkbox.setChecked(True)
        self.password_input.setText(pw)

    def _on_passphrase_generated(self, phrase: str):
        self._pending_passphrase_word_count = len(phrase.split("-"))
        self.show_password_checkbox.setChecked(True)
        self.password_input.setText(phrase)

    def _on_toggle_show_password(self, checked: bool):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.password_input.setEchoMode(mode)

    def _on_password_changed(self, text: str):
        patterns = detect_all_patterns(text) if text else []
        penalty_chars = pattern_penalty_chars(text, patterns) if text else 0
        bits = adjusted_entropy_bits(text, penalty_chars)

        if self._pending_passphrase_word_count is not None:
            bits = passphrase_entropy_bits(self._pending_passphrase_word_count)
            self._pending_passphrase_word_count = None

        dict_result = check_dictionary(text) if text else {"is_common": False, "matched_form": None}
        issue_lines = feedback_lines(patterns, max_lines=3)

        if dict_result["is_common"]:
            bucket = "red"
            if dict_result["matched_form"] == "leetspeak-normalized":
                issue_lines.insert(0, "This password appears in known breach/common-password lists (after normalizing common substitutions)")
            else:
                issue_lines.insert(0, "This password appears in known breach/common-password lists")
        else:
            bucket = entropy_to_score_bucket(bits) if text else "red"

        if not text:
            self.strength_meter._set_bucket("red", 0.0, empty=True)
            self.crack_time_grid.update_estimates([])
            self.crack_time_grid.setVisible(False)
            self.strength_meter.set_diversity_neutral()
        else:
            self.strength_meter.update_strength(bucket, bits)
            crack_time_bits = 8.0 if dict_result["is_common"] else bits
            estimates = estimate_crack_times(crack_time_bits)
            self.crack_time_grid.update_estimates(estimates)
            self.crack_time_grid.setVisible(True)
            self.strength_meter.update_diversity(diversity_counts(text))

        self.strength_meter.update_issues(issue_lines)