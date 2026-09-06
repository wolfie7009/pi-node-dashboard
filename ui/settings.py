from utils.i18n import get_language_choices, resolve_language, tr

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QPushButton,
    QFormLayout,
    QMessageBox,
)


class SettingsDialog(QDialog):
    def __init__(
        self,
        config,
        parent=None,
    ):
        super().__init__(parent)

        self.config = config.copy()

        self.setWindowTitle(
            tr("settings_window_title")
        )

        self.resize(
            520,
            300,
        )

        self.build_ui()

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        form = QFormLayout()

        # Wallet
        self.wallet_input = QLineEdit()

        self.wallet_input.setText(
            self.config.get(
                "wallet_address",
                "",
            )
        )

        self.wallet_input.setPlaceholderText(
            "G..."
        )

        form.addRow(
            tr("public_wallet_address"),
            self.wallet_input,
        )

        # Refresh
        self.refresh_input = QSpinBox()

        self.refresh_input.setRange(
            1,
            60,
        )

        self.refresh_input.setSuffix(
            tr("minutes_suffix")
        )

        self.refresh_input.setValue(
            int(
                self.config.get(
                    "refresh_minutes",
                    10,
                )
            )
        )

        form.addRow(
            tr("automatic_refresh"),
            self.refresh_input,
        )

        # CPU
        self.cpu_combo = QComboBox()

        self.cpu_combo.addItem(
            tr("unlimited"),
            0,
        )

        self.cpu_combo.addItem(
            tr("maximum_cores").format(cores=4),
            4,
        )

        self.cpu_combo.addItem(
            tr("maximum_cores").format(cores=3),
            3,
        )

        self.cpu_combo.addItem(
            tr("maximum_cores").format(cores=2),
            2,
        )

        current_cpu = float(
            self.config.get(
                "cpu_limit",
                0,
            )
        )

        for index in range(
            self.cpu_combo.count()
        ):
            if (
                float(
                    self.cpu_combo.itemData(
                        index
                    )
                )
                == current_cpu
            ):
                self.cpu_combo.setCurrentIndex(
                    index
                )
                break

        form.addRow(
            tr("cpu_profile_field"),
            self.cpu_combo,
        )

        # Taal
        self.language_combo = QComboBox()

        for language_code, language_name in get_language_choices():
            self.language_combo.addItem(
                language_name,
                language_code,
            )

        current_language = resolve_language(
            self.config.get(
                "language",
                "en",
            )
        )

        for index in range(
            self.language_combo.count()
        ):
            if (
                self.language_combo.itemData(index)
                == current_language
            ):
                self.language_combo.setCurrentIndex(index)
                break

        form.addRow(
            tr("language_field"),
            self.language_combo,
        )

        main_layout.addLayout(
            form
        )

        info = QLabel(
            tr("cpu_limit_info")
        )

        info.setWordWrap(True)

        main_layout.addWidget(
            info
        )

        button_row = QHBoxLayout()

        cancel_button = QPushButton(
            tr("cancel")
        )

        save_button = QPushButton(
            tr("save")
        )

        cancel_button.clicked.connect(
            self.reject
        )

        save_button.clicked.connect(
            self.validate_and_accept
        )

        button_row.addStretch()

        button_row.addWidget(
            cancel_button
        )

        button_row.addWidget(
            save_button
        )

        main_layout.addLayout(
            button_row
        )

    def validate_and_accept(self):
        wallet = (
            self.wallet_input
            .text()
            .strip()
        )

        if wallet and not wallet.startswith(
            "G"
        ):
            QMessageBox.warning(
                self,
                tr("wallet_address_title"),
                tr("wallet_address_invalid"),
            )

            return

        self.config[
            "wallet_address"
        ] = wallet

        self.config[
            "refresh_minutes"
        ] = self.refresh_input.value()

        self.config[
            "cpu_limit"
        ] = self.cpu_combo.currentData()

        self.config[
            "language"
        ] = self.language_combo.currentData()

        self.accept()

    def get_config(self):
        return self.config