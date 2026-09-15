"""Readable exports for preparation plans: redacted Markdown text and PDF.

The dashboard stays read-only. Exports are rendered in memory from the journal
snapshot and registered, integrity-checked artifacts; nothing is written to the
workspace.
"""

from __future__ import annotations

import html
import io
import re
from pathlib import Path, PurePosixPath

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

TEXT_SUFFIXES = frozenset({".md", ".txt"})
MAX_TEXT_BYTES = 1_000_000
LOCAL_PATH_IN_TEXT = re.compile(
    r"(?:~/|/(?:Users|home|private|var/folders|tmp|root|srv|mnt|Volumes)/)[^\s`'\"<>()\[\]|,;]+"
)
FONT_CANDIDATES = (
    (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ),
    (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ),
    ("/Library/Fonts/Arial Unicode.ttf", None),
)
FONT = "PlanUnicode"
FONT_BOLD = "PlanUnicode-Bold"

LABELS = {
    "ru": {
        "learning": "План подготовки",
        "interview_plans": "План интервью",
        "product": "Продуктовое",
        "technical-leadership": "Техническое лидерство",
        "vacancy": "Вакансия",
        "created": "Создан",
        "hours": "Часов в неделю",
        "interview_date": "Дата интервью",
        "not_set": "не назначена",
        "weeks": "Недельный план",
        "week": "Неделя",
        "focus": "Фокус",
        "deliverable": "Результат",
        "status": "Статус",
        "gaps": "Пробелы и что закрыть",
        "requirement": "Требование",
        "type": "Тип",
        "mandatory": "Обязательное",
        "next_action": "Следующий шаг",
        "done_requires": "Критерий готовности",
        "resources": "Материалы",
        "shared": "Общие материалы",
        "objectives": "Цели",
        "plan": "Подробный план",
        "yes": "да",
        "no": "нет",
        "todo": "к выполнению",
        "in_progress": "в работе",
        "completed": "выполнено",
        "structural": "структурный",
        "evidence": "доказательства",
        "interview": "интервью",
        "practice": "практика",
        "footer": "Career Copilot · приватный документ",
        "missing_plan": "Файл подробного плана недоступен или не прошёл проверку целостности.",
    },
    "en": {
        "learning": "Learning plan",
        "interview_plans": "Interview plan",
        "product": "Product",
        "technical-leadership": "Technical leadership",
        "vacancy": "Vacancy",
        "created": "Created",
        "hours": "Hours per week",
        "interview_date": "Interview date",
        "not_set": "not scheduled",
        "weeks": "Weekly plan",
        "week": "Week",
        "focus": "Focus",
        "deliverable": "Deliverable",
        "status": "Status",
        "gaps": "Gaps to close",
        "requirement": "Requirement",
        "type": "Type",
        "mandatory": "Mandatory",
        "next_action": "Next step",
        "done_requires": "Done when",
        "resources": "Resources",
        "shared": "Shared materials",
        "objectives": "Objectives",
        "plan": "Detailed plan",
        "yes": "yes",
        "no": "no",
        "todo": "to do",
        "in_progress": "in progress",
        "completed": "completed",
        "structural": "structural",
        "evidence": "evidence",
        "interview": "interview",
        "practice": "practice",
        "footer": "Career Copilot · private document",
        "missing_plan": "The detailed plan file is unavailable or failed its integrity check.",
    },
}


def redact_local_text(text: str) -> str:
    """Replace absolute operator paths inside prose with a neutral file reference."""

    def replace(match: re.Match[str]) -> str:
        name = PurePosixPath(match.group(0).rstrip(".:")).name
        return f"[local]/{name}" if name else "[local]"

    return LOCAL_PATH_IN_TEXT.sub(replace, text)


def _register_fonts() -> None:
    if FONT in pdfmetrics.getRegisteredFontNames():
        return
    for regular, bold in FONT_CANDIDATES:
        if Path(regular).is_file():
            pdfmetrics.registerFont(TTFont(FONT, regular))
            bold_path = bold if bold and Path(bold).is_file() else regular
            pdfmetrics.registerFont(TTFont(FONT_BOLD, bold_path))
            pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=FONT_BOLD)
            return
    raise ValueError("A Unicode TTF font is required to render plan PDFs")


