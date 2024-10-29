"""Generates mypy typing reports for the module."""

from pathlib import Path
import subprocess

root = Path(__file__).parent.parent
reports_dir = root / "docs/type_reports/"

reports_dir.mkdir(parents=True, exist_ok=True)

subprocess.run(
    ["mypy", "--check-untyped-defs", "--cache-fine-grained", "--html-report", reports_dir, "."],
    check=True,
)
