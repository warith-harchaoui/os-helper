import os
import sys

# Add the `os_helper` directory to the Python path
sys.path.insert(0, os.path.abspath('../'))

# Sphinx extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # Support for NumPy/Google style docstrings
    'sphinx.ext.viewcode',  # Add links to source code in docs
]

# Project information
project = 'OS Helper'
author = 'Warith Harchaoui'

# Set the theme (optional)
html_theme = 'sphinx_rtd_theme'





autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
    'inherited-members': True,
    'special-members': '__init__',
}

