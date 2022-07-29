#!/usr/bin/env python3

import re
import sys
import io
import os
import traceback


class TextPreprocessorError(Exception):
    def __init__(self, file_id, line, msg):
        super().__init__(f"{file_id}:{line}: {msg}")


def debug_print(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def preprocess(
    file: io.TextIOWrapper,
    definitions: set[str],
    file_id: str = "<stdin>",
):
    import parser

    parser.parse_exec(file, definitions, file_id)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Text preprocessor")
    parser.add_argument(
        "-D", dest="definitions", action="append", help="Set definition"
    )
    parser.add_argument(
        "--deffile",
        dest="deffile",
        help="Set definition file, the definition file is a python file that defines a definitions iterable that contains definitions",
    )
    parser.add_argument(
        "file", nargs="?", default=None, help="Input file (stdin by default)"
    )

    args = parser.parse_args()

    definitions = set()

    if args.deffile:
        import importlib
        import importlib.machinery

        deffile = importlib.machinery.SourceFileLoader(
            "deffile", os.path.realpath(args.deffile)
        )
        deffile = deffile.load_module()
        definitions |= set(deffile.definitions)

    if args.definitions:
        definitions |= set(args.definitions)

    file = sys.stdin if args.file is None else open(args.file, "r")
    file_id = "<stdin>" if args.file is None else args.file
    try:
        preprocess(
            file,
            definitions,
            file_id
        )
    except:
        traceback.print_exc()

        print("Failed to parse / execute file", file_id, file=sys.stderr)

        exit(3)
    finally:
        if args.file is not None:
            file.close()
