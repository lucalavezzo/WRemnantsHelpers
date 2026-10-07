#!/usr/bin/env python3
"""Render a study (or task) SUMMARY.md to SUMMARY.pdf, next to it.

    scripts/summary_pdf.py <slug>                 # studies/<slug>/SUMMARY.md
    scripts/summary_pdf.py <slug>/<YYMMDD-task>   # a task summary
    scripts/summary_pdf.py path/to/SUMMARY.md [-o out.pdf]

The markdown is rendered by the same marked.js + KaTeX the web viewer uses, then printed
by headless chromium, so the PDF matches the web page. Relative image paths resolve
against the summary's own directory, as on the web. chromium is only in the WRemnants
container; run from outside it and the script re-executes itself inside singularity.

The PDF is gitignored (studies/**/*.pdf): SUMMARY.md is the source, this is one rerun away.
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


def resolve(target):
    p = Path(target)
    if p.suffix == ".md" and p.is_file():
        return p.resolve()
    for cand in (p / "SUMMARY.md", STUDIES / target / "SUMMARY.md"):
        if cand.is_file():
            return cand.resolve()
    sys.exit(f"no SUMMARY.md found for '{target}' (tried {p}, {STUDIES / target})")


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
        "target", help="study slug, <slug>/<task>, a directory, or a SUMMARY.md"
    )
    ap.add_argument(
        "-o", "--output", help="output pdf (default: SUMMARY.pdf next to the md)"
    )
    ap.add_argument("--keep-html", action="store_true", help="also keep the print html")
    args = ap.parse_args()

    src = resolve(args.target)
    chromium = shutil.which("chromium") or shutil.which("chromium-browser")
    if not chromium:
        reexec_in_container()

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
