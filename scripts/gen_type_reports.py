"""Generates mypy typing reports for the module."""

from importlib.machinery import SourceFileLoader
from pathlib import Path
import subprocess

utils = SourceFileLoader("utils", str(Path(__file__).parent / "utils.py")).load_module()
REPORTS_DIR = utils.ROOT / "docs/status/type_reports/"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

subprocess.run(
    [
        "mypy",
        "--check-untyped-defs",
        "--cache-fine-grained",
        "--sqlite-cache",
        "--html-report",
        REPORTS_DIR,
        ".",
    ],
    check=True,
)
# Copy index.html of the report to type_reports.md
index = REPORTS_DIR / "index.html"
markdown = REPORTS_DIR.parent / "type_reports.md"
with index.open("rt") as index_file:
    lines = index_file.readlines()
# Add style tag to fix table rendering mistake in dark mode
head_index = lines.index("<head>\n")
lines.insert(head_index + 1, "<style>tbody {color: black;}</style>")
with markdown.open("wt") as markdown_file:
    markdown_file.writelines(lines)
