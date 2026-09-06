from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QFrame, QVBoxLayout


class StatusPill(QLabel):
    def __init__(self, text="-"):
        super().__init__(text)

        self.setAlignment(Qt.AlignCenter)
        self.setMinimumWidth(120)

        self.set_status(
            text,
            "neutral",
        )

    def set_status(
        self,
        text,
        kind="neutral",
    ):
        self.setText(text)

        styles = {
            "good": """
                QLabel {
                    background: #c8f7d0;
                    color: #145c25;
                    border-radius: 10px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
            """,
            "warn": """
                QLabel {
                    background: #ffe7a8;
                    color: #7a5200;
                    border-radius: 10px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
            """,
            "bad": """
                QLabel {
                    background: #ffd0d0;
                    color: #8a1f1f;
                    border-radius: 10px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
            """,
            "neutral": """
                QLabel {
                    background: #d9d9d9;
                    color: #222;
                    border-radius: 10px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
            """,
        }

        self.setStyleSheet(
            styles[kind]
        )


class ValueCard(QFrame):
    def __init__(self, title):
        super().__init__()

        self.setFrameShape(
            QFrame.StyledPanel
        )

        layout = QVBoxLayout(self)

        self.title_label = QLabel(title)
        self.value_label = QLabel("-")

        self.title_label.setAlignment(
            Qt.AlignCenter
        )

        self.value_label.setAlignment(
            Qt.AlignCenter
        )

        self.title_label.setStyleSheet(
            """
            QLabel {
                font-size: 13px;
                color: #666;
                font-weight: bold;
            }
            """
        )

        self.value_label.setStyleSheet(
            """
            QLabel {
                font-size: 21px;
                font-weight: bold;
                padding: 8px;
            }
            """
        )

        layout.addWidget(
            self.title_label
        )

        layout.addWidget(
            self.value_label
        )

    def set_value(self, value):
        self.value_label.setText(value)