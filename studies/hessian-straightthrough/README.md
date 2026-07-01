# hessian-straightthrough

Development and validation scratch for the SCETlib NP param-model **Hessian
straight-through** approach (compact J/K so rabbit's Hessian fit doesn't OOM).
The actual solution landed in `WRemnants` (`wremnants/postprocessing/scetlib_np/`);
these are the toy/validation scripts used to get there:

- `toy_straightthrough.py`, `toy_customgrad.py` — toy models of the straight-through
  / custom-gradient param model.
- `validate_real_jac.py` — checks the compact Jacobian against the real one.
- `test_nestedfa.py`, `test_ops_nestedfa.py` — nested `forward_as` / op tests.

Rescued 2026-07-01 from a Jun-22 `HOME_WIP_BACKUP` tarball (the only place they
survived) before deleting the backup. Kept as reference; not wired into anything.
