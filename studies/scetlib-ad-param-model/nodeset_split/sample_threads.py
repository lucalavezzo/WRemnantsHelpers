#!/usr/bin/env python3
"""Sample a process's running-thread count and CPU rate at 1 Hz.

The member loop's barrier is invisible in any log the builder writes, so measure
it from the outside: within one member step the bin sweep is a tbb::parallel_for
over bins of very unequal cost, so if threads idle at the barrier the RUNNING
thread count must decay before each step boundary and snap back after it.
"""
import os
import sys
import time

pid = int(sys.argv[1])
out = sys.argv[2]
dt = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
CLK = os.sysconf("SC_CLK_TCK")
prev = None
with open(out, "w", buffering=1) as f:
    f.write("t,n_threads,n_running,cores\n")
    t0 = time.time()
    while True:
        try:
            tasks = os.listdir(f"/proc/{pid}/task")
            nrun = 0
            for t in tasks:
                try:
                    with open(f"/proc/{pid}/task/{t}/stat") as g:
                        s = g.read()
                    st = s[s.rindex(")") + 2]
                    if st == "R":
                        nrun += 1
                except OSError:
                    pass
            with open(f"/proc/{pid}/stat") as g:
                fld = g.read().rsplit(") ", 1)[1].split()
            cpu = (int(fld[11]) + int(fld[12])) / CLK
        except OSError:
            break
        now = time.time()
        cores = "" if prev is None else f"{(cpu - prev[1]) / (now - prev[0]):.2f}"
        f.write(f"{now - t0:.2f},{len(tasks)},{nrun},{cores}\n")
        prev = (now, cpu)
        time.sleep(dt)
