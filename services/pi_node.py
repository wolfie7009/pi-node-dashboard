import json
import subprocess
from pathlib import Path
import shutil
import re
import requests
from datetime import datetime


def run_command(
    command,
    timeout=30,
):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    return (
        result.returncode,
        result.stdout,
        result.stderr,
    )


def _get_container_image():
    try:
        code, stdout, _ = run_command(
            [
                "docker",
                "inspect",
                "-f",
                "{{.Config.Image}}",
                "mainnet",
            ]
        )

        if code == 0:
            return stdout.strip() or "-"

    except Exception:
        pass

    return "-"


def _short_container_version(image):
    """
    Voorbeeld:
    pinetwork/pi-node-docker:organization-mainnet-v1.0-p26.1.0
    -> p26.1.0
    """
    if not image or image == "-":
        return "-"

    tag = image.rsplit(":", 1)[-1]

    if "-p" in tag:
        return "p" + tag.rsplit("-p", 1)[-1]

    return tag


def _get_core_info():
    """
    Leest de runtime-info rechtstreeks uit Stellar Core.
    """
    try:
        code, stdout, _ = run_command(
            [
                "docker",
                "exec",
                "mainnet",
                "curl",
                "-s",
                "http://127.0.0.1:11626/info",
            ]
        )

        if code != 0 or not stdout.strip():
            return {}

        data = json.loads(stdout)
        return data.get("info", {})

    except Exception:
        return {}


def _get_horizon_info():
    """
    Leest de runtime-info rechtstreeks uit Horizon.
    """
    try:
        code, stdout, _ = run_command(
            [
                "docker",
                "exec",
                "mainnet",
                "curl",
                "-s",
                "http://127.0.0.1:8000/",
            ]
        )

        if code != 0 or not stdout.strip():
            return {}

        return json.loads(stdout)

    except Exception:
        return {}


def get_node_status():
    code, stdout, stderr = run_command(
        ["pi-node", "status"]
    )

    if code != 0:
        raise RuntimeError(stderr or stdout)

    lines = stdout.splitlines()
    section = None

    data = {
        "container": "-",
        "protocol": "-",
        "horizon": "-",
        "block": "-",
        "quorum": "-",
        "incoming": "-",
        "outgoing": "-",
        "cpu_percent": None,
        "ram": "-",
        "disk": "-",

        # Versies
        "container_image": "-",
        "container_version": "-",
        "protocol_version": "-",
        "stellar_core_version": "-",
        "horizon_version": "-",
    }

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("🐳 Container Status"):
            section = "container"
            continue

        if stripped.startswith("⭐ Protocol Status"):
            section = "protocol"
            continue

        if stripped.startswith("🌅 API Status"):
            section = "horizon"
            continue

        if stripped.startswith("🌐 Peer Connections"):
            section = "peers"
            continue

        if section == "container":
            if stripped.startswith("✅ Container:"):
                data["container"] = (
                    stripped
                    .replace("✅ Container:", "")
                    .strip()
                )

            elif stripped.startswith("CPU:"):
                parts = stripped.split("|")

                cpu_text = (
                    parts[0]
                    .replace("CPU:", "")
                    .replace("%", "")
                    .strip()
                )

                try:
                    data["cpu_percent"] = float(cpu_text)
                except ValueError:
                    data["cpu_percent"] = None

                if len(parts) >= 2:
                    data["ram"] = (
                        parts[1]
                        .replace("RAM:", "")
                        .strip()
                    )

            elif stripped.startswith("Disk:"):
                data["disk"] = (
                    stripped
                    .replace("Disk:", "")
                    .strip()
                )

        elif section == "protocol":
            if stripped.startswith("State:"):
                data["protocol"] = (
                    stripped
                    .replace("State:", "")
                    .strip()
                )

            elif stripped.startswith("Block:"):
                data["block"] = (
                    stripped
                    .replace("Block:", "")
                    .strip()
                )

            elif stripped.startswith("Quorum Block:"):
                data["quorum"] = (
                    stripped
                    .replace("Quorum Block:", "")
                    .strip()
                )

        elif section == "horizon":
            if stripped.startswith("State:"):
                data["horizon"] = (
                    stripped
                    .replace("State:", "")
                    .strip()
                )

        elif section == "peers":
            if stripped.startswith("Authenticated:"):
                peer_text = (
                    stripped
                    .replace("Authenticated:", "")
                    .strip()
                )

                for part in peer_text.split(","):
                    part = part.strip()

                    if "incoming" in part:
                        data["incoming"] = part.split()[0]

                    elif "outgoing" in part:
                        data["outgoing"] = part.split()[0]

    # --------------------------------------------------
    # Containerversie
    # --------------------------------------------------

    image = _get_container_image()
    data["container_image"] = image
    data["container_version"] = _short_container_version(image)

    # --------------------------------------------------
    # Stellar Core / protocol runtime-info
    # --------------------------------------------------

    core_info = _get_core_info()

    if core_info:
        data["stellar_core_version"] = str(
            core_info.get("build", "-")
        )

        protocol_version = core_info.get(
            "protocol_version"
        )

        if protocol_version is None:
            protocol_version = (
                core_info
                .get("ledger", {})
                .get("version")
            )

        if protocol_version is not None:
            data["protocol_version"] = str(
                protocol_version
            )

    # --------------------------------------------------
    # Horizon runtime-info
    # --------------------------------------------------

    horizon_info = _get_horizon_info()

    if horizon_info:
        data["horizon_version"] = str(
            horizon_info.get(
                "horizon_version",
                "-"
            )
        )

        # Extra fallback als Core-info niet beschikbaar was.
        if data["stellar_core_version"] == "-":
            data["stellar_core_version"] = str(
                horizon_info.get(
                    "core_version",
                    "-"
                )
            )

        if data["protocol_version"] == "-":
            protocol_version = horizon_info.get(
                "current_protocol_version"
            )

            if protocol_version is not None:
                data["protocol_version"] = str(
                    protocol_version
                )

    return data



