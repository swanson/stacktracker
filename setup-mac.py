"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['StackTracker.py']
DATA_FILES = [('img', ['img/st_logo.png',
                             'img/stackoverflow_logo.png',
                             'img/metastackoverflow_logo.png',
                             'img/serverfault_logo.png',
                             'img/superuser_logo.png',
                             'img/stackapps_logo.png',
                             ]
                     )]

OPTIONS = {'argv_emulation': True}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)