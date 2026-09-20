"""Synthetic contracts for portable documents, resource safety and print packets."""

import io
import json
from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader

from job_search_agent.cli import parser, run
from job_search_agent.core import Store, init_home
from job_search_agent.pdf_documents import Styles, bind_pdfs, extract_pdf, render_markdown


def reader(data):
    return PdfReader(io.BytesIO(data))


def text(data):
    return "\n".join(page.extract_text() for page in reader(data).pages)


def test_markdown_cyrillic_tables_code_links_and_page_breaks():
    markdown = (
        "# План подготовки\n\n**Сильный** и `точный` текст. [Источник](https://example.org/source)\n\n"
        "3. Первый\n4. Второй\n   - Вложенный\n\n"
        "| Неделя | Результат |\n|---|---|\n| 1 | Решение \\| проверка |\n\n"
        "```python\nif ready:\n    print('<safe>')\n```\n\n"
        "<!-- pagebreak -->\n\n## Следующий раздел\n\n<script>literal</script>\n"
    )
    pdf = render_markdown(markdown)
    assert pdf == render_markdown(markdown)
    document = reader(pdf)
    assert len(document.pages) == 2
    content = text(pdf)
    for expected in [
        "План подготовки",
        "Сильный",
        "точный",
        "Решение | проверка",
        "<safe>",
        "<script>literal</script>",
        "3.",
        "4.",
        "Вложенный",
    ]:
        assert expected in content
    assert (
        document.pages[0]["/Annots"][0].get_object()["/A"]["/URI"] == "https://example.org/source"
    )
    assert document.outline


def test_explicit_word_sized_font_scales_body_and_table_styles():
    styles = Styles(font_size=12)
    assert styles.body.fontSize == 12
    assert styles.body.leading == 16.8
    assert styles.headings[3].fontSize >= 13
    assert render_markdown("# Readable\n\n| A | B |\n|---|---|\n| 1 | 2 |", font_size=12)
    with pytest.raises(ValueError, match="between 8 and 18"):
        Styles(font_size=float("inf"))


def test_long_tables_repeat_headers_and_split_oversized_rows():
    markdown = "# Long plan\n\n| Header A | Header B |\n|---|---|\n"
    markdown += "".join(f"| row {i} | detail {i} |\n" for i in range(100))
    markdown += "| Oversized | " + "word " * 2200 + " END_MARKER |\n"
    pdf = render_markdown(markdown)
    document = reader(pdf)
    assert len(document.pages) > 3
    assert "END_MARKER" in text(pdf)
    assert all("Header A" in page.extract_text() for page in document.pages)
    assert all(page.extract_text().count("Header A") == 1 for page in document.pages)


def test_local_images_are_embedded_and_hashed(tmp_path):
    image = tmp_path / "chart.png"
    Image.new("RGB", (1800, 900), "white").save(image)
    resources = {}
    pdf = render_markdown(
        "# Plan\n\n![Diagram](chart.png)",
        source_dir=tmp_path,
        resource_root=tmp_path,
        resources=resources,
    )
    assert list(resources) == ["chart.png"]
    assert len(resources["chart.png"]) == 64
    assert list(reader(pdf).pages[0].images)
    assert "Diagram" in text(pdf)


def test_unsafe_link_labels_remain_text_without_actions():
    pdf = render_markdown("[Unsafe](javascript:alert) and [Local](file:///tmp/source)")
    assert "Unsafe" in text(pdf) and "Local" in text(pdf)
    assert not reader(pdf).pages[0].get("/Annots")


@pytest.mark.parametrize(
    "src",
    [
        "https://example.org/a.png",
        "file:///tmp/a.png",
        "data:image/png;base64,AA",
        "../outside.png",
    ],
)
def test_unsafe_images_are_rejected_without_fetching(tmp_path, src):
    with pytest.raises(ValueError, match="workspace"):
        render_markdown(f"![unsafe]({src})", source_dir=tmp_path, resource_root=tmp_path)


def test_symlink_image_and_image_in_table_rejected(tmp_path):
    inside = tmp_path / "inside"
    inside.mkdir()
    Image.new("RGB", (2, 2)).save(tmp_path / "outside.png")
    (inside / "escape.png").symlink_to(tmp_path / "outside.png")
    with pytest.raises(ValueError, match="escapes"):
        render_markdown("![escape](escape.png)", source_dir=inside, resource_root=inside)
    with pytest.raises(ValueError, match="outside table"):
        render_markdown("| Image |\n|---|\n| ![unsafe](https://example.org/a.png) |")


