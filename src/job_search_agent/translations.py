"""Presentation translations for journal text, stored beside the original records.

Original payloads are never rewritten. Each translatable string is identified by a
hash of its exact text; a `text_translations` record holds the Russian and English
renderings plus the identity of whoever produced them. Official vacancy titles,
company names and URLs are deliberately not translatable fields.
"""

from __future__ import annotations

import re

from .core import Store, digest, now

LANGUAGES = ("ru", "en")
TRANSLATABLE = {
    "vacancies": ("next_action", "decision", "requirements_note"),
    "companies": ("next_action", "decision", "about", "summary"),
    "activities": ("operation", "next_action"),
    "learning": (
        "warning",
        "weeks[].focus",
        "weeks[].deliverable",
        "gaps[].text",
        "gaps[].next_action",
        "gaps[].done_requires",
        "shared[]",
    ),
    "interview_plans": ("objectives[]",),
    "events": ("note",),
    "assessments": ("requirements[].text", "seniority.reason", "unknowns[]"),
    "packages": ("versions[].change",),
}


def text_id(text: str) -> str:
    return "tr-" + digest(text.encode("utf-8"))[:32]


def language(text: str) -> str:
    cyrillic = len(re.findall(r"[а-яё]", text, re.IGNORECASE))
    latin = len(re.findall(r"[a-z]", text, re.IGNORECASE))
    return "ru" if cyrillic > latin * 0.3 else "en"


def values(payload: object, spec: str) -> list[str]:
    current = [payload]
    for part in spec.split("."):
        found = []
        for item in current:
            if not isinstance(item, dict):
                continue
            value = item.get(part.removesuffix("[]"))
            if part.endswith("[]"):
                found += value if isinstance(value, list) else []
            elif value is not None:
                found.append(value)
        current = found
    return [item for item in current if isinstance(item, str) and item.strip()]


def texts(store: Store) -> dict[str, str]:
    """Every translatable string in the journal, keyed by its translation ID."""
    found = {}
    for kind, specs in TRANSLATABLE.items():
        for record in store.all(kind):
            for spec in specs:
                for text in values(record, spec):
                    found[text_id(text)] = text
    return found


def export(store: Store, missing_only: bool = True) -> dict:
    items = []
    for key, text in sorted(texts(store).items()):
        existing = (store.get("text_translations", key) or {}).get("translations", {})
        source = language(text)
        target = "en" if source == "ru" else "ru"
        if missing_only and existing.get(target):
            continue
        items.append(
            {
                "id": key,
                "source_lang": source,
                "text": text,
                "translations": {source: text, target: existing.get(target, "")},
            }
        )
    return {
        "schema_version": 1,
        "actor": {"environment": None, "model": None, "session": None},
        "items": items,
    }


def import_translations(store: Store, data: dict) -> dict:
    actor = data.get("actor") if isinstance(data, dict) else None
    if not isinstance(actor, dict) or not isinstance(actor.get("model"), str) or not actor["model"]:
        raise ValueError("Translations require the actual translator model identity")
    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError("Translations file requires an items array")  # noqa: TRY004
    imported = 0
    store.db.execute("BEGIN IMMEDIATE")
    try:
        for item in items:
            text = item.get("text") if isinstance(item, dict) else None
            translations = item.get("translations") if isinstance(item, dict) else None
            if not isinstance(text, str) or item.get("id") != text_id(text):
                raise ValueError("Translation ID must match the exact source text")
            if not isinstance(translations, dict) or not set(translations) <= set(LANGUAGES):
                raise ValueError("Translations must be keyed by ru and en")
            clean = {
                lang: value.strip()
                for lang, value in translations.items()
                if isinstance(value, str) and value.strip()
            }
            source = language(text)
            clean[source] = text
            if len(clean) < 2:
                continue
            old = store.get("text_translations", item["id"]) or {}
            value = {
                "id": item["id"],
                "source_lang": source,
                "text": text,
                "translations": {**old.get("translations", {}), **clean},
                "translator": {key: actor.get(key) for key in ("environment", "model", "session")},
                "updated_at": now(),
            }
            store.put("text_translations", value)
            imported += 1
        if imported:
            store.event("translations_imported", [], {"count": imported, "model": actor["model"]})
        store.db.execute("COMMIT")
    except Exception:
        store.db.execute("ROLLBACK")
        raise
    return {"imported": imported}
