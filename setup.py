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
    name='mailparser_reply',
    version=version.VERSION,
    description='eMail reply parser',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['mailparser_reply'],
    package_data={'mailparser_reply': ['../VERSION']},
    author='Alfons Rau',
    author_email='alfonsrv@pm.me',
    url='https://github.com/alfonsrv/mailparser-reply',
    license='MIT',
    test_suite='test',
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        'Topic :: Software Development'
    ]
)
