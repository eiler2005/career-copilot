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
    ],
    "lead": ["руководител", "lead", "principal", "group", "начальник", "partner"],
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


def parse_query(query: str) -> dict:
    """Parse ``title:(engineer | инженер) + (ai | ml) - crypto``.

    ``+`` joins groups that must all match, ``|`` or ``,`` separates alternatives in a
    group, and terms after `` -`` exclude the vacancy. A group written as ``title:…``
    is looked up in the title only; other groups in the title and the stored text.
    Parentheses are optional.
    """
    if not isinstance(query, str) or not query.strip() or len(query) > 300:
        raise ValueError("A query is a non-empty string of up to 300 characters")
    parts = re.split(r"(?:^|\s)-(?=\s*\S)", query.strip())

    def group(chunk: str) -> dict | None:
        chunk = chunk.strip()
        field = "any"
        if chunk.casefold().startswith("title:"):
            field, chunk = "title", chunk[len("title:") :]
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


def match_query(parsed: dict, title: str, text: str) -> dict:
    """Which alternative satisfied each group; ``matched`` only when all do and none excludes.

    ``title`` and ``text`` are already normalised with :func:`norm`.
    """
    hits = []
    for item in parsed["all_of"]:
        where = title if item["field"] == "title" else f"{title} {text}"
        hit = next(iter(found(where, item["terms"])), None)
        if hit is None:
            return {"matched": False, "terms": hits, "missing": item["terms"]}
        hits.append(hit)
    blocked = [
        term
        for item in parsed["none_of"]
        for term in found(title if item["field"] == "title" else f"{title} {text}", item["terms"])
    ]
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
    if not isinstance(levels, dict) or not set(levels) <= {"top", "lead", "below", "individual"}:
        raise ValueError("relevance.levels accepts top, lead, below and individual lists")
    target = config.get("target_level", "lead")
    if target not in {"top", "lead", "any"}:
        raise ValueError("relevance.target_level must be top, lead or any")
    vocabulary = config.get("vocabulary") or {}
    if not isinstance(vocabulary, dict):
        raise ValueError("relevance.vocabulary must map a domain to terms")  # noqa: TRY004
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
        "exclude_title": _strings(config.get("exclude_title"), "relevance.exclude_title"),
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
        "russia_top_only": bool(policy.get("russia_director_only")),
        "exclude_title": _merged(DEFAULT_EXCLUDE_TITLE, config["exclude_title"], extend),
        "exclude_text": [str(item) for item in policy.get("exclude") or [] if str(item).strip()],
        "company_specific_levels": [str(item) for item in policy.get("bigtech_company_ids") or []],
        "domains": active_domains(settings, facts, config),
        "queries": config["queries"],
    }


# --------------------------------------------------------------------------- screening


def vacancy_text(vacancy: dict, extra: str = "") -> str:
    parts = [vacancy.get("text") if isinstance(vacancy.get("text"), str) else ""]
    for requirement in vacancy.get("requirements") or []:
        if isinstance(requirement, dict) and isinstance(requirement.get("text"), str):
            parts.append(requirement["text"])
    parts.append(extra or "")
    return norm(" ".join(parts))[:TEXT_LIMIT]


def _level(title: str, levels: dict) -> tuple[str, list[str]]:
    top = found(title, levels.get("top", []))
    if top:
        return "top", top
    below = found(title, levels.get("below", [])) + found(
        title, levels.get("individual", []), whole=True
    )
    if below:
        return "below", below
    lead = found(title, levels.get("lead", []))
    return ("lead", lead) if lead else ("unknown", [])


def screen(vacancy: dict, resolved: dict, extra_text: str = "") -> dict:
    """Tier, score and reasons for one vacancy. ``resolved`` comes from :func:`profile`."""
    title = norm(vacancy.get("title"))
    text = vacancy_text(vacancy, extra_text)
    has_text = len(text) >= 200
    reasons: list[dict] = []

    queries = []
    for query in resolved["queries"]:
        result = match_query(query["parsed"], title, text)
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
    level, level_words = _level(title, resolved["levels"])
    individual = found(title, resolved["levels"].get("individual", []), whole=True)
    if (
        level == "below"
        and not individual
        and vacancy.get("company_id") in resolved["company_specific_levels"]
        and {norm(word) for word in level_words} <= COMPANY_SPECIFIC
    ):
        # Big-tech bands are mapped per employer (policy.company_levels), not by title words.
        level = "company_specific"
    market = vacancy.get("market") or "unknown"
    wanted = "top" if (market == "ru" and resolved["russia_top_only"]) else resolved["target_level"]
    level_ok = (
        level in {"top", "company_specific"}
        or (level == "lead" and wanted in {"lead", "any"})
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
                }
            )
    title_domain = any(item["in_title"] for item in domains)

    if excluded:
        tier = "off_profile"
        reasons.append({"code": "excluded_function", "terms": excluded})
    elif policy_excluded:
        tier = "off_profile"
        reasons.append({"code": "policy_exclusion", "terms": policy_excluded})
    elif not tracks and not included_by and not (title_domain and level in {"top", "lead"}):
        tier = "off_profile"
        reasons.append({"code": "no_track_function", "terms": []})
    else:
        if not tracks and not included_by:
            reasons.append(
                {
                    "code": "domain_title_only",
                    "terms": [term for item in domains for term in item["in_title"]],
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
        elif has_text:
            reasons.append({"code": "no_domain_overlap", "terms": []})
        else:
            reasons.append({"code": "no_text", "terms": []})
        # A saved query with "include" stands in for the function and domain checks,
        # never for the level: a below-target title stays weak whatever matched it.
        below_target = level == "below" or (level != "unknown" and not level_ok)
        if below_target or (has_text and not domains and not included_by):
            tier = "weak"
        elif (
            level_ok
            and (tracks or included_by)
            and (title_domain or len(domains) >= 2 or included_by)
        ):
            tier = "strong"
        else:
            tier = "possible"

    base = {"strong": 75, "possible": 50, "weak": 25, "off_profile": 0}[tier]
    score = base if tier == "off_profile" else min(99, base + 5 * len(domains) + 5 * title_domain)
    return {
        "tier": tier,
        "relevant": tier in RELEVANT,
        "score": score,
        "tracks": list(tracks),
        "level": level,
        "domains": domains,
        "queries": queries,
        "reasons": reasons,
        "text_checked": has_text,
    }


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
    "level_below_market_rule": "this market requires a director-level title",
    "level_target": "the title is at the target level",
    "domain_overlap": "the candidate's domains appear",
    "no_domain_overlap": "none of the candidate's domains appear in the full text",
    "no_text": "no description is stored, so domains are checked in the title only",
}


def explain(result: dict) -> str:
    """One readable line, used by the CLI."""
    parts = []
    for reason in result["reasons"]:
        words = reason.get("terms") or reason.get("domains") or reason.get("tracks") or []
        text = REASON_TEXT.get(reason["code"], reason["code"])
        parts.append(f"{text} ({', '.join(words)})" if words else text)
    return f"{result['tier']}: " + "; ".join(parts)
