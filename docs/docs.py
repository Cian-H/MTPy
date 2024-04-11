from functools import lru_cache
import inspect
import mtpy
import subprocess

from pathlib import Path

README_FILES = (
    ("Read Me", "docs/README.md"),
)

MODULE_ROOT = Path(mtpy.__modpath__)


def create_readme():
    with open("README.md", "wt") as r:
        for header, file in README_FILES:
            r.write(f"\n\n## {header}\n\n")
            with open(file, "rt") as f:
                r.write(f.read())


def create_documentation():
    package = generate_package_tree(mtpy)
    breakpoint()


@lru_cache
def generate_package_tree(component):
    print(f"{component=}")
    if inspect.ismodule(component):
        print("BRANCH 1")
        return {
            component.__name__: generate_package_tree(v) for k, v in
                filter_public_subcomponents(component).items()
                if generate_package_tree(v) is not None
        }
    elif inspect.isclass(component):
        print("BRANCH 2")
        return {}
    else:
        print("BRANCH 3")
        return None


def filter_public_subcomponents(module):
    out = {}
    for k, v in module.__dict__.items():
        if (k[0] == "_"):
            continue
        parent_file = Path("/")
        try:
            if inspect.ismodule(v):
                parent_file = Path(v.__file__)
            elif inspect.isclass(v):
                parent_file = Path(eval(v.__module__).__file__)
            else:
                continue
        except:
            if not inspect.ismodule(v):
                continue
        if not (MODULE_ROOT in parent_file.parents):
            continue
        out[k] = v
    return out


def update_license():
    with open("LICENSE", "rt") as source, open("docs/license.md", "wt") as target:
        target.write(source.read())


def create_docs():
    subprocess.run("mkdocs build", shell=True, check=True)


def main():
    # create_readme()
    # update_license()
    # create_docs()
    create_documentation()


if __name__ == "__main__":
    main()
