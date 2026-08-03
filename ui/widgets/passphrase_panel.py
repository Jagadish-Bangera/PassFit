"""
ui/widgets/passphrase_panel.py

Passphrase generator panel: word-count control, generate + copy buttons.
Generated passphrase is pushed into the main password field so it
immediately populates the strength meter, same pattern as the password
generator panel (Section 3.7/3.8).
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import pyqtSignal

from core.passphrase import generate_passphrase
from ui.widgets.arrow_spinbox import ArrowSpinBox
from ui import theme


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("sectionLabel")
    return lbl


class PassphrasePanel(QWidget):
    passphrase_generated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addWidget(_section_label("Passphrase Generator"))

        hint = QLabel("Diceware-style — often stronger and easier to remember than a short complex password.")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"font-size: 11px; color: {theme.current_colors()['muted']};")
        layout.addWidget(hint)

        word_row = QHBoxLayout()
        word_label = QLabel("Words")
        word_label.setStyleSheet(f"font-size: 12px; color: {theme.current_colors()['checkbox_text']};")

        self.word_count_spinbox = ArrowSpinBox()
        self.word_count_spinbox.setRange(3, 10)
        self.word_count_spinbox.setValue(5)  # spec default range: 4-6
        self.word_count_spinbox.setFixedWidth(72)

        word_row.addWidget(word_label)
        word_row.addWidget(self.word_count_spinbox)
        word_row.addStretch()
        layout.addLayout(word_row)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        self.generate_button = QPushButton("Generate")
        self.generate_button.setObjectName("primaryButton")
        self.copy_button = QPushButton("Copy")
        self.copy_button.setEnabled(False)
        button_row.addWidget(self.generate_button)
        button_row.addWidget(self.copy_button)
        layout.addLayout(button_row)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"font-size: 11px; color: {theme.current_colors()['muted']};")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.generate_button.clicked.connect(self._on_generate)
        self.copy_button.clicked.connect(self._on_copy)

        self._last_generated = None

    def _on_generate(self):
        word_count = self.word_count_spinbox.value()
        phrase = generate_passphrase(word_count=word_count)
        self._last_generated = phrase
        self.copy_button.setEnabled(True)
        self.status_label.setText("")
        self.passphrase_generated.emit(phrase)

    def _on_copy(self):
        if not self._last_generated:
            return
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._last_generated)
        self.status_label.setText("Copied to clipboard")
        self.status_label.setStyleSheet("font-size: 11px; color: #3dd68c;")