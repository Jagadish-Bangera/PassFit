"""
ui/widgets/generator_panel.py

Password generator panel: length control, character-class toggles,
generate button, copy-to-clipboard. Generated password is pushed into
the main password field so it immediately populates the strength meter
(Section 3.7 requirement).
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.generator import generate_password
from ui.widgets.tick_checkbox import TickCheckBox
from ui.widgets.arrow_spinbox import ArrowSpinBox
from ui import theme


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("sectionLabel")
    return lbl


class GeneratorPanel(QWidget):
    # Emits the generated password so main_window can push it into the
    # password field (and trigger the live strength analysis).
    password_generated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addWidget(_section_label("Password Generator"))

        # Length control
        length_row = QHBoxLayout()
        length_label = QLabel("Length")
        length_label.setStyleSheet(f"font-size: 12px; color: {theme.current_colors()['checkbox_text']};")

        self.length_slider = QSlider(Qt.Orientation.Horizontal)
        self.length_slider.setRange(4, 64)
        self.length_slider.setValue(16)

        self.length_spinbox = ArrowSpinBox()
        self.length_spinbox.setRange(4, 64)
        self.length_spinbox.setValue(16)
        self.length_spinbox.setFixedWidth(72)

        length_row.addWidget(length_label)
        length_row.addWidget(self.length_slider)
        length_row.addWidget(self.length_spinbox)
        layout.addLayout(length_row)

        # Character-class toggles
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(14)
        self.upper_check = TickCheckBox("A-Z")
        self.lower_check = TickCheckBox("a-z")
        self.digits_check = TickCheckBox("0-9")
        self.symbols_check = TickCheckBox("!@#")
        for cb in (self.upper_check, self.lower_check, self.digits_check, self.symbols_check):
            cb.setChecked(True)
            toggle_row.addWidget(cb)
        toggle_row.addStretch()
        layout.addLayout(toggle_row)

        # Generate + copy buttons
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

        # --- wiring ---
        self.length_slider.valueChanged.connect(self.length_spinbox.setValue)
        self.length_spinbox.valueChanged.connect(self.length_slider.setValue)
        self.generate_button.clicked.connect(self._on_generate)
        self.copy_button.clicked.connect(self._on_copy)

        self._last_generated = None

    def _on_generate(self):
        length = self.length_spinbox.value()
        try:
            pw = generate_password(
                length=length,
                use_upper=self.upper_check.isChecked(),
                use_lower=self.lower_check.isChecked(),
                use_digits=self.digits_check.isChecked(),
                use_symbols=self.symbols_check.isChecked(),
            )
        except ValueError as e:
            self.status_label.setText(str(e))
            self.status_label.setStyleSheet("font-size: 11px; color: #e5484d;")
            return

        self._last_generated = pw
        self.copy_button.setEnabled(True)
        self.status_label.setText("")
        self.password_generated.emit(pw)

    def _on_copy(self):
        if not self._last_generated:
            return
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._last_generated)
        self.status_label.setText("Copied to clipboard")
        self.status_label.setStyleSheet("font-size: 11px; color: #3dd68c;")