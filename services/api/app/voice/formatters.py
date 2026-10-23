"""Indian numbering and spoken currency/date formatters for en, hi, ta.

Per Blueprint.txt §5.3:
- speak_amount(amount_paise, lang):
  ₹1,25,00,000 ->
    en: "one crore twenty-five lakh rupees"
    hi: "एक करोड़ पच्चीस लाख रुपये"
    ta: "ஒரு கோடியே இருபத்தைந்து லட்சம் ரூபாய்"
- speak_date(date, lang):
  2026-11-14 ->
    en: "14 November 2026"
    hi: "14 नवंबर 2026"
    ta: "14 நவம்பர் 2026"
- speak_fdr_digits(instrument_number, lang):
  Only last 4 digits, digit-by-digit, spoken only post-PIN.
"""

from datetime import date, datetime
from typing import Any

# Digit and number words in English
_EN_UNITS = [
    "", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen",
]
_EN_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
_EN_DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

# Digit and number words in Hindi (Devanagari)
_HI_NUMS = {
    0: "शून्य", 1: "एक", 2: "दो", 3: "तीन", 4: "चार", 5: "पाँच", 6: "छह", 7: "सात", 8: "आठ", 9: "नौ",
    10: "दस", 11: "ग्यारह", 12: "बारह", 13: "तेरह", 14: "चौदह", 15: "पंद्रह", 16: "सोलह",
    17: "सत्रह", 18: "अठारह", 19: "उन्नीस", 20: "बीस", 21: "इक्कीस", 22: "बाईस", 23: "तेईस",
    24: "चौबीस", 25: "पच्चीस", 26: "छब्बीस", 27: "सत्ताईस", 28: "अट्ठाइस", 29: "उनतीस",
    30: "तीस", 31: "इकत्तीस", 32: "बत्तीस", 33: "तैंतीस", 34: "चौंतीस", 35: "पैंतीस",
    36: "छत्तीस", 37: "सैंतीस", 38: "अड़तीस", 39: "उनतालीस", 40: "चालीस", 41: "इकतालीस",
    42: "बयालीस", 43: "तैंतालीस", 44: "चवालीस", 45: "पैंतालीस", 46: "छियालीस", 47: "सैंतालीस",
    48: "अड़तालीस", 49: "उनचास", 50: "पचास", 51: "इक्यावन", 52: "बावन", 53: "तिरपन",
    54: "चौवन", 55: "पचपन", 56: "छप्पन", 57: "सत्तावन", 58: "अट्ठावन", 59: "उनसठ",
    60: "साठ", 61: "इकसठ", 62: "बासठ", 63: "तिरसठ", 64: "चौंसठ", 65: "पैंसठ",
    66: "छियासठ", 67: "सरसठ", 68: "अड़सठ", 69: "उनहत्तर", 70: "सत्तर", 71: "इकहत्तर",
    72: "बहत्तर", 73: "तिहत्तर", 74: "चौहत्तर", 75: "पचहत्तर", 76: "छिहत्तर", 77: "सतहत्तर",
    78: "अठहत्तर", 79: "उन्नासी", 80: "अस्सी", 81: "इक्यासी", 82: "बयासी", 83: "तिरासी",
    84: "चौरासी", 85: "पचासी", 86: "छियासी", 87: "सतासी", 88: "अट्ठासी", 89: "नवासी",
    90: "नब्बे", 91: "इक्यानवे", 92: "बानवे", 93: "तिरानवे", 94: "चौरानवे", 95: "पंचानवे",
    96: "छियानवे", 97: "सत्तानवे", 98: "अट्ठानवे", 99: "निन्यानवे",
}
_HI_MONTHS = [
    "", "जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून",
    "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर",
]

