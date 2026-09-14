"""SQLite-derived counts; readiness, hiring and actual submissions are independent."""

from collections import Counter
from datetime import datetime

from .activity import refs_valid
from .core import TRACKS, Store
from .workflow import version_checks


def counts(values):
    return dict(sorted(Counter(values).items()))


def duration(value):
    if not value.get("finished_at"):
        return None
    return max(
        0,
        (
            datetime.fromisoformat(value["finished_at"])
            - datetime.fromisoformat(value["started_at"])
        ).total_seconds(),
    )


def latest_assessments(store: Store) -> dict:
    latest = {}
    for assessment in store.insertion_order("assessments"):
        latest[(assessment["vacancy_id"], assessment["track"])] = assessment
    for pointer in store.all("current_assessments"):
        assessment = store.get("assessments", pointer["assessment_id"])
        if assessment:
            latest[(pointer["vacancy_id"], pointer["track"])] = assessment
    return latest


def valid_progress(store: Store, value: dict) -> bool:
    practice = store.get("interview_practices", value.get("practice_id"))
    feedback = store.get("interview_feedback", value.get("feedback_id"))
    return bool(
        practice
        and feedback
        and feedback.get("practice_id") == practice["id"]
        and all(
            row.get(field)
            for row, field in ((value, "evidence"), (practice, "evidence"), (feedback, "feedback"))
        )
        and refs_valid(store, [value["evidence"], practice["evidence"], feedback["feedback"]])
    )


def compute(store: Store) -> dict:
    companies, vacancies = store.all("companies"), store.all("vacancies")
    packages, activities = store.all("packages"), store.all("activities")
    latest = latest_assessments(store)
    current = [next(v for v in p["versions"] if v["id"] == p["current_version"]) for p in packages]
    submissions = [
        s
        for s in store.all("submissions")
        if s.get("user_confirmed") is True
        and s.get("sent_at")
        and s.get("channel")
        and s.get("evidence")
        and refs_valid(store, [s["evidence"]])
    ]
    # Preserve imported assertions without converting them into evidence-backed sends.
    unsupported = [
        p["id"]
        for p in packages
        if p.get("application_status") == "submitted"
        and p["id"] not in {s["package_id"] for s in submissions}
    ]
    health = store.all("source_health")
    responses = [
        r
        for r in store.all("employer_responses")
        if r.get("evidence") and refs_valid(store, [r["evidence"]])
    ]
    progress = [p for p in store.all("interview_progress") if valid_progress(store, p)]
    telemetry = {}
    for field in ("input_tokens", "output_tokens", "cost"):
        known = [a.get("telemetry", {}).get(field) for a in activities]
        telemetry[field] = {
            "total": sum(known) if known and all(v is not None for v in known) else None,
            "known_total": sum(v for v in known if v is not None)
            if any(v is not None for v in known)
            else None,
            "unknown_activities": sum(v is None for v in known),
        }
    return {
        "schema_version": 1,
        "companies": {"unique": len(companies), "dossiers": len(store.all("company_dossiers"))},
        "vacancies": {
            "unique": len(vacancies),
            "hiring_availability": counts(v.get("availability", "unknown") for v in vacancies),
        },
        "assessments": {
            "versions": len(store.all("assessments")),
            "latest_by_track": {
                t: counts(a["decision"] for (_, track), a in latest.items() if track == t)
                for t in TRACKS
            },
        },
        "documents": {
            "packages": len(packages),
            "versions": sum(len(p["versions"]) for p in packages),
            "current_review_readiness": counts(
                "invalid"
                if version_checks(store, v)
                else v.get("review_status", "unknown")
                if "reviews" in v
                else "legacy_unverified"
                for v in current
            ),
            "standalone_letters": len(store.all("cover_letters")),
            "text_revisions": len(store.all("text_revisions")),
        },
        "submissions": {
            "evidence_backed": len(submissions),
            "unique_packages": len({s["package_id"] for s in submissions}),
            "unique_vacancies": len({s["vacancy_id"] for s in submissions}),
            "unverified_legacy_package_ids": unsupported,
        },
        "sources": {
            "statuses": counts(s.get("status", "unknown") for s in health),
            "errors": len(
                [
                    s
                    for s in health
                    if s.get("status") not in {"success", "success_empty", "success_nonempty", "ok"}
                ]
            ),
            "freshness": [
                {
                    key: s.get(key)
                    for key in (
                        "id",
                        "status",
                        "last_success",
                        "last_attempt",
                        "next_attempt",
                        "count",
                    )
                }
                for s in health
            ],
        },
        "interviews": {
            "baseline_learning_plans": len(store.all("learning")),
            "plans": len(store.all("interview_plans")),
            "practices": len(store.all("interview_practices")),
            "feedback": len(store.all("interview_feedback")),
            "evidence_backed_progress": counts(p["decision"] for p in progress),
        },
        "activities": {
            "total": len(activities),
            "statuses": counts(a["status"] for a in activities),
            "skills": counts(a["skill"] for a in activities),
            "actual_models": counts(
                a.get("actor", {}).get("model") or "unknown" for a in activities
            ),
            "durations": [{"id": a["id"], "seconds": duration(a)} for a in activities],
            "telemetry": telemetry,
        },
        "responses": {
            "evidence_backed": len(responses),
            "statuses": counts(r["status"] for r in responses),
            "unique_packages": len({r["package_id"] for r in responses}),
            "legacy_reported_package_statuses": counts(
                p.get("application_status", "unknown") for p in packages
            ),
        },
    }
