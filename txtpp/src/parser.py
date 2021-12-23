import sys
import traceback

"""
# LL(1) grammar

file: lines

condition: IF lines [else_clause] END
else_clause:
    ELIF lines else_clause
    | ELSE lines

lines: %empty
    | lines lines

line: TEXT
    | condition
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

        if self.lines[-1].type == type:
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


first = {"lines": ("if", "text"), "else_clause": ("else", "elif")}


def parse_file(parser):
    try:
        lines = parse_lines(parser)

        if not parser.is_eof():
            print("Failed to parse file, remaining lines")
            return None

        return lines
    except Exception as e:
        traceback.print_exc()

        print(file=sys.stderr)
        print(f"At line {parser.get_line()}: ", end="", file=sys.stderr)
        if parser.is_eof():
            print("<eof>")
        else:
            print(parser.default_lines[parser.get_line() - 1])
        print("error:", e, file=sys.stderr)

        return None


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
    condition = parser.expect("elif" if parse_elif else "if").data
    body = parse_lines(parser)
    if parser.peek().type != "end":
        else_clause = parse_else_clause(parser)
    else:
        else_clause = None

    if not parse_elif:
        parser.expect("end")

    node = Node(
        "condition", data={"condition": condition, "body": body, "else": else_clause}
    )

    return node


def parse_line(parser):
    if line := parser.accept("text"):
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
        if ctx.is_true(node.data["condition"]):
            exec_node(node.data["body"], ctx)
        else:
            exec_node(node.data["else"], ctx)
    else:
        raise Exception(f"Cannot execute {node.type} node")


if __name__ == "__main__":
    lines = [
        Node("text", "world"),
        Node("if", "HELLO"),
        Node("text", "hello"),
        Node("text", "lol"),
        Node("elif", "WORLD"),
        Node("elif", "WORLD2"),
        Node("text", "okay"),
        Node("text", "okey"),
        Node("else"),
        Node("text", ":thinking:"),
        Node("end"),
        Node("text", "ok"),
    ]

    defs = set()
    # defs.add("HELLO")
    defs.add("WORLD2")
    ctx = Context(defs)

    node = parse_file(Parser(lines))
    exec_node(node, ctx)
