import sys
from rabbit import io_tools

p = sys.argv[1]
res = io_tools.get_fitresult(p)
print(sorted(res.keys()))
