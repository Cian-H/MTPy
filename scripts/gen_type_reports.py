"""Generates mypy typing reports for the module."""

from pathlib import Path
import subprocess
from urllib.parse import urlparse

import bs4

from scripts import utils

DOCS_DIR = utils.get_mkdocs_docs_dir()
REPORTS_DIR = utils.get_mkdocs_generated_assets_dir() / "type_reports"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def is_url(s: str) -> bool:
    """Checks that a string is not a URL."""
    parsed = urlparse(s)
    return parsed.scheme in ("http", "https", "ftp")


def process_index(index: Path, root_dir: Path | None = None) -> None:
    """Modifies the html file so that it works when imported as a template."""
    print("Processing type report index")
    root_dir = root_dir if root_dir is not None else Path.cwd()

    with index.open("rt") as file:
        dom = bs4.BeautifulSoup(file, "html.parser")

    # Fix dark mode formatting for all styles using mypy-html.css
    style = dom.new_tag("style")
    style.string = """
    tbody {
        color: black;
    }
    th.summary.summary-filename,
    th.summary.summary-precision,
    th.summary.summary-lines {
        color: black !important;
    }
    """

    for css_link in dom.find_all("link", href=str("mypy-html.css")):
        p = css_link.parent
        assert isinstance(p, bs4.element.Tag)
        p.append(style)

    with index.open("wt") as file:
        file.write(str(dom))


def rebase_hrefs(
    dom: bs4.BeautifulSoup, rebase_dir: Path, root_dir: Path | None = None
) -> bs4.BeautifulSoup:
    """Rebase the hrefs inside a html file to be relative to a different directory."""
    root_dir = root_dir if root_dir is not None else Path.cwd()
    root_dir = root_dir.resolve()
    # Rebase local link hrefs
    for link in dom.find_all("link", href=True):
        assert isinstance(link, bs4.element.Tag)
        href = link["href"]
        assert isinstance(href, str)
        if is_url(href) or href.startswith("#"):
            continue
        target = rebase_dir.resolve() / href
        link["href"] = f"/{target.relative_to(root_dir)}"

    # Rebase local anchor hrefs
    for a in dom.find_all("a", href=True):
        assert isinstance(a, bs4.element.Tag)
        href = a["href"]
        assert isinstance(href, str)
        if is_url(href) or href.startswith("#"):
            continue
        print(f"{href} rebasing onto {rebase_dir.relative_to(root_dir) / href}")
        target = rebase_dir.resolve() / href
        a["href"] = f"/{target.relative_to(root_dir)}"

    return dom


def rebase_relative_leaf(p: Path, root_dir: Path) -> None:
    """Rebase relative html file links in a file."""
    print(f"Rebasing type report file {p.relative_to(Path.cwd())}")
    with p.open("rt") as file:
        dom = bs4.BeautifulSoup(file.read(), "html.parser")
    dom = rebase_hrefs(dom, p.parent, root_dir)
    html = str(dom)
    with p.open("wt") as file:
        file.write(html)


def rebase_relative_tree(p: Path, root_dir: Path) -> None:
    """Recursively rebase all relative html file links in a directory and its subdirectories."""
    print(f"Rebasing type report directory {p.relative_to(Path.cwd())}")
    if not p.exists():
        msg = f"Directory {p} does not exist!"
        raise ValueError(msg)

    if p.is_dir():
        for i in p.iterdir():
            rebase_relative_tree(i, root_dir)
    elif p.suffix.lower() == ".html":
        rebase_relative_leaf(p, root_dir)


def main() -> None:
    """Entrypoint for this script."""
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
    # Process and rebase html files for this website
    index = REPORTS_DIR / "index.html"
    process_index(index, DOCS_DIR)
    rebase_relative_tree(REPORTS_DIR, DOCS_DIR)


main()
