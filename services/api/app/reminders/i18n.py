"""Notification text localisation, en/hi/ta per the brief: "notification
text is localised per user". This is deliberately NOT the LLM gateway —
notification text must be exact and predictable (amounts, dates,
deadlines), so it's templated, matching the project-wide rule that the
LLM never originates a fact that reaches a user. Real human-reviewed
translations, not machine-translated at request time; if a language is
missing a key it falls back to English rather than failing.
"""

WINDOW_LABELS = {
    "T-90": {
        "en": "90 days before maturity",
        "hi": "परिपक्वता से 90 दिन पहले",
        "ta": "முதிர்வுக்கு 90 நாட்களுக்கு முன்",
    },
    "T-60": {
        "en": "60 days before maturity",
        "hi": "परिपक्वता से 60 दिन पहले",
        "ta": "முதிர்வுக்கு 60 நாட்களுக்கு முன்",
    },
    "T-30": {
        "en": "30 days before maturity",
        "hi": "परिपक्वता से 30 दिन पहले",
        "ta": "முதிர்வுக்கு 30 நாட்களுக்கு முன்",
    },
    "T-7": {
        "en": "7 days before maturity",
        "hi": "परिपक्वता से 7 दिन पहले",
        "ta": "முதிர்வுக்கு 7 நாட்களுக்கு முன்",
    },
    "T-0": {"en": "maturity date", "hi": "परिपक्वता तिथि", "ta": "முதிர்வு தேதி"},
}

_TEMPLATES = {
    "reminder.maturity_window": {
        "en": "Instrument {instrument_number} ({amount}) reaches {window_label}. Please review and take action.",
        "hi": "इंस्ट्रूमेंट {instrument_number} ({amount}) {window_label} पर पहुंच रहा है। कृपया समीक्षा करें और कार्रवाई करें।",
        "ta": "கருவி {instrument_number} ({amount}) {window_label} ஐ அடைகிறது. தயவுசெய்து மதிப்பாய்வு செய்து நடவடிக்கை எடுக்கவும்.",
    },
    "escalation.regulation_bureau": {
        "en": "Instrument {instrument_number} has had no response through the full reminder ladder and has been escalated to the Regulation Bureau.",
        "hi": "इंस्ट्रूमेंट {instrument_number} को पूर्ण रिमाइंडर श्रृंखला के माध्यम से कोई प्रतिक्रिया नहीं मिली और इसे विनियमन ब्यूरो को भेज दिया गया है।",
        "ta": "கருவி {instrument_number} க்கு முழு நினைவூட்டல் படிநிலை வழியாக பதில் இல்லை, மேலும் இது ஒழுங்குமுறை ஆணையத்திற்கு அனுப்பப்பட்டுள்ளது.",
    },
}

DEFAULT_LANGUAGE = "en"


def render(template_key: str, language: str, **kwargs) -> str:
    templates = _TEMPLATES[template_key]
    template = templates.get(language, templates[DEFAULT_LANGUAGE])
    return template.format(**kwargs)


def window_label(window: str, language: str) -> str:
    labels = WINDOW_LABELS[window]
    return labels.get(language, labels[DEFAULT_LANGUAGE])
