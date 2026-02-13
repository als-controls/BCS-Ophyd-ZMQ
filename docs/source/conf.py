# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
from pathlib import Path

# Add src to path for autodoc
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'bcsophyd'
copyright = '2025, Joao Gabriel Felipe Machado Gazolla'
author = 'Joao Gabriel Felipe Machado Gazolla'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_parser',  # Markdown support
    'sphinx.ext.autodoc',  # API documentation from docstrings
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',  # Link to other projects' documentation
    'sphinx.ext.viewcode',  # Add links to source code
    'sphinx.ext.napoleon',
    'sphinx_copybutton',
    'sphinx_immaterial',  # Material theme extensions
]

# MyST extensions
myst_enable_extensions = [
    'colon_fence',  # ::: directives
    'deflist',  # Definition lists
    'fieldlist',  # Field lists
    'tasklist',  # Task lists with checkboxes
]

templates_path = ['_templates']
exclude_patterns = []

# Configuration options for plot_directive. See:
# https://github.com/matplotlib/matplotlib/blob/f3ed922d935751e08494e5fb5311d3050a3b637b/lib/matplotlib/sphinxext/plot_directive.py#L81
plot_html_show_source_link = False
plot_html_show_formats = False

# Generate the API documentation when building
autosummary_generate = True
napoleon_numpy_docstring = True
napoleon_google_docstring = True

# get versions
try:
    import bcsophyd
    release = version = bcsophyd.__version__
except ImportError:
    release = version = "0.1.0"

# The suffix(es) of source filenames.
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# The master toctree document.
master_doc = 'index'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_immaterial'
html_static_path = ['_static']
html_css_files = ['custom.css']
html_title = 'bcsophyd Documentation'
html_logo = '_static/bcsophyd.png'
html_favicon = '_static/bcsophyd.png'

# Theme options for sphinx-immaterial
html_theme_options = {
    "icon": {
        "repo": "fontawesome/brands/gitlab",
    },
    "site_url": "https://git.als.lbl.gov/bcs/bluesky/bcsophyd-zmq",
    "repo_url": "https://git.als.lbl.gov/bcs/bluesky/bcsophyd-zmq",
    "repo_name": "bcsophyd-zmq",
    "edit_uri": "blob/main/docs",
    "globaltoc_collapse": True,
    "features": [
        "navigation.expand",
        "navigation.sections",
        "navigation.top",
        "search.highlight",
        "search.share",
        "toc.follow",
        "toc.sticky",
        "content.tabs.link",
        "announce.dismiss",
    ],
    "palette": [
        {
            "media": "(prefers-color-scheme: light)",
            "scheme": "default",
            "primary": "blue",
            "accent": "light-blue",
            "toggle": {
                "icon": "material/brightness-7",
                "name": "Switch to dark mode",
            },
        },
        {
            "media": "(prefers-color-scheme: dark)",
            "scheme": "slate",
            "primary": "blue",
            "accent": "light-blue",
            "toggle": {
                "icon": "material/brightness-4",
                "name": "Switch to light mode",
            },
        },
    ],
    "toc_title_is_page_title": True,
}

# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'bcsophyd'

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/reference/', None),
}

autoclass_content = 'both'
