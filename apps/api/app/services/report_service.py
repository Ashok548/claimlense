"""
Service to generate PDF reports using ReportLab and upload them to Cloudflare R2.
"""

import io
import uuid
import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.services.s3_service import upload_file, generate_presigned_url, object_exists

def generate_analysis_pdf(analysis_data: dict, line_items: list[dict]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    # Custom Styles
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=20, textColor=colors.HexColor('#0ea5e9'))
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=16, spaceAfter=10, textColor=colors.HexColor('#333333'))
    normal_style = styles["Normal"]

    # Header
    elements.append(Paragraph(f"ClaimLense Analysis Report", title_style))
    elements.append(Paragraph(f"<b>Insurer:</b> {analysis_data.get('insurer_name', 'N/A')}", normal_style))
    elements.append(Paragraph(f"<b>Diagnosis:</b> {analysis_data.get('diagnosis', 'General Admission')}", normal_style))
    elements.append(Paragraph(f"<b>Generated At:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    elements.append(Spacer(1, 20))

    # Summary Metrics
    elements.append(Paragraph("Financial Summary", h2_style))
    summary_data = [
        ["Total Billed", "Expected Payable", "Amount At Risk", "Rejection Risk"],
        [
            f"INR {analysis_data.get('total_billed', 0):,.2f}",
            f"INR {analysis_data.get('total_payable', 0):,.2f}",
            f"INR {analysis_data.get('total_at_risk', 0):,.2f}",
            f"{analysis_data.get('rejection_rate_pct', 0)}%"
        ]
    ]
    summary_table = Table(summary_data, colWidths=[120, 120, 120, 120])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0'))
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 30))

    # Line Items
    elements.append(Paragraph("Itemized Analysis", h2_style))
    item_data = [["Description", "Billed", "Payable", "Status", "Reason"]]
    
    for item in line_items:
        desc = str(item.get('description', ''))
        billed = str(item.get('billed_amount', '0'))
        payable = str(item.get('payable_amount', '0')) if item.get('payable_amount') is not None else "TBD"
        status = str(item.get('status', 'VERIFY'))
        reason = str(item.get('rejection_reason', 'Standard item'))
        
        # Crop very long descriptions/reasons to fit the PDF gracefully
        if len(desc) > 30: desc = desc[:27] + "..."
        if len(reason) > 40: reason = reason[:37] + "..."

        item_data.append([desc, billed, payable, status, reason])

    item_table = Table(item_data, colWidths=[160, 60, 60, 80, 160])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#334155')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (2,-1), 'RIGHT'), # Align amounts to right
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 40))

    # Footer Disclaimer
    disclaimer = ("Disclaimer: This analysis is an AI-generated estimate based on standard rules and known insurer "
                  "behaviors. Final settlements are purely at the discretion of the TPA and Insurer.")
    elements.append(Paragraph(disclaimer, ParagraphStyle('Small', parent=styles['Normal'], fontSize=8, textColor=colors.gray)))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

async def get_or_generate_report(analysis_id: uuid.UUID, db_session) -> str:
    """
    Return a fresh presigned URL for the PDF report of *analysis_id*.

    Idempotent: the PDF is generated and uploaded to R2 only on the first
    call.  Subsequent calls skip regeneration and re-sign the existing
    object — saving compute, R2 write costs, and ensuring the PDF snapshot
    never changes for a given analysis.  The presigned URL is always
    regenerated because it carries a time-limited TTL.
    """
    # Import locally to avoid circular dependencies
    from sqlalchemy import text

    s3_key = f"reports/{analysis_id}_report.pdf"

    # --- Idempotency check: skip generation if the PDF already exists in R2 ---
    import asyncio
    already_exists = await asyncio.to_thread(object_exists, s3_key)
    if already_exists:
        return await asyncio.to_thread(generate_presigned_url, s3_key, 3600)

    # 1. Fetch analysis from DB
    result = await db_session.execute(
        text("SELECT * FROM claim_analyses WHERE id = :id"),
        {"id": str(analysis_id)}
    )
    analysis = result.fetchone()
    if not analysis:
        raise ValueError("Analysis not found")

    analysis_dict = dict(analysis._mapping)

    # Fetch Insurer Name
    insurer_result = await db_session.execute(
        text("SELECT name FROM insurers WHERE id = :id"),
        {"id": str(analysis_dict['insurer_id'])}
    )
    insurer = insurer_result.fetchone()
    if insurer:
        analysis_dict['insurer_name'] = insurer[0]

    # Fetch Line items
    items_result = await db_session.execute(
        text("SELECT * FROM bill_line_items WHERE analysis_id = :id"),
        {"id": str(analysis_id)}
    )
    items = [dict(row._mapping) for row in items_result.fetchall()]

    # 2. Build PDF
    pdf_bytes = generate_analysis_pdf(analysis_dict, items)

    # 3. Upload to R2
    await asyncio.to_thread(upload_file, s3_key, pdf_bytes, "application/pdf")

    # 4. Return presigned URL
    return await asyncio.to_thread(generate_presigned_url, s3_key, 3600)
