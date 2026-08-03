"""
ui/widgets/arrow_spinbox.py

A QSpinBox with hand-painted up/down arrow glyphs.

Why: Qt's QSS ::up-arrow/::down-arrow styling is unreliable here. The
original border-triangle CSS hack (border-left/right transparent +
border-bottom/top solid, width:0/height:0) renders as a blank/garbled
box under Fusion. Swapping to an SVG data-URI image fixed it in a Linux
test environment, but that only works because the Qt SVG plugin
happened to be present there — it isn't guaranteed to be bundled once
this app is frozen into a single PyInstaller .exe, so on a real Windows
build the arrows silently disappeared again.

Hand-painting the triangles directly with QPainter has no such
dependency — it's the exact same reasoning that led to painting
TickCheckBox's checkmark manually instead of trusting QSS ::indicator
styling. This renders identically on every OS/Qt install, packaged or
not.
"""

from PyQt6.QtWidgets import QSpinBox, QStyle, QStyleOptionSpinBox
from PyQt6.QtGui import QPainter, QColor, QPolygon
from PyQt6.QtCore import Qt, QPoint

from ui import theme


class ArrowSpinBox(QSpinBox):
    def paintEvent(self, event):
        super().paintEvent(event)

        opt = QStyleOptionSpinBox()
        self.initStyleOption(opt)
        style = self.style()

        up_rect = style.subControlRect(
            QStyle.ComplexControl.CC_SpinBox, opt, QStyle.SubControl.SC_SpinBoxUp, self
        )
        down_rect = style.subControlRect(
            QStyle.ComplexControl.CC_SpinBox, opt, QStyle.SubControl.SC_SpinBoxDown, self
        )

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(theme.current_colors()["text"]))

        self._draw_triangle(painter, up_rect, "up")
        self._draw_triangle(painter, down_rect, "down")
        painter.end()

    @staticmethod
    def _draw_triangle(painter: QPainter, rect, direction: str):
        if rect.width() <= 0 or rect.height() <= 0:
            return

        cx = rect.center().x()
        cy = rect.center().y()
        half_w, half_h = 3, 2

        if direction == "up":
            points = [
                QPoint(cx - half_w, cy + half_h),
                QPoint(cx + half_w, cy + half_h),
                QPoint(cx, cy - half_h),
            ]
        else:
            points = [
                QPoint(cx - half_w, cy - half_h),
                QPoint(cx + half_w, cy - half_h),
                QPoint(cx, cy + half_h),
            ]

        painter.drawPolygon(QPolygon(points))