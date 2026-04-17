---
name: docx-to-latex
description: Convert a .docx resume into a structured LaTeX file and YAML data file using this project's resume template format.
---

# DOCX to LaTeX Resume Converter

Convert a Word document (.docx) resume into a clean LaTeX resume and structured YAML data file using this project's template.

## Trigger

When the user asks to convert a `.docx` file to LaTeX, or says something like "convert my resume", "import my Word resume", or "turn this docx into latex".

## Steps

### 1. Extract text from the DOCX

Use `python3` to extract text from the docx file. If `python-docx` is not installed, install it first:

```bash
pip3 install python-docx
```

Then extract:

```python
from docx import Document
doc = Document("path/to/resume.docx")
for para in doc.paragraphs:
    print(para.text)
```

Also check for tables (some resumes use tables for layout):

```python
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            print(cell.text)
```

### 2. Parse the extracted content

Identify these sections from the extracted text:
- **Personal info**: Name, phone, email, LinkedIn, GitHub
- **Education**: Institution, degree, GPA, dates, certificates
- **Experience**: Job title, company, location, dates, bullet points
- **Projects**: Project name, tech stack, dates, bullet points
- **Skills**: Category and items
- **Awards/Achievements**: Listed honors

### 3. Generate the YAML file

Create a `resume.yaml` following this exact schema:

```yaml
schema_version: 1
lock_rules:
  section_order: [education, experience, projects, skills_achievements]
  section_headings:
    education: Education
    experience: Experience
    projects: Projects
    skills_achievements: Skills and Achievements
  non_editable_sections: [personal, education]
layout:
  margin_in: 0.5
  top_vspace_in: -0.45
  section_heading_font_size_pt: 13.0
  section_heading_line_height_pt: 15.0
  section_spacing_before_pt: 1.0
  section_spacing_after_pt: 1.0
  subheading_itemsep_pt: 2.0
  bullet_itemsep_pt: 1.0
personal:
  section_id: personal
  name: "Full Name"
  phone: "555-123-4567"
  email: "email@example.com"
  links:
    - id: linkedin
      label: linkedin.com/in/username
      url: https://www.linkedin.com/in/username/
    - id: github
      label: github.com/username
      url: https://github.com/username
education:
  section_id: education
  heading: Education
  entries:
    - id: school_name
      institution: "University Name $|$ City"
      date_range: "Aug. 2020 -- May 2024"
      degree: "Bachelor of Science in Computer Science"
      detail: "GPA: 3.8"
      bullets: []
experience:
  section_id: experience
  heading: Experience
  listings:
    - id: job_identifier
      enabled: true
      title: "Job Title"
      date_range: "Jun. 2023 -- Present"
      organization: "Company Name $|$ City, ST"
      bullets:
        - id: bullet_id
          text: "Description with \\textbf{bold keywords} for ATS optimization."
projects:
  section_id: projects
  heading: Projects
  listings:
    - id: project_identifier
      enabled: true
      title: "Project Name"
      tech_stack: "Python, React, Docker"
      date_range: "Jan. 2024 -- Mar. 2024"
      bullets:
        - id: bullet_id
          text: "Description of what you built and the impact."
skills_achievements:
  section_id: skills_achievements
  heading: Skills and Achievements
  listings:
    - id: category_id
      enabled: true
      category: "Languages"
      text: "Python, JavaScript, C++"
```

#### ID conventions
- All IDs must be lowercase `a-z0-9_` only
- Use descriptive, unique IDs (e.g., `nasa_jsc`, `evochess`, `ml_ai`)
- Bullet IDs should be prefixed with their parent listing ID (e.g., `nasa_autoencoder`)

### 4. Generate the LaTeX file

Create `resume.tex` using this template structure. The preamble must match exactly:

```latex
\documentclass[letterpaper,10pt]{article}
\usepackage[margin=0.5in]{geometry}
\usepackage{titlesec}
\usepackage[usenames,dvipsnames]{color}
\usepackage{enumitem}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\input{glyphtounicode}
\usepackage{newtxtext,newtxmath}
\usepackage[hidelinks]{hyperref}

\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\setlist{nosep,leftmargin=*}

\titleformat{\section}{\fontsize{13pt}{15pt}\selectfont\scshape}{}{0em}{}[\color{black}\titlerule]
\titlespacing*{\section}{0pt}{1pt}{1pt}

\pdfgentounicode=1

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0pt,label={},itemsep=2pt]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}[label=\textbullet,leftmargin=0.2in,itemsep=1pt]}
\newcommand{\resumeItemListEnd}{\end{itemize}}
\newcommand{\resumeSubheading}[4]{\item {\textbf{#1}}\hfill{\textbf{#2}}\\
  {#3}\hfill{\textbf{#4}}}
\newcommand{\resumeItem}[1]{\item #1}
```

#### LaTeX formatting rules
- **Bold keywords** that are ATS-relevant: technologies, metrics, methodologies
- Use `\textbf{...}` for bold text
- Use `\href{url}{display text}` for links
- Use `\textbar\` for pipe separators
- Use `$|$` for inline pipe separators in headings (renders as math pipe)
- Use `--` for en-dashes in date ranges
- Escape special LaTeX characters: `%` -> `\%`, `&` -> `\&`, `#` -> `\#`, `$` -> `\$`
- Keep each bullet point as a single line (no line breaks within a bullet)

### 5. Compile to PDF

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error resume.tex
```

If compilation succeeds, inform the user. If it fails, read the `.log` file to diagnose and fix LaTeX errors.

### 6. Clean up auxiliary files

```bash
latexmk -c
```

This removes `.aux`, `.fls`, `.fdb_latexmk`, `.log`, `.out` files while keeping the `.tex` and `.pdf`.

## Important notes

- The resume MUST fit on exactly **one page**. If it overflows, reduce content or adjust `layout` knobs in the YAML.
- Always bold key metrics (percentages, counts, dollar amounts) and technology names.
- Date format should be consistent: `Mon. YYYY` (e.g., `Aug. 2023`).
- If the DOCX has content that doesn't map to these sections, ask the user where to place it.
- After generating, offer to compile to PDF and show the result.
