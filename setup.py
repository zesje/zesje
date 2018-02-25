#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from setuptools import setup, find_packages
from setuptools.command.sdist import sdist as sdist_orig

if sys.version_info < (3, 6):
    print('zesje requires Python 3.6 or higher')
    sys.exit(1)


class sdist(sdist_orig):
    def run(self):
        import subprocess
        subprocess.check_call(['yarn', 'install'])
        subprocess.check_call(['yarn', 'build'])
        super().run()


setup(
    name="zesje",
    version="0.1a",
    url="http://gitlab.kwant-project,org/zesje/zesje",
    description="",
    author="Zesje authors",
    author_email="anton.akhmerov@tudelft.nl",
    packages=find_packages('.'),
    cmdclass=dict(sdist=sdist),
    package_data={'zesje': ['static/*']},
    include_package_data=True,
)
