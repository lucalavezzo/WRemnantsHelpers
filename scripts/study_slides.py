#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

LATEX_SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def tex_escape(text: str) -> str:
    return "".join(LATEX_SPECIALS.get(ch, ch) for ch in text)


def tex_escape_allow_math(text: str) -> str:
    # Escape regular text while preserving inline math fragments delimited by $...$.
    parts = re.split(r"(\$[^$]*\$)", text)
    out = []
    for part in parts:
        if part.startswith("$") and part.endswith("$") and len(part) >= 2:
            out.append(part)
        else:
            out.append(tex_escape(part))
    return "".join(out)


def path_for_graphics(path: str) -> str:
    return rf"\detokenize{{{path}}}"


def sanitize_filename(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "study_slides"


def render_bullets(slide: dict) -> str:
    title = tex_escape_allow_math(slide.get("title", ""))
    items = slide.get("items", [])
    lines = [rf"\begin{{frame}}{{{title}}}", r"\begin{itemize}"]
    for item in items:
        lines.append(rf"  \item {tex_escape_allow_math(str(item))}")
    lines.extend([r"\end{itemize}", r"\end{frame}"])
    return "\n".join(lines)


def render_figure(slide: dict) -> str:
    title = tex_escape_allow_math(slide.get("title", ""))
    path = slide.get("path", "")
    caption = slide.get("caption")
    selection_note = slide.get("selection_note")
    selection_note_latex = slide.get("selection_note_latex")
    conclusion_note = slide.get("conclusion_note")
    conclusion_note_latex = slide.get("conclusion_note_latex")
    width = slide.get("width", "0.9\\textwidth")
    height = slide.get("height")
    lines = [rf"\begin{{frame}}{{{title}}}"]
    if selection_note or selection_note_latex:
        note_text = (
            selection_note_latex if selection_note_latex else tex_escape(selection_note)
        )
        lines.extend(
            [
                r"\begin{itemize}",
                rf"  \item \small {note_text}",
                r"\end{itemize}",
            ]
        )
    lines.append(r"\begin{center}")
    if height:
        lines.append(
            rf"\includegraphics[width={width},height={height},keepaspectratio]{{{path_for_graphics(path)}}}"
        )
    else:
        lines.append(rf"\includegraphics[width={width}]{{{path_for_graphics(path)}}}")
    if caption:
        lines.append(rf"\\ {tex_escape(caption)}")
    lines.append(r"\end{center}")
    if conclusion_note or conclusion_note_latex:
        ctext = (
            conclusion_note_latex
            if conclusion_note_latex
            else tex_escape(conclusion_note)
        )
        lines.extend(
            [
                r"\begin{itemize}",
                rf"  \item \small {ctext}",
                r"\end{itemize}",
            ]
        )
    lines.append(r"\end{frame}")
    return "\n".join(lines)


def render_two_figures(slide: dict) -> str:
    title = tex_escape_allow_math(slide.get("title", ""))
    selection_note = slide.get("selection_note")
    selection_note_latex = slide.get("selection_note_latex")
    conclusion_note = slide.get("conclusion_note")
    conclusion_note_latex = slide.get("conclusion_note_latex")
    left = slide.get("left", {})
    right = slide.get("right", {})
    lw = left.get("width", "0.95\\linewidth")
    rw = right.get("width", "0.95\\linewidth")
    lines = [rf"\begin{{frame}}{{{title}}}"]
    if selection_note or selection_note_latex:
        note_text = (
            selection_note_latex if selection_note_latex else tex_escape(selection_note)
        )
        lines.extend(
            [
                r"\begin{itemize}",
                rf"  \item \small {note_text}",
                r"\end{itemize}",
            ]
        )
    lines.append(r"\begin{columns}[T,onlytextwidth]")
    lines.append(r"\column{0.5\textwidth}")
    lines.append(
        rf"\includegraphics[width={lw}]{{{path_for_graphics(left.get('path', ''))}}}"
    )
    if left.get("caption"):
        lines.append(rf"\\ {tex_escape(left['caption'])}")
    lines.append(r"\column{0.5\textwidth}")
    lines.append(
        rf"\includegraphics[width={rw}]{{{path_for_graphics(right.get('path', ''))}}}"
    )
    if right.get("caption"):
        lines.append(rf"\\ {tex_escape(right['caption'])}")
    lines.append(r"\end{columns}")
    if conclusion_note or conclusion_note_latex:
        ctext = (
            conclusion_note_latex
            if conclusion_note_latex
            else tex_escape(conclusion_note)
        )
        lines.extend(
            [
                r"\begin{itemize}",
                rf"  \item \small {ctext}",
                r"\end{itemize}",
            ]
        )
    lines.append(r"\end{frame}")
    return "\n".join(lines)


def render_text(slide: dict) -> str:
    title = tex_escape_allow_math(slide.get("title", ""))
    body = slide.get("body", "")
    lines = [rf"\begin{{frame}}{{{title}}}", tex_escape(body), r"\end{frame}"]
    return "\n".join(lines)


def render_slide(slide: dict) -> str:
    stype = slide.get("type")
    if stype == "bullets":
        return render_bullets(slide)
    if stype == "figure":
        return render_figure(slide)
    if stype == "two_figures":
        return render_two_figures(slide)
    if stype == "text":
        return render_text(slide)
    raise ValueError(f"Unsupported slide type: {stype}")


def render_tex(config: dict) -> str:
    title = tex_escape(config.get("title", "Study Summary"))
    subtitle = tex_escape(config.get("subtitle", ""))
    author = tex_escape(config.get("author", "Codex"))
    date = config.get("date", r"\today")
    theme = tex_escape(config.get("theme", "Madrid"))
    slides = config.get("slides", [])

    preamble = [
        r"\documentclass[10pt]{beamer}",
        rf"\usetheme{{{theme}}}",
        r"\usepackage{graphicx}",
        r"\usepackage{booktabs}",
        r"\title{" + title + r"}",
        r"\subtitle{" + subtitle + r"}",
        r"\author{" + author + r"}",
        r"\date{" + date + r"}",
        r"\begin{document}",
        r"\frame{\titlepage}",
    ]

    body = [render_slide(slide) for slide in slides]
    ending = [r"\end{document}"]
    return "\n\n".join(preamble + body + ending) + "\n"


def default_output_path(study_dir: Path, title: str) -> Path:
    slides_dir = study_dir / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)
    return slides_dir / f"{sanitize_filename(title)}.tex"


