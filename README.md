# LaTeX Resume Template

A version-controlled, YAML-driven LaTeX resume system. Edit structured YAML, render to LaTeX, compile to PDF — all tracked in Git.

## Why LaTeX for Your Resume?

- **Version control**: Track every change with Git. See exactly what you changed between applications.
- **Company-tailored branches**: `git checkout -b tailor/google` — customize for each company, diff against your base.
- **ATS-optimized**: `\pdfgentounicode=1` ensures machine-readable text. No weird formatting artifacts from Word.
- **Pixel-perfect**: Consistent spacing, fonts, and layout every time. No "it looks different on their computer."
- **Automation**: YAML → LaTeX → PDF pipeline. Edit data, not formatting.

## Quick Start

### 1. Install LaTeX

<details>
<summary><b>macOS (Apple Silicon)</b></summary>

#### Option A: MacTeX (Full install, ~5 GB)

The full TeX Live distribution. Includes everything — you'll never hit a missing package.

```bash
brew install --cask mactex
```

After install, add to your PATH:

```bash
# Add to ~/.zshrc
eval "$(/usr/libexec/path_helper)"
```

Restart your terminal, then verify:

```bash
latexmk --version
pdflatex --version
```

#### Option B: BasicTeX (Minimal install, ~100 MB)

Lighter install, but you'll need to add packages manually.

```bash
brew install --cask basictex
```

Add to PATH:

```bash
# Add to ~/.zshrc
eval "$(/usr/libexec/path_helper)"
```

Restart your terminal, then install required packages:

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

Verify:

```bash
latexmk --version
```

</details>

<details>
<summary><b>Windows 11</b></summary>

#### Option A: MiKTeX (Recommended for Windows)

MiKTeX auto-installs missing packages on first use.

1. Download the installer from [miktex.org/download](https://miktex.org/download)
2. Run the installer — choose "Install for all users" if prompted
3. During setup, set "Install missing packages" to **Yes**
4. Open a **new** PowerShell window and verify:

```powershell
pdflatex --version
```

Install `latexmk` (Perl is required):

```powershell
# Install Strawberry Perl if you don't have it
winget install StrawberryPerl.StrawberryPerl

# Then install latexmk via MiKTeX console, or:
miktex-console --admin
# Go to Packages → search "latexmk" → Install
```

#### Option B: TeX Live (Full install)

1. Download `install-tl-windows.exe` from [tug.org/texlive/acquire-netinstall.html](https://tug.org/texlive/acquire-netinstall.html)
2. Run the installer (full install takes ~5 GB and 30+ minutes)
3. Restart PowerShell and verify:

```powershell
latexmk --version
pdflatex --version
```

</details>

### 2. Clone and Compile

```bash
git clone https://github.com/YOUR_USERNAME/example-resume.git
cd example-resume

# Compile the LaTeX resume to PDF
latexmk -pdf -interaction=nonstopmode -halt-on-error resume.tex

# Or use the YAML pipeline
pip install pyyaml
python3 scripts/yaml-to-latex.py resume.yaml -o resume.tex --pdf
```

### 3. Clean Up Build Artifacts

```bash
latexmk -c  # Removes .aux, .log, .fls, etc. Keeps .tex and .pdf
```

## Project Structure

```
example-resume/
├── resume.tex              # LaTeX source (generated or hand-edited)
├── resume.yaml             # Structured resume data (edit this!)
├── requirements.txt        # Python dependencies
├── scripts/
│   └── yaml-to-latex.py    # YAML → LaTeX converter
├── tools/
│   └── resume-cli.py       # CLI: build, diff, compare, stats, story
└── .claude/
    └── skills/
        └── docx-to-latex.md  # Claude Code skill: convert DOCX → LaTeX
```

## The Workflow

```
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  .docx   │────→│  Claude   │────→│  .yaml   │────→│  .tex    │────→  .pdf
│ (import) │     │ (convert) │     │  (edit)  │     │ (render) │
└─────────┘     └──────────┘     └──────────┘     └──────────┘
```

1. **Import**: Have a Word resume? Use the Claude Code `/docx-to-latex` skill to convert it
2. **Edit**: Modify `resume.yaml` — structured data, not LaTeX syntax
3. **Render**: `python3 scripts/yaml-to-latex.py resume.yaml -o resume.tex`
4. **Compile**: `latexmk -pdf resume.tex`
5. **Commit**: `git add . && git commit -m "Updated experience section"`

## Tailoring for Companies

The killer feature of a Git-based resume:

```bash
# Create a branch for a specific company
git checkout -b tailor/google

# Edit resume.yaml — adjust bullets, reorder skills, toggle listings
# In the YAML, set enabled: false on listings you want to hide

# Compile and review
python3 scripts/yaml-to-latex.py resume.yaml -o resume.tex --pdf

# Commit the tailored version
git add . && git commit -m "Tailored resume for Google ML internship"

# Switch back to base resume anytime
git checkout main
```

## Using with Claude Code

This repo includes a Claude Code skill for converting Word documents to LaTeX:

```bash
# In Claude Code, just say:
# "convert my-resume.docx to latex"
# or use the skill directly:
# /docx-to-latex
```

The skill will:
1. Extract text from your `.docx`
2. Parse sections (education, experience, projects, skills)
3. Generate both `resume.yaml` and `resume.tex`
4. Bold key metrics and technologies for ATS
5. Compile to PDF

## Resume CLI

A command-line tool for managing your resume repo:

```bash
# Install dependencies
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Commands
python tools/resume-cli.py build              # Compile to PDF and open it
python tools/resume-cli.py branches           # List all tailored branches
python tools/resume-cli.py compare            # Compare resume across branches
python tools/resume-cli.py diff               # Visual diff: first commit → latest (generates PDF)
python tools/resume-cli.py diff -b google     # Visual diff: main vs Google branch
python tools/resume-cli.py stats              # Repo stats (uses onefetch)
```

The `diff` command generates a PDF where additions are **blue** and deletions are **red** — a visual before-and-after of how your resume evolved. Works with custom LaTeX resume commands that break `latexdiff`.

The `compare` command shows a table of what skills and bullets changed in each company-tailored branch.

## Tips

- **One page**: The resume MUST fit on one page. Adjust `layout` knobs in the YAML if needed.
- **Bold strategically**: Bold technologies, metrics, and impact numbers for ATS scanners.
- **Date format**: Use `Mon. YYYY` consistently (e.g., `Aug. 2023`).
- **Escape LaTeX**: `%` → `\%`, `&` → `\&`, `#` → `\#` in your YAML text fields.
- **Review diffs**: `git diff` before committing shows exactly what changed — great for catching typos.
