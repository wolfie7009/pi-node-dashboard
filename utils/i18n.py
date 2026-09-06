import json
import locale
import sys
from pathlib import Path


DEFAULT_LANGUAGE = "en"


def get_lang_dir():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "lang"

    return Path(__file__).resolve().parent.parent / "lang"


LANG_DIR = get_lang_dir()
DEFAULT_LANGUAGE = "en"


def get_available_languages():
    if not LANG_DIR.exists():
        return []

    return sorted(
        file.stem
        for file in LANG_DIR.glob("*.json")
        if file.is_file()
    )


def resolve_language(language_code):
    if not language_code:
        return DEFAULT_LANGUAGE

    language_code = str(language_code).strip().lower()
    language_code = language_code.split(".")[0]
    language_code = language_code.replace("-", "_").split("_")[0]

    if language_code in get_available_languages():
        return language_code

    return DEFAULT_LANGUAGE


def get_system_language():
    try:
        language, _ = locale.getlocale()
    except Exception:
        language = None

    return resolve_language(language)


def load_language(language_code):
    language_code = resolve_language(language_code)
    language_file = LANG_DIR / f"{language_code}.json"

    try:
        with open(language_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        if language_code != DEFAULT_LANGUAGE:
            return load_language(DEFAULT_LANGUAGE)

        return {}


def get_language_name(language_code):
    language_code = resolve_language(language_code)
    translations = load_language(language_code)
    return translations.get("language_name", language_code)


def get_language_choices():
    return [
        (language_code, get_language_name(language_code))
        for language_code in get_available_languages()
    ]


_translations = {}
_current_language = DEFAULT_LANGUAGE


def set_language(language_code):
    global _translations
    global _current_language

    _current_language = resolve_language(language_code)
    _translations = load_language(_current_language)


def get_language():
    return _current_language


def tr(key):
    return _translations.get(key, key)
