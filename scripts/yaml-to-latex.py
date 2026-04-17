#!/usr/bin/env python3
"""Convert a resume YAML file to LaTeX using the project template.

Usage:
    python3 scripts/yaml-to-latex.py resume.yaml -o resume.tex
    python3 scripts/yaml-to-latex.py resume.yaml -o resume.tex --pdf
"""

import argparse
import subprocess
import sys
from pathlib import Path

import yaml


def load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fmt(value: float) -> str:
    """Format float compactly for LaTeX."""
    s = f"{value:.3f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


def render_personal(data: dict) -> list[str]:
    personal = data["personal"]
    segments = [personal["phone"]]
    segments.append(f"\\href{{mailto:{personal['email']}}}{{{personal['email']}}}")
    for link in personal.get("links", []):
        segments.append(f"\\href{{{link['url']}}}{{{link['label']}}}")
    contact = " \\textbar\\ ".join(segments)
    return [
        "%----------HEADING----------",
        "\\begin{center}",
        f"  {{\\fontsize{{15pt}}{{16pt}}\\selectfont\\bfseries {personal['name']}}}\\\\",
        "  \\vspace{2pt}",
        f"  {{\\normalsize {contact}}}",
        "\\end{center}",
        "",
    ]


def render_education(data: dict) -> list[str]:
    lines = [
        "%-----------EDUCATION-----------",
        "\\section{\\textbf{Education}}",
        "\\resumeSubHeadingListStart",
    ]
    for entry in data["education"]["entries"]:
        lines.append(
            f"  \\resumeSubheading{{{entry['institution']}}}{{{entry['date_range']}}}"
            f"{{{entry['degree']}}}{{{entry['detail']}}}"
        )
        for bullet in entry.get("bullets", []):
            lines.append(f"  \\item {bullet['text']}")
    lines.extend(["\\resumeSubHeadingListEnd", ""])
    return lines


def render_experience(data: dict) -> list[str]:
    lines = [
        "%-----------EXPERIENCE-----------",
        "\\section{\\textbf{Experience}}",
        "\\resumeSubHeadingListStart",
    ]
    for listing in data["experience"]["listings"]:
        if not listing.get("enabled", True):
            continue
        lines.append(
            f"  \\item {{\\textbf{{{listing['title']}}}}} \\hfill "
            f"{{\\textbf{{{listing['date_range']}}}}}\\\\"
        )
        lines.append(f"    \\textbf{{{listing['organization']}}}")
        lines.append("  \\resumeItemListStart")
        for bullet in listing.get("bullets", []):
            lines.append(f"    \\resumeItem{{{bullet['text']}}}")
        lines.append("  \\resumeItemListEnd")
    lines.extend(["\\resumeSubHeadingListEnd", ""])
    return lines


def render_projects(data: dict) -> list[str]:
    lines = [
        "%-----------PROJECTS-----------",
        "\\section{\\textbf{Projects}}",
        "\\resumeSubHeadingListStart",
    ]
    for listing in data["projects"]["listings"]:
        if not listing.get("enabled", True):
            continue
        title = listing["title"]
        if listing.get("tech_stack", "").strip():
            title = f"{title} $|$ {listing['tech_stack']}"
        lines.append(f"  \\item{{\\textbf{{{title}}}}}\\hfill\\textbf{{{listing['date_range']}}}")
        lines.append("  \\resumeItemListStart")
        for bullet in listing.get("bullets", []):
            lines.append(f"  \\resumeItem{{{bullet['text']}}}")
        lines.append("  \\resumeItemListEnd")
    lines.extend(["\\resumeSubHeadingListEnd", ""])
    return lines


def render_skills(data: dict) -> list[str]:
    lines = [
        "%-----------SKILLS AND ACHIEVEMENTS-----------",
        "\\section{\\textbf{Skills and Achievements}}",
        "\\resumeSubHeadingListStart",
    ]
    for listing in data["skills_achievements"]["listings"]:
        if not listing.get("enabled", True):
            continue
        lines.append(f"  \\item{{\\textbf{{{listing['category']}}}: {listing['text']}}}")
    lines.extend(["\\resumeSubHeadingListEnd", ""])
    return lines


