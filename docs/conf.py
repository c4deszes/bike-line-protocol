import sys, os

with open(os.path.join(os.path.dirname(__file__), "..", "library.properties"), "r") as f:
    version_str = "0.0.0"  # Default version in case of failure to read
    for line in f:
        if line.startswith("version="):
            version_str = line.strip().split("=", 1)[1]
            break

project = "line-protocol"
copyright = "Balazs Eszes, 2025"
author = "Balazs Eszes"
version = version_str

sys.path.append(os.path.abspath("./_ext"))
sys.path.append(os.path.abspath("../python-lib"))

extensions = [
    "breathe",
    "sphinx_rtd_theme",
    'jupyter_sphinx',
    'sphinx.ext.mathjax',
    'matplotlib.sphinxext.mathmpl',
    'matplotlib.sphinxext.plot_directive',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.doctest',
    'sphinxcontrib.mermaid',
    'sphinxcontrib.kroki'
]

autosectionlabel_prefix_document = True

autoclass_content = "init"

# Breathe configuration
breathe_default_project = "line-protocol"
breathe_projects = {}
breathe_show_define_initializer = False

html_static_path = ['_static']
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation" : False,
    "show_navbar_depth": 2
}
html_js_files = ["https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"]
source_suffix = '.rst'
master_doc = 'index'
