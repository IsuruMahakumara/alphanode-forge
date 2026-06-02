import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlmodel import Session

from hub.api.core.db import create_db_and_tables, engine
from hub.api.services.portfolio_service import add_transaction, get_portfolios_with_totals


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AlphaNode Forge")
        self.resize(960, 640)
        self.portfolios: list[dict] = []

        root = QWidget()
        layout = QVBoxLayout(root)

        self.portfolio_table = QTableWidget(0, 3)
        self.portfolio_table.setHorizontalHeaderLabels(["ID", "Name", "Total Value"])
        self.portfolio_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.portfolio_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.portfolio_table.itemSelectionChanged.connect(self.on_portfolio_selected)
        layout.addWidget(self.portfolio_table)

        detail_row = QHBoxLayout()
        detail_row.addWidget(QLabel("Positions:"), alignment=Qt.AlignmentFlag.AlignTop)
        self.positions_label = QLabel("Select a portfolio")
        self.positions_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        detail_row.addWidget(self.positions_label, stretch=1)
        layout.addLayout(detail_row)

        form = QFormLayout()
        self.portfolio_id_input = QLineEdit()
        self.symbol_input = QLineEdit()
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.0, 10_000_000.0)
        self.quantity_input.setDecimals(6)
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0.0, 10_000_000.0)
        self.price_input.setDecimals(6)
        self.side_input = QComboBox()
        self.side_input.addItems(["buy", "sell"])

        form.addRow("Portfolio ID", self.portfolio_id_input)
        form.addRow("Symbol", self.symbol_input)
        form.addRow("Quantity", self.quantity_input)
        form.addRow("Price", self.price_input)
        form.addRow("Side", self.side_input)
        layout.addLayout(form)

        self.submit_button = QPushButton("Add Transaction")
        self.submit_button.clicked.connect(self.create_transaction)
        layout.addWidget(self.submit_button)

        self.setCentralWidget(root)
        self.refresh_portfolios()

    def refresh_portfolios(self):
        with Session(engine) as session:
            self.portfolios = get_portfolios_with_totals(session)

        self.portfolio_table.setRowCount(len(self.portfolios))
        for row, portfolio in enumerate(self.portfolios):
            self.portfolio_table.setItem(row, 0, QTableWidgetItem(str(portfolio["id"])))
            self.portfolio_table.setItem(row, 1, QTableWidgetItem(str(portfolio["name"])))
            self.portfolio_table.setItem(row, 2, QTableWidgetItem(f'{portfolio["total_value"]:.2f}'))

        if self.portfolios:
            self.portfolio_table.selectRow(0)
        else:
            self.positions_label.setText("No portfolios yet.")

    def on_portfolio_selected(self):
        row = self.portfolio_table.currentRow()
        if row < 0 or row >= len(self.portfolios):
            return
        positions = self.portfolios[row]["positions"]
        if not positions:
            self.positions_label.setText("No open positions.")
            return
        lines = [f"{symbol}: {qty:.6f}" for symbol, qty in sorted(positions.items())]
        self.positions_label.setText("\n".join(lines))

    def create_transaction(self):
        portfolio_id_raw = self.portfolio_id_input.text().strip()
        symbol = self.symbol_input.text().strip().upper()
        quantity = float(self.quantity_input.value())
        price = float(self.price_input.value())
        side = self.side_input.currentText()

        if not portfolio_id_raw.isdigit():
            QMessageBox.warning(self, "Invalid input", "Portfolio ID must be a whole number.")
            return
        if not symbol:
            QMessageBox.warning(self, "Invalid input", "Symbol is required.")
            return
        if quantity <= 0 or price <= 0:
            QMessageBox.warning(self, "Invalid input", "Quantity and Price must be greater than zero.")
            return

        with Session(engine) as session:
            add_transaction(
                session=session,
                portfolio_id=int(portfolio_id_raw),
                symbol=symbol,
                quantity=quantity,
                price=price,
                side=side,
            )

        self.refresh_portfolios()
        self.symbol_input.clear()
        self.quantity_input.setValue(0.0)
        self.price_input.setValue(0.0)


def main():
    create_db_and_tables()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
