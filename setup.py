#!/usr/bin/env python

import os
import sys

from setuptools import setup, find_packages

os.chdir(os.path.dirname(sys.argv[0]) or ".")

try:
    long_description = open("README.rst", "U").read()
except IOError:
    long_description = "See https://github.com/wolever/dwdj"

import dwdj
version = "%s.%s.%s" %dwdj.__version__

setup(
    name="dwdj",
    version=version,
    url="https://github.com/wolever/dwdj",
    author="David Wolever",
    author_email="david@wolever.net",
    description="""
        A collection of useful django utilities.
    """,
    long_description=long_description,
    packages=find_packages(),
    license="BSD",
    classifiers=[ x.strip() for x in """
        Development Status :: 4 - Beta
        Intended Audience :: Developers
        License :: OSI Approved :: BSD License
        Natural Language :: English
        Operating System :: OS Independent
        Programming Language :: Python
        Topic :: Utilities
    """.split("\n") if x.strip() ],
)
