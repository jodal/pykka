from distutils.core import setup

import pykka

setup(
    name='Pykka',
    version=pykka.get_version(),
    author='Stein Magnus Jodal',
    author_email='stein.magnus@jodal.no',
    packages=['pykka'],
    url='http://jodal.github.com/pykka/',
    license='Apache License, Version 2.0',
    description='Pykka is easy to use concurrency using the actor model',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
    ],
)
