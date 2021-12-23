import sys
import traceback
import re
import io


"""
# LL(1) grammar

file: lines

condition: [IF | IFNOT] lines [else_clause] END
else_clause:
    [ELIF | ELIFNOT] lines else_clause
    | ELSE lines

lines: %empty
    | lines lines

instruction: DEFINE
    | UNDEF

line: TEXT
    | condition
    | instruction
"""


class Node:
    def __init__(self, type, data=None):
        self.type = type
        self.data = data

    def __repr__(self):
        return f"{self.type}({self.data})"


class Parser:
    def __init__(self, lines):
        self.lines = lines[::-1]
        self.n_lines = len(lines)
        self.default_lines = lines

    def peek(self):
        if self.lines == []:
            return Node("eof")

        return self.lines[-1]

    def consume(self):
        return self.lines.pop()

    def accept(self, type):
        if self.lines == []:
            return None

        if isinstance(type, list) and self.lines[-1].type in type:
            return self.consume()
        elif not isinstance(type, list) and self.lines[-1].type == type:
            return self.consume()

        return None

    def expect(self, type):
        acc = self.accept(type)

        assert acc, f"Expected {type}"

        return acc

    def is_eof(self):
        return self.lines == []

    def get_line(self):
        return self.n_lines - len(self.lines) + 1


first = {
    "lines": ("if", "ifnot", "text", "define", "undef"),
    "else_clause": ("else", "elifnot", "elif"),
}


def parse_file(parser):
    try:
        lines = parse_lines(parser)

        if not parser.is_eof():
            print("Failed to parse file, remaining lines")
            return None

        return lines
    except Exception as e:
        print(f"At line {parser.get_line()}: ", end="", file=sys.stderr)
        if parser.is_eof():
            print("<eof>", file=sys.stderr)
        else:
            print(parser.default_lines[parser.get_line() - 1], file=sys.stderr)

        raise e


def parse_lines(parser):
    lines = []
    while parser.peek().type in first["lines"]:
        lines.append(parse_line(parser))

    return Node("lines", lines)


def parse_else_clause(parser):
    if parser.peek().type == "elif":
        return parse_condition(parser, parse_elif=True)

    parser.expect("else")

    return parse_lines(parser)


def parse_condition(parser, parse_elif=False):
    lookahead_type = ["elif", "elifnot"] if parse_elif else ["if", "ifnot"]
    lookahead = parser.peek()

    if lookahead.type not in lookahead_type:
        raise Exception(f"Failed to parse condition, got {lookahead.type} node")

    parser.consume()

    condition = lookahead.data
    is_not = lookahead.type == lookahead_type[1]

    body = parse_lines(parser)
    if parser.peek().type != "end":
        else_clause = parse_else_clause(parser)
    else:
        else_clause = None

    if not parse_elif:
        parser.expect("end")

    node = Node(
        "condition",
        data={"condition": condition, "body": body, "else": else_clause, "not": is_not},
    )

    return node


def parse_line(parser):
    if line := parser.accept(["text", "define", "undef"]):
        return line
    else:
        return parse_condition(parser)

    raise Exception("Failed to parse line")


class Context:
    def __init__(self, definitions=None):
        self.definitions = definitions or set()

    def is_true(self, definition):
        return definition in self.definitions


def exec_node(node, ctx):
    if node is None:
        pass
    elif node.type in ("line", "text"):
        print(node.data)
    elif node.type == "lines":
        for node in node.data:
            exec_node(node, ctx)
    elif node.type == "condition":
        if ctx.is_true(node.data["condition"]) != node.data["not"]:
            exec_node(node.data["body"], ctx)
        else:
            exec_node(node.data["else"], ctx)
    elif node.type == "define":
        ctx.definitions.add(node.data)
    elif node.type == "undef":
        if node.data in ctx.definitions:
            ctx.definitions.remove(node.data)
    else:
        raise Exception(f"Cannot execute {node.type} node")


def lex(file: io.TextIOWrapper) -> list[str]:
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

    lines = []

    while (text := file.readline()) != "":
        line += 1

        if end_newline := text[-1] == "\n":
            text = text[:-1]

        # Comment
        if (match := re_comment.fullmatch(text)) is not None:
            pass
        # If
        elif (
            (match := re_if.fullmatch(text)) is not None
            and (type := "if")
            or (match := re_ifnot.fullmatch(text)) is not None
            and (type := "ifnot")
            or (match := re_elif.fullmatch(text)) is not None
            and (type := "elif")
            or (match := re_elifnot.fullmatch(text)) is not None
            and (type := "elifnot")
        ):
            key = match.group(1)

            node = Node(type, key)
            lines.append(node)
        # Else
        elif (match := re_else.fullmatch(text)) is not None:
            lines.append(Node("else"))
        # End
        elif (match := re_end.fullmatch(text)) is not None:
            lines.append(Node("end"))
        # Define
        elif (match := re_define.fullmatch(text)) is not None:
            key = match.group(1)

            lines.append(Node("define", key))
        # Undef
        elif (match := re_undef.fullmatch(text)) is not None:
            key = match.group(1)

            lines.append(Node("undef", key))
        else:
            lines.append(Node("text", text))

    return lines


def parse_exec(file: io.TextIOWrapper, definitions: set[str]):
    lines = lex(file)
    ast = parse_file(Parser(lines))

    ctx = Context(definitions)

    exec_node(ast, ctx)
