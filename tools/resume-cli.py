#!/usr/bin/env python3
"""resume-cli: A CLI for managing a Git-versioned LaTeX resume.

Commands:
    build       Compile resume.tex to PDF and open it
    diff        Show visual diff between two resume versions (generates a PDF)
    compare     Compare your resume across company-tailored branches
    stats       Show repo stats (onefetch)
    branches    List all tailored branches and what changed
"""

import argparse
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import git
except ImportError:
    print("Install gitpython: pip install gitpython")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("Install rich: pip install rich")
    sys.exit(1)

console = Console()


def open_file(path: Path) -> None:
    system = platform.system()
    if system == "Darwin":
        subprocess.Popen(["open", str(path)])
    elif system == "Windows":
        subprocess.Popen(["start", str(path)], shell=True)
    else:
        subprocess.Popen(["xdg-open", str(path)])


def find_repo(args_repo: str | None) -> Path:
    if args_repo:
        return Path(args_repo).resolve()
    for candidate in [Path.cwd(), Path.cwd().parent / "resume", Path.home() / "Projects" / "resume"]:
        if (candidate / ".git").exists() and (candidate / "resume.tex").exists():
            return candidate
    console.print("[red]Could not find resume repo. Use --repo to specify.[/]")
    sys.exit(1)


# ─── Commands ───


def cmd_build(repo_path: Path, _args) -> None:
    """Compile resume.tex → PDF and open it."""
    console.print("[cyan]Building resume.pdf...[/]")
    result = subprocess.run(
        ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "resume.tex"],
        cwd=repo_path, capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        console.print("[red]Build failed![/]")
        # Show relevant error lines
        for line in result.stdout.split("\n"):
            if line.startswith("!") or "Error" in line:
                console.print(f"  [red]{line}[/]")
        sys.exit(1)

    pdf = repo_path / "resume.pdf"
    size = f"{pdf.stat().st_size / 1024:.0f} KB" if pdf.exists() else "?"
    console.print(f"[green]Built successfully![/] {pdf} ({size})")
    open_file(pdf)


def cmd_diff(repo_path: Path, args) -> None:
    """Generate a visual latexdiff PDF between two commits."""
    repo = git.Repo(repo_path)

    # Determine the two commits to compare
    if args.branch:
        # Compare main vs a tailor branch
        ref_a = "main"
        ref_b = f"origin/tailor/{args.branch}" if not args.branch.startswith("tailor/") else f"origin/{args.branch}"
        label = f"main vs {args.branch}"
    elif args.commits:
        ref_a, ref_b = args.commits.split("..")
        label = f"{ref_a} vs {ref_b}"
    else:
        # Default: first substantive commit vs latest
        tex_commits = list(repo.iter_commits("main", paths=["resume.tex"]))
        if len(tex_commits) < 2:
            console.print("[red]Need at least 2 commits that touch resume.tex[/]")
            return
        ref_a = tex_commits[-1].hexsha  # Oldest
        ref_b = tex_commits[0].hexsha   # Newest
        label = f"first → latest ({len(tex_commits)} versions apart)"

    console.print(f"[cyan]Generating visual diff: {label}[/]")

    # Extract the two versions
    try:
        old_tex = repo.git.show(f"{ref_a}:resume.tex")
        new_tex = repo.git.show(f"{ref_b}:resume.tex")
    except Exception:
        if args.branch:
            console.print(f"[red]Branch 'tailor/{args.branch}' not found.[/]")
            console.print("[dim]List available branches with: resume-cli.py branches[/]")
        else:
            console.print(f"[red]Could not extract resume versions from those commits.[/]")
        return

    # Generate diff using custom differ (handles resume LaTeX commands properly)
    # Import the custom diff generator (sibling module)
    sys.path.insert(0, str(Path(__file__).parent))
    from mkdiff import make_diff_tex

    tmp = Path("/tmp/resume-diff")
    tmp.mkdir(exist_ok=True)

    diff_tex_content = make_diff_tex(old_tex, new_tex)
    diff_tex_path = tmp / "diff.tex"
    diff_tex_path.write_text(diff_tex_content)

    # Compile
    console.print("[dim]Compiling diff PDF...[/]")
    compile_result = subprocess.run(
        ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "diff.tex"],
        cwd=tmp, capture_output=True, text=True, timeout=60,
    )
    if compile_result.returncode != 0:
        console.print("[red]Failed to compile diff PDF[/]")
        # Show errors
        for line in compile_result.stdout.split("\n"):
            if line.startswith("!"):
                console.print(f"  [red]{line}[/]")
        return

    diff_pdf = tmp / "diff.pdf"
    if args.branch:
        output_name = f"diff-main-vs-{args.branch.replace('/', '-')}.pdf"
    else:
        output_name = "diff-evolution.pdf"
    output = repo_path / output_name
    shutil.copy2(diff_pdf, output)

    console.print(f"[green]Diff PDF generated![/] {output}")
    console.print("[dim]Red = removed, Blue = added[/]")
    open_file(output)


