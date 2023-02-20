#!/usr/bin/env python3
"""Clean up and print env path."""

import logging
import os
import sys
from pathlib import Path


# check if verbose arg is passed
if "-v" in sys.argv:
    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    datefmt = "%m/%d/%Y %H:%M:%S"
    logging.basicConfig(level=logging.DEBUG, format=fmt, datefmt=datefmt)
else:
    logging.basicConfig(level=logging.ERROR)

path = os.getenv("PATH", "")
paths = dict.fromkeys(path.split(":")).keys()

_paths = []
_win_paths = []
for p in paths:
    if Path(p).exists():
        if p.startswith("/mnt/"):
            logging.debug("Path %s is a windows path", p)
            _win_paths.append(p.lower())
        else:
            _paths.append(p)
    else:
        logging.debug("Path %s does not exist", p)

_win_paths = list(dict.fromkeys(_win_paths).keys())

logging.debug("Paths: %s", _paths)
logging.debug("Windows paths: %s", _win_paths)

_paths.extend(_win_paths)
_path = ":".join(_paths)
os.environ["PATH"] = _path
print(_path)
