"""Check local Markdown links, language pairs, and canonical skill adapters offline."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


def without_fences(text: str) -> str:
    return re.sub(r"(?ms)^\s*(```|~~~).*?^\s*\1\s*$", "", text)


def anchors(text: str) -> set[str]:
    result = set(re.findall(r'<(?:a|[a-z][\w]*)[^>]+(?:id|name)=["\']([^"\']+)', text))
    seen = {}
    for heading in re.findall(r"(?m)^#{1,6}\s+(.+?)\s*#*\s*$", without_fences(text)):
        heading = re.sub(r"<[^>]+>", "", heading).strip().lower()
        slug = re.sub(r"[^\w\- ]", "", heading).replace(" ", "-")
        occurrence = seen.get(slug, 0)
        seen[slug] = occurrence + 1
        result.add(slug + (f"-{occurrence}" if occurrence else ""))
    return result


def check(root: Path) -> list[str]:
    files = sorted(root.glob("*.md")) + sorted((root / "docs").rglob("*.md"))
    files += sorted((root / ".agents/skills").rglob("*.md"))
    files += sorted((root / ".claude/skills").rglob("*.md"))
    errors = []
    for source in files:
        text = without_fences(source.read_text(encoding="utf-8"))
        links = re.findall(r"!?\[[^\]\n]*\]\(([^\n]*?)\)", text)
        for raw in links:
            target = raw.strip().split(' "', 1)[0].strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc:
                continue
            if not parsed.path and not parsed.fragment:
                continue
            destination = (
                (source.parent / unquote(parsed.path)).resolve() if parsed.path else source
            )
            if not destination.is_relative_to(root):
                errors.append(f"{source.relative_to(root)}: link leaves public project")
            elif not destination.exists():
                errors.append(f"{source.relative_to(root)}: missing {target}")
            elif (
                parsed.fragment
                and destination.suffix == ".md"
                and unquote(parsed.fragment) not in anchors(destination.read_text(encoding="utf-8"))
            ):
                errors.append(f"{source.relative_to(root)}: missing anchor {target}")
    for source in sorted((root / "docs").glob("*.md")):
        if not (root / "docs/ru" / source.name).is_file():
            errors.append(f"Missing Russian document: {source.name}")
    for name in ("README.ru.md", "CONTRIBUTING.ru.md"):
        if not (root / name).is_file():
            errors.append(f"Missing Russian document: {name}")
    canonical = sorted((root / ".agents/skills").glob("*/SKILL.md"))
    if len(canonical) != 8:
        errors.append("Expected eight canonical skills")
    for source in canonical:
        adapter = root / ".claude/skills" / source.parent.name / "SKILL.md"
        if not adapter.is_file() or adapter.is_symlink():
            errors.append(f"Missing ordinary Claude adapter: {source.parent.name}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = check(args.root.resolve())
    for error in errors:
        print(error)
    print(f"Documentation checks: {'failed' if errors else 'passed'} ({len(errors)} errors)")
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
