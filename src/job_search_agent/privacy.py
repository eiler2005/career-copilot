"""Fail-closed publication checks over exact blobs. Never print matched values."""

from __future__ import annotations

import io
import re
import subprocess
import tarfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from pypdf import PdfReader

from .core import read_json

SAFE_ROOT_FILES = {
    "README.md",
    "README.ru.md",
    "CONTRIBUTING.md",
    "CONTRIBUTING.ru.md",
    "AGENTS.md",
    "CLAUDE.md",
    "LICENSE",
    "CHANGELOG.md",
    "pyproject.toml",
    "uv.lock",
    ".gitignore",
    ".gitattributes",
    ".gitleaks.toml",
    ".pre-commit-config.yaml",
    "SECURITY.md",
    "Dockerfile",
    "compose.yaml",
    "compose.public.yaml",
    ".dockerignore",
}
SAFE_ROOT_DIRS = {"src", "tests", "docs", "examples", "scripts", "deploy", ".github", ".githooks"}
SKILL_NAMES = {
    "career-copilot",
    "career-job-search",
    "career-company-research",
    "career-cv-tailor",
    "career-natural-writing",
    "career-cover-letter",
    "career-interview-prep",
    "career-journal-stats",
}
EXCLUDED = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "dist", "build"}
PROTECTED = {"private", "data", "output", "backups", "snapshots", "packages", "revisions"}
TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".jsonl",
    ".csv",
    ".tsv",
    ".tex",
    ".toml",
    ".yaml",
    ".yml",
    ".sh",
    ".lock",
    ".html",
    ".css",
    ".js",
    "",
}
RULES = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "api-key": re.compile(
        r"\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"
    ),
    "credential-url": re.compile(r"https?://[^\s/:]+:[^\s/@]+@"),
    "credential-value": re.compile(
        r"""(?i)(?:api[_-]?key|password|access[_-]?token)\s*[=:]\s*["']?[A-Za-z0-9_+/.-]{16,}"""
    ),
    "private-user-path": re.compile(r"/(?:Users|home)/[A-Za-z][^/\s]+/"),
    "contact-phone": re.compile(r"(?i)(?:phone|телефон|whatsapp)[\s:=]+\+?\d[\d ()-]{8,}\d"),
}
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
SVG_ELEMENTS = {
    "svg",
    "g",
    "title",
    "desc",
    "defs",
    "linearGradient",
    "radialGradient",
    "stop",
    "rect",
    "path",
    "polygon",
    "polyline",
    "circle",
    "ellipse",
    "text",
    "tspan",
    "line",
    "clipPath",
    "marker",
    "use",
}


def static_svg(data: bytes) -> str:
    """Inspect decoded XML as well as source, without resolving external resources."""
    source = data.decode("utf-8")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)|<\?(?!xml\s)", source, re.IGNORECASE):
        raise ValueError("SVG document declarations or processing instructions are forbidden")
    root = ET.fromstring(source)
    if root.tag != f"{{{SVG_NAMESPACE}}}svg":
        raise ValueError("Expected an SVG document")
    decoded = []
    for node in root.iter():
        if not isinstance(node.tag, str) or not node.tag.startswith(f"{{{SVG_NAMESPACE}}}"):
            raise ValueError("Foreign SVG content")
        tag = node.tag.split("}", 1)[1]
        if tag not in SVG_ELEMENTS:
            raise ValueError("Unsupported SVG element")
        decoded.extend(value for value in (node.text, node.tail) if value)
        for key, value in node.attrib.items():
            attribute = key.rsplit("}", 1)[-1].lower()
            decoded.append(value)
            # Presentation attributes also use CSS syntax. An escaped function name
            # such as u\72l can hide external references from literal URL checks.
            # Our static documentation primitives never require attribute escapes.
            if "\\" in value:
                raise ValueError("Escaped SVG attributes are unsupported")
            if attribute.startswith("on") or attribute in {"src", "base", "style"}:
                raise ValueError("Active SVG attribute")
            if attribute == "href" and not re.fullmatch(r"#[A-Za-z_][\w.:-]*", value):
                raise ValueError("External SVG reference")
            if re.search(
                r"javascript\s*:|data\s*:|@import|expression\s*\(|-moz-binding|behavior\s*:",
                value,
                re.IGNORECASE,
            ):
                raise ValueError("Active SVG value")
            without_local_urls = re.sub(r"url\(\s*#[A-Za-z_][\w.:-]*\s*\)", "", value)
            if re.search(r"url\s*\(|https?\s*:|file\s*:", without_local_urls, re.IGNORECASE):
                raise ValueError("External SVG resource")
    return source + "\n" + "\n".join(decoded)


