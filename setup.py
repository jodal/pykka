from distutils.core import setup
import re

def get_version():
    init_py = open('pykka/__init__.py').read()
    metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", init_py))
    return metadata['version']

setup(
    name='Pykka',
    version=get_version(),
    author='Stein Magnus Jodal',
    author_email='stein.magnus@jodal.no',
    packages=['pykka'],
    url='http://pykka.readthedocs.org/',
    license='Apache License, Version 2.0',
    description='Pykka is easy to use concurrency using the actor model',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
    ],
)
