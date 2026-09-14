"""Local-only HTML views, escaped by default; no remote assets or analytics."""

import html
from pathlib import Path

from .core import Store, atomic_write, encode, now
from .stats import compute, latest_assessments
from .workflow import version_checks


def render(store: Store) -> Path:
    esc = lambda value: html.escape(str(value if value is not None else "unknown"))
    sections = []

    def details(label, value):
        return f"<details><summary>{esc(label)}</summary><pre>{esc(encode(value))}</pre></details>"

    def totals(value):
        return (
            ", ".join(f"{count} {key.replace('_', ' ')}" for key, count in value.items())
            or "None recorded"
        )

    def table(title, headings, rows, intro=""):
        body = "".join(
            "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows
        )
        if not body:
            body = (
                f'<tr><td colspan="{len(headings)}" class="muted">Nothing recorded yet.</td></tr>'
            )
        sections.append(
            f'<section id="{title.lower()}"><h2>{title}</h2>{intro}'
            f'<div class="table-scroll" tabindex="0" role="region" aria-label="{esc(title)}"><table><thead><tr>'
            + "".join(f"<th>{esc(h)}</th>" for h in headings)
            + "</tr></thead><tbody>"
            + body
            + "</tbody></table></div></section>"
        )

    statistics = compute(store)
    cards = (
        '<div class="cards">'
        + "".join(
            f'<div class="card"><strong>{esc(value)}</strong><span>{esc(label)}</span></div>'
            for label, value in (
                ("Unique companies", statistics["companies"]["unique"]),
                ("Unique vacancies", statistics["vacancies"]["unique"]),
                ("Document packages", statistics["documents"]["packages"]),
                ("Document versions", statistics["documents"]["versions"]),
                ("Evidence-backed sends", statistics["submissions"]["evidence_backed"]),
                ("Employer responses", statistics["responses"]["evidence_backed"]),
            )
        )
        + "</div>"
    )
    table(
        "Overview",
        ["Area", "Current journal summary"],
        [
            ["Hiring availability", esc(totals(statistics["vacancies"]["hiring_availability"]))],
            [
                "Product assessments",
                esc(totals(statistics["assessments"]["latest_by_track"]["product"])),
            ],
            [
                "Technical leadership assessments",
                esc(totals(statistics["assessments"]["latest_by_track"]["technical-leadership"])),
            ],
            [
                "Current document reviews",
                esc(totals(statistics["documents"]["current_review_readiness"])),
            ],
            ["Activities", esc(totals(statistics["activities"]["statuses"]))],
            ["Actual models", esc(totals(statistics["activities"]["actual_models"]))],
            [
                "Interview preparation",
                esc(
                    f"{statistics['interviews']['baseline_learning_plans']} baseline plans; "
                    f"{statistics['interviews']['plans']} registered plans; {statistics['interviews']['practices']} practice records"
                ),
            ],
            [
                "Demonstrated progress",
                esc(totals(statistics["interviews"]["evidence_backed_progress"])),
            ],
            ["Source health", esc(totals(statistics["sources"]["statuses"]))],
            ["Response outcomes", esc(totals(statistics["responses"]["statuses"]))],
            [
                "Measured usage",
                "Unknown measurements stay unknown. "
                + details("Usage, durations and complete statistics", statistics),
            ],
        ],
        intro=cards,
    )
    table(
        "Activities",
        [
            "Started / finished",
            "Skill / operation",
            "Status / next action",
            "Actual actor",
            "Inputs / outputs",
        ],
        [
            [
                esc(a["started_at"]) + "<br>" + esc(a.get("finished_at") or "Not finished"),
                esc(a["skill"]) + "<br>" + esc(a["operation"]),
                f'<span class="status">{esc(a["status"])}</span><br>{esc(a["next_action"])}',
                esc(a["actor"].get("model") or "Unknown model"),
                esc(
                    f"{len(a['inputs'])} inputs · {len(a.get('artifacts', {}))} artifacts · {len(a.get('records', []))} records"
                )
                + details("Activity details", a),
            ]
            for a in store.all("activities")
        ],
    )
    table(
        "Interviews",
        ["Type", "Progress / next step", "Evidence"],
        [
            [
                esc(kind.removeprefix("interview_").replace("_", " ")),
                esc(
                    value.get("decision")
                    or value.get("exercise")
                    or value.get("objectives")
                    or value.get("findings")
                ),
                details("Evidence and record", value),
            ]
            for kind in (
                "interview_plans",
                "interview_practices",
                "interview_feedback",
                "interview_progress",
            )
            for value in store.all(kind)
        ],
    )
    table(
        "Companies",
        ["Company", "Business", "Size", "Source / reporting period"],
        [
            [
                esc(c.get("name", c["id"])),
                esc(c.get("about", "unknown")),
                esc(c.get("size", {}).get("value"))
                + " "
                + esc(c.get("size", {}).get("metric", ""))
                + details("Size and scope", c.get("size", {})),
                details("Sources and company profile", c),
            ]
            for c in store.all("companies")
        ],
    )
    assessments = latest_assessments(store)
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
                esc((v.get("level") or {}).get("raw"))
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
                esc(f"{len(p['weeks'])} weeks · {p.get('hours_per_week', 'unknown')} hours/week")
                + details("Weekly plan", p["weeks"]),
                esc(f"{len(p['gaps'])} recorded gaps")
                + details("Gaps and evidence requirements", p["gaps"]),
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
                esc(e.get("note", "")) + details("Event details", e),
            ]
            for e in sorted(
                store.all("events"), key=lambda e: e.get("at", e.get("date", "")), reverse=True
            )
        ],
    )
    markup = (
        """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="referrer" content="no-referrer"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark"><title>Private job search workspace</title>
<style>:root{color-scheme:light dark;--bg:#f4f6f8;--surface:#fff;--text:#24323d;--heading:#173c51;--line:#dce2e8;--soft:#e6edf3;--link:#096783;--notice:#fff4ce;--muted:#586b79}
*{box-sizing:border-box}body{font:15px/1.55 system-ui;margin:0 auto;padding:32px;max-width:1500px;color:var(--text);background:var(--bg)}h1,h2{color:var(--heading);line-height:1.2}h1{font-size:clamp(26px,4vw,38px)}h2{font-size:23px}
nav{position:sticky;top:0;z-index:2;background:var(--surface);padding:14px 18px;display:flex;flex-wrap:wrap;gap:8px 22px;border:1px solid var(--line);border-radius:12px}
.table-scroll{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--surface)}table{border-collapse:collapse;width:100%}
td,th{padding:13px 16px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:var(--soft);font-size:13px}tr:last-child td{border-bottom:0}td{min-width:130px;max-width:460px}
section{margin:36px 0;scroll-margin-top:100px}a{color:var(--link);text-underline-offset:3px}.notice{background:var(--notice);padding:14px 18px;border-radius:12px}.muted{color:var(--muted)}
.cards{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px;margin-bottom:18px}.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px}.card strong{display:block;font-size:30px;color:var(--heading)}.card span{font-size:13px;color:var(--muted)}
details{margin-top:8px}summary{cursor:pointer;color:var(--link);font-size:13px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.5 ui-monospace,monospace;max-height:360px;overflow:auto;background:var(--bg);padding:12px;border-radius:8px}.status{display:inline-block;border-radius:6px;background:var(--soft);padding:2px 7px;font-weight:600;font-size:13px}
@media(max-width:1000px){.cards{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:600px){body{padding:16px}.cards{grid-template-columns:repeat(2,minmax(0,1fr))}.card{padding:14px}nav{position:static;gap:8px 16px}td,th{padding:11px 12px}section{scroll-margin-top:16px}}
@media(prefers-color-scheme:dark){:root{--bg:#101820;--surface:#17232e;--text:#dbe5ed;--heading:#e4f1fa;--line:#344552;--soft:#243745;--link:#88cfff;--notice:#3e3521;--muted:#a9bbc9}}
</style>
<h1>Private job search workspace</h1><p class="notice">Local personal data. Do not publish this page.
Drafted, reviewed and submitted are separate states. Imported hiring statuses have not been refreshed.</p>
<nav>"""
        + "".join(
            f'<a href="#{x.lower()}">{x}</a>'
            for x in [
                "Overview",
                "Activities",
                "Companies",
                "Vacancies",
                "Documents",
                "Preparation",
                "Interviews",
                "Sources",
                "History",
            ]
        )
        + "</nav><p>Generated: "
        + esc(now())
        + "</p>"
        + "".join(sections)
        + "</html>"
    )
    path = store.home / "report" / "index.html"
    atomic_write(path, markup)
    atomic_write(store.home / "report" / "stats.json", encode(statistics))
    for kind in ("companies", "vacancies", "packages", "events", "learning", "assessments"):
        atomic_write(store.home / "report" / f"{kind}.json", encode(store.all(kind)))
    return path
