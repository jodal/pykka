"""Pykka documentation build configuration file"""


import configparser
import os
import sys

# -- Workarounds to have autodoc generate API docs ----------------------------

sys.path.insert(0, os.path.abspath(".."))


# -- General configuration ----------------------------------------------------

needs_sphinx = "1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"

project = "Pykka"
copyright = "2010-2020, Stein Magnus Jodal and contributors"


def get_version():
    # Get current library version without requiring the library to be
    # installed, like ``pkg_resources.get_distribution(...).version`` requires.
    cp = configparser.ConfigParser()
    cp.read(os.path.join(os.path.dirname(__file__), "..", "setup.cfg"))
    return cp["metadata"]["version"]


release = get_version()
version = ".".join(release.split(".")[:2])

exclude_patterns = ["_build"]

pygments_style = "sphinx"

modindex_common_prefix = ["pykka."]


# -- Options for HTML output --------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

html_use_modindex = True
html_use_index = True
html_split_index = False
html_show_sourcelink = True

htmlhelp_basename = "Pykka"


# -- Options for LaTeX output -------------------------------------------------

latex_documents = [
    (
        "index",
        "Pykka.tex",
        "Pykka Documentation",
        "Stein Magnus Jodal",
        "manual",
    )
]


# -- Options for manual page output -------------------------------------------

man_pages = []


# -- Options for autodoc extension --------------------------------------------

autodoc_member_order = "bysource"


# -- Options for extlink extension --------------------------------------------

extlinks = {"issue": ("https://github.com/jodal/pykka/issues/%s", "#")}


# -- Options for intersphinx extension ----------------------------------------

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
