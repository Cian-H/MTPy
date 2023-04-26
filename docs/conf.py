import os
import sys
import toml
from sphinx_pyproject import SphinxConfig


# this is just an extremely hacky way to avoid having to write this toml table twice
def to_pep621(in_file: str = "../pyproject.toml", out_file: str = "_pyproject.toml") -> str:
    pyproject = toml.load(in_file)
    pyproject["project"] = pyproject["tool"].pop("poetry")
    poetry_authors = pyproject["project"].pop("authors", [])
    pep621_authors = []
    for author in poetry_authors:
        if "<" and ">" in author:
            name = author.split("<")[0].strip()
            email = author.split("<")[1].split(">")[0]
        else:
            name = author
            email = None
        author = {"name": name}
        if email is not None:
            author["email"] = email
        pep621_authors.append(author)
    pyproject["project"]["authors"] = pep621_authors
    toml.dump(pyproject, open(out_file, "w"))


if __name__ == "builtins":
    sys.path.insert(0, os.path.abspath("../../"))
    to_pep621(out_file="_pyproject.toml")
    config = SphinxConfig("_pyproject.toml", globalns=globals())
