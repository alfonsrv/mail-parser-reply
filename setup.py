# -*- coding: utf-8 -*-

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mailparser_reply'))
import version

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='mail-parser-reply',
    version=version.VERSION,
    description='📧 Email reply parser library for Python with multi-language support',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['mailparser_reply'],
    package_data={'mailparser_reply': ['../VERSION']},
    author='Alfons R.',
    author_email='alfonsrv@pm.me',
    maintainer="Alfons R.",
    maintainer_email='alfonsrv@pm.me',
    url='https://github.com/alfonsrv/mail-parser-reply',
    license='MIT',
    test_suite='test',
    keywords=['mail', 'email', 'parser'],
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        'Topic :: Software Development'
    ]
)
