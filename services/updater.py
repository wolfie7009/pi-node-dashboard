from pathlib import Path
import subprocess
import requests


GITHUB_API = (
    "https://api.github.com/repos/"
    "wolfie7009/pi-node-dashboard/releases/latest"
)


def version_tuple(version):
    """
    Zet bijvoorbeeld:
    1.2   -> (1, 2)
    1.10  -> (1, 10)
    v2.0  -> (2, 0)
    """
    version = str(version).strip().lower().lstrip("v")

    result = []

    for part in version.split("."):
        number = ""

        for char in part:
            if char.isdigit():
                number += char
            else:
                break

        result.append(
            int(number) if number else 0
        )

    return tuple(result)


def check_for_update(current_version):
    response = requests.get(
        GITHUB_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Pi-Node-Dashboard",
        },
        timeout=8,
    )

    response.raise_for_status()

    data = response.json()

    latest_version = (
        data.get("tag_name", "")
        .strip()
        .lstrip("v")
    )

    if not latest_version:
        return None

    if (
        version_tuple(latest_version)
        <= version_tuple(current_version)
    ):
        return None

    deb_asset = None

    for asset in data.get("assets", []):
        name = asset.get("name", "")

        if name.lower().endswith(".deb"):
            deb_asset = asset
            break

    if not deb_asset:
        return None

    return {
        "version": latest_version,
        "name": deb_asset["name"],
        "url": deb_asset["browser_download_url"],
        "notes": data.get("body", ""),
    }


def download_update(update):
    downloads = Path.home() / "Downloads"
    downloads.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = Path(
        update["name"]
    ).name

    destination = (
        downloads / filename
    )

    with requests.get(
        update["url"],
        headers={
            "User-Agent": "Pi-Node-Dashboard",
        },
        stream=True,
        timeout=30,
    ) as response:

        response.raise_for_status()

        with open(
            destination,
            "wb",
        ) as file:

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):
                if chunk:
                    file.write(chunk)

    return destination


def install_update(deb_path):
    result = subprocess.run(
        [
            "pkexec",
            "apt",
            "install",
            "-y",
            str(deb_path),
        ]
    )

    return result.returncode == 0