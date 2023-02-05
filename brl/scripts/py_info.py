#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pylint: disable=multiple-statements

import argparse
import logging
import os
import sys


version_info = [
    "sys.executable",
    "sys.prefix",
    "sys.exec_prefix",
    "sys.version",
    "sys.version_info",
    "sys.implementation",
    "sys.platform",
    "os.name",
]

system_info = [
    "sys.maxunicode",
    "sys.maxsize",
    "sys.int_info",
    "sys.float_repr_style",
    "sys.float_info",
    "sys.thread_info",
    "os.path",
    "os.sep",
    "os.pathsep",
    "os.defpath",
]

extra_info = [
    "sys.hexversion",
    "sys.copyright",
    "sys.hash_info",
    "os.curdir",
    "os.pardir",
    "os.extsep",
    "os.linesep",
    "os.altsep",
    "os.devnull",
    "sys.builtin_module_names",
]

_ARGS_PROPS = {
    "version": version_info,
    "system": system_info,
    "extra": extra_info,
}

# TODO print as pretty table
def print_eval(stmts):
    """Evaluate a list of statements."""
    for _ in stmts:
        out = ""
        try:
            out = str(eval(_))  # nosec, pylint: disable=eval-used
        except Exception as error:  # pylint: disable=broad-except
            logging.exception("Error: %s", error)
            out = "_"
        finally:
            print(_ + " : \t\t" + out + "")


if __name__ == "__main__":

    print("Running Python version: " + sys.version)
    print("Current directory: " + os.getcwd())

    parser = argparse.ArgumentParser(description="Python version info.")
    parser.add_argument(
        "-v", "--version", default=True, action="store_true", help="print version",
    )
    parser.add_argument(
        "-s", "--system", default=False, action="store_true", help="print system info",
    )
    parser.add_argument(
        "-e", "--extra", default=False, action="store_true", help="print extra info",
    )
    args = parser.parse_args()

    for arg, props in _ARGS_PROPS.items():
        if getattr(args, arg):
            print("\n\n **********" + arg.upper() + "INFO ********** \n")
            print_eval(props)
            print()
