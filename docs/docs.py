import subprocess

README_FILES = (
    ("Read Me", "docs/README.md"),
)


def create_readme():
    with open("README.md", "wt") as r:
        for header, file in README_FILES:
            r.write(f"\n\n## {header}\n\n")
            with open(file, "rt") as f:
                r.write(f.read())


def update_license():
    with open("LICENSE", "rt") as source, open("docs/license.md", "wt") as target:
        target.write(source.read())


def create_docs():
    subprocess.run("mkdocs build", shell=True, check=True)


def main():
    create_readme()
    update_license()
    create_docs()
