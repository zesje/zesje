from setuptools import setup, find_packages
from distutils.command.build import build
from setuptools.command.sdist import sdist


def webpack():
    import subprocess
    subprocess.check_call(['npm', 'install'])
    subprocess.check_call(['./node_modules/.bin/webpack'])


class Build(build):
    def run(self):
        webpack()
        super().run()


class Sdist(sdist):
    def run(self):
        webpack()
        super().run()


setup(
    name="zesje",
    version="0.1",
    url="http://gitlab.kwant-project,org/zesje/zesje",
    description="",
    author="Zesje authors",
    author_email="anton.akhmerov@tudelft.nl",
    packages=find_packages('.'),
    cmdclass={'build': Build,
              'sdist': Sdist,
             },
    package_data={'zesje': ['static/*']},
    include_package_data=True,
)
