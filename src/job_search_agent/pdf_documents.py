"""Portable private document rendering and binding; no network or model calls.

The binder follows the reusable A4, numbering and bookmark approach of the
reference print workflow, implemented with the project's cross-platform stack.
"""

from __future__ import annotations

import hashlib
import html
import io
import math
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)

from .core import Store, digest, encode

INK = colors.HexColor("#18364b")
TEAL = colors.HexColor("#137c80")
MUTED = colors.HexColor("#617180")
PALE = colors.HexColor("#eff5f7")
FONT_CANDIDATES = (
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "DejaVuSans-Bold.ttf"),
    ("/System/Library/Fonts/Supplemental/Arial.ttf", "Arial Bold.ttf"),
    ("/Library/Fonts/Arial Unicode.ttf", None),
)


def fonts(font_path: str | None = None) -> tuple[str, str]:
    candidates = [(font_path, None)] if font_path else FONT_CANDIDATES
    for value, bold_name in candidates:
        if value and Path(value).is_file():
            path = Path(value)
            bold = path.with_name(bold_name) if bold_name else path
            if not bold.is_file():
                bold = path
            # Content-derived names avoid collisions between custom fonts/sessions.
            name = "Document-" + hashlib.sha256(path.read_bytes()).hexdigest()[:12]
            if name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(name, str(path)))
                pdfmetrics.registerFont(TTFont(name + "-Bold", str(bold)))
                pdfmetrics.registerFontFamily(
                    name, normal=name, bold=name + "-Bold", italic=name, boldItalic=name + "-Bold"
                )
            return name, name + "-Bold"
    raise ValueError("A Unicode TTF font is required; set pdf_font in private settings")


class Styles:
    def __init__(self, font_path: str | None = None, font_size: float | None = None):
        self.font, bold = fonts(font_path)
        legacy = font_size is None
        if legacy:
            font_size = 9.5
        if (
            not isinstance(font_size, (int, float))
            or not math.isfinite(font_size)
            or not 8 <= font_size <= 18
        ):
            raise ValueError("PDF font size must be a finite number between 8 and 18")
        self.font_size = float(font_size)
        self.body = ParagraphStyle(
            "DocumentBody",
            fontName=self.font,
            fontSize=self.font_size,
            leading=14 if legacy else round(self.font_size * 1.4, 2),
            textColor=INK,
            spaceAfter=6,
            allowWidows=0,
            allowOrphans=0,
            splitLongWords=True,
        )
        small_size = 8 if legacy else max(8, self.font_size - 1)
        self.small = ParagraphStyle(
            "DocumentSmall",
            parent=self.body,
            fontSize=small_size,
            leading=11 if legacy else round(small_size * 1.4, 2),
        )
        self.code = ParagraphStyle(
            "DocumentCode",
            parent=self.small,
            backColor=PALE,
            borderPadding=7,
            spaceBefore=5,
            spaceAfter=8,
        )
        self.caption = ParagraphStyle(
            "DocumentCaption",
            parent=self.small,
            textColor=MUTED,
            spaceAfter=10,
        )
        self.headings = {
            n: ParagraphStyle(
                f"DocumentHeading{n}",
                parent=self.body,
                fontName=bold,
                fontSize={1: 24, 2: 16, 3: (12 if legacy else self.font_size + 1)}.get(
                    n, 10.5 if legacy else self.font_size + 1
                ),
                leading={
                    1: 29,
                    2: 21,
                    3: (17 if legacy else round((self.font_size + 1) * 1.4, 2)),
                }.get(n, 15 if legacy else round((self.font_size + 1) * 1.4, 2)),
                textColor=INK if n == 1 else TEAL,
                spaceBefore=15 if n > 1 else 4,
                spaceAfter=8,
                keepWithNext=True,
            )
            for n in range(1, 7)
        }


