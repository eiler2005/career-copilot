"""Profile relevance: does a vacancy belong to this candidate's search at all?

Relevance is the first, cheap screen. It reads the vacancy title and stored text and
answers four questions, each with the words that decided it:

1. *Function* — does the title name a function of one of the candidate's tracks
   (product; technical leadership)? "Office manager" or "Sales director" does not.
2. *Level* — is the title at the target level (director, head, VP, chief …), below it
   (senior manager, specialist, project manager) or not stated?
3. *Domain* — which of the candidate's domains (derived from verified CV facts and
   policy interests: AI, payments, platforms, developer tools …) appear in the title
   or text?
4. *Queries* — which saved keyword queries (``engineer + ai``) match?

The result is a tier — ``strong``, ``possible``, ``weak`` or ``off_profile`` — with
reasons. It is a search screen, not a qualification judgment: the requirement matrix
in ``matching.py`` and the preferences in ``campaigns.py`` stay separate, and nothing
here changes facts, assessments or availability.
"""

from __future__ import annotations

import re
import unicodedata

from .core import TRACKS, digest

TIERS = ("strong", "possible", "weak", "off_profile")
RELEVANT = frozenset({"strong", "possible"})

# Function words per track, matched in the title only.
DEFAULT_ROLES = {
    "product": [
        "product",
        "cpo",
        "pmt",
        "продукт",
        "продуктов",
    ],
    "technical-leadership": [
        "engineering",
        "engineer",
        "technology",
        "technical",
        "tech",
        "cto",
        "cio",
        "caio",
        "software",
        "software development",
        "product development",
        "front end",
        "frontend",
        "backend",
        "devops",
        "infrastructure",
        "security",
        "machine learning",
        "platform",
        "architecture",
        "it",
        "ai",
        "data",
        "digital",
        "разработ",
        "инженер",
        "технолог",
        "ит",
        "платформ",
        "архитект",
        "цифров",
        "ии",
        "искусствен",
    ],
}

# Level words in the title. A top word wins; otherwise a "below" word beats a lead word,
# so "Руководитель проектов" and "Lead Product Manager" are below a director target.
DEFAULT_LEVELS = {
    "top": [
        "director",
        "head",
        "vp",
        "svp",
        "evp",
        "vice president",
        "chief",
        "cpo",
        "cto",
        "cio",
        "caio",
        "директор",
        "директора",
        # Russian titles where "руководитель" heads a whole function or unit.
        "руководитель разработки",
        "руководителя разработки",
        "руководитель департамента",
        "руководитель управления",
        "руководитель дирекции",
        "руководитель центра",
        "руководитель блока",
        "руководитель практики",
        "руководитель подразделения",
        "начальник управления",
        "начальник департамента",
    ],
    "lead": ["руководител", "lead", "principal", "group", "начальник", "partner"],
    # One level below director. Checked before "below" only where a market's target level is
    # `near`, so "Engineering Manager" or "Staff Product Manager" count there and nowhere else.
    "near": [
        "engineering manager",
        "senior engineering manager",
        "software engineering manager",
        "senior manager",
        "group product manager",
        "lead product manager",
        "product lead",
        "staff",
        "principal",
    ],
    "below": [
        "senior",
        "manager",
        "менеджер",
        "specialist",
        "специалист",
        "analyst",
        "аналитик",
        "junior",
        "middle",
        "intern",
        "стажер",
        "assistant",
        "ассистент",
        "coordinator",
        "координатор",
        "руководитель проект",
        "руководителя проект",
        "owner",
    ],
    # Individual-contributor titles, matched as whole words: "Staff AI Engineer" is not
    # "Director of Engineering".
    "individual": [
        "engineer",
        "engineers",
        "developer",
        "developers",
        "programmer",
        "scientist",
        "researcher",
        "staff",
        "инженер",
        "разработчик",
        "программист",
    ],
}

# Program and project leadership titles. They count as a technical-leadership function only
# at top companies (policy.bigtech_company_ids plus relevance.top_companies) outside Russia,
# where the level is then mapped by the employer's own ladder.
DEFAULT_PROGRAM_ROLES = [
    "technical program manager",
    "program manager",
    "programme manager",
    "project manager",
    "program lead",
    "project lead",
    "tpm",
]

TARGET_LEVELS = ("top", "near", "lead", "any")

# Phrases removed from the title before the function check, so a banking "product" (a loan
# or a card) is not read as product management. Regular expressions on normalised text.
DEFAULT_IGNORE_IN_TITLE = [
    r"продукт\w* (?:для )?банк\w*",
    r"(?:банковск|кредитн|страхов|депозитн|инвестиционн|розничн|ипотечн)\w* продукт\w*",
    r"(?:banking|credit|loan|lending|insurance|deposit|mortgage|investment|financial) products?",
]

