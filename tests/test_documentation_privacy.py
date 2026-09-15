import io
import zipfile

import pytest

from job_search_agent import privacy


def svg(body="", attributes=""):
    return f'<svg xmlns="http://www.w3.org/2000/svg" {attributes}>{body}</svg>'.encode()


def test_bilingual_docs_and_exact_skill_locations():
    for path in ("README.ru.md", "CONTRIBUTING.md", "CONTRIBUTING.ru.md"):
        assert privacy.scan_blob(path, b"Public documentation", []) == []
    for runtime in (".agents", ".claude"):
        for name in privacy.SKILL_NAMES:
            assert privacy.scan_blob(f"{runtime}/skills/{name}/SKILL.md", b"Instructions", []) == []
        assert "path-not-allowlisted" in privacy.scan_blob(f"{runtime}/settings.json", b"{}", [])
        assert not privacy.allowed_path(f"{runtime}/skills/unrelated/SKILL.md")
        assert not privacy.allowed_path(f"{runtime}/skills/career-copilot/private/facts.json")


@pytest.mark.parametrize(
    "name",
    [
        "Dockerfile",
        "compose.yaml",
        "compose.public.yaml",
        ".dockerignore",
        "deploy/public-gateway/Caddyfile",
    ],
)
def test_container_configuration_keeps_content_privacy_checks(name):
    assert privacy.scan_blob(name, b"# Generic container configuration", []) == []
    marker = "Synthetic" + "PrivateMarker"
    assert privacy.scan_blob(name, marker.encode(), [marker]) == ["private-dictionary-match"]
    key_header = b"-----BEGIN " + b"PRIVATE KEY-----"
    assert privacy.scan_blob(name, key_header, []) == ["private-key"]
    assert not privacy.allowed_path(".env")
    assert not privacy.allowed_path(".env.production")
    assert not privacy.allowed_path("private/compose.yaml")
    assert not privacy.allowed_path("deploy/.env")
    assert not privacy.allowed_path("deploy/private/Caddyfile")


def test_static_graphics_scoped_and_decoded_for_privacy():
    assert privacy.scan_blob("docs/assets/flow.svg", svg("<text>Public flow</text>"), []) == []
    assert privacy.scan_blob("docs/assets/flow.dot", b"digraph { a -> b }", []) == []
    assert privacy.scan_blob("docs/flow.svg", svg(), [])
    term = "Fictional" + "PrivateValue"
    encoded_term = "".join(f"&#{ord(char)};" for char in term)
    findings = privacy.scan_blob(
        "docs/assets/flow.svg", svg(f"<text>{encoded_term}</text>"), [term]
    )
    assert findings == ["private-dictionary-match"]
    assert term not in str(findings)


@pytest.mark.parametrize(
    "body,attributes",
    [
        ("<script>run()</script>", ""),
        ("<foreignObject><div>content</div></foreignObject>", ""),
        ('<image href="data:image/png;base64,AA=="/>', ""),
        ('<use href="https://example.invalid/remote.svg#node"/>', ""),
        ('<text style="fill:url(https://example.invalid/color)">Label</text>', ""),
        ('<text style="fill:u\\72l(https://example.invalid/color)">Label</text>', ""),
        ('<style>@import "https://example.invalid/theme"</style>', ""),
        ('<animate attributeName="x"/>', ""),
        ("<text>Label</text>", 'onload="run()"'),
        ('<g xml:base="https://example.invalid/"><use href="#node"/></g>', ""),
    ],
)
def test_reject_active_or_external_svg(body, attributes):
    findings = privacy.scan_blob("docs/assets/flow.svg", svg(body, attributes), [])
    assert "uninspectable-content" in findings


def test_reject_svg_document_entities_and_stylesheet_instruction():
    for declaration in (
        '<!DOCTYPE svg SYSTEM "https://example.invalid/svg.dtd">',
        '<!DOCTYPE svg [<!ENTITY value "secret">]>',
        '<?xml-stylesheet href="https://example.invalid/style.css"?>',
    ):
        assert privacy.scan_blob("docs/assets/flow.svg", declaration.encode() + svg(), [])


@pytest.mark.parametrize("attribute", ["fill", "stroke", "filter", "clip-path", "mask", "cursor"])
@pytest.mark.parametrize("reference", ["//example.invalid/paint.svg#node", "paint.svg#node"])
def test_reject_css_escaped_references_in_presentation_attributes(attribute, reference):
    # These are CSS presentation attributes, not a style attribute. CSS decodes
    # u\\72l as url, including protocol-relative and relative external resources.
    body = f'<rect {attribute}="u\\72l({reference})"/>'
    assert privacy.scan_blob("docs/assets/flow.svg", svg(body), []) == ["uninspectable-content"]


def test_svg_local_references_and_binary_restrictions():
    body = '<defs><linearGradient id="color"><stop offset="0"/></linearGradient></defs>'
    body += '<rect fill="url(#color)"/><g id="node"/><use href="#node"/>'
    assert privacy.scan_blob("docs/assets/flow.svg", svg(body), []) == []
    for suffix in ("png", "jpg", "pdf"):
        assert "private-or-binary-artifact" in privacy.scan_blob(
            f"docs/assets/graphic.{suffix}", b"not-public", []
        )


def test_svg_archive_is_still_inspected():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("example-1.0/docs/assets/flow.svg", svg("<script>run()</script>"))
    assert "uninspectable-content" in privacy.scan_blob(
        "example.zip", buffer.getvalue(), [], check_path=False
    )


def test_skill_symlinks_still_forbidden(tmp_path):
    skill = tmp_path / ".agents/skills/career-copilot"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").symlink_to(tmp_path / "outside.md")
    result = privacy.check(tmp_path, "worktree")
    assert result["passed"] is False
    assert result["findings"][0]["rules"] == ["symlink-forbidden"]