def _inline(tokens: list) -> str:
    output = []
    links = []
    for token in tokens:
        kind = token.type
        if kind in {"text", "html_inline"}:
            output.append(html.escape(token.content))
        elif kind in {"softbreak", "hardbreak"}:
            output.append("<br/>" if kind == "hardbreak" else " ")
        elif kind == "code_inline":
            output.append(f'<font color="#137c80">{html.escape(token.content)}</font>')
        elif kind in {"strong_open", "strong_close", "em_open", "em_close"}:
            output.append(
                {
                    "strong_open": "<b>",
                    "strong_close": "</b>",
                    "em_open": "<i>",
                    "em_close": "</i>",
                }[kind]
            )
        elif kind == "link_open":
            href = token.attrGet("href") or ""
            safe = urlsplit(href).scheme.lower() in {"https", "http", "mailto"}
            links.append(safe)
            if safe:
                output.append(f'<link href="{html.escape(href, quote=True)}" color="#137c80">')
        elif kind == "link_close":
            if links.pop():
                output.append("</link>")
        elif kind == "image":
            output.append(html.escape(token.content))
    return "".join(output)


def _image(
    token,
    source_dir: Path | None,
    resource_root: Path | None,
    width: float,
    height: float,
    resources: dict[str, str] | None,
):
    src = token.attrGet("src") or ""
    # Parsing is explicit: ReportLab must never receive a URL or a raw source path.
    parsed = urlsplit(src)
    if parsed.scheme or parsed.netloc or not source_dir or not resource_root:
        raise ValueError("PDF images require a local workspace resource")
    path = (source_dir / unquote(parsed.path)).resolve()
    if not path.is_relative_to(resource_root.resolve()):
        raise ValueError("PDF image escapes private workspace")
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg"} or not path.is_file():
        raise ValueError("PDF images support existing local PNG and JPEG files")
    data = path.read_bytes()
    if len(data) > 20_000_000:
        raise ValueError("PDF image exceeds the 20 MB resource limit")
    if resources is not None:
        resources[path.relative_to(resource_root.resolve()).as_posix()] = digest(data)
    picture = Image(io.BytesIO(data))
    ratio = min(width / picture.imageWidth, height / picture.imageHeight, 1)
    picture.drawWidth = picture.imageWidth * ratio
    picture.drawHeight = picture.imageHeight * ratio
    picture.hAlign = "LEFT"
    return picture


class _PlanTable(LongTable):
    def split(self, availWidth, availHeight):
        # A remaining ordinary row belongs on the next page. Only a row that
        # cannot fit a fresh frame may split internally; otherwise ReportLab
        # can repeat the header halfway down the current page.
        frame = getattr(self, "_frame", None)
        previous = self.splitInRow
        if frame is not None and not frame._atTop:
            self.splitInRow = 0
        try:
            parts = super().split(availWidth, availHeight)
            for part in parts:
                if isinstance(part, _PlanTable):
                    part.splitInRow = previous
            return parts
        finally:
            self.splitInRow = previous


