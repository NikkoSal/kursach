import sys
import os
from PyQt6.QtWidgets import QApplication
from gui.main_window import CycloneApp

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --no-sandbox --disable-software-rasterizer --ignore-certificate-errors --ignore-ssl-errors"
sys.argv.extend(["--disable-gpu", "--no-sandbox", "--ignore-certificate-errors", "--ignore-ssl-errors"])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CycloneApp()
    window.show()
    sys.exit(app.exec())