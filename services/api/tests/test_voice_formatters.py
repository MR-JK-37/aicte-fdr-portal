from datetime import date

from app.voice.formatters import (
    format_currency_in,
    speak_amount,
    speak_date,
    speak_fdr_digits,
)


def test_speak_amount_blueprint_benchmark():
    # ₹1,25,00,000 in paise is 1_250_000_000 paise
    amount = 1_250_000_000

    assert speak_amount(amount, "en") == "one crore twenty-five lakh rupees"
    assert speak_amount(amount, "hi") == "एक करोड़ पच्चीस लाख रुपये"
    assert speak_amount(amount, "ta") == "ஒரு கோடியே இருபத்தைந்து லட்சம் ரூபாய்"


def test_speak_amount_edge_cases():
    # 0 rupees
    assert speak_amount(0, "en") == "zero rupees"
    assert speak_amount(0, "hi") == "शून्य रुपये"
    assert speak_amount(0, "ta") == "பூஜ்ஜியம் ரூபாய்"

    # 1 rupee
    assert speak_amount(100, "en") == "one rupee"

    # With paise
    assert speak_amount(150, "en") == "one rupee and fifty paise"
    assert speak_amount(250000000, "en") == "twenty-five lakh rupees"
    assert speak_amount(250000000, "hi") == "पच्चीस लाख रुपये"
    assert speak_amount(250000000, "ta") == "இருபத்தைந்து லட்சம் ரூபாய்"


def test_speak_date():
    d = date(2026, 11, 14)
    assert speak_date(d, "en") == "14 November 2026"
    assert speak_date(d, "hi") == "14 नवंबर 2026"
    assert speak_date(d, "ta") == "14 நவம்பர் 2026"


def test_speak_fdr_digits():
    fdr = "FDR-P-12347890"
    assert speak_fdr_digits(fdr, "en") == "ending in seven eight nine zero"
    assert speak_fdr_digits(fdr, "hi") == "अंतिम अंक सात आठ नौ शून्य"
    assert speak_fdr_digits(fdr, "ta") == "கடைசி எண்கள் ஏழு எட்டு ஒன்பது பூஜ்ஜியம்"


def test_format_currency_in():
    assert format_currency_in(1_250_000_000) == "₹1,25,00,000"
    assert format_currency_in(250000000) == "₹25,00,000"
    assert format_currency_in(50000) == "₹500"
    assert format_currency_in(123456789) == "₹12,34,567.89"
