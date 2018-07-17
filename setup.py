#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 6):
    print('zesje requires Python 3.6 or higher')
    sys.exit(1)


# Loads version.py module without importing the whole package.
def get_version_and_cmdclass(package_path):
    import os
    from importlib.util import module_from_spec, spec_from_file_location
    spec = spec_from_file_location('version',
                                   os.path.join(package_path, '_version.py'))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.__version__, module.cmdclass


version, cmdclass = get_version_and_cmdclass('zesje')
# will be replaced by the overriding classes below
_sdist = cmdclass.pop('sdist')


class sdist(_sdist):
    def run(self):
        import subprocess
        subprocess.check_call(['rm', '-r', 'zesje/static'])
        subprocess.check_call(['yarn', 'install'])
        subprocess.check_call(['yarn', 'build'])
        super().run()


cmdclass['sdist'] = sdist


setup(
    name="zesje",
    version=version,
    url="http://gitlab.kwant-project,org/zesje/zesje",
    description="",
    author="Zesje authors",
    author_email="anton.akhmerov@tudelft.nl",
    packages=find_packages('.'),
    cmdclass=cmdclass,
    package_data={'zesje': ['static/*']},
    include_package_data=True,
)
