"""Generate a visual diff PDF between two resume versions.

Strategy: Split each section into individual entries (jobs, projects, skill lines),
diff at the entry level, and color entire entries as added/removed/changed.
"""
import difflib
import re
import sys
from pathlib import Path


def extract_sections(tex: str) -> dict[str, str]:
    """Extract raw text by section from a resume .tex file."""
    sections: dict[str, list[str]] = {}
    current = "PREAMBLE"
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
            for name in ("HEADING", "EDUCATION", "EXPERIENCE", "PROJECTS", "SKILLS AND ACHIEVEMENTS"):
                if name in stripped:
                    current = name
                    break
            continue
        sections.setdefault(current, []).append(line)

    return {k: "\n".join(v) for k, v in sections.items()}


def split_entries(section_text: str) -> list[str]:
    """Split a section into individual entries (job blocks, project blocks, etc.).

    Each entry starts with an \\item line that has \\textbf (a title line).
    Everything until the next such line belongs to the same entry.
    """
    lines = section_text.split("\n")
    entries: list[str] = []
    current: list[str] = []

    for line in lines:
        stripped = line.strip()
        # Detect entry boundaries: \item with \textbf (title lines) or \resumeSubheading
        is_title = (
            (stripped.startswith("\\item") and "\\textbf{" in stripped)
            or stripped.startswith("\\resumeSubheading{")
        )
        # Also: structural commands that wrap entries
        is_struct = stripped in (
            "\\resumeSubHeadingListStart", "\\resumeSubHeadingListEnd",
            "\\section{\\textbf{Education}}", "\\section{\\textbf{Experience}}",
            "\\section{\\textbf{Projects}}", "\\section{\\textbf{Skills and Achievements}}",
        ) or stripped.startswith("\\section{")

        if is_struct:
            # Flush current entry
            if current:
                entries.append("\n".join(current))
                current = []
            entries.append(line)
        elif is_title:
            # Start new entry
            if current:
                entries.append("\n".join(current))
            current = [line]
        else:
            current.append(line)

    if current:
        entries.append("\n".join(current))

    return entries


def color_entry(entry: str, color: str) -> str:
    """Color all content lines in an entry, leaving structural commands untouched."""
    lines = entry.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append(line)
            continue

        structural = (
            "\\resumeSubHeadingListStart", "\\resumeSubHeadingListEnd",
            "\\resumeItemListStart", "\\resumeItemListEnd",
            "\\section{",
        )
        if any(stripped.startswith(cmd) for cmd in structural):
            result.append(line)
            continue

        # For \resumeItem{content}, wrap content in \textcolor
        if stripped.startswith("\\resumeItem{") and stripped.endswith("}"):
            inner = stripped[len("\\resumeItem{"):-1]
            result.append(f"  \\resumeItem{{\\textcolor{{{color}}}{{{inner}}}}}")
            continue

        # For \item lines with complex brace patterns, use \color scoping
        if stripped.startswith("\\item"):
            result.append(f"{{\\color{{{color}}}{stripped}}}")
            continue

        # For org/company lines like \textbf{Company | Location}
        result.append(f"{{\\color{{{color}}}{stripped}}}")

    return "\n".join(result)


def diff_entries(old_entries: list[str], new_entries: list[str]) -> list[str]:
    """Diff two lists of entries and return colored output."""
    matcher = difflib.SequenceMatcher(None, old_entries, new_entries, autojunk=False)
    result: list[str] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            result.extend(new_entries[j1:j2])
        elif tag == "replace":
            # Show old entries in red, then new in blue
            for entry in old_entries[i1:i2]:
                result.append(color_entry(entry, "diffdel"))
            for entry in new_entries[j1:j2]:
                result.append(color_entry(entry, "diffadd"))
        elif tag == "delete":
            for entry in old_entries[i1:i2]:
                result.append(color_entry(entry, "diffdel"))
        elif tag == "insert":
            for entry in new_entries[j1:j2]:
                result.append(color_entry(entry, "diffadd"))

    return result


def make_diff_tex(old_tex: str, new_tex: str) -> str:
    old_sections = extract_sections(old_tex)
    new_sections = extract_sections(new_tex)

    # Use the new resume's preamble
    preamble_end = new_tex.find("\\begin{document}")
    preamble = new_tex[:preamble_end]

    # Replace color package with xcolor (superset, needed for \textcolor and \definecolor)
    preamble = preamble.replace(
        r"\usepackage[usenames,dvipsnames]{color}",
        r"\usepackage[usenames,dvipsnames]{xcolor}",
    )
    # Add diff color definitions
    preamble += r"""
\definecolor{diffdel}{RGB}{200,30,30}
\definecolor{diffadd}{RGB}{0,50,200}

"""

    body_parts = ["\\begin{document}", "\\vspace*{-0.45in}", ""]

    # Use heading from NEW version as-is (contact info doesn't need diffing)
    if "HEADING" in new_sections:
        body_parts.append("%-----------HEADING-----------")
        body_parts.append(new_sections["HEADING"])
        body_parts.append("")

    # Diff each content section
    for section_name in ("EDUCATION", "EXPERIENCE", "PROJECTS", "SKILLS AND ACHIEVEMENTS"):
        old_text = old_sections.get(section_name, "")
        new_text = new_sections.get(section_name, "")

        body_parts.append(f"%-----------{section_name}-----------")

        if not old_text and not new_text:
            continue

        old_entries = split_entries(old_text)
        new_entries = split_entries(new_text)

        diffed = diff_entries(old_entries, new_entries)
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
