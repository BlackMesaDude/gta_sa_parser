# setup.py
from setuptools import setup, find_packages

setup(
    name="gta_sa_parser",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "construct>=2.10.0",
        "Pillow>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "gta_sa_parser=gta_sa_parser.cli:main",
        ],
    },
    author="BlackMesaDude",
    author_email="",
    description="Dynamic parser for GTA:SA game data files",
    keywords="gta, san andreas, parser",
    python_requires=">=3.7",
    include_package_data=True,
)