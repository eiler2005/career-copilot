"""Static contracts for the browser assets and the optional public gateway."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

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
    result = subprocess.run(
        [node, "--check", str(ASSETS / "app.js")], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


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


def test_bento_shell_keeps_navigation_in_the_masthead_without_external_fonts():
    page = (ASSETS / "index.html").read_text(encoding="utf-8")
    styles = (ASSETS / "styles.css").read_text(encoding="utf-8")
    assert '<header class="masthead">' in page and 'id="navigation" class="masthead-nav"' in page
    assert "sidebar" not in page
    # Tiles share hairline borders instead of floating cards with gaps.
    assert (
        ".records-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));border-top:1px solid var(--line)"
        in styles
    )
    for external in ("@import", "@font-face", "fonts.googleapis", "url(http"):
        assert external not in styles
