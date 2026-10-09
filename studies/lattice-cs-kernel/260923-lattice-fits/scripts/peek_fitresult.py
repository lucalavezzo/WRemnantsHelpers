import sys
from rabbit import io_tools

r = io_tools.get_fitresult(sys.argv[1])
for k, v in r.items():
    s = str(v)[:120].replace("\n", " ")
    print(k, type(v).__name__, s)
