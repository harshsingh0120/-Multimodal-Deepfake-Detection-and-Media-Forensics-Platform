"""Minimal, dependency-light Markdown -> PDF converter (ReportLab).

Supports the subset used in this project's reports: #/##/### headings, paragraphs,
**bold**, `inline code`, bullet lists, pipe tables, --- rules, and fenced code blocks.
Non-Latin glyphs (emoji) that the core PDF fonts can't render are mapped/stripped so the
output stays clean.

Usage:
    python scripts/md_to_pdf.py INPUT.md OUTPUT.pdf
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (HRFlowable, ListFlowable, ListItem, Paragraph,
                                Preformatted, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

# Map glyphs the base-14 fonts don't have to safe ASCII; strip the rest.
_GLYPHS = {
    "↑": " (higher better)", "↓": " (lower better)", "→": "->", "⟶": "->",
    "–": "-", "—": "-", "“": '"', "”": '"', "‘": "'", "’": "'", "·": "-",
    "≈": "~", "×": "x", "✅": "", "⚠️": "Note:", "⚠": "Note:", "📈": "",
    "📉": "", "🎯": "", "🛡️": "", "➕": "+", "☐": "[ ]", "☑": "[x]",
    "±": "+/-", "…": "...",
}


def _clean(text: str) -> str:
    for k, v in _GLYPHS.items():
        text = text.replace(k, v)
    # drop any remaining non-latin-1 chars (e.g. stray emoji) to avoid tofu boxes
    return text.encode("latin-1", "ignore").decode("latin-1")


def _inline(text: str) -> str:
    """Convert inline markdown to ReportLab mini-HTML."""
    text = _clean(text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", text)   # bold+italic first
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\w)\*(.+?)\*(?!\w)", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+?)`", r'<font face="Courier">\1</font>', text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<link href="\2"><font color="#2563eb">\1</font></link>', text)
    return text


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("Title2", parent=ss["Title"], fontSize=20, spaceAfter=6,
                          textColor=colors.HexColor("#0f1424")))
    ss.add(ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, spaceBefore=12,
                          spaceAfter=5, textColor=colors.HexColor("#14b8a6")))
    ss.add(ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12.5, spaceBefore=9,
                          spaceAfter=4, textColor=colors.HexColor("#1f2937")))
    ss.add(ParagraphStyle("H3", parent=ss["Heading3"], fontSize=11, spaceBefore=7,
                          spaceAfter=3, textColor=colors.HexColor("#374151")))
    ss.add(ParagraphStyle("Body2", parent=ss["BodyText"], fontSize=9.5, leading=13))
    ss.add(ParagraphStyle("Cell", parent=ss["BodyText"], fontSize=8.2, leading=10.5))
    ss.add(ParagraphStyle("CellH", parent=ss["BodyText"], fontSize=8.4, leading=10.5,
                          textColor=colors.white, fontName="Helvetica-Bold"))
    return ss


def _table(rows, ss, width):
    header, *body = rows
    ncol = len(header)
    data = [[Paragraph(_inline(c), ss["CellH"]) for c in header]]
    for r in body:
        r = (r + [""] * ncol)[:ncol]
        data.append([Paragraph(_inline(c), ss["Cell"]) for c in r])
    t = Table(data, colWidths=[width / ncol] * ncol, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d3748")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f6fa")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def convert(md_path: Path, pdf_path: Path):
    lines = md_path.read_text(encoding="utf-8").splitlines()
    ss = _styles()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, topMargin=16 * mm,
                            bottomMargin=16 * mm, leftMargin=16 * mm, rightMargin=16 * mm,
                            title=md_path.stem)
    avail = A4[0] - 32 * mm
    story = []
    i = 0
    bullets: list = []

    def flush_bullets():
        nonlocal bullets
        if bullets:
            story.append(ListFlowable(
                [ListItem(Paragraph(_inline(b), ss["Body2"]), leftIndent=6) for b in bullets],
                bulletType="bullet", start="•", leftIndent=12))
            story.append(Spacer(1, 2))
            bullets = []

    while i < len(lines):
        line = lines[i]

        if line.strip().startswith("```"):           # fenced code
            flush_bullets()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(_clean(lines[i]))
                i += 1
            i += 1
            story.append(Preformatted("\n".join(buf), ParagraphStyle(
                "code", fontName="Courier", fontSize=7.8, leading=9.5,
                backColor=colors.HexColor("#f3f6fa"), borderPadding=4)))
            story.append(Spacer(1, 4))
            continue

        if line.strip().startswith("|") and "|" in line.strip()[1:]:   # table
            flush_bullets()
            tbl = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not re.match(r"^[\s:\-]+$", "".join(cells)):        # skip |---| row
                    tbl.append(cells)
                i += 1
            if tbl:
                story.append(_table(tbl, ss, avail))
                story.append(Spacer(1, 6))
            continue

        s = line.strip()
        if not s:
            flush_bullets()
            story.append(Spacer(1, 4))
        elif s.startswith("### "):
            flush_bullets(); story.append(Paragraph(_inline(s[4:]), ss["H3"]))
        elif s.startswith("## "):
            flush_bullets(); story.append(Paragraph(_inline(s[3:]), ss["H2"]))
        elif s.startswith("# "):
            flush_bullets(); story.append(Paragraph(_inline(s[2:]), ss["Title2"]))
        elif re.match(r"^(---+|\*\*\*+)$", s):
            flush_bullets(); story.append(HRFlowable(width="100%",
                             color=colors.HexColor("#cbd5e0"), spaceBefore=4, spaceAfter=6))
        elif s.startswith("- ") or s.startswith("* "):
            bullets.append(s[2:])
        else:
            flush_bullets(); story.append(Paragraph(_inline(s), ss["Body2"]))
        i += 1

    flush_bullets()
    doc.build(story)
    return pdf_path


if __name__ == "__main__":
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".pdf")
    out = convert(src, dst)
    print("wrote", out, out.stat().st_size, "bytes")
