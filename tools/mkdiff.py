"""Generate a visual diff PDF between two resume versions.

Strategy: Use the NEW resume's structure as the skeleton, and show
deleted content (from OLD) in red at the positions where it was removed.
New content is shown in blue.
"""
import difflib
import sys
from pathlib import Path


def extract_sections(tex: str) -> dict[str, list[str]]:
    """Extract content by section from a resume .tex file."""
    sections: dict[str, list[str]] = {}
    current = "preamble"
    in_doc = False

    for line in tex.split("\n"):
        stripped = line.strip()
        if "\\begin{document}" in stripped:
            in_doc = True
            continue
        if "\\end{document}" in stripped:
            break
        if not in_doc:
            continue
        if stripped.startswith("%-"):
            # Section marker like %-----------EXPERIENCE-----------
            for name in ("HEADING", "EDUCATION", "EXPERIENCE", "PROJECTS", "SKILLS AND ACHIEVEMENTS"):
                if name in stripped:
                    current = name
                    break
            continue
        sections.setdefault(current, []).append(line)

    return sections


def color_wrap(line: str, color: str) -> str:
    """Wrap a content line in a color, handling resume LaTeX commands."""
    stripped = line.strip()
    if not stripped:
        return line

    # Don't color structural/list commands at all
    structural = (
        "\\resumeSubHeadingListStart", "\\resumeSubHeadingListEnd",
        "\\resumeItemListStart", "\\resumeItemListEnd",
        "\\section{", "\\begin{", "\\end{",
    )
    if any(stripped.startswith(cmd) for cmd in structural):
        return line

    # For \resumeItem{...}, color the inner content only
    if stripped.startswith("\\resumeItem{") and stripped.endswith("}"):
        inner = stripped[len("\\resumeItem{"):-1]
        return "\\resumeItem{{\\color{" + color + "}" + inner + "}}"

    # For \item lines and everything else, prepend a color switch.
    # We use \color{} at the start of the line (no grouping) so it doesn't
    # interfere with brace matching in the original content.
    # The color resets at the next \item or structural command.
    return "\\color{" + color + "}" + stripped + "\\color{black}"


def diff_section_lines(old_lines: list[str], new_lines: list[str]) -> list[str]:
    """Diff two sections and return annotated lines.

    Groups consecutive deletions and insertions so all red (deleted)
    lines appear together, followed by all blue (added) lines.
    """
    result = []
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    opcodes = matcher.get_opcodes()

    # Merge consecutive replace/delete/insert into grouped blocks
    i = 0
    while i < len(opcodes):
        tag, i1, i2, j1, j2 = opcodes[i]

        if tag == "equal":
            result.extend(new_lines[j1:j2])
            i += 1
        else:
            # Collect all consecutive non-equal ops
            del_lines = []
            add_lines = []
            while i < len(opcodes) and opcodes[i][0] != "equal":
                t, a1, a2, b1, b2 = opcodes[i]
                if t in ("replace", "delete"):
                    del_lines.extend(old_lines[a1:a2])
                if t in ("replace", "insert"):
                    add_lines.extend(new_lines[b1:b2])
                i += 1
            # Emit all deletions first (red), then all additions (blue)
            for line in del_lines:
                result.append(color_wrap(line, "diffdel"))
            for line in add_lines:
                result.append(color_wrap(line, "blue"))

    return result


def make_diff_tex(old_tex: str, new_tex: str) -> str:
    old_sections = extract_sections(old_tex)
    new_sections = extract_sections(new_tex)

    # Use the new resume's preamble
    preamble_end = new_tex.find("\\begin{document}")
    preamble = new_tex[:preamble_end]

    # Add diff colors to preamble
    preamble += """
\\usepackage{xcolor}
\\definecolor{diffdel}{RGB}{200,30,30}
\\definecolor{blue}{RGB}{0,40,200}

"""

    body_parts = ["\\begin{document}", "\\vspace*{-0.45in}", ""]

    # Process each section in the order they appear in the new resume
    all_section_names = list(new_sections.keys())
    # Add any sections only in old
    for name in old_sections:
        if name not in all_section_names:
            all_section_names.append(name)

    for section_name in all_section_names:
        old_lines = old_sections.get(section_name, [])
        new_lines = new_sections.get(section_name, [])

        if section_name != "preamble":
            # Re-emit the section comment marker
            body_parts.append(f"%-----------{section_name}-----------")

        diffed = diff_section_lines(old_lines, new_lines)
        body_parts.extend(diffed)
        body_parts.append("")

    body_parts.append("\\end{document}")

    return preamble + "\n".join(body_parts) + "\n"


if __name__ == "__main__":
    old_path = Path(sys.argv[1])
    new_path = Path(sys.argv[2])
    out_path = Path(sys.argv[3])

    diff_tex = make_diff_tex(
        old_path.read_text(encoding="utf-8"),
        new_path.read_text(encoding="utf-8"),
    )
    out_path.write_text(diff_tex, encoding="utf-8")
    print(f"Wrote {out_path}")
