"""Local-only HTML views, escaped by default; no remote assets or analytics."""

import html
from pathlib import Path

from .core import Store, atomic_write, encode, now
from .workflow import version_checks


def render(store: Store) -> Path:
    esc = lambda value: html.escape(str(value if value is not None else "unknown"))
    sections = []

    def table(title, headings, rows):
        body = "".join(
            "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows
        )
        sections.append(
            f'<section id="{title.lower()}"><h2>{title}</h2><table><thead><tr>'
            + "".join(f"<th>{esc(h)}</th>" for h in headings)
            + "</tr></thead><tbody>"
            + body
            + "</tbody></table></section>"
        )

    table(
        "Companies",
        ["Company", "Business", "Size", "Source / reporting period"],
        [
            [
                esc(c.get("name", c["id"])),
                esc(c.get("about", "unknown")),
                esc(encode(c.get("size", {}))),
                esc(c.get("profile_sources", [])),
            ]
            for c in store.all("companies")
        ],
    )
    assessments = {}
    for a in sorted(store.all("assessments"), key=lambda x: x.get("at", "")):
        assessments[(a["vacancy_id"], a["track"])] = a
    table(
        "Vacancies",
        [
            "ID / title",
            "Company / location",
            "Employer level / role",
            "Hiring status",
            "Track / decision",
            "Next step / original",
        ],
        [
            [
                esc(v["id"] + " — " + v["title"]),
                esc(v["company_id"] + " / " + v.get("location", "unknown")),
                esc(encode(v.get("level", {})))
                + "<br>Family: "
                + esc(v.get("role_family"))
                + "<br>Management / IC: "
                + esc(v.get("role_type")),
                esc(v.get("availability", "unknown"))
                + "<br>Checked: "
                + esc(v.get("status_checked_on")),
                "<br>".join(
                    esc(t + ": " + a["decision"] + " — " + a["seniority"]["reason"])
                    for (vid, t), a in assessments.items()
                    if vid == v["id"]
                )
                or esc(v.get("decision", "Not assessed")),
                esc(v.get("next_action", "Review source, track and evidence"))
                + "<br>"
                + "<br>".join(
                    f'<a href="{esc(url)}" rel="noreferrer">Source</a>'
                    for url in v.get("urls", [])
                    if url.startswith(("https://", "http://"))
                ),
            ]
            for v in store.all("vacancies")
        ],
    )
    rows = []
    for package in store.all("packages"):
        for version in package["versions"]:
            links = []
            for label, name in version["files"].items():
                mapped = store.get("legacy_files", name)
                target = store.path(mapped["path"] if mapped else name)
                if target.is_file():
                    links.append(f'<a href="{esc(target.as_uri())}">{esc(label)}</a>')
            valid = not version_checks(store, version)
            status = version.get("review_status", "unknown")
            if "reviews" not in version:
                status = "legacy recorded: " + status + " (not re-reviewed)"
            rows.append(
                [
                    esc(package["id"]),
                    esc(version["id"])
                    + (" (current)" if version["id"] == package["current_version"] else ""),
                    esc(status if valid else "INVALID: missing/changed artifact"),
                    esc(package.get("application_status", "drafted")),
                    " · ".join(links),
                ]
            )
    table("Documents", ["Package", "Version", "Review", "Application", "Files"], rows)
    table(
        "Preparation",
        ["Track", "Vacancy", "Plan", "Gaps"],
        [
            [
                esc(p["track"]),
                esc(p.get("vacancy_id", "General")),
                esc(encode(p["weeks"])),
                esc(encode(p["gaps"])),
            ]
            for p in store.all("learning")
        ],
    )
    table(
        "Sources",
        ["Source", "Status", "Last success", "Next attempt", "Count"],
        [
            [
                esc(s["id"]),
                esc(s["status"]),
                esc(s.get("last_success")),
                esc(s.get("next_attempt")),
                esc(s.get("count")),
            ]
            for s in store.all("source_health")
        ],
    )
    table(
        "History",
        ["Date", "Action", "Details"],
        [
            [
                esc(e.get("at", e.get("date"))),
                esc(e["type"]),
                esc(e.get("note", encode(e.get("details", {})))),
            ]
            for e in sorted(
                store.all("events"), key=lambda e: e.get("at", e.get("date", "")), reverse=True
            )
        ],
    )
    markup = (
        """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="referrer" content="no-referrer"><title>Private job search workspace</title>
<style>body{font:15px system-ui;margin:32px;color:#24323d;background:#f5f7fa}h1,h2{color:#173c51}
nav{position:sticky;top:0;background:#fff;padding:16px;display:flex;gap:22px}table{border-collapse:collapse;width:100%;background:white}
td,th{padding:12px;border:1px solid #dce2e8;text-align:left;vertical-align:top;white-space:pre-wrap;overflow-wrap:anywhere}
th{background:#e6edf3}section{margin:32px 0}a{color:#096783}td{max-width:460px}.notice{background:#fff4ce;padding:16px}</style>
<h1>Private job search workspace</h1><p class="notice">Local personal data. Do not publish this page.
Drafted, reviewed and submitted are separate states. Imported hiring statuses have not been refreshed.</p>
<nav>"""
        + "".join(
            f'<a href="#{x.lower()}">{x}</a>'
            for x in ["Companies", "Vacancies", "Documents", "Preparation", "Sources", "History"]
        )
        + "</nav><p>Generated: "
        + esc(now())
        + "</p>"
        + "".join(sections)
        + "</html>"
    )
    path = store.home / "report" / "index.html"
    atomic_write(path, markup)
    for kind in ("companies", "vacancies", "packages", "events", "learning", "assessments"):
        atomic_write(store.home / "report" / f"{kind}.json", encode(store.all(kind)))
    return path
