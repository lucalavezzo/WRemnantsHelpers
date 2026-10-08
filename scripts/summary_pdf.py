#!/usr/bin/env python3
"""Build a study (or task) summary to SUMMARY.pdf, next to it.

    scripts/summary_pdf.py <slug>                 # studies/<slug>/SUMMARY.tex (or .md)
    scripts/summary_pdf.py <slug>/<YYMMDD-task>   # a task summary
    scripts/summary_pdf.py path/to/SUMMARY.tex [-o out.pdf]

SUMMARY.tex (the format; template studies/_TEMPLATE/SUMMARY.tex) is built with the host's
pdflatex, run from the summary's own directory so figures resolve by relative path, twice,
with -interaction=nonstopmode -halt-on-error. Aux files go to a temporary directory, so
nothing but SUMMARY.pdf lands next to the source; on failure the log is kept as SUMMARY.log
and the LaTeX errors are printed. The title block is typeset from the "% key: value"
metadata lines at the top of the .tex, which this script passes in, so build with this
script rather than with bare pdflatex. pdflatex is NOT in the WRemnants container: run this
on the host for a .tex summary.

SUMMARY.md (deprecated, kept for old summaries) is rendered by the same marked.js + KaTeX
the web viewer uses and printed by headless chromium; chromium is only in the WRemnants
container, so for an .md the script re-executes itself inside singularity.
If both exist, SUMMARY.tex wins.

The PDF is gitignored (studies/**/*.pdf): the source is one rerun away from it.
"""

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STUDIES = REPO / "studies"
MARKED = REPO / "scripts" / "templates" / "vendor" / "marked.min.js"
WEB = "https://submit.mit.edu/~lavezzo/alphaS/studies/"
CONTAINER = (
    "/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/"
    "wmassdevrolling:latest"
)

PAGE = """<!doctype html>
<html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<style>
  @page { size: A4; margin: 16mm 17mm 16mm 17mm; }
  body { font: 10.5pt/1.45 "Helvetica Neue", Helvetica, Arial, sans-serif; color: #111; }
  #meta { font-size: 8.5pt; color: #666; border-bottom: 1px solid #ccc;
          padding-bottom: 4px; margin-bottom: 10px; }
  h1 { font-size: 17pt; margin: 4px 0 8px; }
  h2 { font-size: 12.5pt; margin: 14px 0 5px; border-bottom: 1px solid #ddd;
       padding-bottom: 2px; break-after: avoid; }
  h3 { font-size: 11pt; margin: 10px 0 4px; break-after: avoid; }
  p, li { orphans: 3; widows: 3; }
  blockquote { margin: 8px 0; padding: 6px 10px; border-left: 3px solid #2a78d6;
               background: #eef4fb; }
  blockquote p { margin: 0; }
  code { font-size: 9pt; background: #f2f2f0; padding: 0 3px; border-radius: 3px; }
  pre { font-size: 8.5pt; background: #f2f2f0; padding: 6px 8px; white-space: pre-wrap; }
  pre code { background: none; padding: 0; }
  table { border-collapse: collapse; font-size: 9pt; margin: 8px 0; break-inside: avoid; }
  th, td { border: 1px solid #ccc; padding: 3px 6px; text-align: left; vertical-align: top; }
  th { background: #f2f2f0; }
  img { display: block; max-width: 100%; max-height: 85mm; margin: 6px auto 2px;
        break-inside: avoid; }
  p:has(> img) { break-inside: avoid; }
  em { color: #333; }
  small { font-size: 8.5pt; color: #555; }
  a { color: #1b5fae; text-decoration: none; }
  hr { border: none; border-top: 1px solid #ddd; margin: 12px 0; }
</style></head>
<body><div id="meta">__META__</div><div id="doc"></div>
<script>__MARKED__</script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script>
const SRC = __SRC__;
// same math protection as scripts/templates/study_viewer.php
function protectMath(src, store) {
  const re = /(```[\\s\\S]*?```|~~~[\\s\\S]*?~~~|`[^`\\n]*`)|(\\$\\$[\\s\\S]+?\\$\\$)|(\\\\\\[[\\s\\S]+?\\\\\\])|(\\$(?!\\s)(?:\\\\.|[^$\\\\\\n])+?\\$)|(\\\\\\((?:[\\s\\S]+?)\\\\\\))/g;
  return src.replace(re, (m, code, dd, dbr, inl, ibr) => {
    if (code) return m;
    let tex, display = false;
    if (dd) { tex = dd.slice(2, -2); display = true; }
    else if (dbr) { tex = dbr.slice(2, -2); display = true; }
    else if (inl) { tex = inl.slice(1, -1); }
    else { tex = ibr.slice(2, -2); }
    store.push({tex, display, raw: m});
    return '@@MATH' + (store.length - 1) + '@@';
  });
}
function restoreMath(h, store) {
  return h.replace(/@@MATH(\\d+)@@/g, (_, i) => {
    const m = store[+i];
    if (typeof katex === 'undefined') return m.raw;
    try { return katex.renderToString(m.tex, {displayMode: m.display, throwOnError: false}); }
    catch (e) { return m.raw; }
  });
}
marked.setOptions({gfm: true, breaks: false, mangle: false, headerIds: false});
const store = [];
document.getElementById('doc').innerHTML = restoreMath(marked.parse(protectMath(SRC, store)), store);
// viewer-relative "#slug/task" links mean nothing in a PDF: point them at the web viewer
document.querySelectorAll('a[href^="#"]').forEach(a =>
  a.setAttribute('href', '__WEB__' + a.getAttribute('href')));
</script></body></html>
"""


