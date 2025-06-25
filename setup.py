from setuptools import setup, find_packages
import os
from os import path


def readme():
    with open("README.md") as f:
        return f.read()


ALLOWED_FILETYPES = [".py", ".yaml", ".csv", ".xls", ".txt"]


def listdir(d=""):
    d = os.path.join(os.path.dirname(__file__), d)
    files = [os.path.join(d, f) for f in os.listdir(d)]
    files = [f for f in files if path.isfile(f)]
    return [f for f in files if any(a in f for a in ALLOWED_FILETYPES)]


setup(
    name="hwcomponents-adc",
    version="0.1",
    description="A package for estimating the energy and area of Analog-Digital Converters",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    ],
    keywords="accelerator hardware energy estimation analog adc",
    author="Tanner Andrulis",
    author_email="Andrulis@mit.edu",
    license="MIT",
    install_requires=["PyYAML", "numpy", "pandas"],
    python_requires=">=3.12",
    py_modules=["hwcomponents_adc"],
    packages=find_packages(),
    package_data={
        "hwcomponents_adc": [
            "adc_data/model.yaml",
        ],
    },
    include_package_data=True,
    entry_points={},
)