# Digit and number words in Tamil (Tamil script)
_TA_NUMS = {
    0: "பூஜ்ஜியம்", 1: "ஒன்று", 2: "இரண்டு", 3: "மூன்று", 4: "நான்கு", 5: "ஐந்து",
    6: "ஆறு", 7: "ஏழு", 8: "எட்டு", 9: "ஒன்பது", 10: "பத்து",
    11: "பதினொன்று", 12: "பன்னிரண்டு", 13: "பதின்மூன்று", 14: "பதினான்கு", 15: "பதினைந்து",
    16: "பதினாறு", 17: "பதினேழு", 18: "பதினெட்டு", 19: "பத்தொன்பது", 20: "இருபது",
    30: "முப்பது", 40: "நாற்பது", 50: "ஐம்பது", 60: "அறுபது", 70: "எழுபது", 80: "எண்பது", 90: "தொண்ணூறு",
}
_TA_TENS_PREFIX = {
    20: "இருபத்து", 30: "முப்பத்து", 40: "நாற்பத்து", 50: "ஐம்பத்து",
    60: "அறுபத்து", 70: "எழுபத்து", 80: "எண்பத்து", 90: "தொண்ணூற்று",
}
_TA_MONTHS = [
    "", "ஜனவரி", "பிப்ரவரி", "மார்ச்", "ஏப்ரல்", "மே", "ஜூன்",
    "ஜூலை", "ஆகஸ்ட்", "செப்டம்பர்", "அக்டோபர்", "நவம்பர்", "டிசம்பர்",
]


