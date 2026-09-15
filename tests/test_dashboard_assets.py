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
    assert "prefers-reduced-motion:reduce" in styles


def test_public_gateway_requires_authentication_and_publishes_only_loopback():
    caddyfile = (ROOT / "deploy" / "public-gateway" / "Caddyfile").read_text(encoding="utf-8")
    compose = (ROOT / "compose.public.yaml").read_text(encoding="utf-8")
    base = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    assert "admin off" in caddyfile
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
