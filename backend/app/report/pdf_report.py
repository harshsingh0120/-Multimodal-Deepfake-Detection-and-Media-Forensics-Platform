"""Build a downloadable forensic PDF report from an analysis result (ReportLab)."""
from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (HRFlowable, Image, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from ..utils.imaging import data_uri_to_png_bytes

_BAND_COLORS = {
    "Low": colors.HexColor("#1a7f52"),
    "Guarded": colors.HexColor("#b7791f"),
    "Elevated": colors.HexColor("#c05621"),
    "High": colors.HexColor("#c53030"),
    "Very High": colors.HexColor("#9b2c2c"),
}


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("H1x", parent=ss["Heading1"], fontSize=18, spaceAfter=4,
                          textColor=colors.HexColor("#1a202c")))
    ss.add(ParagraphStyle("H2x", parent=ss["Heading2"], fontSize=13, spaceBefore=10,
                          spaceAfter=4, textColor=colors.HexColor("#2d3748")))
    ss.add(ParagraphStyle("Body", parent=ss["BodyText"], fontSize=9.5, leading=13,
                          alignment=TA_LEFT))
    ss.add(ParagraphStyle("Small", parent=ss["BodyText"], fontSize=8, leading=11,
                          textColor=colors.HexColor("#4a5568")))
    ss.add(ParagraphStyle("Mono", parent=ss["BodyText"], fontSize=8, leading=11,
                          fontName="Courier"))
    return ss


def build_pdf(result: dict, analysis_id: str) -> bytes:
    ss = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=16 * mm, bottomMargin=16 * mm,
                            leftMargin=16 * mm, rightMargin=16 * mm,
                            title=f"Forensic Report {analysis_id}")
    story = []
    fusion = result["fusion"]
    media = result["media"]
    band = fusion["verdict_band"]
    band_color = _BAND_COLORS.get(band, colors.HexColor("#2d3748"))

    # Header
    story.append(Paragraph("Media Forensic Assessment", ss["H1x"]))
    story.append(Paragraph("Multimodal Deepfake Detection &amp; Media Forensics Platform",
                           ss["Small"]))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#cbd5e0"), spaceAfter=8))

    # Verdict box
    overall_pct = f"{fusion['overall_score'] * 100:.0f}%"
    conf_pct = f"{fusion['calibrated_confidence'] * 100:.0f}%"
    verdict_tbl = Table([
        [Paragraph(f"<b>Verdict band:</b> {band}", ss["Body"]),
         Paragraph(f"<b>Manipulation-evidence score:</b> {overall_pct}", ss["Body"])],
        [Paragraph(f"<b>Calibrated confidence:</b> {conf_pct}", ss["Body"]),
         Paragraph(f"<b>Cross-modal consistency:</b> "
                   f"{_fmt(fusion.get('cross_modal_consistency'))}", ss["Body"])],
    ], colWidths=[85 * mm, 85 * mm])
    verdict_tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.2, band_color),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7fafc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(verdict_tbl)
    story.append(Spacer(1, 4))
    story.append(Paragraph(fusion["verdict_text"], ss["Body"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<i>{result['safety_notice']}</i>", ss["Small"]))

    # File metadata
    story.append(Paragraph("File", ss["H2x"]))
    meta_rows = [
        ["Filename", str(media.get("filename"))],
        ["Media type", str(media.get("media_type"))],
        ["Size", f"{media.get('size_bytes', 0) / 1024:.0f} KB"],
        ["Duration", _fmt(media.get("duration_sec"), "s")],
        ["Resolution", f"{media.get('width')}x{media.get('height')}"
            if media.get("width") else "n/a"],
        ["Has audio", str(media.get("has_audio"))],
        ["Analysis ID", analysis_id],
        ["Engine", result.get("engine", "")],
        ["Generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
    ]
    story.append(_kv_table(meta_rows, ss))

    # Per-modality sections
    story.append(Paragraph("Per-Modality Findings", ss["H2x"]))
    mod_summary = [["Modality", "Available", "Score", "Confidence"]]
    for m in result["modalities"]:
        mod_summary.append([
            m["modality"].capitalize(),
            "yes" if m["available"] else "no",
            f"{m['score'] * 100:.0f}%" if m["available"] else "-",
            f"{m['confidence'] * 100:.0f}%" if m["available"] else "-",
        ])
    t = Table(mod_summary, colWidths=[45 * mm, 30 * mm, 35 * mm, 35 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d3748")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    for m in result["modalities"]:
        if not m["available"]:
            story.append(Paragraph(f"<b>{m['modality'].capitalize()}</b> — {m['summary']}",
                                   ss["Small"]))
            continue
        story.append(Paragraph(
            f"{m['modality'].capitalize()} &mdash; score {m['score'] * 100:.0f}% "
            f"(confidence {m['confidence'] * 100:.0f}%)", ss["H2x"]))
        story.append(Paragraph(m["summary"], ss["Body"]))
        for ev in m["evidence"][:6]:
            story.append(Paragraph(
                f"&bull; <b>{ev['name']}</b> ({ev['contribution'] * 100:.0f}%): {ev['detail']}",
                ss["Small"]))
        for note in m.get("notes", []):
            story.append(Paragraph(f"<i>Note: {note}</i>", ss["Small"]))

        # Heatmaps
        for hm in m.get("heatmaps", [])[:2]:
            try:
                img = Image(io.BytesIO(data_uri_to_png_bytes(hm["image"])))
                img._restrictSize(150 * mm, 70 * mm)
                story.append(Spacer(1, 3))
                story.append(img)
                story.append(Paragraph(f"<b>{hm['title']}.</b> {hm['description']}", ss["Small"]))
            except Exception:
                pass

        # Flagged frames / segments
        if m.get("flagged_frames"):
            story.append(Paragraph("Flagged frames: " + ", ".join(
                f"{f['timestamp_sec']}s ({f['score'] * 100:.0f}%)"
                for f in m["flagged_frames"][:8]), ss["Small"]))
        if m.get("flagged_segments"):
            story.append(Paragraph("Flagged audio segments: " + ", ".join(
                f"{s['start_sec']}-{s['end_sec']}s ({s['score'] * 100:.0f}%)"
                for s in m["flagged_segments"][:8]), ss["Small"]))

    # Fusion rationale
    story.append(Paragraph("Fusion Rationale", ss["H2x"]))
    for r in fusion.get("rationale", []):
        story.append(Paragraph(f"&bull; {r}", ss["Small"]))

    # Limitations
    story.append(Paragraph("Limitations &amp; Failure Cases", ss["H2x"]))
    for lim in result.get("limitations", []):
        story.append(Paragraph(f"&bull; {lim}", ss["Small"]))

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#cbd5e0")))
    story.append(Paragraph(
        "Generated by the Multimodal Deepfake Detection &amp; Media Forensics Platform. "
        "For investigative assistance only; not a definitive authentication service.",
        ss["Small"]))

    doc.build(story)
    return buf.getvalue()


def _kv_table(rows, ss):
    data = [[Paragraph(f"<b>{k}</b>", ss["Small"]), Paragraph(str(v), ss["Small"])]
            for k, v in rows]
    t = Table(data, colWidths=[40 * mm, 130 * mm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def _fmt(v, suffix=""):
    if v is None:
        return "n/a"
    try:
        return f"{float(v):.2f}{suffix}"
    except (TypeError, ValueError):
        return str(v)