# ---------------------------------------------------------------- SUMMARY.tex -> pdflatex

META_KEYS = ("title", "slug", "study", "status", "period", "updated", "covers")
TEX_SPECIAL = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "$": r"\$",
    "&": r"\&",
    "#": r"\#",
    "^": r"\textasciicircum{}",
    "_": r"\_",
    "%": r"\%",
    "~": r"\textasciitilde{}",
}


def tex_meta(text):
    """The leading "% key: value" comment lines (same keys as the old md frontmatter)."""
    meta = {}
    for line in text.splitlines():
        if not line.startswith("%"):
            if line.strip():
                break  # metadata lives in the comment block before \documentclass
            continue
        m = re.match(r"^%\s*([a-z]+):\s*(.*?)\s*$", line)
        if m and m.group(1) in META_KEYS and m.group(1) not in meta:
            v = re.sub(r"\s+#.*$", "", m.group(2)).strip()
            if v:
                meta[m.group(1)] = v
    return meta


def tex_escape(v):
    return "".join(TEX_SPECIAL.get(c, c) for c in v)


def latex_errors(log):
    """The error messages of a pdflatex log, each with its l.<n> context line."""
    lines = log.splitlines()
    out = []
    for i, line in enumerate(lines):
        if line.startswith("!") or re.match(r"^\S+\.tex:\d+: ", line):
            block = [line]
            for nxt in lines[i + 1 : i + 12]:
                block.append(nxt)
                if re.match(r"^l\.\d+", nxt):
                    break
            out.append("\n".join(block))
    return out


def latex_warnings(log):
    flat = re.sub(r"\n(?=\S)", " ", log)  # warnings are hard-wrapped at 79 chars
    warns = []
    for pat in (
        r"LaTeX Warning: Reference .*? undefined",
        r"LaTeX Warning: Citation .*? undefined",
        r"LaTeX Warning: Float too large.*?\.",
        r"Missing character: There is no .*? in font [^!]*?!",
        r"Package \w+ Warning: .*?\.",
    ):
        warns += [w.strip() for w in re.findall(pat, flat)]
    n_overfull = len(re.findall(r"^Overfull \\hbox", log, re.M))
    if n_overfull:
        warns.append(f"{n_overfull} overfull \\hbox(es) (text running into the margin)")
    return list(dict.fromkeys(warns))


