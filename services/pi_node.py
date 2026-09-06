import subprocess
from datetime import datetime


def run_command(command):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=30,
    )

    return (
        result.returncode,
        result.stdout,
        result.stderr,
    )


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

            elif stripped.startswith("Protocol:"):
                data["protocol"] = (
                    stripped
                    .replace("Protocol:", "")
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

    return data


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

    # docker logs can use stdout and/or stderr depending on the container
    output = stdout.strip()

    if stderr.strip():
        if output:
            output += "\n" + stderr.strip()
        else:
            output = stderr.strip()

    return output
