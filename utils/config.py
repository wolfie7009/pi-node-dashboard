import json

from utils.paths import CONFIG_FILE
from utils.i18n import get_system_language, resolve_language


BASE_DEFAULT_CONFIG = {
    "wallet_address": "",
    "refresh_minutes": 10,
    "cpu_limit": 0,
}


def get_default_config():
    config = BASE_DEFAULT_CONFIG.copy()
    config["language"] = get_system_language()
    return config


def load_config():
    defaults = get_default_config()

    if not CONFIG_FILE.exists():
        save_config(defaults)
        return defaults

    try:
        with open(
            CONFIG_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except Exception:
        save_config(defaults)
        return defaults

    config = defaults.copy()
    config.update(data)

    changed = False

    # Oude config zonder taal: systeemtaal gebruiken.
    if not data.get("language"):
        config["language"] = get_system_language()
        changed = True
    else:
        resolved_language = resolve_language(data.get("language"))
        if resolved_language != data.get("language"):
            config["language"] = resolved_language
            changed = True

    if changed:
        save_config(config)

    return config


def save_config(config):
    with open(
        CONFIG_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            config,
            file,
            indent=2,
            ensure_ascii=False,
        )
