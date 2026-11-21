"""Resolves test artifact filenames to their location in the project, independent of the working directory."""

import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEARCH_DIRS = ["", "00_data_warehouse", "data", "data/raw", "models", "reports", "results", "docs"]


def find(name):
    for d in SEARCH_DIRS:
        path = os.path.join(ROOT, d, name)
        if os.path.exists(path):
            return path
    return os.path.join(ROOT, name)  # missing: keeps the "file missing" assertion message meaningful
