from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="os-helper",
    version="0.1.0",
    author="Warith Harchaoui",
    author_email="your-email@example.com",  # replace with the correct email
    description="A Python library providing utility functions for working with different operating systems.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/warith-harchaoui/os-helper",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[],
)