# Score bands of the thermometer; hard rules cap a score inside a lower band.
BANDS = (("strong", 70), ("possible", 50), ("weak", 0))
OFF_PROFILE_CAP = 20
BELOW_TARGET_CAP = 49

# Titles whose level is employer-specific at big-tech companies (Senior PM can be L6).
COMPANY_SPECIFIC = {"senior", "staff", "principal", "manager", "lead", "group", "owner"}

# Functions that are never this candidate's search, matched in the title only.
DEFAULT_EXCLUDE_TITLE = [
    "sales",
    "marketing",
    "designer",
    "design",
    "recruit",
    "talent acquisition",
    "people partner",
    "human resources",
    "account executive",
    "account manager",
    "office manager",
    "operating officer",
    "accountant",
    "lawyer",
    "legal counsel",
    "chief commercial",
    "cco",
    "коммерческий директор",
    "продаж",
    "маркетинг",
    "дизайн",
    "рекрут",
    "подбор персонал",
    "офис",
    "бухгалт",
    "кассир",
    "водител",
    "учител",
    "преподават",
    "врач",
    "юрист",
    "торгов",
    "склад",
]

# Domain vocabulary. A group is active for the candidate when its id or one of its
# aliases appears in fact tags or policy interests (or when listed in settings).
DOMAINS = {
    "ai": {
        "aliases": ["ai", "genai", "nlp", "machine learning", "agents"],
        "terms": [
            "ai",
            "genai",
            "gen ai",
            "generative",
            "llm",
            "machine learning",
            "ml",
            "agent",
            "agentic",
            "artificial intelligence",
            "nlp",
            "ии",
            "искусствен",
            "нейросет",
            "машинн обучен",
            "генеративн",
        ],
    },
    "payments": {
        "aliases": ["payments", "fintech", "cbdc", "banking"],
        "terms": [
            "payment",
            "payments",
            "fintech",
            "banking",
            "cbdc",
            "iso 20022",
            "acquiring",
            "платеж",
            "финтех",
            "эквайринг",
            "цифровой рубль",
        ],
    },
    "platforms": {
        "aliases": ["platforms", "enterprise platforms", "on-premise"],
        "terms": [
            "platform",
            "platforms",
            "enterprise",
            "saas",
            "cloud",
            "платформ",
            "облач",
            "корпоративн",
        ],
    },
    "developer-tools": {
        "aliases": ["developer-tools", "developer-platform", "api", "developer tools"],
        "terms": [
            "api",
            "apis",
            "developer",
            "sdk",
            "devtools",
            "developer experience",
            "open source",
            "разработчик",
        ],
    },
    "commercialisation": {
        "aliases": ["commercialisation", "commercialization", "pnl", "p&l"],
        "terms": [
            "commercial",
            "revenue",
            "monetization",
            "monetisation",
            "go to market",
            "gtm",
            "p&l",
            "pnl",
            "коммерциал",
            "монетизац",
            "выручк",
        ],
    },
    "engineering-management": {
        "aliases": ["engineering-management", "engineering leadership", "leadership"],
        "terms": [
            "engineering organization",
            "engineering organisation",
            "engineering teams",
            "engineering leadership",
            "engineering managers",
            "команды разработки",
            "руководство разработкой",
        ],
    },
    "industrial": {
        "aliases": ["industrial", "industrial technology", "robotics"],
        "terms": [
            "industrial",
            "robotics",
            "manufacturing",
            "промышлен",
            "робот",
            "производствен",
        ],
    },
}

TEXT_LIMIT = 40_000


