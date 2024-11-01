"""Generates mypy typing reports for the module."""

from pathlib import Path
import subprocess

root = Path(__file__).parent.parent
reports_dir = root / "docs/status/type_reports/"

reports_dir.mkdir(parents=True, exist_ok=True)

subprocess.run(
    [
        "mypy",
        "--check-untyped-defs",
        "--cache-fine-grained",
        "--sqlite-cache",
        "--html-report",
        reports_dir,
        ".",
    ],
    check=True,
)
# Copy index.html of the report to type_reports.md
index = reports_dir / "index.html"
markdown = reports_dir.parent / "type_reports.md"
with index.open("rt") as index_file:
    lines = index_file.readlines()
# Add style tag to fix table rendering mistake in dark mode
head_index = lines.index("<head>\n")
lines.insert(head_index + 1, "<style>tbody {color: black;}</style>")
with markdown.open("wt") as markdown_file:
    markdown_file.writelines(lines)
