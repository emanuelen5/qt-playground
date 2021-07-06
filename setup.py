import setuptools
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
from setuptools import Command
import os


def _compile_uic():
    os.system("make ui")


class CompileUIWrapper(Command):
    def run(self):
        print(f"Running wrapper function {self.__class__.__name__}")
        _compile_uic()
        super().run()


class BuildPyWrapper(CompileUIWrapper, build_py):
    pass


class DevelopWrapper(CompileUIWrapper, develop):
    pass


setuptools.setup(
    name="timereport",
    author="Erasmus Cedernaes",
    license="GPLv3",
    version="0.0.0",
    package_dir={"": "src"},
    packages=setuptools.find_packages("src"),
    cmdclass={
        "develop": DevelopWrapper,
        "build_py": BuildPyWrapper
    },
    entry_points={"console_scripts": ["trep=timereport.__main__:main"]}
)
