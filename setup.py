from distutils.core import setup
import setuptools
from pathlib import Path

thisdirectory = Path(__file__).parent
with (thisdirectory / "readme.md").open() as f:
    long_description = f.read()

with (thisdirectory / "requirements.txt").open() as f:
    install_requires = [l.strip() for l in f.readlines()]

setup(
    name="matprot",
    version="0.2",
    description="Load the TMS data from our legacy matlab protocol and convert it to python",
    long_description=long_description,
    author="Robert Guggenberger",
    author_email="robert.guggenberger@uni-tuebingen.de",
    url="https://github.com/translationalneurosurgery/tool-load-tms.git",
    download_url="https://github.com/translationalneurosurgery/tool-load-tms.git",
    license="MIT",
    install_requires=install_requires,
    packages=setuptools.find_packages(),
    package_data={"matprot": ["ml/*.m"]},
    entry_points={"console_scripts": ["matprot=matprot.__main__:main",],},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Software Development :: Libraries",
    ],
)
