# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add the project root to the path for autodoc
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
project = 'BSPump'
copyright = '2024, BitSwan'
author = 'BitSwan'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx_copybutton',
    'myst_parser',
    'sphinx_design',
]

# MyST parser configuration
myst_enable_extensions = [
    'colon_fence',
    'deflist',
]

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
}
autodoc_typehints = 'description'

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'aiohttp': ('https://docs.aiohttp.org/en/stable/', None),
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Source file extensions
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# -- Options for HTML output -------------------------------------------------
html_theme = 'furo'

html_theme_options = {
    'light_css_variables': {
        'color-brand-primary': '#0066cc',
        'color-brand-content': '#0066cc',
    },
    'dark_css_variables': {
        'color-brand-primary': '#4da6ff',
        'color-brand-content': '#4da6ff',
    },
    'sidebar_hide_name': False,
    'navigation_with_keys': True,
}

html_static_path = ['_static']
html_css_files = ['custom.css']

html_title = 'BSPump Documentation'
html_short_title = 'BSPump'

# Logo configuration
html_logo = '_static/images/bitswan-logo.svg'
html_favicon = '_static/images/bitswan-logo.svg'

# -- Copy button configuration -----------------------------------------------
copybutton_prompt_text = r'>>> |\.\.\. |\$ '
copybutton_prompt_is_regexp = True