def build_tex(src, out):
    pdflatex = shutil.which("pdflatex")
    if not pdflatex:
        sys.exit(
            "pdflatex not found. It is on the submit host (/usr/bin/pdflatex) but not in "
            "the WRemnants container: run this script outside singularity."
        )
    text = src.read_text()
    meta = tex_meta(text)
    rel = src.parent.relative_to(STUDIES) if STUDIES in src.parents else None
    if rel is not None:
        parts = rel.parts
        study = parts[0]
        view = "/".join(parts)
        if meta.get("slug") and meta["slug"] != parts[-1]:
            print(
                f"WARNING: '% slug: {meta['slug']}' does not match the directory "
                f"'{parts[-1]}'; links use the directory"
            )
    else:
        study = meta.get("study") or meta.get("slug", "?")
        view = f"{meta['study']}/{meta['slug']}" if meta.get("study") else study
    missing = [k for k in META_KEYS if k != "study" and k not in meta]
    placeholder = [
        k for k, v in meta.items() if "<" in v or "YYYY" in v or "YYMMDD" in v
    ]
    if missing:
        print(
            f"WARNING: metadata missing: {', '.join(missing)} (see the template header)"
        )
    if placeholder:
        print(
            f"WARNING: metadata still holds template placeholders: {', '.join(placeholder)}"
        )
    if meta.get("covers") and meta.get("updated") and meta["covers"] > meta["updated"]:
        print("WARNING: covers is later than updated")

    def detok(v):
        return r"\detokenize{" + re.sub(r"[{}\\#%]", "", v) + "}"

    defs = {
        "SumTitle": tex_escape(meta.get("title", src.parent.name)),
        "SumStatus": tex_escape(meta.get("status", "?")),
        "SumPeriod": tex_escape(meta.get("period", "?")),
        "SumUpdated": tex_escape(meta.get("updated", "?")),
        "SumCovers": tex_escape(meta.get("covers", "?")),
    }
    edefs = {
        "SumSlug": detok(meta.get("slug", src.parent.name)),
        "SumStudy": detok(study),
        "SumViewPath": detok(view),
    }
    job = src.stem
    pre = "".join(rf"\def\{k}{{{v}}}" for k, v in defs.items())
    pre += "".join(rf"\edef\{k}{{{v}}}" for k, v in edefs.items())
    tex_arg = pre + rf"\input{{{src.name}}}"

    saved_log = src.with_suffix(".log")
    with tempfile.TemporaryDirectory(prefix="summary_tex_") as tmp:
        cmd = [
            pdflatex,
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            f"-jobname={job}",
            f"-output-directory={tmp}",
            tex_arg,
        ]
        log = ""
        for run in range(3):
            r = subprocess.run(
                cmd,
                cwd=src.parent,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=300,
            )
            logf = Path(tmp) / f"{job}.log"
            log = logf.read_text(errors="replace") if logf.is_file() else r.stdout
            if r.returncode != 0:
                if logf.is_file():
                    shutil.copy(logf, saved_log)
                else:
                    saved_log.write_text(r.stdout)
                errs = latex_errors(log) or [r.stdout[-2500:]]
                print(f"LaTeX FAILED (pass {run + 1}, exit {r.returncode}): {src}")
                for e in errs[:5]:
                    print("  " + e.replace("\n", "\n  "))
                print(f"full log: {saved_log}")
                sys.exit(1)
            # always two passes; a third only if LaTeX still asks for one
            if run >= 1 and "Rerun to get" not in log:
                break
        pdf = Path(tmp) / f"{job}.pdf"
        if not pdf.is_file():
            sys.exit(f"pdflatex succeeded but wrote no {pdf.name}; log:\n{log[-2000:]}")
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(pdf), out)
    saved_log.unlink(missing_ok=True)  # a stale failure log from an earlier run

    m = re.search(r"Output written on .*?\((\d+) pages?", log.replace("\n", ""))
    pages = int(m.group(1)) if m else None
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} kB, {pages} pages)")
    if pages and pages > 4:
        print(f"WARNING: {pages} pages; a summary is 2-4 pages including figures")
    for w in latex_warnings(log):
        print(f"warning: {w}")


