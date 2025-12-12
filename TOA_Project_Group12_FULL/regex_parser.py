
# regex_parser.py - validate and convert infix RE to postfix (explicit concat '.')
def validate_regex(regex: str):
    stack = []
    prev = None
    for i, c in enumerate(regex):
        if c == ' ':
            continue
        if c == '(':
            stack.append(i)
        elif c == ')':
            if not stack:
                raise ValueError(f"Invalid Regular Expression: Unmatched closing parenthesis at position {i}")
            stack.pop()
        elif c == '+':
            if prev is None or prev in '+.(':
                raise ValueError(f"Invalid Regular Expression: Invalid use of '+' at position {i}")
        elif c == '*':
            if prev is None or prev in '+.(':
                raise ValueError(f"Invalid Regular Expression: Invalid use of '*' at position {i}")
            if prev == '*':
                raise ValueError(f"Invalid Regular Expression: Invalid repetition operator '*' at position {i-1}")
        else:
            if not c.isalnum():
                raise ValueError(f"Invalid Regular Expression: Unknown symbol '{c}' at position {i}")
        prev = c
    if stack:
        pos = stack[-1]
        raise ValueError(f"Invalid Regular Expression: Missing closing parenthesis for '(' at position {pos}")
    if prev in '+.':
        raise ValueError(f"Invalid Regular Expression: Expression ends with invalid operator '{prev}'")

def add_concat(regex: str) -> str:
    output = []
    prev = None
    for c in regex:
        if c == ' ':
            continue
        if prev is not None:
            if (prev.isalnum() or prev == '*' or prev == ')') and (c.isalnum() or c == '('):
                output.append('.')
        output.append(c)
        prev = c
    return ''.join(output)

precedence = {'*': 3, '.': 2, '+': 1}

def to_postfix(regex: str) -> str:
    validate_regex(regex)
    regex2 = add_concat(regex)
    out = []
    stack = []
    for token in regex2:
        if token.isalnum():
            out.append(token)
        elif token == '(':
            stack.append(token)
        elif token == ')':
            while stack and stack[-1] != '(':
                out.append(stack.pop())
            if not stack:
                raise ValueError("Invalid Regular Expression: Unmatched parenthesis during parsing")
            stack.pop()
        else:
            while stack and stack[-1] != '(' and precedence.get(stack[-1], 0) >= precedence.get(token, 0):
                out.append(stack.pop())
            stack.append(token)
    while stack:
        t = stack.pop()
        if t in '()':
            raise ValueError("Invalid Regular Expression: Unmatched parenthesis in expression")
        out.append(t)
    return ''.join(out)
