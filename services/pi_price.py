import requests


CURRENCIES = {
    "nl": ("eur", "€"),
    "en": ("usd", "$"),
    "de": ("eur", "€"),
    "es": ("eur", "€"),
    "fr": ("eur", "€"),
    "it": ("eur", "€"),
    "pt": ("eur", "€"),
    "pl": ("pln", "zł"),
    "tr": ("try", "₺"),
    "id": ("idr", "Rp"),
    "vi": ("vnd", "₫"),
    "zh": ("cny", "¥"),
    "ja": ("jpy", "¥"),
    "ko": ("krw", "₩"),
}


def get_currency_for_language(language):
    return CURRENCIES.get(
        language,
        ("usd", "$"),
    )


def get_pi_price(currency="eur"):
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": "pi-network",
                "vs_currencies": currency,
            },
            timeout=5,
        )

        response.raise_for_status()

        data = response.json()

        return float(
            data["pi-network"][currency]
        )

    except Exception:
        return None