def graphic_path(name: str, depth: int = 0) -> bool:
    parts = Path(name).parts
    # A source distribution may add exactly one top-level package directory.
    return parts[:2] == ("docs", "assets") or (depth > 0 and parts[1:3] == ("docs", "assets"))


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)
    if result.returncode:
        raise ValueError("Git privacy inspection failed; no publication allowed")
    return result.stdout


def allowed_path(name: str) -> bool:
    path = Path(name)
    if not path.parts or path.is_absolute() or ".." in path.parts or set(path.parts) & PROTECTED:
        return False
    if any(part == ".env" or part.startswith(".env.") for part in path.parts):
        return False
    if path.parts[0] in {".agents", ".claude"}:
        return len(path.parts) >= 4 and path.parts[1] == "skills" and path.parts[2] in SKILL_NAMES
    if path.suffix.lower() in {".svg", ".dot"} and not graphic_path(name):
        return False
    return path.parts[0] in SAFE_ROOT_DIRS or name in SAFE_ROOT_FILES


def text_content(name: str, data: bytes, depth: int = 0) -> str:
    if len(data) > 10_000_000 or depth > 2:
        raise ValueError("Uninspectable size or archive nesting")
    suffix = Path(name).suffix.lower()
    if suffix in {".svg", ".dot"}:
        if not graphic_path(name, depth) or b"\0" in data:
            raise ValueError("Graphics are restricted to inspectable documentation assets")
        return static_svg(data) if suffix == ".svg" else data.decode("utf-8")
    if name.endswith((".tar.gz", ".tgz")):
        parts = []
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            members = archive.getmembers()
            if len(members) > 2000 or sum(m.size for m in members) > 20_000_000:
                raise ValueError("Oversized archive")
            for member in members:
                if member.isdir():
                    continue
                if (
                    not member.isfile()
                    or Path(member.name).is_absolute()
                    or ".." in Path(member.name).parts
                ):
                    raise ValueError("Unsafe archive member")
                if set(Path(member.name).parts) & PROTECTED:
                    raise ValueError("Private archive member")
                handle = archive.extractfile(member)
                parts += [member.name, text_content(member.name, handle.read(), depth + 1)]
        return "\n".join(parts)
    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise ValueError("Encrypted document")
        text = "\n".join(p.extract_text() or "" for p in reader.pages)
        if not text.strip():
            raise ValueError("Image-only PDF requires manual review")
        # Public candidate PDFs are denied separately even when their text is inspectable.
        return text + str(reader.metadata)
    if suffix in {".zip", ".docx", ".whl"}:
        parts = []
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            if len(infos) > 2000 or sum(i.file_size for i in infos) > 20_000_000:
                raise ValueError("Oversized archive")
            for info in infos:
                if info.is_dir():
                    continue
                if Path(info.filename).is_absolute() or ".." in Path(info.filename).parts:
                    raise ValueError("Unsafe archive entry")
                if set(Path(info.filename).parts) & PROTECTED:
                    raise ValueError("Private archive member")
                body = archive.read(info)
                parts.append(info.filename)
                if Path(info.filename).suffix in {".xml", ".rels"}:
                    parts.append(body.decode("utf-8"))
                else:
                    parts.append(text_content(info.filename, body, depth + 1))
        return "\n".join(parts)
    if suffix not in TEXT_SUFFIXES or b"\0" in data:
        raise ValueError("Unsupported binary")
    return data.decode("utf-8")


def scan_blob(name: str, data: bytes, terms: list[str], *, check_path: bool = True) -> list[str]:
    findings = []
    if check_path and not allowed_path(name):
        findings.append("path-not-allowlisted")
    if Path(name).suffix.lower() in {".pdf", ".docx", ".db", ".sqlite", ".png", ".jpg"}:
        findings.append("private-or-binary-artifact")
    try:
        content = text_content(name, data)
    except Exception as error:  # noqa: BLE001 - fail closed without leaking parser input
        # Parser failures are opaque by design; exceptions may contain private bytes.
        del error
        return findings + ["uninspectable-content"]
    for rule, pattern in RULES.items():
        if pattern.search(content):
            findings.append(rule)
    for email in re.findall(r"[\w.+-]+@([\w.-]+\.[A-Za-z]{2,})", content):
        if email.lower() not in {"example.com", "example.org", "example.net", "example.invalid"}:
            findings.append("contact-email")
            break
    normalized = re.sub(r"\s+", " ", content + " " + name).casefold()
    if any(re.sub(r"\s+", " ", term).casefold() in normalized for term in terms if len(term) >= 4):
        findings.append("private-dictionary-match")
    return sorted(set(findings))