GITHUB_NODE_RELEASE_API = (
    "https://api.github.com/repos/"
    "PiCoreTeam/pi-node-docker/releases/latest"
)


def _node_version_tuple(value):
    match = re.search(
        r"(?:^|-)p(\d+)(?:\.(\d+))?(?:\.(\d+))?",
        str(value),
        re.IGNORECASE,
    )

    if not match:
        return ()

    return tuple(
        int(part or 0)
        for part in match.groups()
    )


def _component_version_tuple(value):
    """
    Haalt de eerste semantische versie uit bijvoorbeeld:
    v26.0.0-(built-from-source) -> (26, 0, 0)
    """
    match = re.search(
        r"v?(\d+)\.(\d+)(?:\.(\d+))?",
        str(value),
        re.IGNORECASE,
    )

    if not match:
        return ()

    return tuple(
        int(part or 0)
        for part in match.groups()
    )


def _clean_component_version(value):
    version = _component_version_tuple(value)

    if not version:
        return "-"

    return "v" + ".".join(
        str(part)
        for part in version
    )


def _parse_release_component_versions(body):
    """
    Leest de nieuwe Stellar Core- en Horizon-versies uit de
    officiële Pi Node Docker release notes.

    De parser gebruikt meerdere vormen zodat kleine wijzigingen
    in de markdown-opmaak niet meteen de updatecheck breken.
    """
    result = {
        "stellar_core": None,
        "horizon": None,
    }

    text = str(body or "")

    def last_version_from_line(keyword):
        for line in text.splitlines():
            if keyword.lower() not in line.lower():
                continue

            versions = re.findall(
                r"v?(\d+\.\d+(?:\.\d+)?)",
                line,
                re.IGNORECASE,
            )

            if versions:
                return _clean_component_version(
                    versions[-1]
                )

        return None

    # Eerst de tabelregels proberen:
    # stellar-core | v26.1.0 | v27.1.0
    # horizon      | v26.0.0 | v27.0.0
    result["stellar_core"] = last_version_from_line(
        "stellar-core"
    )
    result["horizon"] = last_version_from_line(
        "horizon"
    )

    # Fallback op de Makefile-regels in de release notes:
    # CORE_REF bumped from ... to ...
    if result["stellar_core"] is None:
        result["stellar_core"] = last_version_from_line(
            "CORE_REF"
        )

    if result["horizon"] is None:
        result["horizon"] = last_version_from_line(
            "HORIZON_REF"
        )

    return result


def get_latest_node_version():
    try:
        response = requests.get(
            GITHUB_NODE_RELEASE_API,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "Pi-Node-Dashboard",
            },
            timeout=8,
        )
        response.raise_for_status()

        data = response.json()
        tag = str(data.get("tag_name", "")).strip()

        if not tag:
            return None

        version_tuple = _node_version_tuple(tag)

        if not version_tuple:
            return None

        short_version = "p" + ".".join(
            str(part) for part in version_tuple
        )

        components = _parse_release_component_versions(
            data.get("body", "")
        )

        return {
            "tag": tag,
            "version": short_version,
            "version_tuple": version_tuple,
            "stellar_core_version": components["stellar_core"],
            "horizon_version": components["horizon"],
            "url": data.get("html_url", ""),
            "published_at": data.get("published_at", ""),
        }

    except Exception:
        return None


def node_update_available(current_version, latest_version):
    current = _node_version_tuple(current_version)
    latest = _node_version_tuple(latest_version)

    if not current or not latest:
        return False

    return latest > current


def component_update_available(current_version, latest_version):
    current = _component_version_tuple(current_version)
    latest = _component_version_tuple(latest_version)

    if not current or not latest:
        return False

    return latest > current


def clean_component_version(value):
    return _clean_component_version(value)


def _find_compose_file():
    """
    Zoekt het compose-bestand van de Pi Node.
    """
    candidates = [
        Path.home() / "pi-node" / "docker-compose.yml",
        Path.home() / "pi-node" / "compose.yml",
        Path.home() / "Documents" / "pi-node" / "docker-compose.yml",
        Path.home() / "Documents" / "pi-node" / "compose.yml",
    ]

    for path in candidates:
        if path.is_file():
            return path

    return None


