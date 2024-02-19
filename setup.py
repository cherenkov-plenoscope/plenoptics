import os
import setuptools

with open("README.rst", "r", encoding="utf-8") as f:
    long_description = f.read()


with open(os.path.join("plenoptics", "version.py")) as f:
    txt = f.read()
    last_line = txt.splitlines()[-1]
    version_string = last_line.split()[-1]
    version = version_string.strip("\"'")


setuptools.setup(
    name="plenoptics_cherenkov-plenoscope-project",
    version=version,
    description=(
        "Demonstrates the power of plenoptic perception on "
        "deformed and misaligned plenoscopes"
    ),
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/cherenkov-plenoscope/plenoptics",
    author="Sebastian Achim Mueller",
    author_email="sebastian-achim.mueller@mpi-hd.mpg.de",
    packages=[
        "plenoptics",
        "plenoptics.instruments",
        "plenoptics.instruments.mirror",
        "plenoptics.sources",
        "plenoptics.analysis",
        "plenoptics.production",
    ],
    package_data={
        "plenoptics": [
            os.path.join("scripts", "*"),
        ],
    },
    install_requires=[
        "perlin_noise",
        "json_utils_sebastian-achim-mueller",
        "merlict_development_kit_python_cherenkov-plenoscope-project>=0.0.3",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Intended Audience :: Science/Research",
    ],
)
