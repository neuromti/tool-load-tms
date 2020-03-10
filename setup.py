from distutils.core import setup

from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "readme.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="matprot",
    version="0.1",
    description="Load the TMS data from our legacy matlab protocol and convert it to python",
    long_description=long_description,
    author="Robert Guggenberger",
    author_email="robert.guggenberger@uni-tuebingen.de",
    url="https://github.com/translationalneurosurgery/tool-load-tms.git",
    download_url="https://github.com/translationalneurosurgery/tool-load-tms.git",
    license="MIT",
    packages=["matprot", "matprot.convert"],
    entry_points={"console_scripts": [],},
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
