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
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'numpydoc',
    'sphinx_copybutton',
    'myst_parser',
    'sphinx_rtd_dark_mode',
    'sphinx_rtd_theme',
]

# MyST extensions
myst_enable_extensions = ['colon_fence', 'deflist']

templates_path = ['_templates']
exclude_patterns = []

# Configuration options for plot_directive. See:
# https://github.com/matplotlib/matplotlib/blob/f3ed922d935751e08494e5fb5311d3050a3b637b/lib/matplotlib/sphinxext/plot_directive.py#L81
plot_html_show_source_link = False
plot_html_show_formats = False

# Generate the API documentation when building
autosummary_generate = True
numpydoc_show_class_members = False

# get versions
try:
    import bcsophyd
    release = version = bcsophyd.__version__
except ImportError:
    release = version = "0.1.0"

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = '.md'

# The master toctree document.
master_doc = 'index'

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
import sphinx_rtd_theme
html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
# html_logo = "_static/tsuchinoko-real.png"
html_style = 'custom.css'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = dict(
    display_version=True,
    collapse_navigation=False,
    titles_only=False
)

# user starts in dark mode
default_dark_mode = True

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'bcsophyd'

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/reference/', None),
    # 'pandas': ('https://pandas.pydata.org/pandas-docs/stable', None),
    # 'matplotlib': ('https://matplotlib.org/stable', None),
    # 'pyqtgraph': ("https://pyqtgraph.readthedocs.io/en/latest/", None),
    # 'bluesky-adaptive': ("https://blueskyproject.io/bluesky-adaptive/", None),
}

autoclass_content = 'both'