def _two_digits_en(n: int) -> str:
    if n == 0:
        return ""
    if n < 20:
        return _EN_UNITS[n]
    tens = _EN_TENS[n // 10]
    unit = _EN_UNITS[n % 10]
    return f"{tens}-{unit}" if unit else tens


def _three_digits_en(n: int) -> str:
    parts = []
    if n >= 100:
        parts.append(f"{_EN_UNITS[n // 100]} hundred")
        rem = n % 100
        if rem:
            parts.append(_two_digits_en(rem))
    else:
        parts.append(_two_digits_en(n))
    return " ".join(p for p in parts if p)


def _number_to_words_en(n: int) -> str:
    if n == 0:
        return "zero"
    parts = []
    # Indian system: Crores, Lakhs, Thousands, Hundreds, Units
    crores = n // 10_000_000
    rem = n % 10_000_000
    if crores:
        parts.append(f"{_number_to_words_en(crores)} crore")

    lakhs = rem // 100_000
    rem %= 100_000
    if lakhs:
        parts.append(f"{_two_digits_en(lakhs)} lakh")

    thousands = rem // 1_000
    rem %= 1_000
    if thousands:
        parts.append(f"{_two_digits_en(thousands)} thousand")

    if rem:
        parts.append(_three_digits_en(rem))

    return " ".join(parts)


def _number_to_words_hi(n: int) -> str:
    if n == 0:
        return _HI_NUMS[0]
    parts = []
    crores = n // 10_000_000
    rem = n % 10_000_000
    if crores:
        parts.append(f"{_number_to_words_hi(crores)} करोड़")

    lakhs = rem // 100_000
    rem %= 100_000
    if lakhs:
        parts.append(f"{_HI_NUMS.get(lakhs, str(lakhs))} लाख")

    thousands = rem // 1_000
    rem %= 1_000
    if thousands:
        parts.append(f"{_HI_NUMS.get(thousands, str(thousands))} हज़ार")

    hundreds = rem // 100
    rem %= 100
    if hundreds:
        parts.append(f"{_HI_NUMS.get(hundreds, str(hundreds))} सौ")

    if rem:
        parts.append(_HI_NUMS.get(rem, str(rem)))

    return " ".join(parts)


_TA_TENS_COMBINED = {
    20: {1: "இருபத்தொன்று", 2: "இருபத்திரண்டு", 3: "இருபத்திமூன்று", 4: "இருபத்துநான்கு", 5: "இருபத்தைந்து",
         6: "இருபத்தாறு", 7: "இருபத்தேழு", 8: "இருபத்தெட்டு", 9: "இருபத்தொன்பது"},
    30: {1: "முப்பத்தொன்று", 2: "முப்பத்திரண்டு", 3: "முப்பத்துமூன்று", 4: "முப்பத்துநான்கு", 5: "முப்பத்தைந்து",
         6: "முப்பத்தாறு", 7: "முப்பத்தேழு", 8: "முப்பத்தெட்டு", 9: "முப்பத்தொன்பது"},
    40: {1: "நாற்பத்தொன்று", 2: "நாற்பத்திரண்டு", 3: "நாற்பத்துமூன்று", 4: "நாற்பத்துநான்கு", 5: "நாற்பத்தைந்து",
         6: "நாற்பத்தாறு", 7: "நாற்பத்தேழு", 8: "நாற்பத்தெட்டு", 9: "நாற்பத்தொன்பது"},
    50: {1: "ஐம்பத்தொன்று", 2: "ஐம்பத்திரண்டு", 3: "ஐம்பத்துமூன்று", 4: "ஐம்பத்துநான்கு", 5: "ஐம்பத்தைந்து",
         6: "ஐம்பத்தாறு", 7: "ஐம்பத்தேழு", 8: "ஐம்பத்தெட்டு", 9: "ஐம்பத்தொன்பது"},
    60: {1: "அறுபத்தொன்று", 2: "அறுபத்திரண்டு", 3: "அறுபத்துமூன்று", 4: "அறுபத்துநான்கு", 5: "அறுபத்தைந்து",
         6: "அறுபத்தாறு", 7: "அறுபத்தேழு", 8: "அறுபத்தெட்டு", 9: "அறுபத்தொன்பது"},
    70: {1: "எழுபத்தொன்று", 2: "எழுபத்திரண்டு", 3: "எழுபத்துமூன்று", 4: "எழுபத்துநான்கு", 5: "எழுபத்தைந்து",
         6: "எழுபத்தாறு", 7: "எழுபத்தேழு", 8: "எழுபத்தெட்டு", 9: "எழுபத்தொன்பது"},
    80: {1: "எண்பத்தொன்று", 2: "எண்பத்திரண்டு", 3: "எண்பத்துமூன்று", 4: "எண்பத்துநான்கு", 5: "எண்பத்தைந்து",
         6: "எண்பத்தாறு", 7: "எண்பத்தேழு", 8: "எண்பத்தெட்டு", 9: "எண்பத்தொன்பது"},
    90: {1: "தொண்ணூற்றொன்று", 2: "தொண்ணூற்றிரண்டு", 3: "தொண்ணூற்றுமூன்று", 4: "தொண்ணூற்றுநான்கு", 5: "தொண்ணூற்றைந்து",
         6: "தொண்ணூற்றாறு", 7: "தொண்ணூற்றேழு", 8: "தொண்ணூற்றெட்டு", 9: "தொண்ணூற்றொன்பது"},
}


def _two_digits_ta(n: int) -> str:
    if n == 0:
        return ""
    if n in _TA_NUMS:
        return _TA_NUMS[n]
    tens = (n // 10) * 10
    unit = n % 10
    if tens in _TA_TENS_COMBINED and unit in _TA_TENS_COMBINED[tens]:
        return _TA_TENS_COMBINED[tens][unit]
    prefix = _TA_TENS_PREFIX.get(tens, _TA_NUMS.get(tens, ""))
    unit_str = _TA_NUMS.get(unit, "")
    return f"{prefix} {unit_str}".strip()


def _number_to_words_ta(n: int, has_following: bool = False) -> str:
    if n == 0:
        return _TA_NUMS[0]
    parts = []

    crores = n // 10_000_000
    rem = n % 10_000_000
    if crores:
        c_words = _number_to_words_ta(crores, has_following=False)
        # If followed by lakhs/thousands, use conjunctive 'கோடியே' (kodiye)
        kodi = "கோடியே" if rem > 0 else "கோடி"
        parts.append(f"{c_words} {kodi}")

    lakhs = rem // 100_000
    rem %= 100_000
    if lakhs:
        l_words = _two_digits_ta(lakhs)
        parts.append(f"{l_words} லட்சம்")

    thousands = rem // 1_000
    rem %= 1_000
    if thousands:
        t_words = _two_digits_ta(thousands)
        parts.append(f"{t_words} ஆயிரம்")

    hundreds = rem // 100
    rem %= 100
    if hundreds:
        h_map = {1: "நூறு", 2: "இருநூறு", 3: "முந்நூறு", 4: "நாநூறு", 5: "ஐந்நூறு",
                 6: "அறுநூறு", 7: "எழுநூறு", 8: "எண்ணூறு", 9: "தொள்ளாயிரம்"}
        parts.append(h_map.get(hundreds, "நூறு"))

    if rem:
        parts.append(_two_digits_ta(rem))

    return " ".join(parts)


def speak_amount(amount_paise: float | Any, lang: str = "en") -> str:
    """Renders amount in paise into natural spoken words in Indian currency.

    Examples:
      1250000000 paise (₹1,25,00,000)
      en -> "one crore twenty-five lakh rupees"
      hi -> "एक करोड़ पच्चीस लाख रुपये"
      ta -> "ஒரு கோடியே இருபத்தைந்து லட்சம் ரூபாய்"
    """
    amount_int = int(amount_paise)
    rupees = amount_int // 100
    paise = amount_int % 100

    if lang.startswith("hi"):
        r_text = _number_to_words_hi(rupees)
        res = f"{r_text} रुपये"
        if paise:
            res += f" और {_HI_NUMS.get(paise, str(paise))} पैसे"
        return res

    if lang.startswith("ta"):
        r_text = _number_to_words_ta(rupees)
        # If starts with 'ஒன்று கோடியே', naturally spoken as 'ஒரு கோடியே'
        if r_text.startswith("ஒன்று கோடி"):
            r_text = "ஒரு கோடி" + r_text[len("ஒன்று கோடி"):]
        res = f"{r_text} ரூபாய்"
        if paise:
            res += f" மற்றும் {_two_digits_ta(paise)} பைசா"
        return res

    # English default
    r_text = _number_to_words_en(rupees)
    unit = "rupee" if rupees == 1 else "rupees"
    res = f"{r_text} {unit}"
    if paise:
        p_text = _number_to_words_en(paise)
        p_unit = "paisa" if paise == 1 else "paise"
        res += f" and {p_text} {p_unit}"
    return res


def speak_date(d: date | datetime, lang: str = "en") -> str:
    """Renders a date as a natural spoken string in the given language."""
    day = d.day
    month = d.month
    year = d.year

    if lang.startswith("hi"):
        m_name = _HI_MONTHS[month]
        return f"{day} {m_name} {year}"

    if lang.startswith("ta"):
        m_name = _TA_MONTHS[month]
        return f"{day} {m_name} {year}"

    # English default
    m_names = [
        "", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    return f"{day} {m_names[month]} {year}"


def speak_fdr_digits(instrument_number: str, lang: str = "en") -> str:
    """Reads the last 4 digits of an instrument number digit-by-digit.
    Strictly post-PIN only per Blueprint.txt §5.3 / §5.5.
    """
    digits = [c for c in instrument_number if c.isdigit()]
    last4 = digits[-4:] if len(digits) >= 4 else digits
    if not last4:
        return instrument_number[-4:]

    if lang.startswith("hi"):
        words = [_HI_NUMS[int(d)] for d in last4]
        return "अंतिम अंक " + " ".join(words)

    if lang.startswith("ta"):
        words = [_TA_NUMS[int(d)] for d in last4]
        return "கடைசி எண்கள் " + " ".join(words)

    words = [_EN_DIGITS[int(d)] for d in last4]
    return "ending in " + " ".join(words)


def format_currency_in(amount_paise: float | Any) -> str:
    """Formats an amount in paise to Indian lakh/crore grouped ₹ currency."""
    amount_int = int(amount_paise)
    rupees = amount_int // 100
    s = str(rupees)
    if len(s) <= 3:
        grouped = s
    else:
        last3 = s[-3:]
        remaining = s[:-3]
        parts = []
        while remaining:
            parts.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        grouped = ",".join(parts) + "," + last3
    paise = amount_paise % 100
    if paise:
        return f"₹{grouped}.{paise:02d}"
    return f"₹{grouped}"
