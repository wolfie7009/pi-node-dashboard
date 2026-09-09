import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from utils.config import load_config
from utils.i18n import set_language

from ui.dashboard import PiDashboard


if __name__ == "__main__":
    config = load_config()
    set_language(config.get("language", "en"))

    # De UI pas importeren nadat de gekozen taal is geladen.


    app = QApplication(sys.argv)

    icon_path = (
        Path(__file__).resolve().parent
        / "assets"
        / "pi-dashboard.png"
    )

    icon = QIcon(str(icon_path))

    if not icon.isNull():
        app.setWindowIcon(icon)

    window = PiDashboard()
    window.show()

    sys.exit(app.exec())
