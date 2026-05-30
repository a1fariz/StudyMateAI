"""
PDF Exporter service: generate beautiful PDF files from summaries using ReportLab.
"""

import io
import logging
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

logger = logging.getLogger(__name__)


def generate_summary_pdf(filename: str, title: str, summary_points: list[str]) -> io.BytesIO:
    """
    Generate a styled PDF summary using ReportLab.

    Args:
        filename: Original file name.
        title: Title of the document.
        summary_points: List of summary points.

    Returns:
        BytesIO buffer containing the PDF binary.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#312e81"),  # Dark Indigo
        spaceAfter=15,
        alignment=0,  # Left align
    )

    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#4b5563"),  # Gray
        spaceAfter=30,
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#4f46e5"),  # Indigo
        spaceAfter=15,
        keepWithNext=True,
    )

    bullet_style = ParagraphStyle(
        "BulletPoint",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#1f2937"),  # Dark Gray
        spaceAfter=10,
    )

    # Document Header
    story.append(Paragraph("StudyMate AI Summary Report", title_style))
    story.append(
        Paragraph(
            f"<b>Source Document:</b> {filename}<br/>"
            f"<b>Generated On:</b> {colors.HexColor('#000000')}"  # Simple metadata
            f"Study Assistant AI",
            meta_style,
        )
    )

    story.append(Spacer(1, 10))

    # Summary Section
    story.append(Paragraph(f"Key Takeaways: {title}", heading_style))

    # Add points in a styled list format
    for idx, point in enumerate(summary_points, 1):
        point_text = f"<b>{idx}.</b> {point}"
        story.append(Paragraph(point_text, bullet_style))

    # Footer note (Simple table decoration)
    story.append(Spacer(1, 40))
    data = [["Powered by StudyMate AI - Your Intelligent Study Companion"]]
    footer_table = Table(data, colWidths=[500])
    footer_table.setStyle(
        TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#9ca3af")),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Oblique"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LINEABOVE", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    story.append(footer_table)

    try:
        doc.build(story)
        logger.info(f"Successfully generated summary PDF for '{filename}'")
    except Exception as e:
        logger.error(f"Failed to generate summary PDF: {e}")
        raise

    buffer.seek(0)
    return buffer
