"""Shared helpers for applying axis selections to histograms from CLI flags.

Used by compare_file_hists.py and plot_narf_hists.py so both scripts parse
--select / --selectByHist identically.
"""

import argparse

from wremnants.utilities import parsing


def apply_selection(h, sel_str):
    """Apply a single selection string like 'axis val' or 'axis lb ub' to h.

    Returns the selected histogram. If the axis is missing, prints a warning
    and returns h unchanged.
    """
    sel = sel_str.split()
    if len(sel) == 3:
        sel_ax, sel_lb, sel_ub = sel
        sel_lb = parsing.str_to_complex_or_int(sel_lb)
        sel_ub = parsing.str_to_complex_or_int(sel_ub)
        if sel_ax not in h.axes.name:
            print(
                f"Selection axis '{sel_ax}' not found in histogram axes. Available axes: {h.axes.name}"
            )
            return h
        return h[{sel_ax: slice(sel_lb, sel_ub)}]
    elif len(sel) == 2:
        sel_ax, sel_val = sel
        try:
            sel_val = parsing.str_to_complex_or_int(sel_val)
        except argparse.ArgumentTypeError as e:
            print(e)
            print("Trying to use as string...")
            pass
        if sel_ax not in h.axes.name:
            print(
                f"Selection axis '{sel_ax}' not found in histogram axes. Available axes: {h.axes.name}"
            )
            return h
        return h[{sel_ax: sel_val}]
    else:
        raise ValueError(
            f"Invalid selection '{sel_str}'. Expected 'axis value' or 'axis lb ub'."
        )


def apply_selections(h, selections):
    """Apply an iterable of selection strings to h in order."""
    if not selections:
        return h
    for sel in selections:
        h = apply_selection(h, sel)
    return h


def parse_select_by_hist_item(raw):
    """Split a single --selectByHist value by ';' into individual selection strings."""
    if raw is None:
        return []
    return [p.strip() for p in raw.split(";") if p.strip()]


def collect_selections(global_selections, select_by_hist, index):
    """Combine per-histogram selections (from --selectByHist) with global ones.

    Per-hist selections come first, then global selections, matching the order
    used by plot_narf_hists.py.
    """
    combined = []
    if select_by_hist is not None and index < len(select_by_hist):
        combined.extend(parse_select_by_hist_item(select_by_hist[index]))
    if global_selections:
        combined.extend(global_selections)
    return combined


def format_selection_label(selections):
    """Return a newline-joined human-readable label for a list of selections, or None."""
    if not selections:
        return None
    lines = []
    for sel in selections:
        parts = sel.split()
        if len(parts) == 3:
            sel_ax, sel_lb, sel_ub = parts
            lines.append(f"{sel_ax}: [{sel_lb}, {sel_ub})")
        elif len(parts) == 2:
            sel_ax, sel_val = parts
            lines.append(f"{sel_ax}: {sel_val}")
    return "\n".join(lines) if lines else None
