from datetime import datetime

from utils.i18n import tr

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

from services.horizon import (
    get_wallet_details,
)

from ui.transaction_details import (
    TransactionDetailsDialog,
)

class WalletDetailsWidget(QWidget):
    def __init__(
        self,
        wallet_address="",
        parent=None,
    ):
        super().__init__(parent)

        self.wallet_address = wallet_address
        self.loaded_once = False
        self.transaction_records = []

        self.build_ui()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def build_ui(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        layout.setSpacing(12)

        # --------------------------------------------------
        # Titel / refresh
        # --------------------------------------------------

        top_row = QHBoxLayout()

        self.title_label = QLabel(
            tr("wallet_details")
        )

        self.title_label.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: bold;
            }
            """
        )

        self.refresh_button = QPushButton(
            tr("refresh_details")
        )

        self.refresh_button.clicked.connect(
            self.refresh_details
        )

        top_row.addWidget(self.title_label)
        top_row.addStretch()
        top_row.addWidget(
            self.refresh_button
        )

        layout.addLayout(
            top_row
        )

        # --------------------------------------------------
        # Samenvatting
        # --------------------------------------------------

        self.summary_group = QGroupBox(
            tr("mainnet")
        )

        summary_layout = QHBoxLayout()

        self.free_label = QLabel(
            tr("free_value").format(value="-")
        )

        self.locked_label = QLabel(
            tr("locked_value").format(value="-")
        )

        self.total_label = QLabel(
            tr("total_value").format(value="-")
        )

        for label in (
            self.free_label,
            self.locked_label,
            self.total_label,
        ):
            label.setAlignment(
                Qt.AlignCenter
            )

            label.setStyleSheet(
                """
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    padding: 10px;
                }
                """
            )

            summary_layout.addWidget(
                label
            )

        self.summary_group.setLayout(
            summary_layout
        )

        layout.addWidget(
            self.summary_group
        )

        # --------------------------------------------------
        # Claimable balances
        # --------------------------------------------------

        self.claim_group = QGroupBox(
            tr("locked_claimable_balances")
        )

        claim_layout = QVBoxLayout()

        self.claim_table = QTableWidget(
            0,
            4,
        )

        self.claim_table.setHorizontalHeaderLabels(
            [
                tr("amount"),
                tr("unlock_condition"),
                tr("balance_id"),
                tr("sponsor"),
            ]
        )

        self.claim_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.claim_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.claim_table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents,
        )

        self.claim_table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.Stretch,
        )

        self.claim_table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.Stretch,
        )

        self.claim_table.horizontalHeader().setSectionResizeMode(
            3,
            QHeaderView.Stretch,
        )

        claim_layout.addWidget(
            self.claim_table
        )

        self.claim_group.setLayout(
            claim_layout
        )

        layout.addWidget(
            self.claim_group
        )

        # --------------------------------------------------
        # Transacties
        # --------------------------------------------------

        self.transaction_group = QGroupBox(
            tr("latest_transactions")
        )

        transaction_layout = QVBoxLayout()

        self.transaction_table = QTableWidget(
            0,
            4,
        )

        self.transaction_table.cellDoubleClicked.connect(
            self.open_transaction_details
        )

        self.transaction_table.setHorizontalHeaderLabels(
            [
                tr("date"),
                tr("ledger"),
                tr("success"),
                tr("hash"),
            ]
        )

        self.transaction_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.transaction_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.transaction_table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents,
        )

        self.transaction_table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents,
        )

        self.transaction_table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents,
        )

        self.transaction_table.horizontalHeader().setSectionResizeMode(
            3,
            QHeaderView.Stretch,
        )

        transaction_layout.addWidget(
            self.transaction_table
        )

        self.transaction_group.setLayout(
            transaction_layout
        )

        layout.addWidget(
            self.transaction_group
        )

        # --------------------------------------------------
        # Onderaan
        # --------------------------------------------------

        self.last_update_label = QLabel(
            tr("details_not_loaded")
        )

        self.last_update_label.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            self.last_update_label
        )

    # --------------------------------------------------
    # Taal live vernieuwen
    # --------------------------------------------------

    def retranslate_ui(self):
        self.title_label.setText(tr("wallet_details"))
        self.refresh_button.setText(tr("refresh_details"))
        self.summary_group.setTitle(tr("mainnet"))
        self.claim_group.setTitle(tr("locked_claimable_balances"))
        self.transaction_group.setTitle(tr("latest_transactions"))

        self.claim_table.setHorizontalHeaderLabels(
            [
                tr("amount"),
                tr("unlock_condition"),
                tr("balance_id"),
                tr("sponsor"),
            ]
        )

        self.transaction_table.setHorizontalHeaderLabels(
            [
                tr("date"),
                tr("ledger"),
                tr("success"),
                tr("hash"),
            ]
        )

        if self.loaded_once and self.wallet_address:
            self.refresh_details()
        else:
            self.free_label.setText(tr("free_value").format(value="-"))
            self.locked_label.setText(tr("locked_value").format(value="-"))
            self.total_label.setText(tr("total_value").format(value="-"))
            self.last_update_label.setText(tr("details_not_loaded"))

    # --------------------------------------------------
    # Wallet adres wijzigen
    # --------------------------------------------------

    def set_wallet_address(
        self,
        wallet_address,
    ):
        if wallet_address != self.wallet_address:
            self.wallet_address = wallet_address
            self.loaded_once = False

            self.clear_data()

    # --------------------------------------------------
    # Eerste keer laden
    # --------------------------------------------------

    def load_if_needed(self):
        if not self.loaded_once:
            self.refresh_details()

    # --------------------------------------------------
    # Refresh
    # --------------------------------------------------

    def refresh_details(self):
        if not self.wallet_address:
            self.last_update_label.setText(
                tr("no_wallet_address_set")
            )
            return

        self.refresh_button.setEnabled(
            False
        )

        try:
            data = get_wallet_details(
                self.wallet_address
            )

            self.fill_claimables(
                data["claimables"]
            )

            self.fill_transactions(
                data["transactions"]
            )

            locked = sum(
                float(
                    record.get(
                        "amount",
                        0,
                    )
                )
                for record
                in data["claimables"]
                if record.get("asset") == "native"
            )

            free = data["free"]

            total = free + locked

            self.free_label.setText(
                tr("free_value").format(value=f"{free:.7f} π")
            )

            self.locked_label.setText(
                tr("locked_value").format(value=f"{locked:.7f} π")
            )

            self.total_label.setText(
                tr("total_value").format(value=f"{total:.7f} π")
            )

            self.loaded_once = True

            self.last_update_label.setText(
                tr("details_updated").format(
                    value=datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                )
            )

        except Exception as exc:
            self.last_update_label.setText(
                tr("error_value").format(error=exc)
            )

        finally:
            self.refresh_button.setEnabled(
                True
            )

    # --------------------------------------------------
    # Claimables
    # --------------------------------------------------

    def fill_claimables(
        self,
        records,
    ):
        self.claim_table.setRowCount(
            0
        )

        for record in records:
            row = self.claim_table.rowCount()

            self.claim_table.insertRow(
                row
            )

            amount = record.get(
                "amount",
                "-"
            )

            unlock_text = self.get_unlock_text(
                record
            )

            balance_id = record.get(
                "id",
                "-",
            )

            sponsor = record.get(
                "sponsor",
                "-",
            )

            self.claim_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    f"{amount} π"
                ),
            )

            self.claim_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    unlock_text
                ),
            )

            self.claim_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    self.shorten(
                        balance_id
                    )
                ),
            )

            self.claim_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    self.shorten(
                        sponsor
                    )
                ),
            )

    def get_unlock_text(
        self,
        record,
    ):
        claimants = record.get(
            "claimants",
            [],
        )

        for claimant in claimants:
            destination = claimant.get(
                "destination",
                "",
            )

            if destination != self.wallet_address:
                continue

            predicate = claimant.get(
                "predicate",
                {},
            )

            # Direct abs_before
            if "abs_before" in predicate:
                return (
                    tr("before_date").format(date=self.format_date(
                        predicate[
                            "abs_before"
                        ]
                    ))
                )

            # Pi lockup gebruikt o.a.:
            # not -> abs_before
            not_predicate = predicate.get(
                "not"
            )

            if isinstance(
                not_predicate,
                dict,
            ):
                if (
                    "abs_before"
                    in not_predicate
                ):
                    return (
                        tr("from_date").format(date=self.format_date(
                            not_predicate[
                                "abs_before"
                            ]
                        ))
                    )

        return "-"

    # --------------------------------------------------
    # Transacties
    # --------------------------------------------------

    def fill_transactions(
        self,
        records,
    ):
        self.transaction_records = records

        self.transaction_table.setRowCount(
            0
        )

        for record in records:
            row = (
                self.transaction_table
                .rowCount()
            )

            self.transaction_table.insertRow(
                row
            )

            created_at = record.get(
                "created_at",
                "-"
            )

            ledger = str(
                record.get(
                    "ledger",
                    "-",
                )
            )

            successful = (
                tr("yes")
                if record.get(
                    "successful",
                    False,
                )
                else tr("no")
            )

            tx_hash = record.get(
                "hash",
                "-",
            )

            self.transaction_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    self.format_date(
                        created_at
                    )
                ),
            )

            self.transaction_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    ledger
                ),
            )

            self.transaction_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    successful
                ),
            )

            self.transaction_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    self.shorten(
                        tx_hash,
                        12,
                    )
                ),
            )


    def open_transaction_details(
        self,
        row,
        column,
    ):
        if row < 0:
            return

        if row >= len(
            self.transaction_records
        ):
            return

        transaction = (
            self.transaction_records[row]
        )

        transaction_hash = (
            transaction.get(
                "hash"
            )
        )

        if not transaction_hash:
            return

        dialog = TransactionDetailsDialog(
            transaction_hash,
            self,
        )

        dialog.exec()
        
    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def shorten(
        self,
        value,
        size=8,
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
                "%d-%m-%Y %H:%M"
            )

        except Exception:
            return value

    def clear_data(self):
        self.free_label.setText(
            tr("free_value").format(value="-")
        )

        self.locked_label.setText(
            tr("locked_value").format(value="-")
        )

        self.total_label.setText(
            tr("total_value").format(value="-")
        )

        self.claim_table.setRowCount(
            0
        )

        self.transaction_table.setRowCount(
            0
        )

        self.last_update_label.setText(
            tr("details_not_loaded")
        )