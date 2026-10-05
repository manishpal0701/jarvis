import ast

with open('tools/app_builder/node_generator.py', 'r', encoding='utf-8') as f:
    code = f.read()

try:
    ast.parse(code)
    print("AST Parse Successful!")
except SyntaxError as e:
    print(f"SyntaxError on line {e.lineno}, col {e.offset}: {e.msg}")
    lines = code.splitlines()
    start = max(0, e.lineno - 10)
    end = min(len(lines), e.lineno + 10)
    for idx in range(start, end):
        print(f"{idx+1}: {lines[idx]}")