def markdown_flowables(
    markdown: str,
    width: float,
    *,
    styles: Styles | None = None,
    source_dir: Path | None = None,
    resource_root: Path | None = None,
    resources: dict[str, str] | None = None,
    image_height: float = 175 * mm,
    images: bool = True,
) -> list:
    """Render a safe Markdown subset. HTML is literal; pagebreak is a sole marker."""
    styles = styles or Styles()
    parser = MarkdownIt("commonmark", {"html": False}).enable("table")
    # Tokenize every destination so the resource policy can reject unsafe
    # images explicitly instead of silently treating them as literal Markdown.
    parser.validateLink = lambda _url: True
    tokens = parser.parse(markdown)
    story = []
    lists = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        kind = token.type
        if kind == "table_open":
            rows, row = [], []
            index += 1
            while tokens[index].type != "table_close":
                part = tokens[index]
                if part.type == "tr_open":
                    row = []
                elif part.type == "inline":
                    if images and any(child.type == "image" for child in part.children or []):
                        raise ValueError("Place PDF images outside table cells")
                    row.append(Paragraph(_inline(part.children or []), styles.small))
                elif part.type == "tr_close":
                    rows.append(row)
                index += 1
            if rows:
                count = len(rows[0])
                table = _PlanTable(
                    rows,
                    colWidths=[width / count] * count,
                    repeatRows=1,
                    splitByRow=1,
                    splitInRow=1,
                    hAlign="LEFT",
                )
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), PALE),
                            (
                                "ROWBACKGROUNDS",
                                (0, 1),
                                (-1, -1),
                                [colors.white, colors.HexColor("#fafcfc")],
                            ),
                            ("LINEBELOW", (0, 0), (-1, 0), 1, TEAL),
                            ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#d9e3e8")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                            ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ]
                    )
                )
                story.extend([table, Spacer(1, 10)])
        elif kind in {"bullet_list_open", "ordered_list_open"}:
            lists.append([kind == "ordered_list_open", int(token.attrGet("start") or 1)])
        elif kind in {"bullet_list_close", "ordered_list_close"}:
            lists.pop()
        elif kind == "inline":
            previous = tokens[index - 1]
            children = token.children or []
            if token.content.strip() == "<!-- pagebreak -->":
                story.append(PageBreak())
            else:
                style = (
                    styles.headings[int(previous.tag[1:])]
                    if previous.type == "heading_open"
                    else styles.body
                )
                text = _inline(children)
                prefix = ""
                if lists and previous.type == "paragraph_open":
                    ordered, number = lists[-1]
                    marker = f"{number}." if ordered else "•"
                    # Only the first paragraph in an item gets a bullet.
                    first = index >= 2 and tokens[index - 2].type == "list_item_open"
                    if first:
                        lists[-1][1] += 1
                    style = ParagraphStyle(
                        "DocumentList",
                        parent=styles.body,
                        leftIndent=13 * len(lists),
                        firstLineIndent=-10 if first else 0,
                    )
                    if first:
                        prefix = html.escape(marker) + "  "
                        text = prefix + text
                image_tokens = [child for child in children if child.type == "image"]
                if image_tokens and images:
                    # Preserve accompanying inline text, then render each image and its caption.
                    others = [child for child in children if child.type != "image"]
                    if _inline(others).strip() or prefix:
                        story.append(Paragraph(prefix + _inline(others), style))
                    for child in image_tokens:
                        story.append(
                            _image(child, source_dir, resource_root, width, image_height, resources)
                        )
                        if child.content:
                            story.append(Paragraph(html.escape(child.content), styles.caption))
                else:
                    story.append(Paragraph(text or " ", style))
                    if previous.type == "heading_open":
                        story[-1]._document_heading = (int(previous.tag[1:]), token.content)
        elif kind in {"fence", "code_block"}:
            # Separate paragraphs let very long code blocks split across pages.
            for line in token.content.splitlines():
                value = html.escape(line.expandtabs(4)).replace(" ", "&#160;")
                story.append(Paragraph(value or "&#160;", styles.code))
        elif kind == "hr":
            story.append(HRFlowable(width="100%", thickness=0.5, color=TEAL, spaceAfter=9))
        index += 1
    return story


