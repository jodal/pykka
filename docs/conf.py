"""Pykka documentation build configuration file."""

import pathlib
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

project = "Pykka"
author = "Stein Magnus Jodal and contributors"
copyright = f"2010-2025, {author}"  # noqa: A001

pyproject_path = pathlib.Path(__file__).parent.parent / "pyproject.toml"
with pyproject_path.open("rb") as fh:
    pyproject = tomllib.load(fh)
release = pyproject["project"]["version"]
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]

html_theme = "sphinx_rtd_theme"
html_use_modindex = True
html_use_index = True
html_split_index = False
html_show_sourcelink = True
modindex_common_prefix = ["pykka."]

autodoc_member_order = "bysource"

extlinks = {
    "issue": ("https://github.com/jodal/pykka/issues/%s", "#%s"),
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}
