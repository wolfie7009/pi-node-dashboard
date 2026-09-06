from datetime import datetime

from utils.i18n import tr

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
)

from services.horizon import (
    get_transaction_details,
)


class TransactionDetailsDialog(QDialog):
    def __init__(
        self,
        transaction_hash,
        parent=None,
    ):
        super().__init__(parent)

        self.transaction_hash = transaction_hash

        self.setWindowTitle(
            tr("transaction_details_title")
        )

        self.resize(
            900,
            600,
        )

        self.build_ui()
        self.load_data()

    def build_ui(self):
        layout = QVBoxLayout(self)

        # --------------------------------------------------
        # Algemene gegevens
        # --------------------------------------------------

        info_group = QGroupBox(
            tr("transaction")
        )

        info_layout = QFormLayout()

        self.date_label = QLabel("-")
        self.ledger_label = QLabel("-")
        self.success_label = QLabel("-")
        self.source_label = QLabel("-")
        self.fee_label = QLabel("-")

        self.hash_label = QLabel("-")
        self.hash_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )
        self.hash_label.setWordWrap(True)

        self.source_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )
        self.source_label.setWordWrap(True)

        info_layout.addRow(
            tr("date_field"),
            self.date_label,
        )

        info_layout.addRow(
            tr("ledger_field"),
            self.ledger_label,
        )

        info_layout.addRow(
            tr("success_field"),
            self.success_label,
        )

        info_layout.addRow(
            tr("source_account_field"),
            self.source_label,
        )

        info_layout.addRow(
            tr("fee_charged_field"),
            self.fee_label,
        )

        info_layout.addRow(
            tr("hash_field"),
            self.hash_label,
        )

        info_group.setLayout(
            info_layout
        )

        layout.addWidget(
            info_group
        )

        # --------------------------------------------------
        # Operations
        # --------------------------------------------------

        operations_group = QGroupBox(
            tr("operations")
        )

        operations_layout = QVBoxLayout()

        self.operations_table = QTableWidget(
            0,
            4,
        )

        self.operations_table.setHorizontalHeaderLabels(
            [
                tr("type"),
                tr("amount"),
                tr("account_destination"),
                tr("details"),
            ]
        )

        self.operations_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.operations_table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents,
        )

        self.operations_table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents,
        )

        self.operations_table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.Stretch,
        )

        self.operations_table.horizontalHeader().setSectionResizeMode(
            3,
            QHeaderView.Stretch,
        )

        operations_layout.addWidget(
            self.operations_table
        )

        operations_group.setLayout(
            operations_layout
        )

        layout.addWidget(
            operations_group
        )

        # --------------------------------------------------
        # Sluiten
        # --------------------------------------------------

        close_button = QPushButton(
            tr("close")
        )

        close_button.clicked.connect(
            self.accept
        )

        layout.addWidget(
            close_button
        )

    def load_data(self):
        try:
            data = get_transaction_details(
                self.transaction_hash
            )

            transaction = data[
                "transaction"
            ]

            operations = data[
                "operations"
            ]

            self.fill_transaction(
                transaction
            )

            self.fill_operations(
                operations
            )

        except Exception as exc:
            self.date_label.setText(
                tr("error_value").format(error=exc)
            )

    def fill_transaction(
        self,
        transaction,
    ):
        created_at = transaction.get(
            "created_at",
            "-",
        )

        self.date_label.setText(
            self.format_date(
                created_at
            )
        )

        self.ledger_label.setText(
            str(
                transaction.get(
                    "ledger",
                    "-",
                )
            )
        )

        self.success_label.setText(
            tr("yes")
            if transaction.get(
                "successful",
                False,
            )
            else tr("no")
        )

        self.source_label.setText(
            transaction.get(
                "source_account",
                "-",
            )
        )

        fee = transaction.get(
            "fee_charged",
            "-"
        )

        self.fee_label.setText(
            str(fee)
        )

        self.hash_label.setText(
            transaction.get(
                "hash",
                "-",
            )
        )

    def fill_operations(
        self,
        operations,
    ):
        self.operations_table.setRowCount(
            0
        )

        for operation in operations:
            row = (
                self.operations_table
                .rowCount()
            )

            self.operations_table.insertRow(
                row
            )

            op_type = operation.get(
                "type",
                "-",
            )

            amount = self.get_amount(
                operation
            )

            account = self.get_account(
                operation
            )

            details = self.get_details(
                operation
            )

            self.operations_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    op_type
                ),
            )

            self.operations_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    amount
                ),
            )

            self.operations_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    account
                ),
            )

            self.operations_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    details
                ),
            )

    def get_amount(
        self,
        operation,
    ):
        # Normale operation met direct amount veld
        amount = operation.get(
            "amount"
        )

        if amount is not None:
            return f"{amount} π"

        # --------------------------------------------------
        # Claimable balance claim
        # --------------------------------------------------

        if (
            operation.get("type")
            == "claim_claimable_balance"
        ):
            effects = operation.get(
                "effects",
                [],
            )

            for effect in effects:
                if (
                    effect.get("type")
                    == "claimable_balance_claimed"
                ):
                    effect_amount = effect.get(
                        "amount"
                    )

                    if effect_amount is not None:
                        return (
                            f"{effect_amount} π"
                        )

                if (
                    effect.get("type")
                    == "account_credited"
                ):
                    effect_amount = effect.get(
                        "amount"
                    )

                    if effect_amount is not None:
                        return (
                            f"{effect_amount} π"
                        )

        return "-"

    def get_account(
        self,
        operation,
    ):
        for key in (
            "to",
            "from",
            "claimant",
            "source_account",
            "account",
        ):
            value = operation.get(
                key
            )

            if value:
                return self.shorten(
                    value
                )

        return "-"

    def get_details(
        self,
        operation,
    ):
        op_type = operation.get(
            "type",
            "",
        )

        if op_type == "claim_claimable_balance":
            balance_id = operation.get(
                "balance_id",
                "-",
            )

            return tr("claimable_balance_short").format(
                balance_id=self.shorten(balance_id)
            )

        if op_type == "create_claimable_balance":
            return tr("claimable_balance_created")

        if op_type == "payment":
            asset_type = operation.get(
                "asset_type",
                "native",
            )

            return tr("payment_asset").format(
                asset_type=asset_type
            )

        if op_type == "create_account":
            return tr("account_created")

        return "-"

    def shorten(
        self,
        value,
        size=10,
    ):
        if not value:
            return "-"

        if len(value) <= (
            size * 2 + 3
        ):
            return value

        return (
            value[:size]
            + "..."
            + value[-size:]
        )

    def format_date(
        self,
        value,
    ):
        if not value or value == "-":
            return "-"

        try:
            dt = datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00",
                )
            )

            return dt.strftime(
                "%d-%m-%Y %H:%M:%S"
            )

        except Exception:
            return value