import sys

from PyQt6.QtWidgets import QApplication

from hub.ui.crypto_dashboard import CryptoDashboardWindow


def main():
    app = QApplication(sys.argv)
    window = CryptoDashboardWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
