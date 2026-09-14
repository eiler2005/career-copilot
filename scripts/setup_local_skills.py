"""Create local skill entrypoints outside the public source tree without global installation."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

MARKER = "<!-- Generated Career Copilot local adapter -->"


def install(app: Path, targets: list[Path]) -> int:
    app = app.resolve()
    source_root = app / ".agents/skills"
    skills = sorted(source_root.glob("*/SKILL.md"))
    if len(skills) != 8:
        raise ValueError("Expected the eight canonical Career Copilot skills")
    planned = []
    exclusions = {}
    for raw_target in targets:
        target = raw_target.expanduser().resolve()
        if (
            not target.is_dir()
            or target in {Path("/"), Path.home(), app}
            or target.is_relative_to(app)
        ):
            raise ValueError("Choose an existing local workspace outside the public application")
        for source in skills:
            canonical = source.read_text(encoding="utf-8")
            if not canonical.startswith("---\n"):
                raise ValueError("Canonical skill has no frontmatter")
            _, header, _ = canonical.split("---\n", 2)
            name = source.parent.name
            for runtime in (".agents", ".claude"):
                destination = target / runtime / "skills" / name / "SKILL.md"
                if destination.is_symlink() or any(
                    parent.is_symlink() for parent in destination.parents if parent != target.parent
                ):
                    raise ValueError("Refusing a symlinked adapter destination")
                if destination.exists() and MARKER not in destination.read_text(encoding="utf-8"):
                    raise ValueError("An unrelated local skill already uses this name")
                reference = Path(os.path.relpath(source, destination.parent)).as_posix()
                # Reuse the canonical skill's own routing language; only the relative link changes.
                adapter = (
                    "---\n"
                    + header
                    + "---\n\n"
                    + MARKER
                    + "\n\n"
                    + f"Read and follow the [canonical skill]({reference}).\n"
                    + f"Application root: `{app}`.\n"
                    + "Read the local AGENTS.md for the explicit private workspace before running CLI commands.\n"
                )
                planned.append((destination, adapter))
                exclusions.setdefault(target, []).append(f"/{runtime}/skills/{name}/")
    # Validate every target before writing any adapter.
    for destination, content in planned:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
    for target, entries in exclusions.items():
        git_dir = target / ".git"
        if git_dir.is_dir():
            exclude = git_dir / "info/exclude"
            existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
            missing = [entry for entry in entries if entry not in existing.splitlines()]
            if missing:
                exclude.parent.mkdir(parents=True, exist_ok=True)
                exclude.write_text(
                    existing.rstrip()
                    + "\n\n# Career Copilot local skill entrypoints\n"
                    + "\n".join(missing)
                    + "\n",
                    encoding="utf-8",
                )
    return len(planned)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--target", type=Path, action="append", required=True)
    args = parser.parse_args()
    print(f"Local skill adapters installed: {install(args.app_root, args.target)}")


if __name__ == "__main__":
    main()
