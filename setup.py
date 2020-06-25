"""
setup
=====

``setuptools`` for package.
"""
import setuptools

import categorpy


with open("README.rst") as file:
    README = file.read()


setuptools.setup(
    name=categorpy.__name__,
    author=categorpy.__author__,
    maintainer=categorpy.__author__,
    author_email=categorpy.__email__,
    maintainer_email=categorpy.__email__,
    version=categorpy.__version__,
    license=categorpy.__license__,
    description="A turbo-charged torrent scraper for Transmission",
    long_description=README,
    platforms="GNU/Linux",
    long_description_content_type="text/x-rst",
    url="https://github.com/jshwi/categorpy",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    keywords="python3.8 transmission-daemon torrent scrape",
    packages=setuptools.find_packages(exclude=("tests",)),
    include_package_data=True,
    zip_safe=True,
    install_requires=["beautifulsoup4==4.9.3", "fuzzywuzzy==0.18.0"],
    python_requires=">=3.8",
    entry_points={"console_scripts": ["categorpy=categorpy.__main__:main"]},
)
