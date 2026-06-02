"""Minimal PyQt crypto summary table (Yahoo Finance via yfinance)."""

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from hub.crypto_market import CryptoSummary, fetch_crypto_summaries


class FetchWorker(QThread):
    finished = pyqtSignal(list)
    failed = pyqtSignal(str)

    def run(self):
        try:
            self.finished.emit(fetch_crypto_summaries())
        except Exception as exc:
            self.failed.emit(str(exc))


class CryptoDashboardWindow(QMainWindow):
    COLUMNS = ("Symbol", "Price (USD)", "Change %", "Volume")

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crypto — Most Active (Yahoo Finance)")
        self.resize(640, 420)
        self._worker: FetchWorker | None = None

        root = QWidget()
        layout = QVBoxLayout(root)

        header = QHBoxLayout()
        header.addWidget(QLabel("Fixed majors · sorted by volume · manual refresh"))
        header.addStretch()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        self.status = QLabel("Loading…")
        layout.addWidget(self.status)

        self.setCentralWidget(root)
        self.refresh()

    def refresh(self):
        if self._worker and self._worker.isRunning():
            return
        self.refresh_btn.setEnabled(False)
        self.status.setText("Fetching from Yahoo Finance…")
        self._worker = FetchWorker()
        self._worker.finished.connect(self._on_data)
        self._worker.failed.connect(self._on_error)
        self._worker.finished.connect(lambda: self.refresh_btn.setEnabled(True))
        self._worker.failed.connect(lambda: self.refresh_btn.setEnabled(True))
        self._worker.start()

    def _on_data(self, rows: list[CryptoSummary]):
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(row.symbol))
            self.table.setItem(i, 1, QTableWidgetItem(f"{row.price:,.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{row.change_pct:+.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{row.volume:,.0f}"))
        self.table.resizeColumnsToContents()
        self.status.setText(f"{len(rows)} symbols · by volume")

    def _on_error(self, message: str):
        self.status.setText("Fetch failed")
        QMessageBox.warning(self, "Yahoo Finance", message)
