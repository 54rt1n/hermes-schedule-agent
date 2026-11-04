"""Install a plugin-owned runtime from pinned GitHub packages or optional local sources."""

import argparse
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sources = parser.add_mutually_exclusive_group()
    sources.add_argument(
        "--source",
        type=Path,
        help="Build a snapshot of the current local Schedule Agent tree, including edits",
    )
    sources.add_argument(
        "--editable-source",
        type=Path,
        help="Install a local Schedule Agent checkout editable for development",
    )
    args = parser.parse_args()
    if not (3, 11) <= sys.version_info[:2] < (3, 14):
        parser.error(
            "Schedule Agent requires Python 3.11–3.13; run this script with a supported interpreter"
        )
    root = Path(__file__).resolve().parents[1]
    destination = root / ".venv"
    if destination.exists() or destination.is_symlink():
        raise SystemExit(
            "Refusing an existing .venv; inspect and move it aside before provisioning"
        )
    source_path = args.editable_source or args.source
    source = source_path.resolve() if source_path else None
    if source:
        revision = subprocess.check_output(
            ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
        ).strip()
        dirty = subprocess.check_output(
            ["git", "-C", str(source), "status", "--porcelain"], text=True
        ).strip()
        print(f"Local Schedule Agent: {source} HEAD={revision} dirty={bool(dirty)}")
    venv.EnvBuilder(with_pip=True).create(destination)
    python = destination / (
        "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
    )
    install = [str(python), "-m", "pip", "install"]
    if args.editable_source:
        subprocess.run(
            install
            + [
                "-e",
                str(source / "packages/schedule-core"),
                "-e",
                str(source / "packages/schedule-cli"),
                "-e",
                str(source / "packages/schedule-mcp"),
            ],
            check=True,
        )
    elif source:
        # Snapshot includes intentional local edits; package build never writes to source.
        with tempfile.TemporaryDirectory(prefix="schedule-agent-source-") as temporary:
            extracted = Path(temporary) / "source"
            shutil.copytree(
                source,
                extracted,
                ignore=shutil.ignore_patterns(
                    ".git",
                    ".venv",
                    "venv",
                    "__pycache__",
                    "*.pyc",
                    "*.egg-info",
                    "build",
                    "dist",
                    ".pytest_cache",
                    ".mypy_cache",
                    ".ruff_cache",
                    ".env",
                    "*.db",
                    "*.db-wal",
                    "*.db-shm",
                    "volume",
                    "local",
                ),
            )
            subprocess.run(
                install
                + [
                    str(extracted / "packages/schedule-core"),
                    str(extracted / "packages/schedule-cli"),
                    str(extracted / "packages/schedule-mcp"),
                ],
                check=True,
            )
    else:
        subprocess.run(
            install + ["-r", str(root / "runtime-requirements.txt")], check=True
        )
    subprocess.run(
        install
        + ["--no-deps"]
        + (["-e"] if args.editable_source else [])
        + [str(root / "integration")],
        check=True,
    )
    subprocess.run([str(python), "-m", "pip", "check"], check=True)
    print(f"Runtime ready: {python}")


if __name__ == "__main__":
    main()
