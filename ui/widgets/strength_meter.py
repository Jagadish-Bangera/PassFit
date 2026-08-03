"""
ui/widgets/strength_meter.py

Color-coded strength bar, entropy readout, diversity chips, and issues panel.
Spec ref: Section 3.1 (meter), 3.2 (entropy), 3.3 (diversity), 3.4 (pattern feedback).
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, QLabel, QFrame
)
from PyQt6.QtCore import Qt

from ui import theme

BUCKET_COLORS = {
    "red": "#e5484d",
    "orange": "#f5a524",
    "yellow": "#e8d44d",
    "green": "#3dd68c",
}

BUCKET_FILL = {
    "red": 25,
    "orange": 50,
    "yellow": 75,
    "green": 100,
}

BUCKET_LABELS = {
    "red": "Very Weak",
    "orange": "Weak",
    "yellow": "Reasonable",
    "green": "Strong",
}

CHIP_ACTIVE_STYLE = """
    QLabel {{
        background-color: {bg};
        color: {fg};
        border-radius: 10px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 600;
    }}
"""

CHIP_MISSING_STYLE = """
    QLabel {
        background-color: rgba(229, 72, 77, 0.12);
        color: #e5484d;
        border: 1px solid rgba(229, 72, 77, 0.4);
        border-radius: 10px;
        padding: 3px 9px;
        font-size: 11px;
        font-weight: 600;
    }
"""


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("sectionLabel")
    return lbl


class StrengthMeter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        # --- Strength section ---
        strength_section = QVBoxLayout()
        strength_section.setSpacing(6)
        strength_section.addWidget(_section_label("Strength"))

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(10)
        strength_section.addWidget(self.bar)

        status_row = QHBoxLayout()
        self.status_label = QLabel("Enter a password")
        self.status_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        self.entropy_label = QLabel("Entropy: — bits")
        self.entropy_label.setStyleSheet("font-size: 12px; color: #8b92a5;")
        self.entropy_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        status_row.addWidget(self.entropy_label)
        strength_section.addLayout(status_row)

        layout.addLayout(strength_section)

        # --- Composition section ---
        composition_section = QVBoxLayout()
        composition_section.setSpacing(8)
        composition_section.addWidget(_section_label("Composition"))

        chip_row = QHBoxLayout()
        chip_row.setSpacing(8)
        self.upper_label = QLabel("Uppercase 0")
        self.lower_label = QLabel("Lowercase 0")
        self.digit_label = QLabel("Digits 0")
        self.symbol_label = QLabel("Symbols 0")
        for lbl in (self.upper_label, self.lower_label, self.digit_label, self.symbol_label):
            chip_row.addWidget(lbl)
        chip_row.addStretch()
        composition_section.addLayout(chip_row)

        layout.addLayout(composition_section)

        # --- Issues line: single compact, subtle line (not a bulleted panel) ---
        self.issues_label = QLabel("")
        self.issues_label.setWordWrap(True)
        self.issues_label.setVisible(False)
        layout.addWidget(self.issues_label)

        self.setLayout(layout)

        self._set_bucket("red", entropy_bits=0.0, empty=True)
        self._set_diversity_neutral()

    # ---------------------------------------------------------------
    def update_strength(self, bucket: str, entropy_bits: float):
        self._set_bucket(bucket, entropy_bits, empty=False)

    def update_diversity(self, counts: dict):
        c = theme.current_colors()
        active_style = CHIP_ACTIVE_STYLE.format(bg=c["chip_active_bg"], fg=c["chip_active_text"])

        def apply(lbl: QLabel, label_text: str, count: int):
            lbl.setText(f"{label_text} {count}")
            lbl.setStyleSheet(CHIP_MISSING_STYLE if count == 0 else active_style)

        apply(self.upper_label, "Uppercase", counts["upper"])
        apply(self.lower_label, "Lowercase", counts["lower"])
        apply(self.digit_label, "Digits", counts["digit"])
        apply(self.symbol_label, "Symbols", counts["symbol"])

    def update_issues(self, issue_lines: list):
        if not issue_lines:
            self.issues_label.setVisible(False)
            self.issues_label.setText("")
            return

        is_critical = issue_lines[0].startswith("This password appears")
        color = "#e5484d" if is_critical else "#f5a524"

        text = "  ·  ".join(issue_lines)
        self.issues_label.setText(f"\u26a0  {text}")
        self.issues_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        self.issues_label.setVisible(True)

    def set_diversity_neutral(self):
        """Neutral (non-alarming) state for when there's no password at all yet."""
        self._set_diversity_neutral()

    def _set_diversity_neutral(self):
        self.update_diversity({"upper": 0, "lower": 0, "digit": 0, "symbol": 0})
        c = theme.current_colors()
        for lbl in (self.upper_label, self.lower_label, self.digit_label, self.symbol_label):
            lbl.setStyleSheet(f"""
                QLabel {{
                    background-color: {c['chip_neutral_bg']};
                    color: {c['chip_neutral_text']};
                    border-radius: 10px;
                    padding: 4px 10px;
                    font-size: 11px;
                    font-weight: 600;
                }}
            """)

    def _set_bucket(self, bucket: str, entropy_bits: float, empty: bool):
        color = BUCKET_COLORS[bucket]
        fill = 0 if empty else BUCKET_FILL[bucket]
        c = theme.current_colors()

        self.bar.setValue(fill)
        self.bar.setStyleSheet(
            f"""
            QProgressBar {{
                border: 1px solid {c['card_border']};
                border-radius: 5px;
                background-color: {c['input_bg']};
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
            """
        )

        if empty:
            self.status_label.setText("Enter a password")
            self.status_label.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {c['muted']};")
            self.entropy_label.setText("Entropy: — bits")
            self.entropy_label.setStyleSheet(f"font-size: 12px; color: {c['muted']};")
        else:
            self.status_label.setText(BUCKET_LABELS[bucket])
            self.status_label.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {color};")
            self.entropy_label.setText(f"Entropy: {entropy_bits:.1f} bits")
            self.entropy_label.setStyleSheet(f"font-size: 12px; color: {c['muted']};")