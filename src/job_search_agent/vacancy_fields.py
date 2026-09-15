"""Normalised vacancy conditions with their origin.

`conditions` keeps what a source actually states and marks everything else `unknown`:

* `salary` is the original range, currency, period and gross/net wording. A single
  amount appears only when the source gives one; no monthly figure is invented.
* `provider_conversion` holds a provider's recalculation (for example an aggregator's
  monthly USD estimate) separately from the employer's range.
* `work_mode`, `employment`, `language` carry `value` and `source`.
* `allowed_geography` says where the work may be done. "Remote" without a country list
  stays `unknown`: it does not prove that any particular country is allowed.
* `published_on` / `updated_on` / `valid_through` come from the source; discovery and
  verification dates live on the vacancy (`first_seen`, availability checks).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

METHOD = "conditions-v1"
UNKNOWN = "unknown"
WORK_MODES = ("remote", "hybrid", "office")
EMPLOYMENT = ("full_time", "part_time", "contract", "internship", "temporary")
CURRENCY_SYMBOLS = {
    "₽": "RUB",
    "руб": "RUB",
    "rub": "RUB",
    "rur": "RUB",
    "$": "USD",
    "usd": "USD",
    "€": "EUR",
    "eur": "EUR",
    "£": "GBP",
    "gbp": "GBP",
    "chf": "CHF",
    "aed": "AED",
    "₸": "KZT",
    "kzt": "KZT",
    "cad": "CAD",
    "aud": "AUD",
    "sgd": "SGD",
    "pln": "PLN",
}
PERIOD_WORDS = (
    ("hour", r"per hour|an hour|/\s*h(?:ou)?r\b|hourly|в час"),
    ("month", r"per month|a month|/\s*mo(?:nth)?\b|monthly|в месяц|/\s*мес|ежемесячно"),
    ("year", r"per year|a year|per annum|annual(?:ly)?|/\s*y(?:ea)?r\b|в год|годовой"),
)
NET_WORDS = r"на руки|после вычета|\bnet\b"
GROSS_WORDS = r"до вычета|\bgross\b|before tax"
LANGUAGE_NAMES = {
    "english": "en",
    "английский": "en",
    "russian": "ru",
    "русский": "ru",
    "german": "de",
    "немецкий": "de",
    "french": "fr",
    "французский": "fr",
    "spanish": "es",
    "испанский": "es",
    "chinese": "zh",
    "китайский": "zh",
    "mandarin": "zh",
    "japanese": "ja",
    "arabic": "ar",
}
REGION_WORDS = {
    "us": "United States",
    "usa": "United States",
    "united states": "United States",
    "uk": "United Kingdom",
    "united kingdom": "United Kingdom",
    "eu": "European Union",
    "europe": "Europe",
    "emea": "EMEA",
    "canada": "Canada",
    "germany": "Germany",
    "россия": "Russia",
    "россии": "Russia",
    "рф": "Russia",
    "russia": "Russia",
    "latam": "Latin America",
    "apac": "APAC",
}


def field(value: object = UNKNOWN, source: str | None = None, raw: object = None) -> dict:
    result = {"value": value if value not in (None, "") else UNKNOWN, "source": source}
    if raw not in (None, ""):
        result["raw"] = raw
    return result


def empty() -> dict:
    return {
        "method": METHOD,
        "salary": None,
        "provider_conversion": None,
        "work_mode": field(),
        "employment": field(),
        "language": field([]),
        "posting_language": UNKNOWN,
        "allowed_geography": {"status": UNKNOWN, "countries": [], "basis": None, "source": None},
        "published_on": None,
        "updated_on": None,
        "valid_through": None,
    }


def _number(text: str) -> float | None:
    text = text.strip().lower().replace(" ", " ").replace(" ", " ")
    multiplier = 1000 if text.endswith(("k", "к", "тыс")) else 1
    digits = re.sub(r"[^\d.,]", "", text)
    if not digits:
        return None
    # "150,000" and "150 000" are thousands; "1.5" with k is a decimal.
    if multiplier == 1000 and re.fullmatch(r"\d+[.,]\d", digits):
        digits = digits.replace(",", ".")
    else:
        digits = (
            digits.replace(",", "").replace(".", "")
            if re.search(r"[.,]\d{3}\b", digits)
            else digits.replace(",", ".")
        )
    try:
        value = float(digits) * multiplier
    except ValueError:
        return None
    return int(value) if value.is_integer() else value


def _currency(text: str) -> str | None:
    lowered = text.lower()
    for token, code in CURRENCY_SYMBOLS.items():
        if token in {"$", "€", "£", "₽", "₸"}:
            if token in text:
                return code
        elif re.search(rf"(?<![a-zа-я]){re.escape(token)}", lowered):
            return code
    return None


def _period(text: str) -> str:
    lowered = text.lower()
    for name, pattern in PERIOD_WORDS:
        if re.search(pattern, lowered):
            return name
    return UNKNOWN


def _gross_net(text: str) -> str:
    lowered = text.lower()
    if re.search(NET_WORDS, lowered):
        return "net"
    if re.search(GROSS_WORDS, lowered):
        return "gross"
    return UNKNOWN


AMOUNT = r"[$€£₽₸]?\s?\d[\d\s  .,]*\s?(?:k|к|тыс\.?)?"
SALARY_LINE = re.compile(
    rf"(?ix)"
    rf"(?:(?:от|from)\s*)?(?P<low>{AMOUNT})"
    rf"(?:\s*(?:[A-Za-z]{{3}}|руб\.?)?\s*(?:[-–—]|до|to)\s*(?P<high>{AMOUNT}))?"
)


def salary_from_text(text: str, source: str) -> dict | None:
    """Parse one explicit salary statement; returns None unless a currency is stated."""
    if not isinstance(text, str) or not text.strip():
        return None
    snippet = re.sub(r"\s+", " ", text.strip())[:300]
    currency = _currency(snippet)
    if not currency:
        return None
    upper_only = re.search(r"(?i)(?:^|\s)(?:до|up to)\s*[$€£₽₸]?\s?\d", snippet)
    lower_only = re.search(r"(?i)(?:^|\s)(?:от|from)\s*[$€£₽₸]?\s?\d", snippet)
    match = next(
        (m for m in SALARY_LINE.finditer(snippet) if (_number(m.group("low") or "") or 0) >= 100),
        None,
    )
    if not match:
        return None
    low, high = _number(match.group("low")), _number(match.group("high") or "")
    if upper_only and high is None:
        low, high = None, low
    elif high is None and not lower_only:
        high = low  # a single stated amount
    if low is not None and high is not None and low > high:
        low, high = high, low
    if (low or 0) < 100 and (high or 0) < 100:
        return None
    return {
        "min": low,
        "max": high,
        "currency": currency,
        "period": _period(snippet),
        "gross_net": _gross_net(snippet),
        "raw": snippet,
        "source": source,
    }


def posting_language(text: str) -> str:
    letters = re.findall(r"[a-zA-Zа-яА-ЯёЁ]", text or "")
    if len(letters) < 40:
        return UNKNOWN
    cyrillic = sum(1 for char in letters if re.match(r"[а-яА-ЯёЁ]", char))
    return "ru" if cyrillic / len(letters) > 0.5 else "en"


def languages_from_text(text: str) -> list[str]:
    """Languages that the posting explicitly requires (a named language near a requirement word)."""
    found = []
    for sentence in re.split(r"(?<=[.;!?\n])", text or ""):
        lowered = sentence.lower()
        if not re.search(
            r"fluen|proficien|required|must|native|business|working knowledge|level|владение|знание|уровн|свободн",
            lowered,
        ):
            continue
        for name, code in LANGUAGE_NAMES.items():
            if re.search(rf"\b{name}\b", lowered) and code not in found:
                found.append(code)
    return found


def work_mode_from_text(*texts: str) -> tuple[str, str | None]:
    joined = " ".join(value for value in texts if isinstance(value, str)).lower()
    if re.search(r"\bhybrid\b|гибрид", joined):
        return "hybrid", "hybrid"
    if re.search(r"\bremote\b|удал[её]нн|remote-first|fully remote|work from home", joined):
        return "remote", "remote"
    if re.search(r"\bon-?site\b|in office|office-based|в офисе|офис\b", joined):
        return "office", "office"
    return UNKNOWN, None


def geography_from_text(text: str) -> dict | None:
    """Explicit statements such as "Remote (US only)" or "must be based in the EU"."""
    patterns = (
        r"(?i)remote\s*[\(\-–—,:]\s*(?P<region>[A-Za-z .]{2,30}?)\s*(?:only|based)?\s*\)",
        r"(?i)(?P<region>[A-Za-z .]{2,20}?)[- ]only\b",
        r"(?i)(?:must|should)\s+(?:be\s+)?(?:based|located|resid\w*)\s+in\s+(?:the\s+)?(?P<region>[A-Za-z .]{2,30})",
        r"(?i)(?:удал[её]нно|remote)\s+(?:из|from|within)\s+(?P<region>[A-Za-zА-Яа-яё .]{2,30})",
    )
    for pattern in patterns:
        match = re.search(pattern, text or "")
        if not match:
            continue
        region = match.group("region").strip(" .").lower()
        names = [
            value
            for key, value in REGION_WORDS.items()
            if re.fullmatch(rf"(?:the\s+)?{key}", region)
        ]
        if names:
            return {
                "status": "listed",
                "countries": names,
                "basis": match.group(0).strip()[:200],
                "source": "posting_text",
            }
    return None


def _date(value: object) -> str | None:
    if isinstance(value, (int, float)) and value > 10**11:  # epoch milliseconds (Lever)
        return datetime.fromtimestamp(value / 1000, UTC).date().isoformat()
    if isinstance(value, str) and re.match(r"\d{4}-\d{2}-\d{2}", value):
        return value[:10]
    return None


def _employment(value: object) -> str:
    text = " ".join(value) if isinstance(value, list) else str(value or "")
    text = text.lower().replace("-", "_").replace(" ", "_")
    for pattern, name in (
        (r"full|полная", "full_time"),
        (r"part|частичная", "part_time"),
        (r"contract|contractor|project|проектная|freelance", "contract"),
        (r"intern|стаж", "internship"),
        (r"temporary|temp\b|seasonal", "temporary"),
    ):
        if re.search(pattern, text):
            return name
    return UNKNOWN


def _mode(value: object) -> str:
    text = str(value or "").lower()
    if re.search(r"hybrid|гибрид", text):
        return "hybrid"
    if re.search(r"remote|telecommute|удал", text):
        return "remote"
    if re.search(r"on_?-?site|onsite|office|fullday|full_day|полный день|in_person", text):
        return "office"
    return UNKNOWN


def _country_list(requirements: object) -> list[str]:
    items = requirements if isinstance(requirements, list) else [requirements]
    names = []
    for item in items:
        name = item.get("name") if isinstance(item, dict) else item
        if isinstance(name, str) and name.strip() and name.strip() not in names:
            names.append(name.strip())
    return names


def _finalize(result: dict, text: str, location: str) -> dict:
    """Fill gaps from the posting text without overriding structured values."""
    if result["salary"] is None:
        for line in (text or "").splitlines()[:400]:
            if re.search(
                r"(?i)salary|compensation|pay range|зарплат|оклад|доход|вознаграждение", line
            ):
                parsed = salary_from_text(line, "posting_text")
                if parsed:
                    result["salary"] = parsed
                    break
    if result["work_mode"]["value"] == UNKNOWN:
        mode, raw = work_mode_from_text(location)
        if mode != UNKNOWN:
            result["work_mode"] = field(mode, "location", raw)
    if not result["language"]["value"]:
        languages = languages_from_text(text)
        if languages:
            result["language"] = field(languages, "posting_text")
    result["posting_language"] = posting_language(text)
    if result["allowed_geography"]["status"] == UNKNOWN:
        stated = geography_from_text(" ".join([location or "", (text or "")[:20000]]))
        if stated:
            result["allowed_geography"] = stated
    return result


def from_provider(provider: str, item: dict, text: str = "", location: str = "") -> dict:
    """Conditions from one raw provider item (HH, Greenhouse, Lever, Ashby, JSON-LD)."""
    result = empty()
    if provider == "hh":
        salary = item.get("salary_range") or item.get("salary")
        if isinstance(salary, dict) and (salary.get("from") or salary.get("to")):
            mode = (
                (salary.get("mode") or {}).get("id")
                if isinstance(salary.get("mode"), dict)
                else None
            )
            result["salary"] = {
                "min": salary.get("from"),
                "max": salary.get("to"),
                "currency": "RUB"
                if salary.get("currency") in {"RUR", "RUB"}
                else salary.get("currency"),
                "period": {"MONTH": "month", "HOUR": "hour", "YEAR": "year"}.get(
                    mode or "", UNKNOWN
                ),
                "gross_net": {True: "gross", False: "net"}.get(salary.get("gross"), UNKNOWN),
                "raw": {key: salary.get(key) for key in ("from", "to", "currency", "gross")},
                "source": "hh.salary",
            }
        formats = [
            entry.get("id") for entry in item.get("work_format") or [] if isinstance(entry, dict)
        ]
        schedule = (
            (item.get("schedule") or {}).get("id")
            if isinstance(item.get("schedule"), dict)
            else None
        )
        raw_mode = (
            formats[0] if len(formats) == 1 else ("HYBRID" if "HYBRID" in formats else schedule)
        )
        if raw_mode:
            result["work_mode"] = field(
                _mode(raw_mode), "hh.work_format" if formats else "hh.schedule", raw_mode
            )
        employment = item.get("employment_form") or item.get("employment")
        if isinstance(employment, dict) and employment.get("id"):
            result["employment"] = field(
                _employment(employment["id"]), "hh.employment", employment["id"]
            )
        languages = [
            LANGUAGE_NAMES.get(
                str(entry.get("name", "")).lower(), str(entry.get("id") or entry.get("name"))
            )
            for entry in item.get("languages") or []
            if isinstance(entry, dict)
        ]
        if languages:
            result["language"] = field(languages, "hh.languages")
        result["published_on"] = _date(item.get("published_at"))
        if (
            isinstance(item.get("area"), dict)
            and item["area"].get("name")
            and raw_mode
            and _mode(raw_mode) != "remote"
        ):
            result["allowed_geography"] = {
                "status": "office_location",
                "countries": [],
                "basis": item["area"]["name"],
                "source": "hh.area",
            }
    elif provider == "greenhouse":
        result["updated_on"] = _date(item.get("updated_at"))
        result["published_on"] = _date(item.get("first_published"))
    elif provider == "lever":
        categories = item.get("categories") or {}
        if categories.get("commitment"):
            result["employment"] = field(
                _employment(categories["commitment"]), "lever.commitment", categories["commitment"]
            )
        if item.get("workplaceType"):
            result["work_mode"] = field(
                _mode(item["workplaceType"]), "lever.workplaceType", item["workplaceType"]
            )
        salary = item.get("salaryRange")
        if isinstance(salary, dict) and (salary.get("min") or salary.get("max")):
            interval = str(salary.get("interval") or "")
            result["salary"] = {
                "min": salary.get("min"),
                "max": salary.get("max"),
                "currency": salary.get("currency"),
                "period": next(
                    (name for name in ("hour", "month", "year") if name in interval), UNKNOWN
                ),
                "gross_net": UNKNOWN,
                "raw": salary,
                "source": "lever.salaryRange",
            }
        result["published_on"] = _date(item.get("createdAt"))
    elif provider == "ashby":
        if item.get("employmentType"):
            result["employment"] = field(
                _employment(item["employmentType"]), "ashby.employmentType", item["employmentType"]
            )
        if item.get("workplaceType"):
            result["work_mode"] = field(
                _mode(item["workplaceType"]), "ashby.workplaceType", item["workplaceType"]
            )
        elif item.get("isRemote") is True:
            result["work_mode"] = field("remote", "ashby.isRemote", True)
        compensation = item.get("compensation") or {}
        for component in compensation.get("summaryComponents") or []:
            if not isinstance(component, dict) or component.get("compensationType") != "Salary":
                continue
            interval = str(component.get("interval") or "").lower()
            result["salary"] = {
                "min": component.get("minValue"),
                "max": component.get("maxValue"),
                "currency": component.get("currencyCode"),
                "period": next(
                    (name for name in ("hour", "month", "year") if name in interval), UNKNOWN
                ),
                "gross_net": UNKNOWN,
                "raw": compensation.get("compensationTierSummary") or component,
                "source": "ashby.compensation",
            }
            break
        result["published_on"] = _date(item.get("publishedAt"))
    elif provider in {"corporate", "jsonld"}:
        salary = item.get("baseSalary")
        if isinstance(salary, dict):
            value = (
                salary.get("value")
                if isinstance(salary.get("value"), dict)
                else {"value": salary.get("value")}
            )
            low = value.get("minValue", value.get("value"))
            high = value.get("maxValue", value.get("value"))
            if low or high:
                unit = str(value.get("unitText") or "").lower()
                result["salary"] = {
                    "min": low,
                    "max": high,
                    "currency": salary.get("currency"),
                    "period": next(
                        (name for name in ("hour", "month", "year") if name in unit), UNKNOWN
                    ),
                    "gross_net": UNKNOWN,
                    "raw": salary,
                    "source": "jsonld.baseSalary",
                }
        if item.get("employmentType"):
            result["employment"] = field(
                _employment(item["employmentType"]), "jsonld.employmentType", item["employmentType"]
            )
        if str(item.get("jobLocationType", "")).upper() == "TELECOMMUTE":
            result["work_mode"] = field("remote", "jsonld.jobLocationType", item["jobLocationType"])
        countries = _country_list(item.get("applicantLocationRequirements"))
        if countries:
            result["allowed_geography"] = {
                "status": "listed",
                "countries": countries,
                "basis": "applicantLocationRequirements",
                "source": "jsonld",
            }
        result["published_on"] = _date(item.get("datePosted"))
        result["valid_through"] = _date(item.get("validThrough"))
    return _finalize(result, text, location)


def from_aggregate(item: dict) -> dict:
    """LinkedIn Salaries: provider labels and a provider conversion, never an employer offer."""
    result = empty()
    if isinstance(item.get("salaryCite"), str) and item["salaryCite"].strip():
        result["salary"] = salary_from_text(item["salaryCite"], "linkedinsalaries.salaryCite")
    amount = item.get("salaryUsdMo")
    if isinstance(amount, (int, float)) and not isinstance(amount, bool) and amount > 0:
        result["provider_conversion"] = {
            "amount": amount,
            "currency": "USD",
            "period": "month",
            "provider": "linkedinsalaries.com",
            "note": "provider recalculation, not an employer offer",
        }
    if item.get("jobMode"):
        result["work_mode"] = field(
            _mode(item["jobMode"]), "linkedinsalaries.jobMode", item["jobMode"]
        )
    if item.get("jobTime"):
        result["employment"] = field(
            _employment(item["jobTime"]), "linkedinsalaries.jobTime", item["jobTime"]
        )
    result["published_on"] = _date(item.get("dayKey"))
    return result


def from_posting(
    text: str, meta: dict | None = None, location: str = "", source: str = "posting"
) -> dict:
    """Conditions from a retained posting or pasted text with optional header fields."""
    result = empty()
    meta = meta or {}
    if meta.get("salary"):
        result["salary"] = salary_from_text(meta["salary"], f"{source}.salary")
    for key in ("employment", "schedule"):
        if meta.get(key):
            mode = _mode(meta[key])
            if key == "schedule" and mode != UNKNOWN:
                result["work_mode"] = field(mode, f"{source}.{key}", meta[key])
            employment = _employment(meta[key])
            if key == "employment" and employment != UNKNOWN:
                result["employment"] = field(employment, f"{source}.{key}", meta[key])
    for key in ("posted", "date"):
        if meta.get(key) and not result["published_on"]:
            result["published_on"] = _date(meta[key])
    return _finalize(result, text, location or meta.get("location", ""))


def merge(old: dict | None, new: dict | None) -> dict | None:
    """Known values win over unknown ones; a newer known value replaces an older one."""
    if not old:
        return new
    if not new:
        return old
    merged = {**old}
    for key, value in new.items():
        previous = old.get(key)
        if isinstance(value, dict) and "value" in value:
            if value["value"] not in (UNKNOWN, [], None) or not previous:
                merged[key] = value
        elif key == "allowed_geography":
            if value.get("status") != UNKNOWN or not previous:
                merged[key] = value
        elif value not in (None, UNKNOWN):
            merged[key] = value
    return merged


def changed_fields(old: dict | None, new: dict | None) -> list[str]:
    old, new = old or {}, new or {}
    return sorted(
        key for key in set(old) | set(new) if key != "method" and old.get(key) != new.get(key)
    )
