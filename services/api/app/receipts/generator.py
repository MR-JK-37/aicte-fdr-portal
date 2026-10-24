"""PDF Receipt generation with embedded verifiable QR code (SPEC §8.1 / F-20)."""

import io
from datetime import UTC, datetime

from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.authz import mask_identifier
from app.receipts.signer import sign_receipt_payload


def generate_submission_receipt_pdf(
    *,
    receipt_id: str,
    instrument_id: str,
    instrument_number: str,
    instrument_type: str,
    amount: float,
    institution_code: str,
    institution_name: str,
    version_number: int,
    content_hash: str,
    submitted_at: datetime | None = None,
    submitted_by_name: str = "Authorized Representative",
    policy_version: str = "APH-2024-27-v1.0",
) -> tuple[bytes, str]:
    """Generates a tamper-evident submission receipt PDF.

    Returns:
        (pdf_bytes, signature_b64)
    """
    if submitted_at is None:
        submitted_at = datetime.now(UTC)

    masked_ref = mask_identifier(instrument_number)
    hash_prefix = content_hash[:16]
    issued_iso = submitted_at.isoformat()

    # Minimal payload encoded in QR code and signed
    qr_payload = {
        "rid": receipt_id,
        "iid": instrument_id,
        "inst": institution_code,
        "ver": version_number,
        "h": hash_prefix,
        "ts": issued_iso,
    }
    signature = sign_receipt_payload(qr_payload)

    # Verification URL for public verification
    verify_url = (
        f"https://portal.aicte-india.org/v1/public/receipts/verify"
        f"?rid={receipt_id}&iid={instrument_id}&inst={institution_code}&ver={version_number}&h={hash_prefix}&ts={issued_iso}&sig={signature}"
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,  # Center
    )
    subtitle_style = ParagraphStyle(
        "HeaderSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        alignment=1,
    )
    badge_style = ParagraphStyle(
        "Badge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1e3a8a"),
        alignment=1,
    )
    label_style = ParagraphStyle(
        "FieldLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155"),
    )
    value_style = ParagraphStyle(
        "FieldValue",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0f172a"),
    )
    mono_style = ParagraphStyle(
        "MonoValue",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )
    footer_style = ParagraphStyle(
        "FooterNotice",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b"),
        alignment=1,
    )

    elements = []

    # AICTE Header
    elements.append(Paragraph("ALL INDIA COUNCIL FOR TECHNICAL EDUCATION", title_style))
    elements.append(
        Paragraph(
            "Regulation Bureau · Financial Compliance & Security Deposit Vault",
            subtitle_style,
        )
    )
    elements.append(Spacer(1, 8))
    elements.append(
        Paragraph("OFFICIAL SUBMISSION RECEIPT · CRYPTOGRAPHIC RECORD", badge_style)
    )
    elements.append(Spacer(1, 14))

    # Summary table
    table_data = [
        [
            Paragraph("Receipt Identifier", label_style),
            Paragraph(receipt_id, mono_style),
        ],
        [
            Paragraph("Institution AICTE Code", label_style),
            Paragraph(institution_code, value_style),
        ],
        [
            Paragraph("Institution Name", label_style),
            Paragraph(institution_name, value_style),
        ],
        [
            Paragraph("Instrument Type", label_style),
            Paragraph(instrument_type, value_style),
        ],
        [
            Paragraph("Instrument Reference (Masked)", label_style),
            Paragraph(masked_ref, mono_style),
        ],
        [
            Paragraph("Security Deposit Amount", label_style),
            Paragraph(f"₹ {amount:,.2f}", value_style),
        ],
        [
            Paragraph("Submission Version", label_style),
            Paragraph(f"Version {version_number} (Immutable Snapshot)", value_style),
        ],
        [
            Paragraph("Snapshot Content Hash (SHA-256)", label_style),
            Paragraph(content_hash, mono_style),
        ],
        [
            Paragraph("Submission Timestamp (UTC)", label_style),
            Paragraph(submitted_at.strftime("%Y-%m-%d %H:%M:%S UTC"), value_style),
        ],
        [
            Paragraph("Submitted By", label_style),
            Paragraph(submitted_by_name, value_style),
        ],
        [
            Paragraph("Governing Policy Version", label_style),
            Paragraph(policy_version, value_style),
        ],
    ]

    t = Table(table_data, colWidths=[200, 320])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(t)
    elements.append(Spacer(1, 14))

    # QR Code for public verification
    qr_code = qr.QrCodeWidget(verify_url)
    qr_code.barWidth = 110
    qr_code.barHeight = 110
    qr_code.qrVersion = 3
    qr_drawing = Drawing(110, 110)
    qr_drawing.add(qr_code)

    qr_table = Table(
        [
            [
                qr_drawing,
                Paragraph(
                    "<b>Scan QR to Verify Authenticity Online</b><br/><br/>"
                    "This QR code encodes an Ed25519-signed verification token.<br/>"
                    f"Signature prefix: <code>{signature[:24]}...</code><br/><br/>"
                    "Verify at official portal: <i>portal.aicte-india.org</i>",
                    subtitle_style,
                ),
            ]
        ],
        colWidths=[130, 390],
    )
    qr_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (1, 0), (1, 0), 12),
            ]
        )
    )
    elements.append(qr_table)
    elements.append(Spacer(1, 18))

    # Mandatory Legal Notice (per MASTER_PROMPT §F-20: Never labelled eSign/DSC)
    disclaimer = (
        "<b>LEGAL & COMPLIANCE NOTICE:</b> This document is a computer-generated cryptographic submission receipt "
        "issued by the AICTE Regulation Bureau for portal audit and workflow tracking. "
        "It establishes cryptographic non-repudiation of the submitted document version hash at the recorded timestamp. "
        "This receipt does NOT constitute a statutory digital signature (eSign / DSC under the IT Act 2000), "
        "nor does it represent final AICTE regulatory approval or verification of the underlying security deposit."
    )
    elements.append(Paragraph(disclaimer, footer_style))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes, signature
