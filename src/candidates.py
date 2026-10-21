"""Loads the candidate list from config/candidates.json instead of hardcoding
party names in the voting script. Edit that file to change candidates without
touching any code."""

import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'candidates.json')


def load_candidates(path=None):
    """Returns a dict keyed by the keyboard key, e.g. {'1': {'name': ..., 'party': ...}}."""
    path = path or CONFIG_PATH
    with open(path, 'r') as f:
        data = json.load(f)
    return {c['key']: c for c in data['candidates']}