def update_node_container(latest_version, progress_callback=None):
    """Werk de Pi Node-container veilig bij naar latest_version."""
    def progress(percent, stage):
        if progress_callback:
            progress_callback(percent, stage)

    progress(5, "prepare")
    compose_path = _find_compose_file()
    if compose_path is None:
        raise RuntimeError("docker-compose.yml kon niet worden gevonden.")

    latest_version = str(latest_version).strip()
    if not re.fullmatch(r"p\d+(?:\.\d+){0,2}", latest_version, re.IGNORECASE):
        raise RuntimeError(f"Ongeldige nodeversie: {latest_version}")

    original = compose_path.read_text(encoding="utf-8")
    image_pattern = re.compile(
        r"(?m)^(\s*image:\s*pinetwork/pi-node-docker:[^\n]*?-p)"
        r"\d+(?:\.\d+){0,2}(\s*)$"
    )
    matches = list(image_pattern.finditer(original))
    if len(matches) != 1:
        raise RuntimeError(
            "De verwachte Pi Node image-regel kon niet eenduidig worden gevonden in docker-compose.yml."
        )

    current_match = re.search(r"-p(\d+(?:\.\d+){0,2})", matches[0].group(0), re.IGNORECASE)
    current_version = f"p{current_match.group(1)}" if current_match else "-"

    updated = image_pattern.sub(
        lambda m: f"{m.group(1)}{latest_version.lstrip('pP')}{m.group(2)}",
        original,
        count=1,
    )
    if updated == original:
        raise RuntimeError("De containerversie kon niet worden aangepast.")

    progress(15, "backup")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = compose_path.with_name(f"{compose_path.name}.backup_{timestamp}")
    shutil.copy2(compose_path, backup_path)

    progress(25, "compose")
    compose_path.write_text(updated, encoding="utf-8")

    try:
        progress(35, "download")
        code, stdout, stderr = run_command(
            ["docker", "compose", "-f", str(compose_path), "pull", "mainnet"],
            timeout=600,
        )
        if code != 0:
            raise RuntimeError(stderr or stdout or "Nieuwe Pi Node image kon niet worden gedownload.")

        progress(75, "recreate")
        code, stdout, stderr = run_command(
            [
                "docker", "compose", "-f", str(compose_path),
                "up", "-d", "--force-recreate", "mainnet",
            ],
            timeout=180,
        )
        if code != 0:
            raise RuntimeError(stderr or stdout or "Pi Node container kon niet opnieuw worden gestart.")

        progress(95, "starting")

    except Exception as exc:
        progress(90, "rollback")
        shutil.copy2(backup_path, compose_path)
        try:
            code, stdout, stderr = run_command(
                [
                    "docker", "compose", "-f", str(compose_path),
                    "up", "-d", "--force-recreate", "mainnet",
                ],
                timeout=180,
            )
            if code != 0:
                raise RuntimeError(stderr or stdout or "oude container kon niet worden hersteld")
        except Exception as rollback_exc:
            raise RuntimeError(f"{exc}\nRollback mislukt: {rollback_exc}") from exc
        raise

    progress(100, "done")
    return {
        "compose_path": str(compose_path),
        "backup_path": str(backup_path),
        "old_version": current_version,
        "new_version": latest_version,
    }

def get_container_uptime():
    code, stdout, stderr = run_command(
        [
            "docker",
            "inspect",
            "-f",
            "{{.State.StartedAt}}",
            "mainnet",
        ]
    )

    if code != 0:
        return "-"

    started_text = stdout.strip()

    started = datetime.fromisoformat(
        started_text.replace("Z", "+00:00")
    )

    now = datetime.now(started.tzinfo)
    delta = now - started

    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60

    if days > 0:
        return f"{days}d {hours}u {minutes}m"

    return f"{hours}u {minutes}m"


def node_action(action):
    code, stdout, stderr = run_command(
        ["pi-node", action]
    )

    if code != 0:
        raise RuntimeError(stderr or stdout)


def set_cpu_limit(cores):
    cores = float(cores)

    if cores <= 0:
        cpu_value = "0"
    else:
        cpu_value = str(cores)

    code, stdout, stderr = run_command(
        [
            "docker",
            "update",
            "--cpus",
            cpu_value,
            "mainnet",
        ]
    )

    if code != 0:
        raise RuntimeError(
            stderr or stdout
        )


def get_node_logs(lines=200):
    try:
        lines = int(lines)
    except (TypeError, ValueError):
        lines = 200

    lines = max(1, min(lines, 5000))

    code, stdout, stderr = run_command(
        [
            "docker",
            "logs",
            "--tail",
            str(lines),
            "--timestamps",
            "mainnet",
        ]
    )

    if code != 0:
        raise RuntimeError(stderr or stdout)

    output = stdout.strip()

    if stderr.strip():
        if output:
            output += "\n" + stderr.strip()
        else:
            output = stderr.strip()

    return output
