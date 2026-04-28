from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Image, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
import os, re
from datetime import datetime


def clean_text(text: str) -> str:
    """Remove problematic unicode characters and clean markdown syntax."""
    # Remove zero-width and special unicode characters
    text = re.sub(r'[\u200b-\u200f\u202a-\u202e\ufeff]', '', text)
    # Remove box drawing characters
    text = re.sub(r'[\u2500-\u257f]', '', text)
    # Replace em-dash, en-dash with regular dash
    text = text.replace('—', '-').replace('–', '-')
    # Replace smart quotes with regular quotes
    text = text.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
    # Remove remaining non-ASCII printable chars
    text = ''.join(c if ord(c) < 128 or c in '°±×÷' else '' for c in text)
    return text.strip()


def parse_markdown_table(lines: list[str]) -> list[list[str]]:
    """Extract rows from a markdown table."""
    rows = []
    for line in lines:
        line = clean_text(line)
        if not line:
            continue
        # Skip separator lines like |---|---|
        if set(line.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
            continue
        if "|" in line:
            cells = [clean_text(c) for c in line.strip("|").split("|")]
            rows.append(cells)
    return rows


def build_pdf_table(rows: list[list[str]]):
    """Build a ReportLab Table from parsed markdown rows with text wrapping."""
    if not rows:
        return None

    col_count = max(len(r) for r in rows)
    # Normalize row lengths
    normalized = [r + [""] * (col_count - len(r)) for r in rows]

    # Clean bold markers and wrap text in Paragraphs for proper word wrapping
    cell_style = ParagraphStyle(
        "CellStyle",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=HexColor("#333333"),
    )
    header_style = ParagraphStyle(
        "HeaderStyle",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.white,
        alignment=TA_CENTER,
    )

    wrapped_data = []
    for i, row in enumerate(normalized):
        wrapped_row = []
        for cell in row:
            cell_clean = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", cell)
            cell_clean = clean_text(cell_clean)
            style = header_style if i == 0 else cell_style
            wrapped_row.append(Paragraph(cell_clean, style))
        wrapped_data.append(wrapped_row)

    page_width = A4[0] - 4 * cm
    col_width = page_width / col_count

    table = Table(wrapped_data, colWidths=[col_width] * col_count, repeatRows=1)
    table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        # Body rows
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f9f9f9"), HexColor("#ffffff")]),
        ("TEXTCOLOR", (0, 1), (-1, -1), HexColor("#333333")),
        ("ALIGN", (0, 1), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def generate_pdf_report(report_text: str, plots: list[str], output_path: str = "report.pdf"):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("CustomTitle", parent=styles["Title"],
                                fontSize=22, textColor=HexColor("#1a1a2e"), spaceAfter=6)
    subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"],
                                    fontSize=10, textColor=HexColor("#666666"), spaceAfter=20)
    h1_style = ParagraphStyle("H1", parent=styles["Heading1"],
                            fontSize=14, textColor=HexColor("#16213e"), spaceBefore=16, spaceAfter=6)
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"],
                            fontSize=12, textColor=HexColor("#0f3460"), spaceBefore=12, spaceAfter=4)
    body_style = ParagraphStyle("Body", parent=styles["Normal"],
                                fontSize=10, leading=16, textColor=HexColor("#333333"), spaceAfter=6)
    bullet_style = ParagraphStyle("Bullet", parent=styles["Normal"],
                                fontSize=10, leading=16, leftIndent=20,
                                textColor=HexColor("#333333"), spaceAfter=4)
    footer_style = ParagraphStyle("Footer", parent=styles["Normal"],
                                fontSize=8, textColor=HexColor("#999999"), alignment=TA_CENTER)

    story = []

    # Header
    story.append(Paragraph("Data Analyst Agent — Report", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=HexColor("#1a1a2e")))
    story.append(Spacer(1, 0.4*cm))

    # Parse report
    lines = report_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = clean_text(line.strip())

        # Skip markdown horizontal rules
        if re.fullmatch(r"-{2,}|={2,}", stripped):
            story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#cccccc")))
            i += 1
            continue

        # Detect markdown table
        if "|" in stripped and i + 1 < len(lines) and re.match(r"[\|\s\-:]+", lines[i + 1]):
            table_lines = []
            while i < len(lines) and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1
            rows = parse_markdown_table(table_lines)
            if rows:
                tbl = build_pdf_table(rows)
                if tbl:
                    story.append(Spacer(1, 0.2*cm))
                    story.append(tbl)
                    story.append(Spacer(1, 0.3*cm))
            continue

        # Headings
        if stripped.startswith("# "):
            story.append(Paragraph(clean_text(stripped[2:]), h1_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#dddddd")))
        elif stripped.startswith("## "):
            story.append(Paragraph(clean_text(stripped[3:]), h2_style))
        elif stripped.startswith("### "):
            story.append(Paragraph(clean_text(stripped[4:]), h2_style))

        # Bullets
        elif stripped.startswith("- ") or stripped.startswith("* "):
            clean = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", stripped[2:])
            clean = clean_text(clean)
            story.append(Paragraph(f"• {clean}", bullet_style))

        # Empty line
        elif not stripped:
            story.append(Spacer(1, 0.2*cm))

        # Normal paragraph
        else:
            clean = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", stripped)
            clean = clean_text(clean)
            if clean:  # Only add non-empty paragraphs
                story.append(Paragraph(clean, body_style))

        i += 1

    # Plots
    if plots:
        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(width="100%", thickness=2, color=HexColor("#1a1a2e")))
        story.append(Paragraph("Generated Visualizations", h1_style))
        story.append(Spacer(1, 0.3*cm))
        for plot_path in plots:
            if os.path.exists(plot_path):
                story.append(Image(plot_path, width=16*cm, height=10*cm, kind="proportional"))
                story.append(Spacer(1, 0.4*cm))

    # Footer
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#cccccc")))
    story.append(Paragraph("Generated by Agentic Data Analyst — Powered by LangGraph", footer_style))

    doc.build(story)
    return output_path