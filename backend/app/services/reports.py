import io
import csv
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.models import Violation

def generate_csv_report(violations: List[Violation]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "Fine Reference",
        "License Plate",
        "Violation Type",
        "Location",
        "Date & Time",
        "Fine Amount (INR)",
        "Status",
        "Source",
        "Needs Review",
        "Paid At",
        "Payment Ref",
        "Notes"
    ])
    
    for v in violations:
        writer.writerow([
            v.fine_ref,
            v.plate_number,
            v.violation_type,
            v.location,
            v.occurred_at.strftime("%Y-%m-%d %H:%M:%S") if v.occurred_at else "",
            f"{v.fine_amount:.2f}",
            v.status,
            v.source,
            "Yes" if v.needs_review else "No",
            v.paid_at.strftime("%Y-%m-%d %H:%M:%S") if v.paid_at else "N/A",
            v.payment_ref or "N/A",
            v.notes or ""
        ])
        
    return output.getvalue()


def generate_pdf_report(violations: List[Violation], summary: Dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=15
    )
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1E293B")
    )
    header_cell_style = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("TRAFFIC SENSE — Smart Violation & Fine Management", title_style))
    story.append(Paragraph(
        f"Official Traffic Enforcement Report | Total Records: {len(violations)} | "
        f"Generated On: {summary.get('generated_at', '')}",
        subtitle_style
    ))

    # Summary Cards Table
    summary_data = [
        [
            Paragraph(f"<b>Total Violations:</b> {summary.get('total_violations', 0)}", cell_style),
            Paragraph(f"<b>Pending Fines:</b> {summary.get('pending_count', 0)}", cell_style),
            Paragraph(f"<b>Paid Fines:</b> {summary.get('paid_count', 0)}", cell_style),
            Paragraph(f"<b>Cancelled:</b> {summary.get('cancelled_count', 0)}", cell_style),
        ],
        [
            Paragraph(f"<b>Total Amount:</b> Rs. {summary.get('total_amount', 0):,.2f}", cell_style),
            Paragraph(f"<b>Pending Amount:</b> Rs. {summary.get('pending_amount', 0):,.2f}", cell_style),
            Paragraph(f"<b>Collected Amount:</b> Rs. {summary.get('collected_amount', 0):,.2f}", cell_style),
            Paragraph(f"<b>Needs Review:</b> {summary.get('needs_review_count', 0)}", cell_style),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[180, 180, 180, 180])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    # Violations Table
    headers = [
        Paragraph("Fine Ref", header_cell_style),
        Paragraph("Plate No.", header_cell_style),
        Paragraph("Violation Type", header_cell_style),
        Paragraph("Location", header_cell_style),
        Paragraph("Date & Time", header_cell_style),
        Paragraph("Amount (Rs.)", header_cell_style),
        Paragraph("Status", header_cell_style),
        Paragraph("Source", header_cell_style),
    ]
    
    rows = [headers]
    for v in violations:
        status_color = "#EAB308" if v.status == "Pending" else ("#22C55E" if v.status == "Paid" else "#EF4444")
        rows.append([
            Paragraph(v.fine_ref, cell_style),
            Paragraph(f"<b>{v.plate_number}</b>", cell_style),
            Paragraph(v.violation_type, cell_style),
            Paragraph(v.location[:25] + ('...' if len(v.location) > 25 else ''), cell_style),
            Paragraph(v.occurred_at.strftime("%Y-%m-%d %H:%M") if v.occurred_at else "", cell_style),
            Paragraph(f"Rs. {v.fine_amount:.2f}", cell_style),
            Paragraph(f"<font color='{status_color}'><b>{v.status}</b></font>", cell_style),
            Paragraph(v.source, cell_style),
        ])

    col_widths = [100, 90, 110, 150, 100, 70, 60, 50]
    violation_table = Table(rows, colWidths=col_widths, repeatRows=1)
    violation_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    
    story.append(violation_table)
    doc.build(story)
    
    return buffer.getvalue()
