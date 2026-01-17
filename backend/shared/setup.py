from setuptools import setup, find_packages
import os

# Distribution metadata
NAME = "highlighting-shared"
VERSION = os.environ.get("PACKAGE_VERSION", "0.0.0")

setup(
    name=NAME,
    version=VERSION,
    description="Shared utilities for Highlighting backend",
    packages=find_packages(include=["shared", "shared.*"]),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[],
)
