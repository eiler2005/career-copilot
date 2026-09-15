"""Search campaigns: what the user is looking for, kept separate from qualification.

A campaign lives in `settings.json -> campaigns[]`. Matching a vacancy against a
campaign compares *preferences* (market, role, level, countries, format, language,
employment, salary, exclusions). Each criterion is `match`, `mismatch` or `unknown`
with a basis. The result never changes the qualification assessment; a vacancy stays
one record even when several campaigns fit it.
"""

from __future__ import annotations

import re
import unicodedata

from .core import TRACKS, safe_id

MARKETS = ("ru", "intl")
WORK_MODES = ("remote", "hybrid", "office")
EMPLOYMENT = ("full_time", "part_time", "contract", "internship", "temporary")
PERIODS = ("hour", "month", "year")
LIST_FIELDS = ("role_titles", "levels", "work_countries", "languages", "exclusions", "source_ids")


def _norm(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"\s+", " ", text).strip()


def _contains(haystack: str, needle: str) -> bool:
    """Whole-word match, so "CTO" does not match "Director"."""
    needle = _norm(needle)
    return bool(needle) and re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", haystack) is not None


def _strings(value: object, name: str, limit: int = 40) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > limit:
        raise ValueError(f"{name} must be a list of up to {limit} strings")
    result = []
    for item in value:
        if not isinstance(item, str) or not item.strip() or len(item) > 120:
            raise ValueError(f"{name} must contain short non-empty strings")
        if item.strip() not in result:
            result.append(item.strip())
    return result


def _subset(value: object, name: str, allowed: tuple[str, ...]) -> list[str]:
    items = _strings(value, name)
    if not set(items) <= set(allowed):
        raise ValueError(f"{name} accepts {list(allowed)}")
    return items


def validate(campaign: object) -> dict:
    """Normalise one campaign; raises ValueError with a readable message."""
    if not isinstance(campaign, dict):
        raise ValueError("Campaign must be an object")  # noqa: TRY004
    name = campaign.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 120:
        raise ValueError("Campaign name is required (up to 120 characters)")
    market = campaign.get("market") or "any"
    if market not in (*MARKETS, "any"):
        raise ValueError("market must be ru, intl or any")
    track = campaign.get("track")
    if track not in TRACKS:
        raise ValueError(f"track must be one of {list(TRACKS)}")
    salary = campaign.get("salary")
    if salary is not None:
        if not isinstance(salary, dict):
            raise ValueError("salary must be an object")
        minimum = salary.get("min")
        if minimum is not None and (
            isinstance(minimum, bool) or not isinstance(minimum, (int, float)) or minimum < 0
        ):
            raise ValueError("salary.min must be a positive number")
        currency = salary.get("currency")
        if minimum is not None and (
            not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency)
        ):
            raise ValueError("salary.currency must be a 3-letter code")
        period = salary.get("period")
        if minimum is not None and period not in PERIODS:
            raise ValueError("salary.period must be hour, month or year")
        gross_net = salary.get("gross_net") or "unknown"
        if gross_net not in {"gross", "net", "unknown"}:
            raise ValueError("salary.gross_net must be gross, net or unknown")
        salary = {"min": minimum, "currency": currency, "period": period, "gross_net": gross_net}
    value = {
        "id": safe_id(
            str(
                campaign.get("id")
                or re.sub(r"[^a-z0-9]+", "-", _norm(name)).strip("-")
                or "campaign"
            )
        ),
        "name": name.strip(),
        "market": market,
        "track": track,
        "work_modes": _subset(campaign.get("work_modes"), "work_modes", WORK_MODES),
        "employment": _subset(campaign.get("employment"), "employment", EMPLOYMENT),
        "salary": salary,
        "active": campaign.get("active", True) is not False,
    }
    for key in LIST_FIELDS:
        value[key] = _strings(campaign.get(key), key)
    return value


def validate_all(campaigns: object) -> list[dict]:
    if not isinstance(campaigns, list):
        raise ValueError("campaigns must be a list")  # noqa: TRY004
    result = [validate(item) for item in campaigns]
    ids = [item["id"] for item in result]
    if len(ids) != len(set(ids)):
        raise ValueError("Campaign IDs must be unique")
    return result


def configured(settings: dict) -> list[dict]:
    try:
        return validate_all(settings.get("campaigns") or [])
    except ValueError:
        return []


def problem(settings: dict) -> str | None:
    """Why the stored campaigns are ignored, or None when they are valid."""
    try:
        validate_all(settings.get("campaigns") or [])
    except ValueError as error:
        return str(error)
    return None


def _criterion(name: str, status: str, basis: str) -> dict:
    return {"name": name, "status": status, "basis": basis}


def _value(conditions: dict, key: str) -> object:
    entry = conditions.get(key)
    return entry.get("value") if isinstance(entry, dict) else None