class _Document(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        heading = getattr(flowable, "_document_heading", None)
        if heading:
            level, title = heading
            count = getattr(self, "_heading_count", 0)
            key = f"heading-{count}"
            self._heading_count = count + 1
            self.canv.bookmarkPage(key)
            # PDF outlines cannot skip hierarchy levels.
            actual = min(level - 1, getattr(self, "_outline_level", -1) + 1)
            self._outline_level = actual
            self.canv.addOutlineEntry(title, key, level=actual, closed=False)


def render_markdown(
    markdown: str,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    font_path: str | None = None,
    font_size: float | None = None,
    wide: bool = False,
    source_dir: Path | None = None,
    resource_root: Path | None = None,
    resources: dict[str, str] | None = None,
) -> bytes:
    styles = Styles(font_path, font_size)
    first = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    inferred = first.group(1) if first else "Document"
    display_title = title or inferred
    target = io.BytesIO()
    document = _Document(
        target,
        pagesize=landscape(A4) if wide else A4,
        leftMargin=19 * mm,
        rightMargin=19 * mm,
        topMargin=20 * mm,
        bottomMargin=19 * mm,
        title=display_title,
        author="",
        invariant=1,
    )
    story = []
    if title:
        story.append(Paragraph(html.escape(title), styles.headings[1]))
    if subtitle:
        story.append(Paragraph(html.escape(subtitle), styles.caption))
    story += markdown_flowables(
        markdown,
        document.width,
        styles=styles,
        source_dir=source_dir,
        resource_root=resource_root,
        resources=resources,
        image_height=document.height - 60,
    )
    if not story:
        story.append(Paragraph(" ", styles.body))

    def furniture(canv, doc):
        canv.saveState()
        page_width, page_height = doc.pagesize
        canv.setStrokeColor(TEAL)
        canv.setLineWidth(1.2)
        canv.line(
            doc.leftMargin,
            page_height - 12 * mm,
            page_width - doc.rightMargin,
            page_height - 12 * mm,
        )
        canv.setFont(styles.font, 7)
        canv.setFillColor(MUTED)
        label = display_title
        while pdfmetrics.stringWidth(label, styles.font, 7) > doc.width - 50 and label:
            label = label[:-1]
        canv.drawString(doc.leftMargin, 10 * mm, label)
        canv.drawRightString(page_width - doc.rightMargin, 10 * mm, str(doc.page))
        canv.restoreState()

    document.build(story, onFirstPage=furniture, onLaterPages=furniture)
    return target.getvalue()


def inspect_pdf(data: bytes) -> dict:
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported")
    return {"pages": len(reader.pages), "sha256": digest(data), "bytes": len(data)}


def bind_pdfs(
    documents: list[tuple[str, bytes]],
    *,
    title: str = "Documents",
    font_path: str | None = None,
    preserve_size: bool = False,
) -> bytes:
    """Fit originals above an A4 footer, or preserve source geometry, and add bookmarks."""
    font, _ = fonts(font_path)
    writer = PdfWriter()
    readers = [(label, PdfReader(io.BytesIO(data))) for label, data in documents]
    if any(reader.is_encrypted for _, reader in readers):
        raise ValueError("Encrypted PDFs are not supported")
    total = sum(len(reader.pages) for _, reader in readers)
    if not total:
        raise ValueError("At least one PDF page is required")
    for label, reader in readers:
        start = len(writer.pages)
        for page in reader.pages:
            page.transfer_rotation_to_content()
            source_width = float(page.cropbox.width)
            source_height = float(page.cropbox.height)
            if source_width <= 0 or source_height <= 0:
                raise ValueError("PDF page has invalid dimensions")
            size = (
                (source_width, source_height)
                if preserve_size
                else (landscape(A4) if source_width > source_height else A4)
            )
            width, height = size
            if preserve_size:
                scale = 1
                x = y = 0
            else:
                area_width, area_height = width - 24 * mm, height - 30 * mm
                scale = min(area_width / source_width, area_height / source_height)
                x = (width - source_width * scale) / 2
                y = 18 * mm + (area_height - source_height * scale) / 2
            target = writer.add_blank_page(width, height)
            transform = Transformation().translate(
                -float(page.cropbox.left), -float(page.cropbox.bottom)
            )
            target.merge_transformed_page(page, transform.scale(scale).translate(x, y))
            overlay = io.BytesIO()
            stamp = canvas.Canvas(overlay, pagesize=size, invariant=1)
            stamp.setFont(font, 7.5)
            stamp.setFillColor(MUTED)
            text = label
            while pdfmetrics.stringWidth(text, font, 7.5) > width - 70 * mm and text:
                text = text[:-1]
            stamp_y = 4 * mm if preserve_size else 9 * mm
            stamp.drawString(12 * mm, stamp_y, text)
            stamp.drawRightString(width - 12 * mm, stamp_y, f"{len(writer.pages)} / {total}")
            stamp.save()
            target.merge_page(PdfReader(overlay).pages[0])
        if len(reader.pages):
            writer.add_outline_item(label, start)
    writer.add_metadata({"/Title": title, "/Author": ""})
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def extract_pdf(data: bytes, pages: list[int]) -> bytes:
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported")
    if not pages or any(number < 1 or number > len(reader.pages) for number in pages):
        raise ValueError("Page numbers must be within the source PDF (1-based)")
    writer = PdfWriter()
    for number in pages:
        writer.add_page(reader.pages[number - 1])
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def export(store: Store, args) -> dict:
    """CLI adapter: workspace confinement, immutable output and provenance manifest."""
    sources = args.sources if args.pdf_command == "bind" else [args.source]
    paths = [store.path(str(source)) for source in sources]
    for path in paths:
        if not path.is_file():
            raise ValueError("PDF source must be an existing file in the private workspace")
    bodies = [path.read_bytes() for path in paths]
    if args.pdf_command == "inspect":
        return inspect_pdf(bodies[0])
    output = Path(args.output)
    if output.is_absolute() or output.suffix.lower() != ".pdf":
        raise ValueError("PDF output must be a relative .pdf path inside the private workspace")
    destination = store.path(str(output))
    if destination in paths:
        raise ValueError("PDF input and output must be different files")
    relative = destination.relative_to(store.home).as_posix()
    resources = {}
    if args.pdf_command == "render":
        if paths[0].suffix.lower() not in {".md", ".txt"}:
            raise ValueError("PDF render accepts Markdown and text files")
        data = render_markdown(
            bodies[0].decode("utf-8"),
            title=args.title,
            subtitle=args.subtitle,
            font_size=args.font_size,
            wide=args.landscape,
            font_path=store.settings.get("pdf_font"),
            source_dir=paths[0].parent,
            resource_root=store.home,
            resources=resources,
        )
    else:
        if any(path.suffix.lower() != ".pdf" for path in paths):
            raise ValueError("PDF bind and extract accept PDF files")
        if args.pdf_command == "bind":
            data = bind_pdfs(
                [(path.stem, body) for path, body in zip(paths, bodies)],
                title=args.title or "Documents",
                font_path=store.settings.get("pdf_font"),
                preserve_size=args.preserve_size,
            )
        else:
            data = extract_pdf(bodies[0], args.pages)
    manifest = {
        "schema_version": 1,
        "operation": args.pdf_command,
        "output": relative,
        **inspect_pdf(data),
        "sources": [
            {"path": path.relative_to(store.home).as_posix(), "sha256": digest(body)}
            for path, body in zip(paths, bodies)
        ],
        "resources": resources,
        "options": {
            key: getattr(args, key)
            for key in ("title", "subtitle", "landscape", "pages", "font_size", "preserve_size")
            if hasattr(args, key)
        },
        "review_status": "pending",
        "note": "Mechanical export; not content or visual approval",
    }
    manifest_path = relative + ".manifest.json"
    manifest_bytes = encode(manifest).encode()
    # Preflight both artifacts so an immutable manifest conflict cannot leave a new PDF.
    for name, value in [(relative, data), (manifest_path, manifest_bytes)]:
        target = store.path(name)
        if target.exists() and target.read_bytes() != value:
            raise ValueError("Immutable artifact conflict; create a new version")
        row = store.db.execute("SELECT sha256 FROM artifacts WHERE path=?", (name,)).fetchone()
        if row and row[0] != digest(value):
            raise ValueError("Registered artifact integrity conflict; create a new version")
    store.artifact(relative, data)
    store.artifact(manifest_path, manifest_bytes)
    record = {"id": "pdf-" + digest(manifest_bytes)[:20], **manifest, "manifest": manifest_path}
    store.put("pdf_documents", record, immutable=True)
    store.event(
        "pdf_exported",
        [],
        {
            "output": relative,
            "manifest": manifest_path,
            "sha256": manifest["sha256"],
            "operation": args.pdf_command,
        },
    )
    return record
