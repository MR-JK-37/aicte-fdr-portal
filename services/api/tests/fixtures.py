"""Synthetic FDR document generation for tests and the accuracy benchmark
(scripts/gen_synthetic_fdrs.py reuses this). Layouts are plain
label:-value text blocks rendered via reportlab — enough to exercise OCR
+ extraction end to end without needing real scanned FDR samples (which
the source blueprint notes AICTE has not provided — see Blueprint.txt
§17 item 2).
"""

import io
import random

from faker import Faker
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

fake = Faker("en_IN")

BANKS = [
    "State Bank of India",
    "HDFC Bank",
    "ICICI Bank",
    "Punjab National Bank",
    "Axis Bank",
]


_ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
_TEENS = [
    "Ten",
    "Eleven",
    "Twelve",
    "Thirteen",
    "Fourteen",
    "Fifteen",
    "Sixteen",
    "Seventeen",
    "Eighteen",
    "Nineteen",
]
_TENS = [
    "",
    "",
    "Twenty",
    "Thirty",
    "Forty",
    "Fifty",
    "Sixty",
    "Seventy",
    "Eighty",
    "Ninety",
]


def _two_digit_words(n: int) -> str:
    if n < 10:
        return _ONES[n]
    if n < 20:
        return _TEENS[n - 10]
    tens, ones = divmod(n, 10)
    return f"{_TENS[tens]} {_ONES[ones]}".strip()


def _amount_to_words(amount: int) -> str:
    """Only used by this synthetic-fixture generator — produces the kind
    of spelled-out count validation.py's amount-words cross-check parses
    (e.g. "Twenty Five Lakh", not a digit like "25 Lakh")."""
    lakh, remainder = divmod(amount, 100_000)
    if lakh:
        return f"Rupees {_two_digit_words(lakh)} Lakh Only"
    thousand = remainder // 1000
    return f"Rupees {_two_digit_words(thousand)} Thousand Only"


def random_fdr_fields(seed: int | None = None) -> dict:
    rnd = random.Random(seed)
    issue = fake.date_between(start_date="-3y", end_date="-1y")
    tenor_months = rnd.choice([12, 24, 36, 60])
    from dateutil.relativedelta import relativedelta

    maturity = issue + relativedelta(months=tenor_months)
    amount = rnd.choice([500000, 1000000, 1500000, 2000000, 2500000])
    bank = rnd.choice(BANKS)
    ifsc = f"{''.join(rnd.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))}0{rnd.randint(100000, 999999)}"
    return {
        "instrument_number": f"FDR{rnd.randint(100000, 999999)}",
        "bank_name": bank,
        "ifsc": ifsc,
        "amount": amount,
        "amount_words": _amount_to_words(amount),
        "issue_date": issue.strftime("%d-%m-%Y"),
        "maturity_date": maturity.strftime("%d-%m-%Y"),
        "tenor_months": tenor_months,
    }


# Each layout is a list of (label, field_key) pairs in a different order/
# wording — "8 layouts" per the brief's acceptance criterion.
LAYOUTS = [
    [
        ("FDR No.", "instrument_number"),
        ("Bank Name", "bank_name"),
        ("IFSC Code", "ifsc"),
        ("Amount (Rs.)", "amount"),
        ("Amount (words)", "amount_words"),
        ("Date of Issue", "issue_date"),
        ("Date of Maturity", "maturity_date"),
        ("Tenor (months)", "tenor_months"),
    ],
    [
        ("Instrument Number", "instrument_number"),
        ("Bank Name", "bank_name"),
        ("IFSC", "ifsc"),
        ("Amount (INR)", "amount"),
        ("Amount (words)", "amount_words"),
        ("Issue Date", "issue_date"),
        ("Maturity Date", "maturity_date"),
        ("Tenor (months)", "tenor_months"),
    ],
    [
        ("Receipt No", "instrument_number"),
        ("Bank Name", "bank_name"),
        ("IFSC Code", "ifsc"),
        ("Amount (figures)", "amount"),
        ("Date of Issue", "issue_date"),
        ("Date of Maturity", "maturity_date"),
        ("Tenor", "tenor_months"),
        ("Amount (words)", "amount_words"),
    ],
    [
        ("FDR Number", "instrument_number"),
        ("IFSC Code", "ifsc"),
        ("Bank Name", "bank_name"),
        ("Issue Date", "issue_date"),
        ("Maturity Date", "maturity_date"),
        ("Amount (Rs.)", "amount"),
        ("Amount (words)", "amount_words"),
        ("Tenor (months)", "tenor_months"),
    ],
    [
        ("Instrument No.", "instrument_number"),
        ("Bank Name", "bank_name"),
        ("IFSC", "ifsc"),
        ("Date of Issue", "issue_date"),
        ("Date of Maturity", "maturity_date"),
        ("Amount (INR)", "amount"),
        ("Tenor (months)", "tenor_months"),
        ("Amount (words)", "amount_words"),
    ],
    [
        ("FDR No.", "instrument_number"),
        ("IFSC Code", "ifsc"),
        ("Bank Name", "bank_name"),
        ("Amount (figures)", "amount"),
        ("Amount (words)", "amount_words"),
        ("Tenor (months)", "tenor_months"),
        ("Date of Issue", "issue_date"),
        ("Date of Maturity", "maturity_date"),
    ],
    [
        ("Receipt Number", "instrument_number"),
        ("Bank Name", "bank_name"),
        ("IFSC Code", "ifsc"),
        ("Amount (Rs.)", "amount"),
        ("Date of Issue", "issue_date"),
        ("Date of Maturity", "maturity_date"),
        ("Tenor (months)", "tenor_months"),
        ("Amount (words)", "amount_words"),
    ],
    [
        ("FDR No.", "instrument_number"),
        ("Bank Name", "bank_name"),
        ("IFSC", "ifsc"),
        ("Amount (words)", "amount_words"),
        ("Amount (Rs.)", "amount"),
        ("Date of Issue", "issue_date"),
        ("Date of Maturity", "maturity_date"),
        ("Tenor (months)", "tenor_months"),
    ],
]


def render_fdr_pdf(fields: dict, layout_index: int) -> bytes:
    layout = LAYOUTS[layout_index % len(LAYOUTS)]
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 780, "FIXED DEPOSIT RECEIPT")
    c.setFont("Helvetica", 11)
    y = 740
    for label, field_key in layout:
        c.drawString(72, y, f"{label}: {fields[field_key]}")
        y -= 24
    c.showPage()
    c.save()
    return buf.getvalue()
