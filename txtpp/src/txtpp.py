#!/usr/bin/env python3

import re
import sys
import io
import os


class TextPreprocessorError(Exception):
    def __init__(self, file_id, line, msg):
        super().__init__(f"{file_id}:{line}: {msg}")


def debug_print(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def preprocess(
    file: io.TextIOWrapper,
    definitions: set[str],
    debug: bool = False,
    file_id: str = "<stdin>",
):
    line = 0

    re_comment = re.compile(r"@@.*")
    re_define = re.compile(r"@\s*define\s+(\w+)")
    re_undef = re.compile(r"@\s*undef\s+(\w+)")
    re_if = re.compile(r"@\s*if\s+(\w+)")
    re_elif = re.compile(r"@\s*elif\s+(\w+)")
    re_ifnot = re.compile(r"@\s*ifnot\s+(\w+)")
    re_elifnot = re.compile(r"@\s*elifnot\s+(\w+)")
    re_else = re.compile(r"@\s*else")
    re_end = re.compile(r"@\s*end")

    conditions = []

    while (text := file.readline()) != "":
        line += 1
        is_ifnot = False
        is_elif = False

        if end_newline := text[-1] == "\n":
            text = text[:-1]

        # Comment
        if (match := re_comment.fullmatch(text)) is not None:
            if debug:
                debug_print("@Comment")
        # If
        elif (
            (match := re_if.fullmatch(text)) is not None
            or (match := re_ifnot.fullmatch(text)) is not None
            and (is_ifnot := True)
            or (match := re_elif.fullmatch(text)) is not None
            and (is_elif := True)
            or (match := re_elifnot.fullmatch(text)) is not None
            and (is_elif := True)
            and (is_elifnot := True)
        ):
            key = match.group(1)

            is_true = key in definitions
            if is_ifnot:
                is_true = not is_true

            if is_elif:
                if conditions == []:
                    raise TextPreprocessorError(file_id, line, "@elif without @if")

                conditions[-1] = not conditions[-1] and is_true

                if debug:
                    debug_print(
                        f"@({'Elifnot' if is_ifnot else 'Elif'}({key}): {is_true}"
                    )
            else:
                # Push condition state
                conditions.append(is_true)

                if debug:
                    debug_print(f"@({'Ifnot' if is_ifnot else 'If'}({key}): {is_true}")
        # Else
        elif (match := re_else.fullmatch(text)) is not None:
            if conditions == []:
                raise TextPreprocessorError(file_id, line, "@else without @if")

            conditions[-1] = not conditions[-1]

            if debug:
                debug_print(f"@Else")
        # End
        elif (match := re_end.fullmatch(text)) is not None:
            if conditions == []:
                raise TextPreprocessorError(file_id, line, "@end without @if")

            conditions.pop(-1)

            if debug:
                debug_print(f"@End")
        # Define
        elif (match := re_define.fullmatch(text)) is not None:
            key = match.group(1)

            definitions.add(key)

            if debug:
                debug_print(f"@Define({key})")
        # Undef
        elif (match := re_undef.fullmatch(text)) is not None:
            key = match.group(1)

            del definitions[key]

            if debug:
                debug_print(f"@Undef({key})")
        # Text data
        # TODO : Opti
        elif all(conditions):
            print(text, end="\n" if end_newline else "")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Text preprocessor")
    parser.add_argument(
        "--debug", dest="debug", action="store_true", default=False, help="Debug mode"
    )
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

        deffile = importlib.machinery.SourceFileLoader(
            "deffile", os.path.realpath(args.deffile)
        )
        deffile = deffile.load_module()
        definitions |= set(deffile.definitions)

    if args.definitions:
        definitions |= args.definitions

    file = sys.stdin if args.file is None else open(args.file, "r")
    try:
        preprocess(
            file,
            definitions,
            debug=args.debug,
            file_id="<stdin>" if args.file is None else args.file,
        )
    finally:
        if args.file is not None:
            file.close()
