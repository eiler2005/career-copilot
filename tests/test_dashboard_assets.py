"""Static contracts for the browser assets and the optional public gateway."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from job_search_agent import relevance

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src" / "job_search_agent" / "web_assets"


def app_js() -> str:
    return (ASSETS / "app.js").read_text(encoding="utf-8")


def test_every_element_id_used_by_the_script_exists_in_the_page():
    page = (ASSETS / "index.html").read_text(encoding="utf-8")
    page_ids = set(re.findall(r'\bid="([\w-]+)"', page))
    script = app_js()
    script_ids = set(re.findall(r'\$\("([\w-]+)"\)', script))
    created_ids = set(re.findall(r'\.id = "([\w-]+)"', script))
    assert script_ids - page_ids - created_ids == set()


def test_every_i18n_key_in_the_page_has_russian_and_english_copy():
    page = (ASSETS / "index.html").read_text(encoding="utf-8")
    script = app_js()
    for key in set(re.findall(r'data-i18n="(\w+)"', page)):
        assert len(re.findall(rf"\b{key}: \"", script)) >= 2, key


def test_script_never_injects_markup_or_evaluates_journal_text():
    script = app_js()
    for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval("):
        assert sink not in script
    assert "new Function" not in script


def test_script_is_syntactically_valid_javascript():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed")
    for script in ("app.js", "design.js"):
        result = subprocess.run(
            [node, "--check", str(ASSETS / script)], capture_output=True, text=True, check=False
        )
        assert result.returncode == 0, result.stderr


def test_design_selector_precedence_persistence_and_url_updates():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed")
    harness = r"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync(process.argv[1], "utf8");

function run(options) {
  const state = {stored: options.saved, writes: [], replaced: null};
  const stylesheetV2 = {disabled: false};
  const stylesheetV3 = {disabled: false};
  const designOnly = [
    {dataset: {designOnly: "v3"}, hidden: false},
    {dataset: {designOnly: "v2"}, hidden: false},
  ];
  const select = {
    value: "",
    listeners: {},
    addEventListener(name, callback) { this.listeners[name] = callback; }
  };
  const document = {
    documentElement: {dataset: {}},
    getElementById(id) {
      if (id === "design-v2") return stylesheetV2;
      if (id === "design-v3") return stylesheetV3;
      return select;
    },
    querySelectorAll(selector) { selector; return designOnly; },
    addEventListener(name, callback) { this.listeners[name] = callback; },
    listeners: {}
  };
  const context = {
    URL,
    location: {href: options.href},
    history: {state: "history-state", replaceState(state, title, url) { state; title; this.last = url; }},
    document,
    localStorage: {
      getItem() {
        if (options.getThrows) throw new Error("unavailable");
        return state.stored;
      },
      setItem(key, value) {
        key;
        if (options.setThrows) throw new Error("unavailable");
        state.stored = value;
        state.writes.push(value);
      }
    }
  };
  vm.runInNewContext(source, context);
  document.listeners.DOMContentLoaded();
  if (options.change) {
    select.value = options.change;
    select.listeners.change();
  }
  state.dataset = document.documentElement.dataset.design;
  state.disabled = stylesheetV2.disabled;
  state.disabledV3 = stylesheetV3.disabled;
  state.designOnly = designOnly.map((node) => node.hidden);
  state.selected = select.value;
  state.replaced = context.history.last || null;
  return state;
}

process.stdout.write(JSON.stringify({
  default: run({href: "https://example.test/dashboard?filter=ai#role"}),
  saved: run({href: "https://example.test/dashboard", saved: "v1"}),
  override: run({href: "https://example.test/dashboard?design=v2", saved: "v1"}),
  v3: run({href: "https://example.test/dashboard?design=v3", saved: "v1"}),
  invalid: run({href: "https://example.test/dashboard?design=legacy", saved: "v1"}),
  invalidFallback: run({href: "https://example.test/dashboard?design=legacy", saved: "legacy"}),
  storageFailure: run({href: "https://example.test/dashboard", getThrows: true, setThrows: true}),
  changed: run({
    href: "https://example.test/dashboard?filter=ai&design=v2#role",
    saved: "v2",
    change: "v1"
  })
}));
"""
    result = subprocess.run(
        [node, "-e", harness, str(ASSETS / "design.js")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    scenarios = json.loads(result.stdout)
    assert scenarios["default"] == {
        "stored": "v3",
        "writes": ["v3"],
        "replaced": None,
        "dataset": "v3",
        "disabled": False,
        "disabledV3": False,
        "designOnly": [False, True],
        "selected": "v3",
    }
    assert scenarios["saved"]["dataset"] == "v1"
    assert scenarios["saved"]["disabled"] is True
    assert scenarios["saved"]["disabledV3"] is True
    assert scenarios["saved"]["designOnly"] == [True, True]
    assert scenarios["override"]["dataset"] == "v2"
    assert scenarios["override"]["writes"] == ["v2"]
    assert scenarios["override"]["disabled"] is False
    assert scenarios["override"]["disabledV3"] is True
    assert scenarios["override"]["designOnly"] == [True, False]
    assert scenarios["v3"]["dataset"] == "v3"
    assert scenarios["v3"]["disabled"] is False
    assert scenarios["v3"]["disabledV3"] is False
    assert scenarios["invalid"]["dataset"] == "v1"
    assert scenarios["invalidFallback"]["dataset"] == "v3"
    assert scenarios["invalidFallback"]["disabledV3"] is False
    assert scenarios["storageFailure"]["dataset"] == "v3"
    assert scenarios["storageFailure"]["disabled"] is False
    assert scenarios["storageFailure"]["disabledV3"] is False
    assert scenarios["changed"]["dataset"] == "v1"
    assert scenarios["changed"]["disabled"] is True
    assert scenarios["changed"]["disabledV3"] is True
    assert scenarios["changed"]["designOnly"] == [True, True]
    assert scenarios["changed"]["replaced"] == (
        "https://example.test/dashboard?filter=ai&design=v1#role"
    )


def test_styles_keep_mobile_filters_collapsible_and_respect_reduced_motion():
    styles = (ASSETS / "styles.css").read_text(encoding="utf-8")
    assert ".toolbar.filters-open .filter-row{display:flex}" in styles
    assert ".toolbar .filter-row{display:none}" in styles
    assert "prefers-reduced-motion:reduce" in styles


def test_public_gateway_requires_authentication_and_publishes_only_loopback():
    caddyfile = (ROOT / "deploy" / "public-gateway" / "Caddyfile").read_text(encoding="utf-8")
    compose = (ROOT / "compose.public.yaml").read_text(encoding="utf-8")
    base = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    assert "admin off" in caddyfile
    assert '?X-Frame-Options "DENY"' in caddyfile
    assert "disable_http_challenge" in caddyfile
    assert "{$CC_BASIC_USER} {$CC_BASIC_HASH}" in caddyfile
    # Only the health probe and robots.txt are reachable before basic authentication.
    unauthenticated, authenticated = caddyfile.split("basic_auth", 1)
    assert "reverse_proxy dashboard:8100 {" in authenticated
    assert unauthenticated.count("reverse_proxy") == 1
    assert "@health path /healthz" in unauthenticated
    assert (
        re.search(r"^\s*log\b", caddyfile.split("{$CC_PUBLIC_HOST} {", 1)[1], re.MULTILINE) is None
    )
    published = re.findall(r'^\s*- "([^"]+:\d+)"\s*$', compose + base, re.MULTILINE)
    assert published and all(port.startswith("127.0.0.1:") for port in published)
    assert "AJH_DASHBOARD_ALLOWED_HOSTS" in compose
    for secret in ("CC_BASIC_HASH", "CC_BASIC_USER", "ACME_EMAIL", "CC_PUBLIC_HOST"):
        assert f"${{{secret}:?" in compose


def test_pipeline_stages_count_only_confirmed_employer_events():
    script = app_js()
    body = script.split("function vacancyStage(record) {", 1)[1].split("\n  }\n", 1)[0]
    assert "interview_practices" not in body and "interview_feedback" not in body
    assert (
        "item.payload.user_confirmed === true && item.payload.sent_at && item.payload.evidence"
        in body
    )
    assert '["interview", "offer"].includes(item.payload.status)' in body


def test_vacancy_detail_uses_accessible_tabs_and_requests_never_claim_completion():
    script = app_js()
    for name in (
        '"vacancy", "fit", "company", "resume", "prep"',
        'setAttribute("role", "tablist")',
        'setAttribute("aria-selected"',
        '"ArrowRight"',
    ):
        assert name in script
    assert '"X-Career-Copilot": "request"' in script
    # A saved request is described as waiting for sync, not as done.
    assert "awaitingImport" in script and "requestQueued" in script
    styles = (ASSETS / "styles.css").read_text(encoding="utf-8")
    assert ".vc-salary{" in styles and ".tabs{" in styles


def test_preparation_layout_keeps_document_tables_readable():
    styles = (ASSETS / "styles.css").read_text(encoding="utf-8")
    script = app_js()
    # The source catalog's no-wrap column rule must not reach plan documents or module views.
    assert ".sources-view .plan-table" not in styles
    assert ".source-catalog .plan-table td:nth-child(3){white-space:nowrap}" in styles
    assert ".markdown .plan-table th,.markdown .plan-table td{min-width:120px" in styles
    body = script.split("function renderPreparationModule(list) {", 1)[1][:400]
    assert '"module-view prep-view"' in body and "sources-view" not in body
    assert "function markdownWithToc(text)" in script and "function prepSummary(list)" in script


def test_preparation_overview_is_rendered_with_tabs_evidence_labels_and_practice():
    script = app_js()
    body = script.split("function overviewView(record) {", 1)[1].split(
        "\n  function focusSession", 1
    )[0]
    for tab in (
        '"summary"',
        '"product"',
        '"technical-leadership"',
        '"plan"',
        '"questions"',
        '"stories"',
        '"cv"',
    ):
        assert tab in script.split("const OVERVIEW_TABS = [", 1)[1].split("];", 1)[0]
    assert 'setAttribute("role", "tablist")' in body and '"ArrowRight"' in body
    assert 'plan_kind: "preparation_overviews"' in script
    for key in ("strength_verified", "strength_reported", "strength_gap", "strength_unknown"):
        assert f'{key}: "' in script
    # The overview never presents itself as verified progress or a CV change.
    assert "overviewNote" in body
    assert (
        "currentOverview()" in script.split("function renderPreparationModule(list) {", 1)[1][:600]
    )


def test_workspace_keeps_navigation_in_the_masthead_without_external_fonts():
    page = (ASSETS / "index.html").read_text(encoding="utf-8")
    assert '<header class="masthead">' in page and 'id="navigation" class="masthead-nav"' in page
    assert '<link id="design-v3" rel="stylesheet" href="/assets/styles-v3.css">' in page
    assert re.search(
        r'<select id="design-version">\s*<option value="v3" selected>v3</option>', page
    )
    assert "sidebar" not in page
    for stylesheet in ("styles.css", "styles-v2.css"):
        styles = (ASSETS / stylesheet).read_text(encoding="utf-8")
        for external in ("@import", "@font-face", "fonts.googleapis", "url(http"):
            assert external not in styles


def test_vacancy_lists_open_on_the_profile_and_share_the_query_grammar():
    script = app_js()
    assert 'section === "vacancies" ? {kind: section, relevance: "relevant"}' in script
    assert 'section === "pipeline" ? {relevance: "relevant"}' in script
    # The dashboard parses the same query grammar and field aliases as `ajh relevance search`.
    for part in ('split("+")', "(?:^|\\s)-(?=\\s*\\S)"):
        assert part in script
    fields = relevance.FIELD_ALIASES
    for alias, field in fields.items():
        assert f'"{alias}": "{field}"' in script or f'{alias}: "{field}"' in script, alias
    # Scores are shown as a thermometer with the method, and an agent review can be requested.
    assert "function thermometer(result" in script and 'task_type: "review_relevance"' in script
    # Overview shows only vacancies that fit the profile.
    assert "isRelevant(record)).sort((a, b) => tierOf(a) - tierOf(b)" in script
