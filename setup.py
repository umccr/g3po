from setuptools import setup, find_packages

from g3po import __version__

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="g3po",
    description="Assorted utility CLI to work with Gen3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/umccr/g3po",
    author="UMCCR",
    author_email="services@umccr.org",
    license="MIT",
    version=__version__,
    packages=find_packages(),
    entry_points={
        "console_scripts": ["g3po=g3po.main:cli"],
    },
    install_requires=[
        "click<8.0.0",
        "gen3>=4.2.0",
        "indexclient>=2.1",
        "dictionaryutils>=3.4.2",
        "ldap3>=2.9.1",
        "yglu>=1.1.1",
        "importlib_metadata<2.0.0",
        "jsonschema==2.5.1"
    ],
    extras_require={
        "test": [
            "pytest",
        ],
        "dev": [
            "twine",
            "setuptools",
            "wheel",
        ],
    },
    python_requires=">=3.6",
)