def norm(value: object) -> str:
    """Casefolded text with separators turned into spaces, so AI/ML reads as "ai ml"."""
    text = unicodedata.normalize("NFKC", str(value or "")).casefold().replace("ё", "е")
    text = re.sub(r"[/_\-–—·•|()\[\],;:!?\"'«»]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _pattern(term: str, whole: bool = False) -> re.Pattern:
    """Short terms match whole words; longer ones also match word endings (инженер-а)."""
    term = norm(term)
    tail = r"(?!\w)" if whole or len(term) <= 3 else ""
    return re.compile(rf"(?<!\w){re.escape(term)}{tail}")


def found(text: str, terms: list[str], whole: bool = False) -> list[str]:
    """Terms present in already normalised text, in configuration order."""
    return [term for term in terms if term.strip() and _pattern(term, whole).search(text)]


# --------------------------------------------------------------------------- queries


# Field prefixes a query group may start with; Russian aliases for the same fields.
FIELDS = ("title", "company", "location", "text")
FIELD_ALIASES = {
    "title": "title",
    "role": "title",
    "должность": "title",
    "название": "title",
    "company": "company",
    "компания": "company",
    "location": "location",
    "локация": "location",
    "где": "location",
    "text": "text",
    "tech": "text",
    "текст": "text",
    "стек": "text",
}
_PREFIX = re.compile(r"^\s*([^\W\d_]+)\s*:", re.UNICODE)


def parse_query(query: str) -> dict:
    """Parse ``company:(sber | сбер) + title:(директор | head) + (ai | ии) - crypto``.

    ``+`` joins groups that must all match, ``|`` or ``,`` separates alternatives in a
    group, and groups after `` -`` exclude the vacancy. A group may start with a field —
    ``title:``, ``company:``, ``location:`` or ``text:`` (Russian aliases
    ``должность:``, ``компания:``, ``локация:``/``где:``, ``текст:``/``стек:``) — to be
    looked up there only; a group without a field is looked up in all of them.
    Parentheses are optional and a term with spaces is a phrase.
    """
    if not isinstance(query, str) or not query.strip() or len(query) > 300:
        raise ValueError("A query is a non-empty string of up to 300 characters")
    parts = re.split(r"(?:^|\s)-(?=\s*\S)", query.strip())

    def group(chunk: str) -> dict | None:
        field = "any"
        prefix = _PREFIX.match(chunk)
        if prefix and prefix.group(1).casefold() in FIELD_ALIASES:
            field, chunk = FIELD_ALIASES[prefix.group(1).casefold()], chunk[prefix.end() :]
        terms = [
            norm(item)
            for item in re.split(r"[|,]", chunk.replace("(", " ").replace(")", " "))
            if norm(item)
        ]
        return {"field": field, "terms": terms} if terms else None

    groups = [item for chunk in parts[0].split("+") if (item := group(chunk))]
    excluded = [item for chunk in parts[1:] if (item := group(chunk))]
    if not groups:
        raise ValueError("A query needs at least one term to include")
    return {"all_of": groups, "none_of": excluded}


def match_query(parsed: dict, fields: dict[str, str]) -> dict:
    """Which alternative satisfied each group; ``matched`` only when all do and none excludes.

    ``fields`` maps ``title``, ``company``, ``location`` and ``text`` to text already
    normalised with :func:`norm` (see :func:`search_fields`); a missing field is empty.
    """
    everything = " ".join(fields.get(name, "") for name in FIELDS)

    def where(item: dict) -> str:
        return everything if item["field"] == "any" else fields.get(item["field"], "")

    hits = []
    for item in parsed["all_of"]:
        hit = next(iter(found(where(item), item["terms"])), None)
        if hit is None:
            return {"matched": False, "terms": hits, "missing": item["terms"]}
        hits.append(hit)
    blocked = [term for item in parsed["none_of"] for term in found(where(item), item["terms"])]
    return {"matched": not blocked, "terms": hits, "excluded_by": blocked}


# --------------------------------------------------------------------------- configuration


def _strings(value: object, name: str, limit: int = 200) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > limit:
        raise ValueError(f"{name} must be a list of up to {limit} strings")
    items = []
    for item in value:
        if not isinstance(item, str) or not item.strip() or len(item) > 80:
            raise ValueError(f"{name} must contain short non-empty strings")
        items.append(item.strip())
    return items


def validate(config: object) -> dict:
    """Normalise ``settings.json -> relevance``; raises ValueError with a readable message."""
    if config is None:
        config = {}
    if not isinstance(config, dict):
        raise ValueError("relevance must be an object")  # noqa: TRY004
    roles = config.get("roles") or {}
    if not isinstance(roles, dict):
        raise ValueError("relevance.roles must map a track to title words")  # noqa: TRY004
    levels = config.get("levels") or {}
    if not isinstance(levels, dict) or not set(levels) <= {
        "top",
        "near",
        "lead",
        "below",
        "individual",
    }:
        raise ValueError("relevance.levels accepts top, near, lead, below and individual lists")
    target = config.get("target_level", "lead")
    if target not in TARGET_LEVELS:
        raise ValueError("relevance.target_level must be top, near, lead or any")
    market_levels = config.get("market_levels") or {}
    if not isinstance(market_levels, dict) or any(
        not isinstance(market, str) or value not in TARGET_LEVELS
        for market, value in market_levels.items()
    ):
        raise ValueError("relevance.market_levels maps a market to top, near, lead or any")
    vocabulary = config.get("vocabulary") or {}
    if not isinstance(vocabulary, dict):
        raise ValueError("relevance.vocabulary must map a domain to terms")  # noqa: TRY004
    ignore = _strings(config.get("ignore_in_title"), "relevance.ignore_in_title", 40)
    for pattern in ignore:
        try:
            re.compile(pattern)
        except re.error as error:
            raise ValueError(f"relevance.ignore_in_title has an invalid pattern: {error}") from None
    queries = []
    for index, item in enumerate(config.get("queries") or []):
        if not isinstance(item, dict):
            raise ValueError("Each relevance query is an object with a query string")  # noqa: TRY004
        parsed = parse_query(item.get("query"))
        name = str(item.get("name") or item["query"]).strip()[:80]
        queries.append(
            {
                "id": re.sub(r"[^a-z0-9]+", "-", norm(item.get("id") or name)).strip("-")
                or f"query-{index + 1}",
                "name": name,
                "query": item["query"].strip(),
                "include": item.get("include", False) is True,
                "parsed": parsed,
            }
        )
    return {
        "roles": {
            track: _strings(words, f"relevance.roles.{track}") for track, words in roles.items()
        },
        "levels": {key: _strings(levels.get(key), f"relevance.levels.{key}") for key in levels},
        "target_level": target,
        "market_levels": dict(market_levels),
        "top_companies": _strings(config.get("top_companies"), "relevance.top_companies", 100),
        "program_roles": _strings(config.get("program_roles"), "relevance.program_roles"),
        "exclude_title": _strings(config.get("exclude_title"), "relevance.exclude_title"),
        "ignore_in_title": ignore,
        "domains": _strings(config.get("domains"), "relevance.domains", 40),
        "vocabulary": {
            key: _strings(terms, f"relevance.vocabulary.{key}") for key, terms in vocabulary.items()
        },
        "queries": queries,
        "extend_defaults": config.get("extend_defaults", True) is not False,
    }


def problem(settings: dict) -> str | None:
    try:
        validate(settings.get("relevance"))
    except ValueError as error:
        return str(error)
    return None


def active_domains(settings: dict, facts: dict | None, config: dict) -> dict[str, list[str]]:
    """Domain groups this candidate targets: explicit list, else fact tags and interests."""
    vocabulary = {key: list(value["terms"]) for key, value in DOMAINS.items()}
    for key, terms in config["vocabulary"].items():
        vocabulary[key] = [*vocabulary.get(key, []), *terms] if config["extend_defaults"] else terms
    if config["domains"]:
        return {key: vocabulary[key] for key in config["domains"] if key in vocabulary}
    items = (facts or {}).get("facts") if isinstance(facts, dict) else None
    signals = {
        norm(tag)
        for fact in items or []
        if isinstance(fact, dict) and fact.get("verification") != "conflicting"
        for tag in fact.get("tags") or []
    }
    interests = norm(" ".join(map(str, (settings.get("policy") or {}).get("interests") or [])))
    chosen = {}
    for key, terms in vocabulary.items():
        aliases = [key, *DOMAINS.get(key, {}).get("aliases", [])]
        if key in config["vocabulary"] or any(
            norm(alias) in signals or _pattern(alias).search(interests) for alias in aliases
        ):
            chosen[key] = terms
    return chosen


def domain_support(facts: dict | None, domains: dict) -> dict[str, dict]:
    """How much of the candidate's CV stands behind each domain.

    A verified fact counts 1, a self-reported one 0.5; conflicting facts and targets
    (aspirations) do not count. ``weight`` saturates at two points of support.
    """
    items = (facts or {}).get("facts") if isinstance(facts, dict) else None
    result = {}
    for key in domains:
        aliases = {norm(alias) for alias in [key, *DOMAINS.get(key, {}).get("aliases", [])]}
        count, points = 0, 0.0
        for fact in items or []:
            if (
                not isinstance(fact, dict)
                or fact.get("verification") == "conflicting"
                or fact.get("claim_type") == "target"
                or not aliases & {norm(tag) for tag in fact.get("tags") or []}
            ):
                continue
            count += 1
            points += 1.0 if fact.get("verification") == "verified" else 0.5
        result[key] = {"facts": count, "weight": round(min(1.0, points / 2), 2)}
    return result


def _merged(defaults: dict | list, custom: dict | list, extend: bool) -> dict | list:
    if isinstance(defaults, list):
        return [*defaults, *custom] if extend else (custom or defaults)
    result = {key: list(value) for key, value in defaults.items()}
    for key, value in custom.items():
        result[key] = [*result.get(key, []), *value] if extend else value
    return result


def profile(settings: dict, facts: dict | None = None) -> dict:
    """Everything the screen needs, resolved once per run."""
    config = validate(settings.get("relevance"))
    extend = config["extend_defaults"]
    policy = settings.get("policy") or {}
    tracks = [track for track in policy.get("tracks") or DEFAULT_ROLES if track]
    roles = _merged(DEFAULT_ROLES, config["roles"], extend)
    return {
        "roles": {track: roles.get(track, []) for track in tracks},
        "levels": _merged(DEFAULT_LEVELS, config["levels"], extend),
        "target_level": config["target_level"],
        "market_levels": config["market_levels"],
        "russia_top_only": bool(policy.get("russia_director_only")),
        "exclude_title": _merged(DEFAULT_EXCLUDE_TITLE, config["exclude_title"], extend),
        "exclude_text": [str(item) for item in policy.get("exclude") or [] if str(item).strip()],
        # Top companies: employer-specific level ladders, and program roles abroad.
        "company_specific_levels": list(
            dict.fromkeys(
                [
                    *(str(item) for item in policy.get("bigtech_company_ids") or []),
                    *config["top_companies"],
                ]
            )
        ),
        "program_roles": _merged(DEFAULT_PROGRAM_ROLES, config["program_roles"], extend),
        "domains": (domains := active_domains(settings, facts, config)),
        "support": domain_support(facts, domains),
        "ignore_in_title": _merged(DEFAULT_IGNORE_IN_TITLE, config["ignore_in_title"], extend),
        "queries": config["queries"],
    }


# --------------------------------------------------------------------------- screening


def search_fields(
    vacancy: dict, extra_text: str = "", company: str = "", location: str = ""
) -> dict[str, str]:
    """Normalised title, company, location and text that queries look in.

    ``company`` adds the employer name and aliases from the company record; ``location``
    adds a display location (country, city). The vacancy's own location, work mode and
    allowed countries are always included.
    """
    conditions = vacancy.get("conditions") if isinstance(vacancy.get("conditions"), dict) else {}
    work_mode = conditions.get("work_mode") if isinstance(conditions.get("work_mode"), dict) else {}
    geography = conditions.get("allowed_geography") or {}
    place = vacancy.get("location")
    places = [
        place if isinstance(place, str) else " ".join(map(str, (place or {}).values())),
        str(work_mode.get("value") or ""),
        " ".join(map(str, geography.get("countries") or [])),
        location,
    ]
    return {
        "title": norm(vacancy.get("title")),
        "company": norm(f"{vacancy.get('company_name') or ''} {company}"),
        "location": norm(" ".join(places)),
        "text": vacancy_text(vacancy, extra_text),
    }


def vacancy_text(vacancy: dict, extra: str = "") -> str:
    parts = [vacancy.get("text") if isinstance(vacancy.get("text"), str) else ""]
    for requirement in vacancy.get("requirements") or []:
        if isinstance(requirement, dict) and isinstance(requirement.get("text"), str):
            parts.append(requirement["text"])
    parts.append(extra or "")
    return norm(" ".join(parts))[:TEXT_LIMIT]


def _level(title: str, levels: dict, near: bool = False) -> tuple[str, list[str]]:
    """Title level. With ``near`` (a market that accepts one level below director) the
    near words are read before the "below" ones, so "Engineering Manager" is not "manager"."""
    top = found(title, levels.get("top", []))
    if top:
        return "top", top
    near_words = found(title, levels.get("near", [])) if near else []
    if near_words:
        return "near", near_words
    below = found(title, levels.get("below", [])) + found(
        title, levels.get("individual", []), whole=True
    )
    if below:
        return "below", below
    lead = found(title, levels.get("lead", []))
    return ("lead", lead) if lead else ("unknown", [])


def band(score: int) -> str:
    return next(name for name, floor in BANDS if score >= floor)


def screen(
    vacancy: dict, resolved: dict, extra_text: str = "", company: str = "", location: str = ""
) -> dict:
    """Thermometer, tier and reasons for one vacancy. ``resolved`` comes from :func:`profile`.

    The score (0–100) adds four parts — function (30), level (25), domains (25) and CV
    support for those domains (20). Hard rules cap it: an excluded or missing function
    is off profile, a below-target level or a full text without the candidate's domains
    stays weak. ``company`` and ``location`` only feed saved queries with those fields.
    """
    fields = search_fields(vacancy, extra_text, company, location)
    text = fields["text"]
    title = fields["title"]
    for pattern in resolved.get("ignore_in_title", []):
        title = re.sub(pattern, " ", title)
    # Saved queries see the same title as the function check, without ignored phrases.
    fields = {**fields, "title": title}
    has_text = len(text) >= 200
    reasons: list[dict] = []

    queries = []
    for query in resolved["queries"]:
        result = match_query(query["parsed"], fields)
        queries.append(
            {
                "id": query["id"],
                "name": query["name"],
                "query": query["query"],
                "include": query["include"],
                **result,
            }
        )
    included_by = [item for item in queries if item["matched"] and item["include"]]

    excluded = found(title, resolved["exclude_title"])
    policy_excluded = found(text, resolved["exclude_text"])
    tracks = {
        track: hits for track, words in resolved["roles"].items() if (hits := found(title, words))
    }
    market = vacancy.get("market") or "unknown"
    wanted = (
        "top"
        if (market == "ru" and resolved["russia_top_only"])
        else resolved.get("market_levels", {}).get(market, resolved["target_level"])
    )
    top_company = is_top_company(vacancy.get("company_id"), company, resolved)
    # Program and project leadership counts as a function only at top companies abroad.
    program = (
        found(title, resolved.get("program_roles", []))
        if top_company and market != "ru" and "technical-leadership" in resolved["roles"]
        else []
    )
    if program:
        tracks["technical-leadership"] = list(
            dict.fromkeys([*tracks.get("technical-leadership", []), *program])
        )
    level, level_words = _level(title, resolved["levels"], near=wanted in {"near", "any"})
    individual = found(title, resolved["levels"].get("individual", []), whole=True)
    if (
        (not individual or level == "near")
        and top_company
        and (
            level in {"lead", "near"}
            or (level == "below" and {norm(word) for word in level_words} <= COMPANY_SPECIFIC)
        )
    ):
        # Big-tech bands are mapped per employer (policy.company_levels), not by title words,
        # and the Russian director-only rule does not override that mapping.
        level = "company_specific"
    level_ok = (
        level in {"top", "company_specific"}
        or (level == "lead" and wanted in {"near", "lead", "any"})
        or (level == "near" and wanted in {"near", "any"})
        or wanted == "any"
    ) and level != "below"

    domains = []
    for key, terms in resolved["domains"].items():
        in_title, in_text = found(title, terms), found(text, terms)
        if in_title or in_text:
            domains.append(
                {
                    "id": key,
                    "in_title": in_title[:4],
                    "in_text": in_text[:4] if not in_title else [],
                    "facts": resolved.get("support", {}).get(key, {}).get("facts", 0),
                }
            )
    title_domains = [item for item in domains if item["in_title"]]
    domain_title_only = (
        not tracks and not included_by and title_domains and level in {"top", "lead"}
    )

    # Thermometer parts.
    role_points = 30 if tracks else 24 if included_by else 18 if domain_title_only else 0
    if level == "top":
        level_points = 25
    elif level == "company_specific":
        level_points = 22
    elif level in {"lead", "near"}:
        level_points = 20 if level_ok else 10
    elif level == "unknown":
        level_points = 12
    else:
        level_points = 5
    domain_points = min(
        25,
        (12 + 3 * (len(title_domains) - 1) if title_domains else 0)
        + min(10, 4 * (len(domains) - len(title_domains))),
    )
    if included_by and not domains:
        domain_points = 12
    support = resolved.get("support", {})
    backing = sum(support.get(item["id"], {}).get("weight", 0) for item in domains)
    evidence_points = round(20 * min(1.0, backing / 2))
    parts = {
        "role": role_points,
        "level": level_points,
        "domains": domain_points,
        "evidence": evidence_points,
    }
    score = sum(parts.values())

    if excluded:
        reasons.append({"code": "excluded_function", "terms": excluded})
    elif policy_excluded:
        reasons.append({"code": "policy_exclusion", "terms": policy_excluded})
    elif not tracks and not included_by and not domain_title_only:
        reasons.append({"code": "no_track_function", "terms": []})
    off_profile = bool(reasons)
    if not off_profile:
        if domain_title_only:
            reasons.append(
                {
                    "code": "domain_title_only",
                    "terms": [term for item in title_domains for term in item["in_title"]],
                }
            )
        if tracks:
            reasons.append(
                {
                    "code": "track_function",
                    "tracks": list(tracks),
                    "terms": [term for hits in tracks.values() for term in hits],
                }
            )
        if program:
            reasons.append({"code": "program_role_top_company", "terms": program})
        for item in included_by:
            reasons.append(
                {"code": "query_included", "query": item["query"], "terms": item["terms"]}
            )
        if level == "below":
            reasons.append({"code": "level_below", "terms": level_words})
        elif level == "unknown":
            reasons.append({"code": "level_unknown", "terms": []})
        elif level == "company_specific":
            reasons.append({"code": "level_company_specific", "terms": level_words})
        elif not level_ok:
            reasons.append({"code": "level_below_market_rule", "terms": level_words})
        else:
            reasons.append({"code": "level_target", "terms": level_words})
        if domains:
            reasons.append({"code": "domain_overlap", "domains": [item["id"] for item in domains]})
            backed = [
                {"id": item["id"], "facts": item["facts"]} for item in domains if item["facts"]
            ]
            if backed:
                reasons.append({"code": "cv_support", "domains": backed})
        elif has_text:
            reasons.append({"code": "no_domain_overlap", "terms": []})
        else:
            reasons.append({"code": "no_text", "terms": []})

    below_target = level == "below" or (level != "unknown" and not level_ok)
    # A saved query with "include" stands in for the function and domain checks,
    # never for the level: a below-target title stays weak whatever matched it.
    if off_profile:
        score = min(score, OFF_PROFILE_CAP)
        tier = "off_profile"
    else:
        if below_target or (has_text and not domains and not included_by):
            score = min(score, BELOW_TARGET_CAP)
        tier = band(score)
    return {
        "tier": tier,
        "relevant": tier in RELEVANT,
        "score": score,
        "parts": parts,
        "method": "rules",
        "tracks": list(tracks),
        "level": level,
        "domains": domains,
        "queries": queries,
        "reasons": reasons,
        "text_checked": has_text,
    }


def is_top_company(company_id: object, company: str, resolved: dict) -> bool:
    """A top company by stable ID, or by name when a source stored it under another ID.

    Entries of ``policy.bigtech_company_ids`` and ``relevance.top_companies`` are compared
    with the employer name and aliases as whole words: "amazon" matches "Amazon" on a card
    whose company ID came from an aggregator.
    """
    listed = resolved.get("company_specific_levels", [])
    if company_id in listed:
        return True
    name = norm(company)
    return bool(name) and bool(found(name, [norm(item) for item in listed], whole=True))


def company_terms(company: dict | None) -> str:
    """Employer name and aliases, as queries see them."""
    if not isinstance(company, dict):
        return ""
    aliases = company.get("aliases") if isinstance(company.get("aliases"), list) else []
    return " ".join(str(item) for item in [company.get("name"), *aliases] if item)


def screen_settings(
    vacancy: dict, settings: dict, facts: dict | None = None, extra_text: str = ""
) -> dict:
    return screen(vacancy, profile(settings, facts), extra_text)


REASON_TEXT = {
    "excluded_function": "the title names an excluded function",
    "policy_exclusion": "the text mentions a policy exclusion",
    "no_track_function": "the title names no function of the candidate's tracks",
    "track_function": "the title names a track function",
    "query_included": "a saved query includes it",
    "level_below": "the title is below the target level",
    "level_unknown": "the level is not stated in the title",
    "level_company_specific": "big-tech level is mapped per employer, not by title words",
    "domain_title_only": "no track function, but a candidate domain is in a leadership title",
    "cv_support": "CV facts back these domains",
    "level_below_market_rule": "this market requires a director-level title",
    "level_target": "the title is at the target level",
    "program_role_top_company": "a program or project leadership role at a top company abroad",
    "domain_overlap": "the candidate's domains appear",
    "no_domain_overlap": "none of the candidate's domains appear in the full text",
    "no_text": "no description is stored, so domains are checked in the title only",
}


def explain(result: dict) -> str:
    """One readable line, used by the CLI."""
    parts = []
    for reason in result["reasons"]:
        words = [
            f"{item['id']}: {item['facts']} facts" if isinstance(item, dict) else item
            for item in reason.get("terms") or reason.get("domains") or reason.get("tracks") or []
        ]
        text = REASON_TEXT.get(reason["code"], reason["code"])
        parts.append(f"{text} ({', '.join(words)})" if words else text)
    line = f"{result['tier']} {result['score']}/100: " + "; ".join(parts)
    review = result.get("review")
    if review and not review.get("stale"):
        line += f" | agent: {review['summary']}"
    return line


# --------------------------------------------------------------------------- semantic review
#
# A flagship agent session reads the posting against the candidate's profile and records a
# `relevance_review` activity result. A current review takes precedence over the rules; it
# becomes stale when the vacancy text or the candidate's facts change.

REVIEW_REASON_KINDS = frozenset({"fit", "gap", "risk"})


def review_input(vacancy: dict) -> str:
    """Digest of what a semantic review read: title, employer, text and requirements."""
    return digest(
        {
            "title": vacancy.get("title"),
            "company_id": vacancy.get("company_id"),
            "text": vacancy.get("text") if isinstance(vacancy.get("text"), str) else "",
            "requirements": [
                item.get("text")
                for item in vacancy.get("requirements") or []
                if isinstance(item, dict)
            ],
        }
    )


def facts_version(facts: dict | None) -> str:
    items = (facts or {}).get("facts") if isinstance(facts, dict) else None
    return digest(
        [
            {key: fact.get(key) for key in ("id", "text", "tags", "verification", "claim_type")}
            for fact in items or []
            if isinstance(fact, dict)
        ]
    )


def validate_review(store, data: dict) -> dict:
    """Validate a `relevance_review` result: one verdict per vacancy with a score and reasons.

    The score must sit in the verdict's band of the thermometer (strong 70–100, possible
    50–69, weak 0–49, off profile 0–20), so the tier and the number never disagree.
    """
    reviews = data.get("reviews")
    if not isinstance(reviews, list) or not 1 <= len(reviews) <= 300:
        raise ValueError("relevance_review needs 1–300 reviews")
    facts = store.facts
    fact_ids = {fact["id"] for fact in facts.get("facts", []) if isinstance(fact, dict)}
    seen, clean = set(), []
    for index, item in enumerate(reviews):
        name = f"reviews[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{name} must be an object")  # noqa: TRY004
        vacancy = store.get("vacancies", str(item.get("vacancy_id") or ""))
        if not vacancy:
            raise ValueError(f"{name}.vacancy_id does not name a stored vacancy")
        if vacancy["id"] in seen:
            raise ValueError(f"{name}.vacancy_id is reviewed twice")
        seen.add(vacancy["id"])
        verdict, score = item.get("verdict"), item.get("score")
        if verdict not in TIERS:
            raise ValueError(f"{name}.verdict must be one of {list(TIERS)}")
        if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
            raise ValueError(f"{name}.score must be an integer 0–100")
        expected = "off_profile" if verdict == "off_profile" else band(score)
        if expected != verdict or (verdict == "off_profile" and score > OFF_PROFILE_CAP):
            raise ValueError(f"{name}.score {score} is outside the {verdict} band")
        track = item.get("track")
        if track is not None and track not in TRACKS:
            raise ValueError(f"{name}.track must be one of {list(TRACKS)} or null")
        summary = item.get("summary")
        if not isinstance(summary, str) or not summary.strip() or len(summary) > 400:
            raise ValueError(f"{name}.summary must be text up to 400 characters")
        reasons = item.get("reasons")
        if not isinstance(reasons, list) or not 1 <= len(reasons) <= 6:
            raise ValueError(f"{name}.reasons must list 1–6 reasons")
        for reason in reasons:
            if (
                not isinstance(reason, dict)
                or reason.get("kind") not in REVIEW_REASON_KINDS
                or not isinstance(reason.get("text"), str)
                or not reason["text"].strip()
                or len(reason["text"]) > 240
            ):
                raise ValueError(f"{name}.reasons need kind fit|gap|risk and text up to 240")
        linked = item.get("fact_ids") or []
        if not isinstance(linked, list) or not set(linked) <= fact_ids:
            raise ValueError(f"{name}.fact_ids must name existing facts")
        clean.append(
            {
                "vacancy_id": vacancy["id"],
                "verdict": verdict,
                "score": score,
                "track": track,
                "summary": summary.strip(),
                "reasons": [
                    {"kind": reason["kind"], "text": reason["text"].strip()} for reason in reasons
                ],
                "fact_ids": linked,
                "input_sha256": review_input(vacancy),
            }
        )
    return {**data, "reviews": clean, "facts_sha256": facts_version(facts)}


