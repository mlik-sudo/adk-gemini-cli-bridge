#!/usr/bin/env python3
"""Setup script for ADK-Gemini CLI Bridge."""

from pathlib import Path
from setuptools import setup, find_packages

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="adk-gemini-cli-bridge",
    version="1.0.0",
    description="STDIO bridge to expose ADK agents as tools for Gemini CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="mlik-sudo",
    url="https://github.com/mlik-sudo/adk-gemini-cli-bridge",
    license="MIT",

    # Python version requirement
    python_requires=">=3.8",

    # Package discovery
    py_modules=["bridge"],

    # Dependencies
    install_requires=[
        "pyyaml>=6.0.1",
    ],

    # Development dependencies
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-timeout>=2.1.0",
            "pytest-mock>=3.11.1",
            "pylint>=3.0.0",
            "mypy>=1.5.0",
            "black>=23.7.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "bandit>=1.7.5",
            "safety>=2.3.5",
            "pre-commit>=3.3.3",
        ],
    },

    # Entry points
    entry_points={
        "console_scripts": [
            "adk-bridge=bridge:main",
        ],
    },

    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Software Distribution",
    ],

    # Additional files to include
    include_package_data=True,
    package_data={
        "": ["config.yaml", "mcp_servers.json.template"],
    },
)