def render_tex(data: dict) -> str:
    layout = data.get("layout", {})
    margin = fmt(layout.get("margin_in", 0.5))
    top_vspace = fmt(layout.get("top_vspace_in", -0.45))
    heading_size = fmt(layout.get("section_heading_font_size_pt", 13.0))
    heading_height = fmt(layout.get("section_heading_line_height_pt", 15.0))
    before = fmt(layout.get("section_spacing_before_pt", 1.0))
    after = fmt(layout.get("section_spacing_after_pt", 1.0))
    sub_sep = fmt(layout.get("subheading_itemsep_pt", 2.0))
    bullet_sep = fmt(layout.get("bullet_itemsep_pt", 1.0))

    lines = [
        "\\documentclass[letterpaper,10pt]{article}",
        f"\\usepackage[margin={margin}in]{{geometry}}",
        "\\usepackage{titlesec}",
        "\\usepackage[usenames,dvipsnames]{color}",
        "\\usepackage{enumitem}",
        "\\usepackage{fancyhdr}",
        "\\usepackage[english]{babel}",
        "\\input{glyphtounicode}",
        "% Use Times New Roman font",
        "\\usepackage{newtxtext,newtxmath}",
        "\\usepackage[hidelinks]{hyperref}",
        "",
        "% Page style and spacing",
        "\\pagestyle{fancy}",
        "\\fancyhf{}",
        "\\renewcommand{\\headrulewidth}{0pt}",
        "\\renewcommand{\\footrulewidth}{0pt}",
        "\\setlist{nosep,leftmargin=*}",
        "",
        "% Section formatting",
        f"\\titleformat{{\\section}}{{\\fontsize{{{heading_size}pt}}{{{heading_height}pt}}\\selectfont\\scshape}}{{}}{{0em}}{{}}[\\color{{black}}\\titlerule]",
        f"\\titlespacing*{{\\section}}{{0pt}}{{{before}pt}}{{{after}pt}}",
        "",
        "% Ensure machine-readable PDF",
        "\\pdfgentounicode=1",
        "",
        "% List commands",
        f"\\newcommand{{\\resumeSubHeadingListStart}}{{\\begin{{itemize}}[leftmargin=0pt,label={{}},itemsep={sub_sep}pt]}}",
        "\\newcommand{\\resumeSubHeadingListEnd}{\\end{itemize}}",
        f"\\newcommand{{\\resumeItemListStart}}{{\\begin{{itemize}}[label=\\textbullet,leftmargin=0.2in,itemsep={bullet_sep}pt]}}",
        "\\newcommand{\\resumeItemListEnd}{\\end{itemize}}",
        "\\newcommand{\\resumeSubheading}[4]{\\item {\\textbf{#1}}\\hfill{\\textbf{#2}}\\\\",
        "  {#3}\\hfill{\\textbf{#4}}}",
        "\\newcommand{\\resumeItem}[1]{\\item #1}",
        "",
        "% Document start",
        "\\begin{document}",
        f"\\vspace*{{{top_vspace}in}}",
        "",
    ]

    lines.extend(render_personal(data))
    lines.extend(render_education(data))
    lines.extend(render_experience(data))
    lines.extend(render_projects(data))
    lines.extend(render_skills(data))
    lines.extend(["\\end{document}", ""])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Convert resume YAML to LaTeX")
    parser.add_argument("yaml_file", type=Path, help="Input YAML file")
    parser.add_argument("-o", "--output", type=Path, default=Path("resume.tex"), help="Output .tex file")
    parser.add_argument("--pdf", action="store_true", help="Also compile to PDF via latexmk")
    args = parser.parse_args()

    data = load_yaml(args.yaml_file)
    tex = render_tex(data)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(tex, encoding="utf-8")
    print(f"Wrote {args.output}")

    if args.pdf:
        print("Compiling to PDF...")
        result = subprocess.run(
            ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", args.output.name],
            cwd=args.output.parent,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("LaTeX compilation failed:", file=sys.stderr)
            print(result.stdout, file=sys.stderr)
            sys.exit(1)
        pdf_path = args.output.with_suffix(".pdf")
        print(f"Compiled {pdf_path}")


if __name__ == "__main__":
    main()
