#!/usr/bin/env python3
from setuptools import setup

install_requires = ['PyYAML', 'Babel', 'blinker', 'docutils', 'Jinja2>=2.4', 'Werkzeug', 'markdown', 'pygments', 'lxml']

setup(
    name='rstblog',
    version='1.0',
    author='Armin Ronacher <armin.ronacher@active-4.com>',
    packages=['rstblog', 'rstblog.modules'],
    description='',
    long_description='',
    license='BSD License',
    entry_points = {
        'console_scripts': ['run-rstblog = rstblog.cli:main'],
    },
    install_requires=install_requires
)
