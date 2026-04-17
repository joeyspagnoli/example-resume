# LaTeX Resume Template

A version-controlled, YAML-driven LaTeX resume system with CLI tools for building, diffing, and comparing tailored versions across Git branches.

## Why LaTeX for Your Resume?

- **Version control**: Track every change with Git. See exactly what you changed between applications.
- **Company-tailored branches**: `git checkout -b tailor/google` — customize for each company, diff against your base.
- **ATS-optimized**: `\pdfgentounicode=1` ensures machine-readable text. No weird formatting artifacts from Word.
- **Pixel-perfect**: Consistent spacing, fonts, and layout every time. No "it looks different on their computer."
- **Automation**: YAML → LaTeX → PDF pipeline. Edit data, not formatting.

## Prerequisites

You need three things: LaTeX (to compile the resume), Python 3.9+ (for the CLI tools), and Git.

### LaTeX

<details>
<summary><b>macOS (Apple Silicon)</b></summary>

**Option A: MacTeX (Full install, ~5 GB)** — includes everything, you'll never hit a missing package.

```bash
brew install --cask mactex
```

After install, add to your PATH (add this line to `~/.zshrc`):

```bash
eval "$(/usr/libexec/path_helper)"
```

Restart your terminal, then verify:

```bash
latexmk --version
pdflatex --version
```

**Option B: BasicTeX (Minimal install, ~100 MB)** — lighter, but you need to add packages manually.

```bash
brew install --cask basictex
```

Add to PATH (same as above), restart terminal, then install required packages:

```bash
sudo tlmgr update --self
sudo tlmgr install latexmk \
  collection-fontsrecommended \
  newtx \
  titlesec \
  enumitem \
  fancyhdr \
  babel \
  hyperref \
  geometry \
  xcolor \
  glyphtounicode
```

</details>

<details>
<summary><b>Windows 11</b></summary>

**Option A: MiKTeX (Recommended)** — auto-installs missing packages on first use.

