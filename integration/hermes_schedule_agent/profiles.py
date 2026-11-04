"""Delegate profile resolution to Hermes' own profile command."""

from pathlib import Path
import hashlib
import re
import subprocess


def profile_adapter(action, name=None):
    # Hermes CLI owns profile normalization, tombstones and home selection.
    args = (
        ["hermes", "profile", "list"]
        if action == "list"
        else ["hermes", "profile", "show", name]
    )
    result = subprocess.run(args, text=True, capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError(
            result.stderr.strip() or "Hermes could not resolve that profile"
        )
    if action == "list":
        return {"listing": result.stdout.strip()}
    matches = re.findall(r"^Path:\s+(.+)$", result.stdout, re.MULTILINE)
    if len(matches) != 1 or not Path(matches[0]).is_absolute():
        raise ValueError(
            "Hermes profile response has no unique absolute Path; update the adapter"
        )
    home = Path(matches[0])
    key = "hermes-schedule-agent"
    namespace = (
        "agent-plugin-" + key + "-" + hashlib.sha256(key.encode()).hexdigest()[:8]
    )
    data = home / "plugin-data" / namespace
    return (
        str(data)
        if action == "resolve"
        else {"name": name, "home": str(home), "data_dir": str(data)}
    )