def latest_reviews(records: list[dict]) -> dict[str, dict]:
    """The newest review per vacancy across `relevance_reviews` records."""
    result = {}
    for record in sorted(records, key=lambda item: str(item.get("created_at") or "")):
        for review in record.get("reviews") or []:
            result[review["vacancy_id"]] = {
                **review,
                "facts_sha256": record.get("facts_sha256"),
                "created_at": record.get("created_at"),
                "activity_id": record.get("activity_id"),
                "actor": record.get("actor") or {},
            }
    return result


def combine(result: dict, review: dict | None, vacancy: dict, facts_sha: str) -> dict:
    """Merge a semantic review into a rule result: a current review decides tier and score."""
    if not review:
        return result
    stale = review["input_sha256"] != review_input(vacancy) or review["facts_sha256"] != facts_sha
    shown = {
        key: review.get(key)
        for key in ("verdict", "score", "track", "summary", "reasons", "fact_ids", "created_at")
    }
    shown["model"] = (review.get("actor") or {}).get("model")
    shown["activity_id"] = review.get("activity_id")
    shown["stale"] = stale
    if stale:
        return {**result, "review": shown}
    return {
        **result,
        "tier": review["verdict"],
        "relevant": review["verdict"] in RELEVANT,
        "score": review["score"],
        "method": "agent",
        "rules": {"tier": result["tier"], "score": result["score"]},
        "review": shown,
    }


def pending(vacancies: list[dict], results: dict[str, dict], include_off_profile: bool = False):
    """Vacancies without a current semantic review, most promising first."""
    rows = [
        vacancy
        for vacancy in vacancies
        if results[vacancy["id"]]["method"] != "agent"
        and (include_off_profile or results[vacancy["id"]]["tier"] != "off_profile")
    ]
    return sorted(rows, key=lambda vacancy: -results[vacancy["id"]]["score"])
