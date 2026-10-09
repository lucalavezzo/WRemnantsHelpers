"""Print the meta_info command (and rabbit/WRemnants hashes) of fitresults files. No alphaS value is read."""

import sys
from rabbit import io_tools

for f in sys.argv[1:]:
    _, meta = io_tools.get_fitresult(f, None, meta=True)
    mi = meta["meta_info"]
    print("==", f)
    for k, v in mi.items():
        if k != "command":
            print("  ", k, str(v)[:200])
    print("  command:", mi["command"])
