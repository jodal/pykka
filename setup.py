import re

from setuptools import find_packages, setup


def get_version():
    init_py = open('pykka/__init__.py').read()
    metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", init_py))
    return metadata['version']


setup(
    name='Pykka',
    version=get_version(),
    author='Stein Magnus Jodal',
    author_email='stein.magnus@jodal.no',
    packages=find_packages(exclude=['tests', 'tests.*']),
    url='https://www.pykka.org/',
    license='Apache License, Version 2.0',
    description='Pykka is a Python implementation of the actor model',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries',
    ],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
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
)
