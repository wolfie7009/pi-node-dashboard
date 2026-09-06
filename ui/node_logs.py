from datetime import datetime

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QPlainTextEdit,
    QMessageBox,
)

from services.pi_node import get_node_logs
from utils.i18n import tr


class NodeLogsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.loaded_once = False

        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)

        controls = QHBoxLayout()

        self.lines_label = QLabel(
            tr("log_lines")
        )

        self.lines_combo = QComboBox()

        for count in (
            100,
            200,
            500,
            1000,
        ):
            self.lines_combo.addItem(
                str(count),
                count,
            )

        self.lines_combo.setCurrentIndex(1)

        self.refresh_button = QPushButton(
            tr("refresh_logs")
        )

        self.copy_button = QPushButton(
            tr("copy_logs")
        )

        self.clear_button = QPushButton(
            tr("clear_logs")
        )

        self.refresh_button.clicked.connect(
            self.refresh_logs
        )

        self.copy_button.clicked.connect(
            self.copy_logs
        )

        self.clear_button.clicked.connect(
            self.clear_logs
        )

        controls.addWidget(
            self.lines_label
        )

        controls.addWidget(
            self.lines_combo
        )

        controls.addStretch()

        controls.addWidget(
            self.refresh_button
        )

        controls.addWidget(
            self.copy_button
        )

        controls.addWidget(
            self.clear_button
        )

        layout.addLayout(
            controls
        )

        self.log_view = QPlainTextEdit()

        self.log_view.setReadOnly(
            True
        )

        self.log_view.setLineWrapMode(
            QPlainTextEdit.NoWrap
        )

        self.log_view.setPlaceholderText(
            tr("logs_not_loaded")
        )

        self.log_view.setStyleSheet(
            """
            QPlainTextEdit {
                font-family: monospace;
                font-size: 12px;
            }
            """
        )

        layout.addWidget(
            self.log_view
        )

        self.updated_label = QLabel(
            tr("logs_last_update").format(
                value="-"
            )
        )

        layout.addWidget(
            self.updated_label
        )

    def load_if_needed(self):
        if not self.loaded_once:
            self.refresh_logs()

    def refresh_logs(self):
        self.refresh_button.setEnabled(
            False
        )

        QApplication.processEvents()

        try:
            lines = self.lines_combo.currentData()

            text = get_node_logs(
                lines
            )

            if not text:
                text = tr("no_logs")

            self.log_view.setPlainText(
                text
            )

            self.log_view.moveCursor(
                QTextCursor.End
            )

            self.updated_label.setText(
                tr("logs_last_update").format(
                    value=datetime.now().strftime(
                        "%d-%m-%Y %H:%M:%S"
                    )
                )
            )

            self.loaded_once = True

        except Exception as exc:
            QMessageBox.critical(
                self,
                tr("node_logs"),
                tr("logs_load_error").format(
                    error=exc
                ),
            )

        finally:
            self.refresh_button.setEnabled(
                True
            )

    def copy_logs(self):
        text = self.log_view.toPlainText()

        if not text:
            return

        QApplication.clipboard().setText(
            text
        )

    def clear_logs(self):
        self.log_view.clear()

        self.updated_label.setText(
            tr("logs_last_update").format(
                value="-"
            )
        )

    def retranslate_ui(self):
        self.lines_label.setText(
            tr("log_lines")
        )

        self.refresh_button.setText(
            tr("refresh_logs")
        )

        self.copy_button.setText(
            tr("copy_logs")
        )

        self.clear_button.setText(
            tr("clear_logs")
        )

        self.log_view.setPlaceholderText(
            tr("logs_not_loaded")
        )

        current = self.updated_label.text()

        if ":" in current:
            value = current.split(":", 1)[1].strip()
        else:
            value = "-"

        self.updated_label.setText(
            tr("logs_last_update").format(
                value=value
            )
        )
