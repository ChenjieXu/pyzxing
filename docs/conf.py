from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

project = "pyzxing"
author = "Chenjie Xu"
copyright = "2026, Chenjie Xu"
release = runpy.run_path(ROOT / "pyzxing" / "__version__.py")["__version__"]

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
]

autodoc_member_order = "bysource"
autodoc_typehints = "description"
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

html_theme = "sphinx_rtd_theme"
html_title = f"pyzxing {release}"
html_theme_options = {
    "navigation_depth": 3,
    "collapse_navigation": False,
}

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