def check(root: Path, scope: str, dictionary: Path | None = None) -> dict:
    root = root.resolve()
    if dictionary and dictionary.resolve().is_relative_to(root):
        raise ValueError("Private dictionary must be outside public repository")
    terms = read_json(dictionary).get("terms", []) if dictionary else []
    blobs = []
    if scope == "index":
        for entry in git(root, "ls-files", "--stage", "-z").split(b"\0"):
            if not entry:
                continue
            header, path = entry.split(b"\t", 1)
            mode, oid, stage = header.decode().split()
            if stage != "0":
                raise ValueError("Unmerged index")
            blobs.append(
                (
                    path.decode(),
                    git(root, "cat-file", "blob", oid),
                    mode != "100644" and mode != "100755",
                )
            )
    elif scope == "history":
        commits = git(root, "rev-list", "--all").decode().splitlines()
        seen = set()
        for commit in commits:
            for entry in git(root, "ls-tree", "-rz", commit).split(b"\0"):
                if not entry:
                    continue
                header, path = entry.split(b"\t", 1)
                mode, kind, oid = header.decode().split()
                key = (path, oid)
                if key in seen:
                    continue
                seen.add(key)
                if kind != "blob":
                    raise ValueError("Git submodules are not public-release allowlisted")
                blobs.append((path.decode(), git(root, "cat-file", "blob", oid), mode == "120000"))
    elif scope == "worktree":
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root)
            if set(relative.parts) & EXCLUDED:
                continue
            if path.is_symlink():
                blobs.append((str(relative), b"", True))
            elif path.is_file():
                blobs.append((str(relative), path.read_bytes(), False))
    else:
        raise ValueError("Unknown scan scope")
    findings = []
    for index, (name, body, symlink) in enumerate(blobs):
        rules = ["symlink-forbidden"] if symlink else scan_blob(name, body, terms)
        if rules:
            # Do not print filenames: a filename can itself contain private data.
            findings.append({"blob_number": index + 1, "rules": rules})
    return {
        "scope": scope,
        "scanned": len(blobs),
        "dictionary_loaded": dictionary is not None,
        "passed": not findings,
        "findings": findings,
    }


def check_artifact(path: Path, dictionary: Path | None = None) -> dict:
    terms = read_json(dictionary).get("terms", []) if dictionary else []
    findings = scan_blob(path.name, path.read_bytes(), terms, check_path=False)
    return {
        "passed": not findings,
        "artifact_sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest(),
        "findings": findings,
        "dictionary_loaded": dictionary is not None,
    }


def gitleaks_check(root: Path, scope: str) -> dict:
    import shutil
    import tempfile

    executable = shutil.which("gitleaks")
    if not executable:
        return {"passed": False, "reason": "gitleaks_not_installed"}
    with tempfile.TemporaryDirectory(prefix="ajh-index-scan-") as temporary:
        target = root
        if scope == "index":
            target = Path(temporary)
            for entry in git(root, "ls-files", "--stage", "-z").split(b"\0"):
                if not entry:
                    continue
                header, name = entry.split(b"\t", 1)
                mode, oid, stage = header.decode().split()
                relative = Path(name.decode())
                if mode not in {"100644", "100755"} or stage != "0" or ".." in relative.parts:
                    return {"passed": False, "reason": "unsafe_index"}
                output = target / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(git(root, "cat-file", "blob", oid))
        command = [
            executable,
            "git" if scope == "history" else "dir",
            str(target),
            "--redact",
            "--no-banner",
        ]
        if scope == "history":
            command += ["--log-opts=--all"]
        result = subprocess.run(command, capture_output=True, timeout=120, check=False)
    return {
        "passed": result.returncode == 0,
        "reason": "passed" if result.returncode == 0 else "gitleaks_failed",
    }
