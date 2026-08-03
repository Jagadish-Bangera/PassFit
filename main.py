"""
main.py

App entry point. Run with: python main.py
"""

import sys
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    # Force Fusion style: Qt's native platform styles (e.g. Windows'
    # "windowsvista") partially ignore custom QSS on certain widgets —
    # notably QCheckBox's ::indicator image, which silently drops the
    # checkmark while still applying the background color. Fusion fully
    # respects our stylesheet on every OS.
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()