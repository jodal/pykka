from distutils.core import setup

import pykka

setup(
    name='Pykka',
    version=pykka.get_version(),
    author='Stein Magnus Jodal',
    author_email='stein.magnus@jodal.no',
    packages=['pykka'],
    url='http://github.com/jodal/pykka',
    license='Apache License, Version 2.0',
    description='Pykka makes actors look like regular objects',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries',
    ],
)
