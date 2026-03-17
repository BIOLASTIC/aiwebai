import re

with open('backend/app/adapters/mcpcli_adapter.py', 'r') as f:
    lines = f.readlines()

with open('backend/app/adapters/mcpcli_adapter.py', 'w') as f:
    i = 0
    while i < len(lines):
        if '"source": "mcpcli",
' in lines[i] and '},
' in lines[i+1]:
            f.write(lines[i])
            f.write('                "capabilities": {"chat": True}
')
        else:
            f.write(lines[i])
        i += 1

