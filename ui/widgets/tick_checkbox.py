"""
ui/widgets/tick_checkbox.py

A self-drawn checkbox. Qt's QSS ::indicator styling (background-color,
image) has proven unreliable across platforms/styles — the checkmark
image silently failed to render even after switching from SVG to PNG
data URIs and forcing the Fusion style. Rather than keep guessing at
style-engine quirks, this widget paints its own box, border, and
checkmark directly with QPainter, so rendering is 100% consistent on
every OS regardless of native theme or Qt style.
"""

from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QRect, QSize, QPoint

from ui import theme

BOX_SIZE = 16
GAP = 8


class TickCheckBox(QCheckBox):
    def paintEvent(self, event):
        c = theme.current_colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        box_rect = QRect(0, (self.height() - BOX_SIZE) // 2, BOX_SIZE, BOX_SIZE)

        if self.isChecked():
            painter.setBrush(QColor(theme.ACCENT_BLUE))
            painter.setPen(QPen(QColor(theme.ACCENT_BLUE), 1.5))
        elif self.underMouse():
            painter.setBrush(QColor(c["checkbox_unchecked_bg"]))
            painter.setPen(QPen(QColor(theme.ACCENT_BLUE), 1.5))
        else:
            painter.setBrush(QColor(c["checkbox_unchecked_bg"]))
            painter.setPen(QPen(QColor(c["checkbox_unchecked_border"]), 1.5))

        painter.drawRoundedRect(box_rect, 4, 4)

        if self.isChecked():
            pen = QPen(QColor("white"))
            pen.setWidth(2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            x, y = box_rect.x(), box_rect.y()
            painter.drawPolyline(
                QPoint(x + 3, y + 8), QPoint(x + 6, y + 11), QPoint(x + 13, y + 4)
            )

        if self.text():
            painter.setPen(QColor(c["text"] if self.isChecked() else c["checkbox_text"]))
            text_rect = QRect(BOX_SIZE + GAP, 0, self.width() - BOX_SIZE - GAP, self.height())
            painter.drawText(text_rect, int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), self.text())

    def sizeHint(self) -> QSize:
        fm = self.fontMetrics()
        text_width = fm.horizontalAdvance(self.text()) if self.text() else 0
        extra = (GAP + text_width) if self.text() else 0
        return QSize(BOX_SIZE + extra, max(BOX_SIZE, fm.height()))

    def hitButton(self, pos) -> bool:
        return self.rect().contains(pos)