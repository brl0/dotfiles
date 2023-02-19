#!/usr/bin/env python3
"""Clean up and print env path."""

import logging
import os
from pathlib import Path


path = os.getenv("PATH")
paths = path.split(":")
paths = dict.fromkeys(paths).keys()

_paths = []
_win_paths = []
for p in paths:
    if Path(p).exists():
        if p.startswith("/mnt/"):
            _win_paths.append(p)
        else:
            _paths.append(p)
    else:
        logging.debug(f"Path {p} does not exist")

_paths.extend(_win_paths)
_path = ":".join(_paths)
os.environ["PATH"] = _path
print(_path)
