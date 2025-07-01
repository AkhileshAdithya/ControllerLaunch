#!/usr/bin/env python3
# ControllerLaunch - Setup Script for Developers

from setuptools import setup, find_packages
import os

def read_requirements():
    """Read requirements file and return a list of requirements."""
    with open('requirements.txt') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="controller-launch",
    version="1.0.0",
    description="A controller-friendly game launcher for Linux",
    author="Akhilesh Adithya",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "controller-launch=main:main",
            "controller-launch-daemon=controller_daemon:main",
        ],
    },
    python_requires=">=3.6",
    data_files=[
        ('share/applications', ['install/controller-launch.desktop']),
        ('share/controller-launch', ['config/default_config.json']),
    ],
)