def match(
    vacancy: dict, campaign: dict, company: dict | None = None, country: str | None = None
) -> dict:
    """Compare one vacancy with one campaign. Only preferences; unknown stays unknown."""
    conditions = vacancy.get("conditions") or {}
    criteria = []
    title = _norm(vacancy.get("title"))

    market = vacancy.get("market") or "unknown"
    if campaign["market"] != "any":
        criteria.append(
            _criterion(
                "market",
                "unknown"
                if market == "unknown"
                else "match"
                if market == campaign["market"]
                else "mismatch",
                f"vacancy market: {market}",
            )
        )
    track = vacancy.get("target_track") or vacancy.get("role_family")
    if track in TRACKS:
        criteria.append(
            _criterion(
                "track",
                "match" if track == campaign["track"] else "mismatch",
                f"vacancy track: {track}",
            )
        )
    else:
        criteria.append(_criterion("track", "unknown", "vacancy track not recorded"))
    if campaign["role_titles"]:
        hit = next((role for role in campaign["role_titles"] if _contains(title, role)), None)
        criteria.append(
            _criterion(
                "role_titles",
                "match" if hit else "mismatch" if title else "unknown",
                f"title contains “{hit}”"
                if hit
                else "no configured role title in the vacancy title",
            )
        )
    if campaign["levels"]:
        level = _norm(
            (vacancy.get("level") or {}).get("raw")
            if isinstance(vacancy.get("level"), dict)
            else vacancy.get("level")
        )
        haystack = f"{level} {title}"
        hit = next((item for item in campaign["levels"] if _contains(haystack, item)), None)
        criteria.append(
            _criterion(
                "levels",
                "match" if hit else "unknown",
                f"level or title mentions “{hit}”"
                if hit
                else "level is not stated in a comparable form",
            )
        )
    if campaign["work_countries"]:
        wanted = {_norm(item) for item in campaign["work_countries"]}
        geography = conditions.get("allowed_geography") or {}
        mode = _value(conditions, "work_mode")
        listed = {_norm(item) for item in geography.get("countries") or []}
        if listed:
            status = "match" if listed & wanted else "mismatch"
            basis = f"allowed: {', '.join(geography.get('countries'))} ({geography.get('basis')})"
        elif mode in {"office", "hybrid"} and country and country != "unknown":
            status = "match" if _norm(country) in wanted else "mismatch"
            basis = f"{mode} work in {country}"
        else:
            status = "unknown"
            basis = (
                "remote without a country list"
                if mode == "remote"
                else "where the work may be done is not stated"
            )
        criteria.append(_criterion("work_countries", status, basis))
    for key, name in (("work_modes", "work_mode"), ("employment", "employment")):
        if not campaign[key]:
            continue
        stated = _value(conditions, name)
        criteria.append(
            _criterion(
                key,
                "unknown"
                if stated in (None, "unknown")
                else "match"
                if stated in campaign[key]
                else "mismatch",
                f"vacancy {name.replace('_', ' ')}: {stated or 'unknown'}",
            )
        )
    if campaign["languages"]:
        stated = _value(conditions, "language") or []
        wanted = set(campaign["languages"])
        criteria.append(
            _criterion(
                "languages",
                "unknown" if not stated else "match" if set(stated) <= wanted else "mismatch",
                f"required languages: {', '.join(stated)}"
                if stated
                else "language requirement not stated",
            )
        )
    wanted_salary = campaign.get("salary") or {}
    if wanted_salary.get("min") is not None:
        salary = conditions.get("salary") or {}
        top = salary.get("max") if salary.get("max") is not None else salary.get("min")
        if not salary:
            status, basis = "unknown", "salary not stated"
        elif (
            salary.get("currency") != wanted_salary["currency"]
            or salary.get("period") != wanted_salary["period"]
        ):
            status, basis = "unknown", "different currency or period; no conversion is assumed"
        elif top is None:
            status, basis = "unknown", "no amount in the stated range"
        else:
            status = "match" if top >= wanted_salary["min"] else "mismatch"
            basis = f"stated up to {top} {salary.get('currency')}/{salary.get('period')}"
        criteria.append(_criterion("salary", status, basis))
    if campaign["exclusions"]:
        text = _norm(
            " ".join(
                str(part)
                for part in (
                    vacancy.get("title"),
                    vacancy.get("text"),
                    (company or {}).get("about"),
                    " ".join((company or {}).get("business_areas") or []),
                )
            )
        )
        hit = next((item for item in campaign["exclusions"] if _contains(text, item)), None)
        criteria.append(
            _criterion(
                "exclusions",
                "mismatch" if hit else "match",
                f"mentions excluded “{hit}”"
                if hit
                else "no excluded term found in the stored text",
            )
        )
    statuses = {item["status"] for item in criteria}
    overall = (
        "mismatch" if "mismatch" in statuses else "unknown" if "unknown" in statuses else "match"
    )
    return {
        "campaign_id": campaign["id"],
        "campaign_name": campaign["name"],
        "status": overall,
        "criteria": criteria,
    }


def matches(
    settings: dict, vacancy: dict, company: dict | None = None, country: str | None = None
) -> list[dict]:
    return [
        match(vacancy, campaign, company, country)
        for campaign in configured(settings)
        if campaign["active"]
    ]


def upsert(settings: dict, campaign: dict) -> tuple[dict, dict | None]:
    """Return new settings with the campaign inserted or replaced, and the previous value."""
    value = validate(campaign)
    current = list(settings.get("campaigns") or [])
    previous = next((item for item in current if item.get("id") == value["id"]), None)
    updated = [item for item in current if item.get("id") != value["id"]] + [value]
    validate_all(updated)
    return {**settings, "campaigns": updated}, previous
