"""Generate the code reference pages."""

from importlib.machinery import SourceFileLoader
from pathlib import Path

import mkdocs_gen_files

utils = SourceFileLoader("utils", str(Path(__file__).parent / "utils.py")).load_module()

nav = mkdocs_gen_files.Nav()


for path in sorted(utils.SRC.rglob("*.py")):
    module_path = path.relative_to(utils.ROOT).with_suffix("")
    doc_path = path.relative_to(utils.ROOT).with_suffix(".md")
    full_doc_path = Path("documentation/reference", doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] in ("__init__", "__main__"):
        continue

    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        identifier = ".".join(parts)
        print(fd)
        print("::: " + identifier, file=fd)

    mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(utils.ROOT))


with mkdocs_gen_files.open("documentation/reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
