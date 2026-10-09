import sys
from rabbit import io_tools

for p in sys.argv[1:]:
    r = io_tools.get_fitresult(p)
    print(f"{p}: nllvalreduced {r.get('nllvalreduced')!r}  edmval {r.get('edmval')!r}")