def compile_pdf(tex_path: Path) -> None:
    cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name]
    for _ in range(2):
        try:
            proc = subprocess.run(
                cmd,
                cwd=tex_path.parent,
                text=True,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "LaTeX compilation requested, but `pdflatex` is not available in PATH. "
                "Run in a TeX-enabled environment or omit --compile."
            ) from exc
        if proc.returncode != 0:
            raise RuntimeError(
                "LaTeX compilation failed.\n"
                f"stdout:\n{proc.stdout}\n\n"
                f"stderr:\n{proc.stderr}"
            )


def copy_pdf_to_plot_dir(pdf_path: Path, subdir: Optional[str] = None) -> Path:
    import os

    my_plot_dir = os.environ.get("MY_PLOT_DIR")
    if not my_plot_dir:
        raise RuntimeError("MY_PLOT_DIR is not set; cannot copy PDF to plot directory.")

    if subdir:
        target_dir = Path(my_plot_dir) / subdir
    else:
        target_dir = (
            Path(my_plot_dir) / f"{datetime.now().strftime('%y%m%d')}_study_slides"
        )
    target_dir.mkdir(parents=True, exist_ok=True)

    target_pdf = target_dir / pdf_path.name
    shutil.copy2(pdf_path, target_pdf)
    return target_pdf


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a study summary Beamer deck from JSON outline."
    )
    parser.add_argument(
        "--study-dir", required=True, help="Path to agents/studies/<topic>"
    )
    parser.add_argument(
        "--outline",
        default=None,
        help="Path to outline JSON file. Defaults to <study-dir>/slides/outline.json",
    )
    parser.add_argument("--output-tex", default=None, help="Output .tex file path")
    parser.add_argument(
        "--compile", action="store_true", help="Run pdflatex after generating .tex"
    )
    parser.add_argument(
        "--copy-pdf-to-plot-dir",
        action="store_true",
        help="After compile, copy PDF to $MY_PLOT_DIR/<YYMMDD>_study_slides by default.",
    )
    parser.add_argument(
        "--plot-subdir",
        default=None,
        help="Optional subdir under $MY_PLOT_DIR used with --copy-pdf-to-plot-dir.",
    )
    args = parser.parse_args()

    study_dir = Path(args.study_dir).resolve()
    outline = (
        Path(args.outline).resolve()
        if args.outline
        else study_dir / "slides" / "outline.json"
    )

    if not outline.exists():
        raise FileNotFoundError(f"Outline not found: {outline}")

    with open(outline, "r", encoding="utf-8") as f:
        config = json.load(f)

    output_tex = (
        Path(args.output_tex).resolve()
        if args.output_tex
        else default_output_path(study_dir, config.get("title", "study_slides"))
    )
    output_tex.parent.mkdir(parents=True, exist_ok=True)

    tex_content = render_tex(config)
    output_tex.write_text(tex_content, encoding="utf-8")
    print(f"Wrote {output_tex}")

    if args.compile:
        try:
            compile_pdf(output_tex)
        except RuntimeError as exc:
            raise SystemExit(str(exc))
        pdf_path = output_tex.with_suffix(".pdf")
        print(f"Wrote {pdf_path}")
        if args.copy_pdf_to_plot_dir:
            copied_to = copy_pdf_to_plot_dir(pdf_path, args.plot_subdir)
            print(f"Copied {copied_to}")


if __name__ == "__main__":
    main()
