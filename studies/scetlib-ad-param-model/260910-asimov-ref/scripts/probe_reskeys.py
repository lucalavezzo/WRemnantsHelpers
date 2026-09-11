import sys

sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants/rabbit")
from rabbit import io_tools

res, meta = io_tools.get_fitresult(sys.argv[1], meta=True)
print("RESULT KEYS:")
for k, v in res.items():
    print("  ", k, type(v).__name__)
