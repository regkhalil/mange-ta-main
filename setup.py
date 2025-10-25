"""Configuration du package Mangetamain Streamlit."""

from pathlib import Path

from setuptools import find_packages, setup

# Lire le README pour la description longue
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as fh:
        long_description = fh.read()

setup(
    name="mangetamain-streamlit",
    version="1.0.0",
    author="Équipe Mangetamain",
    author_email="contact@mangetamain.fr",
    description="Application web de recherche et recommandation de recettes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/regkhalil/mange-ta-main",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.13",
    install_requires=[
        "kagglehub[pandas-datasets]>=0.3.13",
        "pandas>=2.3.3",
        "plotly>=5.17.0",
        "python-dotenv>=1.0.0",
        "scikit-learn>=1.7.2",
        "streamlit>=1.50.0",
        "visidata>=3.3",
    ],
    entry_points={
        "console_scripts": [
            "mangetamain=app:main",
        ],
    },
)
