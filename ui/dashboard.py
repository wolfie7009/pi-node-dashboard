from datetime import (
    datetime,
    timedelta,
)

from PySide6.QtCore import (
    Qt,
    QTimer,
)

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QMessageBox,
)

from services.pi_node import (
    get_node_status,
    get_container_uptime,
    node_action,
    set_cpu_limit,
)

from services.horizon import (
    get_wallet_data,
)

from ui.widgets import (
    StatusPill,
    ValueCard,
)

from ui.settings import (
    SettingsDialog,
)

from utils.i18n import tr, set_language

from utils.config import (
    load_config,
    save_config,
)


from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QMessageBox,
    QTabWidget,
)

from ui.wallet_details import (
    WalletDetailsWidget,
)

from ui.node_logs import NodeLogsWidget

from ui.about import AboutDialog

from services.pi_price import (
    get_pi_price,
    get_currency_for_language,
)

from services.updater import (
    check_for_update,
    download_update,
    install_update,
)

VERSION = "1.2.1"


class PiDashboard(QWidget):
    def __init__(self):
        super().__init__()

        self.config = load_config()

        self.wallet_address = (
            self.config
            .get(
                "wallet_address",
                "",
            )
            .strip()
        )

        self.refresh_minutes = int(
            self.config.get(
                "refresh_minutes",
                10,
            )
        )

        self.node_running = False

        self.setWindowTitle(
            f"Pi Node Dashboard v{VERSION}"
        )

        self.resize(
            1000,
            790,
        )

        self.build_ui()

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.refresh_all
        )

        self.update_timer()

        self.refresh_all()

        QTimer.singleShot(
            2000,
            self.check_for_updates,
        )

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        main_layout.setSpacing(16)

        # Titel
        top_row = QHBoxLayout()

        title = QLabel(
            "π  Pi Node Dashboard"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 30px;
                font-weight: bold;
                padding: 10px;
            }
            """
        )

        self.settings_button = QPushButton(
            tr("settings_button")
        )

        self.settings_button.setMinimumHeight(
            36
        )

        self.settings_button.clicked.connect(
            self.open_settings
        )

        self.about_button = QPushButton(
            tr("info_button")
        )

        self.about_button.setMinimumHeight(
            36
        )

        self.about_button.clicked.connect(
            self.open_about
        )

        top_row.addStretch()
        top_row.addWidget(title)
        top_row.addStretch()

        top_row.addWidget(
            self.about_button
        )

        top_row.addWidget(
            self.settings_button
        )

        main_layout.addLayout(
            top_row
        )

        # Samenvatting
        self.summary_label = QLabel(
            tr("checking_status")
        )

        self.summary_label.setAlignment(
            Qt.AlignCenter
        )

        main_layout.addWidget(
            self.summary_label
        )

        self.tabs = QTabWidget()

        self.overview_tab = QWidget()
        self.overview_layout = QVBoxLayout(
            self.overview_tab
        )

        self.wallet_details_tab = (
            WalletDetailsWidget(
                self.wallet_address
            )
        )

        self.node_logs_tab = NodeLogsWidget()

        self.tabs.addTab(
            self.overview_tab,
            tr("overview"),
        )

        self.tabs.addTab(
            self.wallet_details_tab,
            tr("wallet_details"),
        )

        self.tabs.addTab(
            self.node_logs_tab,
            tr("node_logs"),
        )

        self.tabs.currentChanged.connect(
            self.tab_changed
        )

        main_layout.addWidget(
            self.tabs
        )

        # ----------------------------------------------
        # Node
        # ----------------------------------------------

        self.node_group = QGroupBox(
            tr("node_status")
        )

        node_layout = QVBoxLayout()

        status_row = QHBoxLayout()

        self.container_pill = StatusPill()
        self.protocol_pill = StatusPill()
        self.horizon_pill = StatusPill()

        self.container_status_label = QLabel(tr("container"))
        status_row.addWidget(
            self.container_status_label
        )

        status_row.addWidget(
            self.container_pill
        )

        status_row.addSpacing(15)

        self.protocol_status_label = QLabel(tr("protocol"))
        status_row.addWidget(
            self.protocol_status_label
        )

        status_row.addWidget(
            self.protocol_pill
        )

        status_row.addSpacing(15)

        self.horizon_status_label = QLabel(tr("horizon"))
        status_row.addWidget(
            self.horizon_status_label
        )

        status_row.addWidget(
            self.horizon_pill
        )

        node_layout.addLayout(
            status_row
        )

        # Node kaarten
        cards = QHBoxLayout()

        self.block_card = ValueCard(
            tr("block")
        )

        self.quorum_card = ValueCard(
            tr("quorum_block")
        )

        self.incoming_card = ValueCard(
            tr("incoming_peers")
        )

        self.outgoing_card = ValueCard(
            tr("outgoing_peers")
        )

        cards.addWidget(
            self.block_card
        )

        cards.addWidget(
            self.quorum_card
        )

        cards.addWidget(
            self.incoming_card
        )

        cards.addWidget(
            self.outgoing_card
        )

        node_layout.addLayout(
            cards
        )

        self.cpu_label = QLabel(
            "CPU: -"
        )

        self.ram_label = QLabel(
            "RAM: -"
        )

        self.disk_label = QLabel(
            tr("disk_value").format(value="-")
        )

        self.uptime_label = QLabel(
            tr("container_uptime").format(value="-")
        )

        self.cpu_limit_label = QLabel(
            tr("cpu_limit_value").format(value="-")
        )

        self.cpu_profile_label = QLabel(
            tr("cpu_profile_value").format(value="-")
        )

        self.cpu_profile_label.setAlignment(
            Qt.AlignCenter
        )

        self.cpu_profile_label.setMinimumWidth(
            180
        )

        for label in (
            self.cpu_label,
            self.cpu_limit_label, 
            self.ram_label,
            self.disk_label,
            self.uptime_label,
            self.cpu_profile_label,
        ):
            node_layout.addWidget(label)

        self.node_group.setLayout(
            node_layout
        )

        self.overview_layout.addWidget(
            self.node_group
        )

        # ----------------------------------------------
        # Wallet
        # ----------------------------------------------

        self.wallet_group = QGroupBox(
            tr("wallet")
        )

        wallet_layout = QHBoxLayout()

        self.free_card = ValueCard(
            tr("free_upper")
        )

        self.locked_card = ValueCard(
            tr("locked_claimable_upper")
        )

        self.total_card = ValueCard(
            tr("mainnet_total_upper")
        )

        self.value_card = ValueCard(
            tr("estimated_value")
        )

        wallet_layout.addWidget(
            self.free_card
        )

        wallet_layout.addWidget(
            self.locked_card
        )

        wallet_layout.addWidget(
            self.total_card
        )

        wallet_layout.addWidget(
            self.value_card
        )

        self.wallet_group.setLayout(
            wallet_layout
        )

        self.overview_layout.addWidget(
            self.wallet_group
        )

        # ----------------------------------------------
        # Knoppen
        # ----------------------------------------------

        buttons = QHBoxLayout()

        self.refresh_button = QPushButton(
            tr("refresh_now")
        )

        self.start_button = QPushButton(
            tr("start")
        )

        self.stop_button = QPushButton(
            tr("stop")
        )

        self.restart_button = QPushButton(
            tr("restart")
        )

        for button in (
            self.refresh_button,
            self.start_button,
            self.stop_button,
            self.restart_button,
        ):
            button.setMinimumHeight(
                36
            )

        self.refresh_button.clicked.connect(
            self.refresh_all
        )

        self.start_button.clicked.connect(
            self.start_node
        )

        self.stop_button.clicked.connect(
            self.stop_node
        )

        self.restart_button.clicked.connect(
            self.restart_node
        )

        buttons.addWidget(
            self.refresh_button
        )

        buttons.addWidget(
            self.start_button
        )

        buttons.addWidget(
            self.stop_button
        )

        buttons.addWidget(
            self.restart_button
        )

        self.overview_layout.addLayout(
            buttons
        )

        # ----------------------------------------------
        # Refresh info
        # ----------------------------------------------

        self.last_update_label = QLabel(
            tr("last_update").format(value="-")
        )

        self.next_update_label = QLabel(
            tr("next_update").format(value="-")
        )

        self.last_update_label.setAlignment(
            Qt.AlignCenter
        )

        self.next_update_label.setAlignment(
            Qt.AlignCenter
        )

        self.overview_layout.addWidget(
            self.last_update_label
        )

        self.overview_layout.addWidget(
            self.next_update_label
        )

        self.version_label = QLabel(
            tr("version_label").format(version=VERSION)
        )

        self.version_label.setAlignment(
            Qt.AlignRight
        )

        self.version_label.setStyleSheet(
            "color: gray;"
        )

        self.overview_layout.addWidget(
            self.version_label
        )

    # --------------------------------------------------
    # Taal live vernieuwen
    # --------------------------------------------------

    def retranslate_ui(self):
        self.settings_button.setText(tr("settings_button"))
        self.about_button.setText(tr("info_button"))

        self.tabs.setTabText(0, tr("overview"))
        self.tabs.setTabText(1, tr("wallet_details"))
        self.tabs.setTabText(2, tr("node_logs"))

        self.node_group.setTitle(tr("node_status"))
        self.container_status_label.setText(tr("container"))
        self.protocol_status_label.setText(tr("protocol"))
        self.horizon_status_label.setText(tr("horizon"))

        self.block_card.title_label.setText(tr("block"))
        self.quorum_card.title_label.setText(tr("quorum_block"))
        self.incoming_card.title_label.setText(tr("incoming_peers"))
        self.outgoing_card.title_label.setText(tr("outgoing_peers"))
        self.value_card.title_label.setText(tr("estimated_value"))

        self.wallet_group.setTitle(tr("wallet"))
        self.free_card.title_label.setText(tr("free_upper"))
        self.locked_card.title_label.setText(tr("locked_claimable_upper"))
        self.total_card.title_label.setText(tr("mainnet_total_upper"))

        self.refresh_button.setText(tr("refresh_now"))
        self.start_button.setText(tr("start"))
        self.stop_button.setText(tr("stop"))
        self.restart_button.setText(tr("restart"))

        self.version_label.setText(
            tr("version_label").format(version=VERSION)
        )

        self.wallet_details_tab.retranslate_ui()
        self.node_logs_tab.retranslate_ui()

    # --------------------------------------------------
    # Timer
    # --------------------------------------------------

    def update_timer(self):
        self.timer.stop()

        self.timer.start(
            self.refresh_minutes
            * 60
            * 1000
        )

    # --------------------------------------------------
    # Refresh
    # --------------------------------------------------

    def refresh_all(self):
        self.refresh_button.setEnabled(
            False
        )

        QApplication.processEvents()

        try:
            node_data = get_node_status()

            self.apply_node_status(
                node_data
            )

            uptime = get_container_uptime()

            self.uptime_label.setText(
                tr("container_uptime").format(value=uptime)
            )

            self.refresh_wallet()

            self.update_refresh_labels()

        except Exception as exc:
            self.summary_label.setText(
                tr("error_value").format(error=exc)
            )

        finally:
            self.refresh_button.setEnabled(
                True
            )

    def refresh_wallet(self):
        if not self.wallet_address:
            self.free_card.set_value(
                tr("no_wallet_address")
            )

            self.locked_card.set_value(
                "-"
            )

            self.total_card.set_value(
                "-"
            )

            self.value_card.set_value(
                "-"
            )

            return

        try:
            wallet = get_wallet_data(
                self.wallet_address
            )

            self.free_card.set_value(
                f"{wallet['free']:.7f} π"
            )

            self.locked_card.set_value(
                f"{wallet['locked']:.7f} π"
            )

            self.total_card.set_value(
                f"{wallet['total']:.7f} π"
            )

            language = self.config.get(
                "language",
                "en",
            )

            currency, symbol = get_currency_for_language(
                language
            )

            price = get_pi_price(currency)

            if price is not None:
                fiat_value = wallet["total"] * price

                self.value_card.set_value(
                    f"{symbol} {fiat_value:,.2f}"
                )
            else:
                self.value_card.set_value("-")

        except Exception:
            self.free_card.set_value(
                tr("error")
            )

            self.locked_card.set_value(
                "-"
            )

            self.total_card.set_value(
                "-"
            )

            self.value_card.set_value(
                "-"
            )

    def update_refresh_labels(self):
        now = datetime.now()

        next_update = now + timedelta(
            minutes=self.refresh_minutes
        )

        self.last_update_label.setText(
            tr("last_update").format(
                value=now.strftime("%d-%m-%Y %H:%M:%S")
            )
        )

        self.next_update_label.setText(
            tr("next_automatic_update").format(
                time=next_update.strftime("%H:%M:%S"),
                minutes=self.refresh_minutes,
            )
        )

    # --------------------------------------------------
    # Node data
    # --------------------------------------------------

    def apply_node_status(
        self,
        data,
    ):
        self.node_running = (
            "Running"
            in data["container"]
        )

        self.set_status_pill(
            self.container_pill,
            data["container"],
        )

        self.set_status_pill(
            self.protocol_pill,
            data["protocol"],
        )

        self.set_status_pill(
            self.horizon_pill,
            data["horizon"],
        )

        self.block_card.set_value(
            data["block"]
        )

        self.quorum_card.set_value(
            data["quorum"]
        )

        self.incoming_card.set_value(
            data["incoming"]
        )

        self.outgoing_card.set_value(
            data["outgoing"]
        )

        cpu_percent = data[
            "cpu_percent"
        ]

        if cpu_percent is not None:
            cpu_cores = (
                cpu_percent / 100
            )

            self.cpu_label.setText(
                f"CPU: "
                f"{cpu_cores:.2f} cores "
                f"({cpu_percent:.2f}%)"
            )

        else:
            self.cpu_label.setText(
                "CPU: -"
            )

        self.ram_label.setText(
            f"RAM: {data['ram']}"
        )

        self.disk_label.setText(
            tr("disk_value").format(value=data["disk"])
        )

        limit = float(
            self.config.get(
                "cpu_limit",
                0,
            )
        )

        if limit <= 0:
            limit_text = tr("unlimited")
            profile_text = tr("profile_full_power")

            profile_style = """
                QLabel {
                    background: #c8f7d0;
                    color: #145c25;
                    border-radius: 10px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
            """

        elif limit >= 4:
            limit_text = tr("maximum_cores").format(cores=f"{limit:g}")
            profile_text = tr("profile_normal")

            profile_style = """
                QLabel {
                    background: #dff5d8;
                    color: #296b2c;
                    border-radius: 10px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
            """

        elif limit >= 3:
            limit_text = tr("maximum_cores").format(cores=f"{limit:g}")
            profile_text = tr("profile_economy")

            profile_style = """
                QLabel {
                    background: #ffe7a8;
                    color: #7a5200;
                    border-radius: 10px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
            """

        else:
            limit_text = tr("maximum_cores").format(cores=f"{limit:g}")
            profile_text = tr("profile_eco")

            profile_style = """
                QLabel {
                    background: #ffd6b3;
                    color: #8a4300;
                    border-radius: 10px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
            """

        self.cpu_limit_label.setText(
            tr("cpu_limit_value").format(value=limit_text)
        )

        self.cpu_profile_label.setText(
            tr("cpu_profile_value").format(value=profile_text)
        )

        self.cpu_profile_label.setStyleSheet(
            profile_style
        )

        self.start_button.setEnabled(
            not self.node_running
        )

        self.stop_button.setEnabled(
            self.node_running
        )

        self.restart_button.setEnabled(
            self.node_running
        )

        if (
            self.node_running
            and "synced"
            in data["protocol"].lower()
            and "synced"
            in data["horizon"].lower()
        ):
            self.summary_label.setText(
                tr("everything_normal")
            )

            self.summary_label.setStyleSheet(
                """
                QLabel {
                    color: #187a35;
                    font-size: 16px;
                    font-weight: bold;
                }
                """
            )

        else:
            self.summary_label.setText(
                tr("node_not_fully_synced")
            )

            self.summary_label.setStyleSheet(
                """
                QLabel {
                    color: #9a6a00;
                    font-size: 16px;
                    font-weight: bold;
                }
                """
            )

    def set_status_pill(
        self,
        pill,
        value,
    ):
        lower = value.lower()

        if (
            "synced" in lower
            or "running" in lower
        ):
            kind = "good"

        elif (
            "syncing" in lower
            or "catching" in lower
            or "starting" in lower
        ):
            kind = "warn"

        elif (
            "stopped" in lower
            or "error" in lower
            or "failed" in lower
        ):
            kind = "bad"

        else:
            kind = "neutral"

        status_key = {
            "running": "status_running",
            "synced": "status_synced",
            "synced!": "status_synced",
            "syncing": "status_syncing",
            "catching up": "status_catching_up",
            "starting": "status_starting",
            "stopped": "status_stopped",
            "error": "status_error",
            "failed": "status_failed",
        }.get(lower.strip())

        display_value = (
            tr(status_key)
            if status_key
            else value
        )

        pill.set_status(
            display_value,
            kind,
        )

    # --------------------------------------------------
    # Settings
    # --------------------------------------------------

    def tab_changed(
        self,
        index,
    ):
        current_tab = self.tabs.widget(index)

        if current_tab is self.wallet_details_tab:
            self.wallet_details_tab.load_if_needed()

        elif current_tab is self.node_logs_tab:
            self.node_logs_tab.load_if_needed()


    def open_settings(self):
        dialog = SettingsDialog(
            self.config,
            self,
        )

        if dialog.exec():
            old_cpu_limit = float(
                self.config.get(
                    "cpu_limit",
                    0,
                )
            )

            old_language = self.config.get(
                "language",
                "en",
            )

            new_config = (
                dialog.get_config()
            )

            new_cpu_limit = float(
                new_config.get(
                    "cpu_limit",
                    0,
                )
            )

            new_language = new_config.get(
                "language",
                "en",
            )

            try:
                save_config(
                    new_config
                )

                self.config = new_config

                self.wallet_address = (
                    self.config.get(
                        "wallet_address",
                        "",
                    ).strip()
                )

                self.wallet_details_tab.set_wallet_address(
                    self.wallet_address
                )

                self.refresh_minutes = int(
                    self.config.get(
                        "refresh_minutes",
                        10,
                    )
                )

                self.update_timer()

                if (
                    new_cpu_limit
                    != old_cpu_limit
                ):
                    set_cpu_limit(
                        new_cpu_limit
                    )

                if new_language != old_language:
                    set_language(new_language)
                    self.retranslate_ui()

                self.refresh_all()

            except Exception as exc:
                QMessageBox.critical(
                    self,
                    tr("settings"),
                    tr("settings_apply_error").format(error=exc),
                )


    # --------------------------------------------------
    # About
    # --------------------------------------------------

    def open_about(self):
        dialog = AboutDialog(
            VERSION,
            self,
        )

        dialog.exec()

    # --------------------------------------------------
    # Node acties
    # --------------------------------------------------

    def start_node(self):
        self.run_action(
            "start"
        )

    def stop_node(self):
        answer = QMessageBox.question(
            self,
            tr("stop_node_title"),
            tr("stop_node_question"),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer == QMessageBox.Yes:
            self.run_action(
                "stop"
            )

    def restart_node(self):
        answer = QMessageBox.question(
            self,
            tr("restart_node_title"),
            tr("restart_node_question"),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer == QMessageBox.Yes:
            self.run_action(
                "restart"
            )

    def run_action(
        self,
        action,
    ):
        try:
            node_action(
                action
            )

            self.refresh_all()

        except Exception as exc:
            QMessageBox.critical(
                self,
                tr("pi_node_error"),
                str(exc),
            )

    # --------------------------------------------------
    # Updates
    # --------------------------------------------------

    def check_for_updates(self):
        try:
            update = check_for_update(
                VERSION
            )

            if not update:
                return

            latest_version = update[
                "version"
            ]

            box = QMessageBox(self)

            box.setWindowTitle(
                tr("update_available_title")
            )

            box.setText(
                tr("update_available_message").format(
                    current=VERSION,
                    latest=latest_version,
                )
            )

            yes_button = box.addButton(
                tr("yes"),
                QMessageBox.AcceptRole,
            )

            no_button = box.addButton(
                tr("no"),
                QMessageBox.RejectRole,
            )

            box.exec()

            if box.clickedButton() != yes_button:
                return

        except Exception:
            # Geen internet of GitHub niet bereikbaar:
            # dashboard gewoon normaal laten werken.
            pass


    def download_and_install_update(
        self,
        update,
    ):
        try:
            QApplication.setOverrideCursor(
                Qt.WaitCursor
            )

            deb_path = download_update(
                update
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                tr("update_error_title"),
                tr(
                    "update_download_error"
                ).format(
                    error=exc
                ),
            )

            return

        finally:
            QApplication.restoreOverrideCursor()

            box = QMessageBox(self)

            box.setWindowTitle(
                tr("update_ready_title")
            )

            box.setText(
                tr("update_ready_message").format(
                    version=update["version"],
                )
            )

            yes_button = box.addButton(
                tr("yes"),
                QMessageBox.AcceptRole,
            )

            no_button = box.addButton(
                tr("no"),
                QMessageBox.RejectRole,
            )

            box.exec()

            if box.clickedButton() != yes_button:
                return

        try:
            success = install_update(
                deb_path
            )

            if success:
                QMessageBox.information(
                    self,
                    tr(
                        "update_complete_title"
                    ),
                    tr(
                        "update_complete_message"
                    ),
                )

            else:
                QMessageBox.warning(
                    self,
                    tr(
                        "update_error_title"
                    ),
                    tr(
                        "update_install_error"
                    ),
                )

        except Exception as exc:
            QMessageBox.critical(
                self,
                tr("update_error_title"),
                tr(
                    "update_install_error_detail"
                ).format(
                    error=exc
                ),
            )