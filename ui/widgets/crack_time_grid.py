"""
ui/widgets/crack_time_grid.py

Side-by-side display of crack-time estimates across the three attack
models (Section 3.6 — the "headline feature"). Shown as three cards so
the difference between hashing algorithms is immediately visible, not
buried in one number.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame

from ui import theme

CARD_BORDER_COLORS = {
    "online_throttled": "#4f8cff",
    "offline_fast": "#e5484d",
    "offline_slow": "#3dd68c",
}


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("sectionLabel")
    return lbl


class CrackTimeGrid(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(_section_label("Estimated Time to Crack"))

        self.row = QHBoxLayout()
        self.row.setSpacing(10)

        self.cards = {}
        for key in ("online_throttled", "offline_fast", "offline_slow"):
            card, value_label, desc_label = self._build_card()
            self.cards[key] = (card, value_label, desc_label)
            self.row.addWidget(card)

        layout.addLayout(self.row)
        self.setLayout(layout)
        self.setVisible(False)  # hidden until there's a password to estimate

    def _build_card(self):
        card = QFrame()
        card.setObjectName("crackTimeCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(2)

        title_label = QLabel("")
        title_label.setObjectName("crackCardTitle")
        title_label.setStyleSheet("font-size: 10px; font-weight: 700;")
        title_label.setWordWrap(True)

        value_label = QLabel("—")
        value_label.setStyleSheet("font-size: 15px; font-weight: 700;")
        value_label.setWordWrap(True)

        desc_label = QLabel("")
        desc_label.setObjectName("crackCardDesc")
        desc_label.setStyleSheet("font-size: 10px;")
        desc_label.setWordWrap(True)

        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        card_layout.addWidget(desc_label)

        card._title_label = title_label
        card._desc_label = desc_label
        return card, value_label, desc_label

    def update_estimates(self, estimates: list):
        """estimates: list of core.crack_time.CrackTimeEstimate"""
        if not estimates:
            self.setVisible(False)
            return

        self.setVisible(True)
        c = theme.current_colors()
        for est in estimates:
            card, value_label, desc_label = self.cards[est.key]
            border_color = CARD_BORDER_COLORS.get(est.key, c["card_border"])

            card._title_label.setText(est.label)
            card._title_label.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {c['muted']};")
            value_label.setText(est.human_readable)
            desc_label.setText(est.description)
            desc_label.setStyleSheet(f"font-size: 10px; color: {c['section_label']};")
            card.setStyleSheet(
                f"""
                QFrame#crackTimeCard {{
                    background-color: {c['crack_card_bg']};
                    border: 1px solid {border_color}55;
                    border-left: 3px solid {border_color};
                    border-radius: 6px;
                }}
                """
            )