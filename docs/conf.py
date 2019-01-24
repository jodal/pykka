# encoding: utf-8

"""Pykka documentation build configuration file"""

from __future__ import unicode_literals

import os
import re
import sys


# -- Workarounds to have autodoc generate API docs ----------------------------

sys.path.insert(0, os.path.abspath('..'))


class Mock(object):
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return Mock()

    @classmethod
    def __getattr__(self, name):
        if name in ('__file__', '__path__'):
            return '/dev/null'
        elif name[0] == name[0].upper():
            return type(name, (), {})
        else:
            return Mock()


MOCK_MODULES = [
    'gevent',
    'gevent.event',
    'gevent.queue',
    'eventlet',
    'eventlet.event',
    'eventlet.queue',
]
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = Mock()


# -- General configuration ----------------------------------------------------

needs_sphinx = '1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.extlinks',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

project = u'Pykka'
copyright = u'2010-2019, Stein Magnus Jodal and contributors'


def get_version():
    init_py = open('../pykka/__init__.py').read()
    metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", init_py))
    return metadata['version']


release = get_version()
version = '.'.join(release.split('.')[:2])

exclude_patterns = ['_build']

pygments_style = 'sphinx'

modindex_common_prefix = ['pykka.']


# -- Options for HTML output --------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

html_use_modindex = True
html_use_index = True
html_split_index = False
html_show_sourcelink = True

htmlhelp_basename = 'Pykka'


# -- Options for LaTeX output -------------------------------------------------

latex_documents = [
    (
        'index',
        'Pykka.tex',
        'Pykka Documentation',
        'Stein Magnus Jodal',
        'manual',
    )
]


# -- Options for manual page output -------------------------------------------

man_pages = []


# -- Options for autodoc extension --------------------------------------------

autodoc_member_order = 'bysource'


# -- Options for extlink extension --------------------------------------------

extlinks = {'issue': ('https://github.com/jodal/pykka/issues/%s', '#')}


# -- Options for intersphinx extension ----------------------------------------

intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}
