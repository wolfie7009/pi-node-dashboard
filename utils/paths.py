import sys
from pathlib import Path


def get_app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent.parent


def get_config_dir():
    config_dir = (
        Path.home()
        / ".config"
        / "pi-node-dashboard"
    )

    config_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return config_dir


APP_DIR = get_app_dir()
CONFIG_DIR = get_config_dir()

CONFIG_FILE = (
    CONFIG_DIR
    / "config.json"
)