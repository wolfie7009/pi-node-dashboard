from PySide6.QtCore import Qt
from utils.i18n import tr

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
)


class AboutDialog(QDialog):
    def __init__(self, version, parent=None):
        super().__init__(parent)

        self.setWindowTitle(tr("about_window_title"))
        self.resize(460, 360)

        layout = QVBoxLayout(self)

        title = QLabel("π  Pi Node Dashboard")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: bold;
                padding: 12px;
            }
            """
        )

        version_label = QLabel(tr("version_label").format(version=version))
        version_label.setAlignment(Qt.AlignCenter)

        text = QLabel(
            tr("about_description")
        )

        text.setAlignment(Qt.AlignLeft)
        text.setWordWrap(True)

        close_button = QPushButton(tr("close"))
        close_button.clicked.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(version_label)
        layout.addWidget(text)
        layout.addStretch()
        layout.addWidget(close_button)