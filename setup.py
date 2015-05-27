#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

from setuptools import setup, find_packages


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    "cached-property",
    "pignacio_scripts",
    "unidecode",
]

setup(
    name='vld',
    version='0.0.1',
    description="A diet logger.",
    long_description=readme + '\n\n' + history,
    author="Ignacio Rossi",
    author_email='rossi.ignacio@gmail.com ',
    url='https://github.com/pignacio/vld',
    packages=find_packages(exclude=['contrib', 'test*', 'docs']),
    include_package_data=True,
    install_requires=requirements,
    license='GPLv3',
    zip_safe=False,
    keywords='vld var log dieta diet calories',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'vld=vld.commands:vld_report',
            'vld-report=vld.commands:vld_report',
            'vld-new-ingredient=vld.commands:vld_new_ingredient',
            'vld-count=vld.commands:vld_count',
            'vld-show-ingredients=vld.commands:vld_show_ingredients',
            'vld-price=vld.commands:vld_price',
        ],
    }
)