def cmd_compare(repo_path: Path, _args) -> None:
    """Compare resume across all tailored branches."""
    repo = git.Repo(repo_path)

    # Get main resume content
    main_tex = repo.git.show("main:resume.tex")

    # Find tailor branches
    tailor_refs = []
    seen = set()
    for ref in repo.references:
        name = str(ref)
        if "tailor/" not in name:
            continue
        canonical = name.replace("origin/", "")
        if canonical in seen:
            continue
        seen.add(canonical)
        tailor_refs.append((canonical, str(ref)))

    if not tailor_refs:
        console.print("[yellow]No tailor branches found.[/]")
        console.print("[dim]Create one with: git checkout -b tailor/company-name[/]")
        return

    console.print(f"\n[bold cyan]Resume Tailoring Comparison[/] — {len(tailor_refs)} branches\n")

    def extract_bullets(tex: str) -> list[str]:
        return [b.strip() for b in re.findall(r"\\resumeItem\{(.+?)\}", tex, re.DOTALL)]

    def extract_skills(tex: str) -> set[str]:
        skills = set()
        match = re.search(r"SKILLS AND ACHIEVEMENTS.*?\\resumeSubHeadingListEnd", tex, re.DOTALL)
        if match:
            for items in re.findall(r"\\item\{\\textbf\{[^}]+\}:\s*([^}]+)\}", match.group()):
                skills.update(s.strip() for s in items.split(",") if s.strip())
        return skills

    main_bullets = extract_bullets(main_tex)
    main_skills = extract_skills(main_tex)

    table = Table(title="Branch Comparison", show_lines=True)
    table.add_column("Branch", style="cyan", width=20)
    table.add_column("Bullets Changed", justify="center", width=16)
    table.add_column("Skills Added", style="green", width=30)
    table.add_column("Skills Removed", style="red", width=30)

    for canonical, ref_name in sorted(tailor_refs):
        company = canonical.split("tailor/")[-1].replace("_", " ").title()
        try:
            branch_tex = repo.git.show(f"{ref_name}:resume.tex")
        except Exception:
            continue

        branch_bullets = extract_bullets(branch_tex)
        branch_skills = extract_skills(branch_tex)

        # Count changed bullets
        changed = sum(1 for b in branch_bullets if b not in main_bullets)
        removed = sum(1 for b in main_bullets if b not in branch_bullets)
        bullet_str = f"+{changed} / -{removed}" if (changed or removed) else "same"

        added_skills = branch_skills - main_skills
        removed_skills = main_skills - branch_skills

        table.add_row(
            company,
            bullet_str,
            ", ".join(sorted(added_skills)[:5]) or "—",
            ", ".join(sorted(removed_skills)[:5]) or "—",
        )

    console.print(table)


def cmd_stats(repo_path: Path, _args) -> None:
    """Show repo stats using onefetch."""
    if shutil.which("onefetch"):
        subprocess.run(["onefetch"], cwd=repo_path)
    else:
        console.print("[yellow]Install onefetch: brew install onefetch[/]")

    # Also show our own stats
    tex = (repo_path / "resume.tex").read_text(encoding="utf-8", errors="ignore")
    bullets = tex.count("\\resumeItem{")
    sections = len(re.findall(r"\\section\{", tex))

    repo = git.Repo(repo_path)
    tailor_count = len([r for r in repo.references if "tailor/" in str(r)]) // 2  # dedup origin/

    console.print(f"\n[bold cyan]Resume Metrics[/]")
    console.print(f"  Bullet points: [bold]{bullets}[/]")
    console.print(f"  Sections: [bold]{sections}[/]")
    console.print(f"  Tailored versions: [bold]{tailor_count}[/]")


def cmd_branches(repo_path: Path, _args) -> None:
    """List all tailored branches."""
    repo = git.Repo(repo_path)

    table = Table(title="Tailored Resume Branches")
    table.add_column("Company", style="cyan bold")
    table.add_column("Branch", style="dim")
    table.add_column("Ahead", justify="center")
    table.add_column("Last Updated")
    table.add_column("Last Commit", style="dim")

    seen = set()
    for ref in sorted(repo.references, key=lambda r: str(r)):
        name = str(ref)
        if "tailor/" not in name:
            continue
        canonical = name.replace("origin/", "")
        if canonical in seen:
            continue
        seen.add(canonical)

        company = canonical.split("tailor/")[-1].replace("_", " ").title()
        try:
            commit = ref.commit
            ahead = len(list(repo.iter_commits(f"main..{ref}")))
            date = datetime.fromtimestamp(commit.committed_date).strftime("%Y-%m-%d")
            msg = commit.message.strip()[:50]
            table.add_row(company, canonical, str(ahead), date, msg)
        except Exception:
            continue

    console.print(table)


def main():
    parser = argparse.ArgumentParser(
        description="CLI for managing a Git-versioned LaTeX resume",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--repo", type=str, default=None, help="Path to resume repo")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("build", help="Compile to PDF and open")
    sub.add_parser("stats", help="Show repo stats")
    sub.add_parser("branches", help="List tailored branches")
    sub.add_parser("compare", help="Compare resume across branches")

    diff_p = sub.add_parser("diff", help="Generate visual diff PDF")
    diff_p.add_argument("--branch", "-b", help="Compare main vs this tailor branch (e.g. google)")
    diff_p.add_argument("--commits", "-c", help="Compare two commits (e.g. abc1234..def5678)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    repo_path = find_repo(args.repo)

    commands = {
        "build": cmd_build,
        "diff": cmd_diff,
        "compare": cmd_compare,
        "stats": cmd_stats,
        "branches": cmd_branches,
    }
    commands[args.command](repo_path, args)


if __name__ == "__main__":
    main()