1. Download the installer from [miktex.org/download](https://miktex.org/download)
2. Run the installer — choose "Install for all users" if prompted
3. During setup, set "Install missing packages" to **Yes**
4. Open a new PowerShell window and verify: `pdflatex --version`

Install `latexmk` (requires Perl):

```powershell
winget install StrawberryPerl.StrawberryPerl
# Then open MiKTeX Console → Packages → search "latexmk" → Install
```

**Option B: TeX Live (Full install, ~5 GB)**

1. Download `install-tl-windows.exe` from [tug.org/texlive](https://tug.org/texlive/acquire-netinstall.html)
2. Run the installer (takes 30+ minutes)
3. Restart PowerShell and verify: `latexmk --version`

</details>

### Python

Python 3.9 or newer. Check with `python3 --version`.

- **macOS**: Comes with macOS or install via `brew install python`
- **Windows**: `winget install Python.Python.3.12` or download from [python.org](https://www.python.org/downloads/)

### Optional: onefetch

The `stats` command uses [onefetch](https://github.com/o2sh/onefetch) to show a visual repo summary card.

```bash
brew install onefetch    # macOS
winget install onefetch  # Windows
```

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/example-resume.git
cd example-resume

# Set up Python environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Compile the resume to PDF
latexmk -pdf -interaction=nonstopmode -halt-on-error resume.tex

# Or use the YAML pipeline (edit YAML, generate LaTeX, compile to PDF)
python scripts/yaml-to-latex.py resume.yaml -o resume.tex --pdf

# Clean up build artifacts (.aux, .log, etc.)
latexmk -c
```

## Project Structure

```
example-resume/
├── resume.tex              # LaTeX source (hand-edit or generate from YAML)
├── resume.yaml             # Structured resume data
├── requirements.txt        # Python dependencies (pyyaml, gitpython, rich)
├── scripts/
│   └── yaml-to-latex.py    # YAML → LaTeX → PDF converter
├── tools/
│   ├── resume-cli.py       # CLI for build, diff, compare, branches, stats
│   └── mkdiff.py           # Visual diff engine (used by resume-cli.py diff)
└── docx-to-latex-skill/
    └── docx-to-latex.md      # Instructions for converting a .docx resume to LaTeX + YAML
```

## Resume CLI

All commands are run from the repo root with the venv activated.

```bash
source .venv/bin/activate
```

### `build` — Compile and view your resume

Compiles `resume.tex` to PDF using `latexmk` and opens it in your default PDF viewer.

```bash
python tools/resume-cli.py build
```

### `diff` — Generate a visual before/after PDF

Creates a PDF where **removed content is red** and **added content is blue**. This is the visual "money shot" — you can see exactly how your resume evolved over time.

```bash
# Compare your first commit to your latest (full evolution)
python tools/resume-cli.py diff

# Compare main branch vs a company-tailored branch
python tools/resume-cli.py diff -b google
python tools/resume-cli.py diff -b cap1

# Compare two specific commits
python tools/resume-cli.py diff -c "abc1234..def5678"
```

The diff PDF is saved to your repo directory (e.g., `diff-evolution.pdf`, `diff-main-vs-google.pdf`) and auto-opens.

> **Note**: This uses a custom diff engine (`tools/mkdiff.py`) instead of `latexdiff` because `latexdiff` can't handle the custom resume LaTeX commands (`\resumeItem`, `\resumeSubheading`, etc.).

### `compare` — See what changed across all tailored branches

Shows a table of what bullets and skills you added or removed for each company compared to your base resume.

```bash
python tools/resume-cli.py compare
```

Example output:
```
                               Branch Comparison
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Branch        ┃  Bullets  ┃ Skills Added       ┃ Skills Removed      ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ Google        │ +15 / -15 │ AI Fundamentals,   │ AWS, Autoencoders,  │
│               │           │ Data Structures... │ CNNs...             │
│ Cap1          │ +15 / -15 │ AWS (S3), Agile,   │ AI Scholar (2025),  │
│               │           │ Big Data...        │ Autoencoders...     │
└───────────────┴───────────┴────────────────────┴─────────────────────┘
```

### `branches` — List all company-tailored branches

Shows every `tailor/*` branch with how many commits it's ahead of main, last updated date, and last commit message.

```bash
python tools/resume-cli.py branches
```

### `stats` — Show repo and resume metrics

Displays an [onefetch](https://github.com/o2sh/onefetch) repo card (if installed) plus resume metrics: bullet count, section count, skills count, and number of tailored versions.

```bash
python tools/resume-cli.py stats
```

### Pointing to a different repo

All commands default to auto-detecting a resume repo (current directory, `../resume`, or `~/Projects/resume`). To use a specific repo:

```bash
python tools/resume-cli.py --repo /path/to/your/resume/repo diff
```

## YAML → LaTeX Pipeline

Instead of editing LaTeX directly, you can edit `resume.yaml` and generate the `.tex` file:

```bash
# Generate LaTeX from YAML
python scripts/yaml-to-latex.py resume.yaml -o resume.tex

# Generate LaTeX and compile to PDF in one step
python scripts/yaml-to-latex.py resume.yaml -o resume.tex --pdf
```

The YAML schema supports:
- **`personal`**: Name, phone, email, links
- **`education`**: Entries with institution, degree, GPA, dates, bullets
- **`experience`**: Listings with title, organization, dates, bullets, `enabled` flag
- **`projects`**: Listings with title, tech stack, dates, bullets, `enabled` flag
- **`skills_achievements`**: Category/text pairs with `enabled` flag
- **`layout`**: Knobs for margins, spacing, font sizes (for page fitting)

Set `enabled: false` on any listing to hide it without deleting it — useful for swapping content between tailored versions.

## Tailoring for Companies

The killer feature of a Git-based resume:

```bash
# Create a branch for a specific company
git checkout -b tailor/google

# Edit resume.yaml — adjust bullets, reorder skills, toggle listings
# Set enabled: false on listings you want to hide for this company

# Compile and review
python scripts/yaml-to-latex.py resume.yaml -o resume.tex --pdf

# Commit the tailored version
git add . && git commit -m "Tailored resume for Google ML internship"

# Switch back to base resume anytime
git checkout main

# See what you changed
python tools/resume-cli.py diff -b google
python tools/resume-cli.py compare
```

## Importing a Word Resume

Use the docx-to-latex skill to have claude code or any coding agent easily convert your Word resume into LaTeX.

## Tips

- **One page**: The resume MUST fit on one page. Adjust `layout` knobs in the YAML if it overflows.
- **Bold strategically**: Bold technologies, metrics, and impact numbers for ATS scanners.
- **Date format**: Use `Mon. YYYY` consistently (e.g., `Aug. 2023`).
- **Escape LaTeX**: `%` → `\%`, `&` → `\&`, `#` → `\#` in YAML text fields.
- **Review diffs**: `git diff` before committing shows exactly what changed — great for catching typos.