def resolve(target):
    p = Path(target)
    if p.suffix in (".md", ".tex") and p.is_file():
        return p.resolve()
    for d in (p, STUDIES / target):
        for name in ("SUMMARY.tex", "SUMMARY.md"):
            if (d / name).is_file():
                if name == "SUMMARY.tex" and (d / "SUMMARY.md").is_file():
                    print(
                        f"note: {d / 'SUMMARY.md'} is superseded by SUMMARY.tex; "
                        "delete it once the tex builds"
                    )
                return (d / name).resolve()
    sys.exit(
        f"no SUMMARY.tex or SUMMARY.md found for '{target}' (tried {p}, {STUDIES / target})"
    )


# ---------------------------------------------------------------- SUMMARY.md -> chromium


def frontmatter(md):
    m = re.match(r"^---\n(.*?)\n---\n", md, re.S)
    if not m:
        return {}, md
    fm = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        v = re.sub(r"\s+#.*$", "", v).strip()
        if k.strip() and v:
            fm[k.strip()] = v
    return fm, md[m.end() :]


def reexec_in_container():
    if not shutil.which("singularity"):
        sys.exit(
            "chromium not found and singularity unavailable: run inside the container"
        )
    binds = ",".join(
        d
        for d in ("/home/", "/work/", "/ceph/", "/scratch/", "/tmp/")
        if os.path.isdir(d)
    )
    cmd = [
        "singularity",
        "exec",
        "--bind",
        binds,
        CONTAINER,
        "python3",
        str(Path(__file__).resolve()),
        *sys.argv[1:],
    ]
    sys.exit(subprocess.call(cmd))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "target",
        help="study slug, <slug>/<task>, a directory, or a SUMMARY.tex / SUMMARY.md",
    )
    ap.add_argument(
        "-o", "--output", help="output pdf (default: SUMMARY.pdf next to the source)"
    )
    ap.add_argument(
        "--keep-html", action="store_true", help="md only: also keep the print html"
    )
    args = ap.parse_args()

    src = resolve(args.target)
    if src.suffix == ".tex":
        out = Path(args.output).resolve() if args.output else src.with_suffix(".pdf")
        build_tex(src, out)
        return

    chromium = shutil.which("chromium") or shutil.which("chromium-browser")
    if not chromium:
        reexec_in_container()
    print(
        "note: Markdown summary (deprecated; new summaries are SUMMARY.tex, "
        "template studies/_TEMPLATE/SUMMARY.tex)"
    )

    fm, body = frontmatter(src.read_text())
    rel = src.parent.relative_to(STUDIES) if STUDIES in src.parents else None
    url = f"{WEB}#{rel}" if rel else ""
    bits = [f"<b>{html.escape(fm.get('title', src.parent.name))}</b>"]
    for key, label in (
        ("period", "period"),
        ("status", "status"),
        ("updated", "summary written"),
        ("covers", "logbook through"),
    ):
        if key in fm:
            bits.append(f"{label}: {html.escape(fm[key])}")
    if url:
        bits.append(f'<a href="{url}">{html.escape(url)}</a>')

    page = (
        PAGE.replace("__META__", " · ".join(bits))
        .replace("__WEB__", WEB)
        .replace("__MARKED__", MARKED.read_text())
        .replace("__SRC__", json.dumps(body).replace("</", "<\\/"))
    )
    out = Path(args.output).resolve() if args.output else src.with_suffix(".pdf")

    # the html must sit in the summary's directory so relative images resolve
    with tempfile.NamedTemporaryFile(
        "w", suffix=".html", prefix=".summary_print_", dir=src.parent, delete=False
    ) as fh:
        fh.write(page)
        page_path = Path(fh.name)
    try:
        with tempfile.TemporaryDirectory() as profile:
            cmd = [
                chromium,
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                f"--user-data-dir={profile}",
                "--no-pdf-header-footer",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=20000",
                f"--print-to-pdf={out}",
                page_path.as_uri(),
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if r.returncode != 0 or not out.is_file():
            sys.exit(f"chromium failed ({r.returncode}):\n{r.stderr[-2000:]}")
    finally:
        if args.keep_html:
            keep = out.with_suffix(".print.html")
            page_path.replace(keep)
            print(f"html: {keep}")
        else:
            page_path.unlink(missing_ok=True)
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} kB)")


if __name__ == "__main__":
    main()
