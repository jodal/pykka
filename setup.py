import re

from setuptools import find_packages, setup


def get_version():
    init_py = open('pykka/__init__.py').read()
    metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", init_py))
    return metadata['version']


with open('README.rst') as fh:
    long_description = fh.read()


setup(
    name='Pykka',
    version=get_version(),
    description='Pykka is a Python implementation of the actor model',
    long_description=long_description,
    url='https://www.pykka.org/',
    author='Stein Magnus Jodal',
    author_email='stein.magnus@jodal.no',
    license='Apache License, Version 2.0',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    packages=find_packages(exclude=['tests', 'tests.*']),
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
    extras_require={
        'dev': [
            'black',
            'check-manifest',
            'flake8',
            'flake8-import-order',
            'pytest',
            'pytest-cov',
            'pytest-mock',
            'sphinx',
            'sphinx_rtd_theme',
            'tox',
            'twine',
            'wheel',
        ]
    },
    project_urls={
        'Issues': 'https://github.com/jodal/pykka/issues',
        'Source': 'https://github.com/jodal/pykka',
    },
)