def _inline(text: str) -> str:
    """Escape text, then allow the small Markdown subset used by plans."""
    escaped = html.escape(redact_local_text(str(text)), quote=False)
    escaped = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", escaped)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"`([^`]+)`", r'<font color="#192b88">\1</font>', escaped)
    return escaped


def markdown_blocks(text: str) -> list[tuple]:
    """Parse headings, paragraphs, lists and pipe tables; everything else stays text."""
    blocks: list[tuple] = []
    paragraph: list[str] = []
    lines = text.replace("\r\n", "\n").split("\n")

    def flush() -> None:
        if paragraph:
            blocks.append(("p", " ".join(part.strip() for part in paragraph)))
            paragraph.clear()

    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if not stripped:
            flush()
        elif heading:
            flush()
            blocks.append(("h", len(heading.group(1)), heading.group(2).strip()))
        elif stripped.startswith("|"):
            flush()
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells if cell):
                    rows.append(cells)
                index += 1
            if rows:
                blocks.append(("table", rows))
            continue
        elif re.match(r"^([-*]|\d+\.)\s+", stripped):
            flush()
            ordered = bool(re.match(r"^\d+\.", stripped))
            items = []
            marker = r"^\s*\d+\.\s+" if ordered else r"^\s*[-*]\s+"
            while index < len(lines) and re.match(marker, lines[index]):
                items.append(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[index]).strip())
                index += 1
            blocks.append(("ol" if ordered else "ul", items))
            continue
        else:
            paragraph.append(stripped)
        index += 1
    flush()
    return blocks


class _Styles:
    def __init__(self) -> None:
        self.body = ParagraphStyle("body", fontName=FONT, fontSize=9.5, leading=13.5, spaceAfter=5)
        self.small = ParagraphStyle(
            "small", parent=self.body, fontSize=8, leading=10.5, spaceAfter=0
        )
        self.muted = ParagraphStyle("muted", parent=self.body, textColor=colors.HexColor("#575e70"))
        self.title = ParagraphStyle(
            "title", fontName=FONT_BOLD, fontSize=19, leading=23, spaceAfter=8
        )
        self.h = {
            1: ParagraphStyle(
                "h1", fontName=FONT_BOLD, fontSize=15, leading=19, spaceBefore=10, spaceAfter=6
            ),
            2: ParagraphStyle(
                "h2", fontName=FONT_BOLD, fontSize=12.5, leading=16, spaceBefore=10, spaceAfter=5
            ),
            3: ParagraphStyle(
                "h3", fontName=FONT_BOLD, fontSize=10.5, leading=14, spaceBefore=8, spaceAfter=4
            ),
        }


def _table(rows: list[list[str]], styles: _Styles, width: float) -> Table:
    columns = max(len(row) for row in rows)
    padded = [row + [""] * (columns - len(row)) for row in rows]
    data = [[Paragraph(_inline(cell), styles.small) for cell in row] for row in padded]
    table = Table(data, colWidths=[width / columns] * columns, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cacbd0")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaedf8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _markdown_flowables(text: str, styles: _Styles, width: float) -> list:
    flowables: list = []
    for block in markdown_blocks(text):
        if block[0] == "h":
            flowables.append(Paragraph(_inline(block[2]), styles.h[min(block[1], 3)]))
        elif block[0] == "p":
            flowables.append(Paragraph(_inline(block[1]), styles.body))
        elif block[0] in {"ul", "ol"}:
            items = [ListItem(Paragraph(_inline(item), styles.body)) for item in block[1]]
            kind = "1" if block[0] == "ol" else "bullet"
            flowables.append(
                ListFlowable(items, bulletType=kind, leftIndent=12, bulletFontName=FONT)
            )
        elif block[0] == "table":
            flowables += [_table(block[1], styles, width), Spacer(1, 6)]
    return flowables


def _value(labels: dict, value: object) -> str:
    if isinstance(value, bool):
        return labels["yes"] if value else labels["no"]
    if value is None or value == "":
        return "—"
    return labels.get(str(value), str(value))


def plan_pdf(
    record: dict,
    lang: str,
    vacancy: dict | None = None,
    company: dict | None = None,
    plan_text: str | None = None,
) -> bytes:
    """Render a learning or interview plan into a PDF document."""
    _register_fonts()
    labels = LABELS["en" if lang == "en" else "ru"]
    payload = record["payload"]
    kind = record["kind"]
    styles = _Styles()
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"{labels[kind]} · {_value(labels, payload.get('track'))}",
        author="Career Copilot",
    )
    width = document.width
    story: list = [
        Paragraph(_inline(f"{labels[kind]} · {_value(labels, payload.get('track'))}"), styles.title)
    ]
    meta = []
    if vacancy:
        name = vacancy["payload"].get("title") or vacancy["id"]
        company_name = (company or {}).get("payload", {}).get("name")
        meta.append(f"{labels['vacancy']}: {name}" + (f" · {company_name}" if company_name else ""))
    if payload.get("created_at"):
        meta.append(f"{labels['created']}: {str(payload['created_at'])[:16].replace('T', ' ')} UTC")
    if kind == "learning":
        meta.append(f"{labels['hours']}: {_value(labels, payload.get('hours_per_week'))}")
        meta.append(
            f"{labels['interview_date']}: {payload.get('interview_date') or labels['not_set']}"
        )
    for line in meta:
        story.append(Paragraph(_inline(line), styles.muted))
    if payload.get("warning"):
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>!</b> {_inline(payload['warning'])}", styles.body))

    if kind == "learning":
        weeks = payload.get("weeks") if isinstance(payload.get("weeks"), list) else []
        if weeks:
            story.append(Paragraph(labels["weeks"], styles.h[2]))
            rows = [[labels["week"], labels["focus"], labels["deliverable"], labels["status"]]]
            rows += [
                [
                    str(week.get("week", "")),
                    str(week.get("focus", "")),
                    str(week.get("deliverable", "")),
                    _value(labels, week.get("status")),
                ]
                for week in weeks
                if isinstance(week, dict)
            ]
            table = _table(rows, styles, width)
            table._argW = [width * 0.1, width * 0.3, width * 0.42, width * 0.18]
            story.append(table)
        gaps = payload.get("gaps") if isinstance(payload.get("gaps"), list) else []
        if gaps:
            story.append(Paragraph(labels["gaps"], styles.h[2]))
            for number, gap in enumerate((gap for gap in gaps if isinstance(gap, dict)), start=1):
                lines = [Paragraph(f"<b>{number}. {_inline(gap.get('text', ''))}</b>", styles.body)]
                details = [
                    (labels["type"], _value(labels, gap.get("gap_type"))),
                    (labels["mandatory"], _value(labels, gap.get("mandatory"))),
                    (labels["status"], _value(labels, gap.get("status"))),
                    (labels["next_action"], _value(labels, gap.get("next_action"))),
                    (labels["done_requires"], _value(labels, gap.get("done_requires"))),
                ]
                resources = gap.get("resources")
                if isinstance(resources, list) and resources:
                    details.append((labels["resources"], "; ".join(map(str, resources))))
                for name, value in details:
                    lines.append(Paragraph(f"{_inline(name)}: {_inline(value)}", styles.small))
                lines.append(Spacer(1, 6))
                story.append(KeepTogether(lines))
        shared = payload.get("shared")
        if isinstance(shared, list) and shared:
            story.append(Paragraph(labels["shared"], styles.h[2]))
            story.append(
                ListFlowable(
                    [ListItem(Paragraph(_inline(item), styles.body)) for item in shared],
                    bulletType="bullet",
                    leftIndent=12,
                )
            )
    else:
        objectives = payload.get("objectives")
        if isinstance(objectives, list) and objectives:
            story.append(Paragraph(labels["objectives"], styles.h[2]))
            story.append(
                ListFlowable(
                    [ListItem(Paragraph(_inline(item), styles.body)) for item in objectives],
                    bulletType="1",
                    leftIndent=12,
                )
            )
        story.append(Paragraph(labels["plan"], styles.h[2]))
        if plan_text:
            story += _markdown_flowables(plan_text, styles, width)
        else:
            story.append(Paragraph(labels["missing_plan"], styles.muted))

    def footer(canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont(FONT, 7.5)
        canvas.setFillColor(colors.HexColor("#575e70"))
        canvas.drawString(doc.leftMargin, 9 * mm, labels["footer"])
        canvas.drawRightString(doc.leftMargin + doc.width, 9 * mm, str(doc.page))
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
