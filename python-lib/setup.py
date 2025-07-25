from setuptools import setup, find_packages
import os

with open(os.path.join(os.path.dirname(__file__), "..", "library.properties"), "r") as f:
    version_str = "0.0.0"  # Default version in case of failure to read
    for line in f:
        if line.startswith("version="):
            version_str = line.strip().split("=", 1)[1]
            break

with open("README.md", "r") as fh:
    long_description = fh.read()
setup(
    name='line-protocol',
    version=version_str,
    author="Balazs Eszes",
    author_email="c4deszes@gmail.com",
    description="Simple protocol for serial communication devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/c4deszes/bike-line-protocol",
    packages=find_packages(),
    package_data={},
    license='MIT',
    keywords=['LINE'],
    install_requires=[
        'pyserial',
        'bitstruct',
        'jinja2',
        'dataclasses-json'
    ],
    extras_require={
        'dev': [
            # Packaging
            "setuptools",
            "wheel",
            "twine",
            # Testing
            "pytest",
            "pytest-cov",
            # Linting
            "pylint",
            "flake8"
        ]
    },
    python_requires='!=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, <4',
    entry_points={
        'console_scripts': [
            'line-codegen=line_protocol.codegen.generator:main',
            'line-monitor=line_protocol.monitor.cli:main',
            'line-plot=line_protocol.plot.ui:main',
            'line-discovery=line_protocol.util.discovery:main'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    project_urls={
        "Documentation": "https://c4deszes.github.io/bike-line-protocol/",
        "Source Code": "https://github.com/c4deszes/bike-line-protocol",
    }
)
