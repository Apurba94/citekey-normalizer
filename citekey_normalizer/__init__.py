"""Rewrite BibTeX citation keys to a consistent scheme and update LaTeX sources."""
from .core import make_key, plan_keys, rewrite_bib, rewrite_tex, read_entries

__version__ = "0.1.0"
__all__ = ["make_key", "plan_keys", "rewrite_bib", "rewrite_tex", "read_entries"]