def test_binder_and_extract_preserve_order_orientation_and_bookmarks():
    portrait = render_markdown("# Первый\n\nНачало\n\n<!-- pagebreak -->\n\nКонец")
    wide = render_markdown("# Second\n\nLandscape", wide=True)
    packet = bind_pdfs([("Первый", portrait), ("Second", wide)])
    assert packet == bind_pdfs([("Первый", portrait), ("Second", wide)])
    document = reader(packet)
    assert len(document.pages) == 3
    assert float(document.pages[2].mediabox.width) > float(document.pages[2].mediabox.height)
    assert [item.title for item in document.outline] == ["Первый", "Second"]
    assert "3 / 3" in document.pages[2].extract_text()
    selected = extract_pdf(packet, [3, 1, 3])
    assert "Landscape" in reader(selected).pages[0].extract_text()
    assert "Начало" in reader(selected).pages[1].extract_text()
    assert len(reader(selected).pages) == 3


def test_binder_preserve_size_keeps_source_page_geometry():
    source = render_markdown("# Source\n\nBody", wide=True)
    source_page = reader(source).pages[0]
    packet = bind_pdfs([("Source", source)], preserve_size=True)
    page = reader(packet).pages[0]
    assert float(page.mediabox.width) == float(source_page.mediabox.width)
    assert float(page.mediabox.height) == float(source_page.mediabox.height)
    assert "Source" in page.extract_text()
    with pytest.raises(ValueError, match="1-based"):
        extract_pdf(packet, [0])


def invoke(home: Path, *args):
    return run(parser().parse_args(["--home", str(home), "pdf", *args]))


def test_cli_manifest_registration_immutability_and_workspace_confinement(tmp_path):
    home = init_home(tmp_path / "workspace", demo=True)
    (home / "plan.md").write_text("# План\n\nПроверяемый результат", encoding="utf-8")
    args = ("render", "plan.md", "--output", "pdf/plan.pdf")
    result = invoke(home, *args)
    assert result["pages"] == 1
    assert result["review_status"] == "pending"
    assert result["manifest"] == "pdf/plan.pdf.manifest.json"
    manifest = json.loads((home / result["manifest"]).read_text())
    assert manifest["sources"][0]["path"] == "plan.md"
    assert invoke(home, *args)["sha256"] == result["sha256"]
    with Store(home) as store:
        assert store.artifact_intact(result["output"])
        assert store.artifact_intact(result["manifest"])
        assert len(store.all("pdf_documents")) == 1
    assert invoke(home, "inspect", "pdf/plan.pdf")["pages"] == 1
    (home / "plan.md").write_text("# Changed", encoding="utf-8")
    with pytest.raises(ValueError, match="Immutable"):
        invoke(home, *args)
    with pytest.raises(ValueError, match="escapes"):
        invoke(home, "render", "../outside.md", "--output", "pdf/escape.pdf")
    with pytest.raises(ValueError, match="relative"):
        invoke(home, "render", "plan.md", "--output", str(tmp_path / "escape.pdf"))
    with pytest.raises(ValueError, match="escapes"):
        invoke(home, "render", "plan.md", "--output", "../escape.pdf")


def test_cli_rejects_registered_artifact_tampering_and_bad_extract(tmp_path):
    home = init_home(tmp_path / "workspace", demo=True)
    (home / "plan.md").write_text("# Plan", encoding="utf-8")
    invoke(home, "render", "plan.md", "--output", "plan.pdf")
    with pytest.raises(ValueError, match="different"):
        invoke(home, "extract", "plan.pdf", "--pages", "1", "--output", "plan.pdf")
    with pytest.raises(ValueError, match="1-based"):
        invoke(home, "extract", "plan.pdf", "--pages", "2", "--output", "bad.pdf")
    assert not (home / "bad.pdf").exists()
    (home / "plan.pdf").unlink()
    (home / "plan.pdf.manifest.json").unlink()
    (home / "plan.md").write_text("# Other plan", encoding="utf-8")
    with pytest.raises(ValueError, match="integrity"):
        invoke(home, "render", "plan.md", "--output", "plan.pdf")


def test_cli_manifest_preflight_and_symlink_boundaries(tmp_path):
    home = init_home(tmp_path / "workspace", demo=True)
    (home / "plan.md").write_text("# Plan", encoding="utf-8")
    args = ("render", "plan.md", "--output", "plan.pdf")
    result = invoke(home, *args)
    original = (home / "plan.pdf").read_bytes()
    # Empty and omitted titles produce the same PDF but distinct requested options.
    with pytest.raises(ValueError, match="Immutable"):
        invoke(home, *args, "--title", "")
    assert (home / "plan.pdf").read_bytes() == original
    assert json.loads((home / result["manifest"]).read_text())["options"]["title"] is None
    external = tmp_path / "outside"
    external.mkdir()
    (external / "source.md").write_text("# Outside", encoding="utf-8")
    (home / "source-link.md").symlink_to(external / "source.md")
    (home / "destination-link").symlink_to(external, target_is_directory=True)
    with pytest.raises(ValueError, match="escapes"):
        invoke(home, "render", "source-link.md", "--output", "new.pdf")
    with pytest.raises(ValueError, match="escapes"):
        invoke(home, "render", "plan.md", "--output", "destination-link/new.pdf")
    assert not (external / "new.pdf").exists()
