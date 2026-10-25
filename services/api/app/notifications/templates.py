"""Notification templates with localisation and lock-screen privacy enforcement (SPEC §11.2, §11.5, MASTER_PROMPT §10.3, §10.4)."""

from __future__ import annotations

from typing import Any

TEMPLATE_VERSION = "v1.0"

# Catalogue of versioned, reviewed templates per SPEC §10.3
# Each template provides in-app rich text and strictly generic lock-screen text.
# Canary tests verify that lock-screen text NEVER leaks FDR numbers, amounts, bank names, or PII.

TEMPLATES: dict[str, dict[str, dict[str, str]]] = {
    "instrument.submitted": {
        "en": {
            "title": "FDR Submission Received",
            "body": "Your deposit instrument {instrument_number} for ₹{amount} has been successfully submitted and entered the intake queue.",
            "lock_title": "AICTE FDR Portal — Action Needed",
            "lock_body": "A new deposit submission requires intake review.",
        },
        "hi": {
            "title": "एफडीआर प्रस्तुति प्राप्त हुई",
            "body": "आपका जमा पत्र {instrument_number} (₹{amount}) सफलतापूर्वक प्रस्तुत कर दिया गया है।",
            "lock_title": "एआईसीटीई एफडीआर पोर्टल — सूचना",
            "lock_body": "एक नई जमा प्रस्तुति समीक्षा के लिए उपलब्ध है।",
        },
        "ta": {
            "title": "வைப்புத்தொகை ஆவணம் பெறப்பட்டது",
            "body": "உங்கள் வைப்பு ஆவணம் {instrument_number} (₹{amount}) வெற்றிகரமாக சமர்ப்பிக்கப்பட்டது.",
            "lock_title": "AICTE FDR போர்டல் — தகவல்",
            "lock_body": "புதிய வைப்பு சமர்ப்பிப்பு பரிசீலனையில் உள்ளது.",
        },
    },
    "instrument.returned": {
        "en": {
            "title": "Submission Returned for Correction",
            "body": "Instrument {instrument_number} was returned by the intake officer. Reason: {reason}.",
            "lock_title": "AICTE FDR Portal — Action Needed",
            "lock_body": "A submission was returned for correction. Open the app to view.",
        },
        "hi": {
            "title": "प्रस्तुति सुधार हेतु वापस",
            "body": "दस्तावेज़ {instrument_number} सुधार के लिए लौटाया गया। कारण: {reason}।",
            "lock_title": "एआईसीटीई एफडीआर पोर्टल — कार्रवाई आवश्यक",
            "lock_body": "सुधार के लिए एक प्रस्तुति वापस की गई है।",
        },
        "ta": {
            "title": "திருத்தத்திற்கு திருப்பி அனுப்பப்பட்டது",
            "body": "ஆவணம் {instrument_number} திருத்தத்திற்காக திருப்பி அனுப்பப்பட்டுள்ளது. காரணம்: {reason}.",
            "lock_title": "AICTE FDR போர்டல் — நடவடிக்கை தேவை",
            "lock_body": "திருத்தத்திற்கான சமர்ப்பிப்பு திரும்ப வந்துள்ளது.",
        },
    },
    "instrument.expiring": {
        "en": {
            "title": "Deposit Horizon Reached",
            "body": "Security deposit instrument {instrument_number} matures on {maturity_date}. Days remaining: {days_remaining}.",
            "lock_title": "AICTE FDR Portal — Deadline Notice",
            "lock_body": "An active deposit obligation is approaching maturity.",
        },
        "hi": {
            "title": "परिपक्वता सीमा निकट",
            "body": "सुरक्षा जमा {instrument_number} की परिपक्वता तिथि {maturity_date} है। शेष दिन: {days_remaining}।",
            "lock_title": "एआईसीटीई एफडीआर पोर्टल — समय-सीमा सूचना",
            "lock_body": "एक सक्रिय जमा दायित्व परिपक्वता के करीब है।",
        },
        "ta": {
            "title": "முதிர்வு தேதி நெருங்குகிறது",
            "body": "வைப்பு ஆவணம் {instrument_number} முதிர்வு தேதி: {maturity_date}. மீதமுள்ள நாட்கள்: {days_remaining}.",
            "lock_title": "AICTE FDR போர்டல் — காலக்கெடு அறிவிப்பு",
            "lock_body": "வைப்புத்தொகை முதிர்வு நிலையை எட்டுகிறது.",
        },
    },
    "instrument.matured": {
        "en": {
            "title": "Deposit Instrument Matured",
            "body": "Instrument {instrument_number} has reached maturity on {maturity_date}. Action required: submit renewal, replacement, or release request.",
            "lock_title": "AICTE FDR Portal — Action Needed",
            "lock_body": "A compliance instrument has matured. Action is required.",
        },
        "hi": {
            "title": "जमा पत्र परिपक्व",
            "body": "दस्तावेज़ {instrument_number} परिपक्व हो चुका है। नवीनीकरण या विमुक्ति हेतु अनुरोध दर्ज करें।",
            "lock_title": "एआईसीटीई एफडीआर पोर्टल — कार्रवाई आवश्यक",
            "lock_body": "एक जमा पत्र परिपक्व हो गया है। कृपया समीक्षा करें।",
        },
        "ta": {
            "title": "வைப்பு முதிர்வடைந்தது",
            "body": "வைப்பு ஆவணம் {instrument_number} முதிர்வடைந்துள்ளது. புதுப்பித்தல் அல்லது விடுவிப்பு கோரிக்கையை சமர்ப்பிக்கவும்.",
            "lock_title": "AICTE FDR போர்டல் — நடவடிக்கை தேவை",
            "lock_body": "வைப்பு ஆவணம் முதிர்வடைந்துள்ளது.",
        },
    },
    "observation.created": {
        "en": {
            "title": "Scrutiny Observation Raised",
            "body": "Observation #{observation_number} has been opened: {title}. Response due: {due_date}.",
            "lock_title": "AICTE FDR Portal — Notice",
            "lock_body": "A scrutiny observation requires your institutional response.",
        },
        "hi": {
            "title": "जांच टिप्पणी दर्ज",
            "body": "टिप्पणी #{observation_number} दर्ज की गई: {title}। अंतिम तिथि: {due_date}।",
            "lock_title": "एआईसीटीई एफडीआर पोर्टल — सूचना",
            "lock_body": "एक नई जांच टिप्पणी दर्ज की गई है।",
        },
        "ta": {
            "title": "பரிசீலனை குறிப்பு உருவாக்கப்பட்டது",
            "body": "பரிசீலனை குறிப்பு #{observation_number} உருவாக்கப்பட்டது: {title}. கடைசி நாள்: {due_date}.",
            "lock_title": "AICTE FDR போர்டல் — தகவல்",
            "lock_body": "பரிசீலனை குறிப்பிற்கு பதில் தேவைப்படுகிறது.",
        },
    },
    "observation.responded": {
        "en": {
            "title": "Institution Response Received",
            "body": "Institution submitted response for observation #{observation_number}.",
            "lock_title": "AICTE FDR Portal — Update",
            "lock_body": "A response to a scrutiny observation was submitted.",
        },
        "hi": {
            "title": "संस्थान की प्रतिक्रिया प्राप्त",
            "body": "टिप्पणी #{observation_number} के लिए संस्थान ने प्रतिक्रिया प्रस्तुत की।",
            "lock_title": "एआईसीटीई एफडीआर पोर्टल — अद्यतन",
            "lock_body": "टिप्पणी के लिए प्रतिक्रिया दर्ज की गई है।",
        },
        "ta": {
            "title": "பதில் பெறப்பட்டது",
            "body": "பரிசீலனை குறிப்பு #{observation_number} க்கான பதில் சமர்ப்பிக்கப்பட்டது.",
            "lock_title": "AICTE FDR போர்டல் — புதுப்பிப்பு",
            "lock_body": "பரிசீலனை குறிப்பிற்கு பதில் அளிக்கப்பட்டுள்ளது.",
        },
    },
    "release.submitted": {
        "en": {
            "title": "Release Request Submitted",
            "body": "Release request for instrument {instrument_number} has been submitted for scrutiny.",
            "lock_title": "AICTE FDR Portal — Workflow Update",
            "lock_body": "A release request has been submitted for review.",
        },
        "hi": {
            "title": "विमुक्ति अनुरोध प्रस्तुत",
            "body": "दस्तावेज़ {instrument_number} की विमुक्ति हेतु अनुरोध दर्ज किया गया है।",
            "lock_title": "एआईसीटीई एफडीआर पोर्टल — कार्यप्रवाह अद्यतन",
            "lock_body": "एक विमुक्ति अनुरोध समीक्षा हेतु प्रस्तुत किया गया।",
        },
        "ta": {
            "title": "விடுவிப்பு கோரிக்கை சமர்ப்பிக்கப்பட்டது",
            "body": "வைப்பு ஆவணம் {instrument_number} விடுவிப்பு கோரிக்கை சமர்ப்பிக்கப்பட்டது.",
            "lock_title": "AICTE FDR போர்டல் — பணிப்பாய்வு புதுப்பிப்பு",
            "lock_body": "விடுவிப்பு கோரிக்கை சமர்ப்பிக்கப்பட்டுள்ளது.",
        },
    },
    "release.decision": {
        "en": {
            "title": "Release Decision Recorded",
            "body": "Release request for instrument {instrument_number} was marked {decision} by Competent Authority.",
            "lock_title": "AICTE FDR Portal — Decision Notice",
            "lock_body": "A Competent Authority decision has been recorded on a release request.",
        },
        "hi": {
            "title": "विमुक्ति निर्णय दर्ज",
            "body": "दस्तावेज़ {instrument_number} के विमुक्ति अनुरोध पर निर्णय: {decision}।",
            "lock_title": "एआईसीटीई एफडीआर पोर्टल — निर्णय सूचना",
            "lock_body": "विमुक्ति अनुरोध पर सक्षम प्राधिकारी का निर्णय दर्ज हुआ।",
        },
        "ta": {
            "title": "விடுவிப்பு முடிவு பதிவு செய்யப்பட்டது",
            "body": "வைப்பு ஆவணம் {instrument_number} விடுவிப்பு முடிவு: {decision}.",
            "lock_title": "AICTE FDR போர்டல் — முடிவு அறிவிப்பு",
            "lock_body": "விடுவிப்பு கோரிக்கை முடிவு பதிவு செய்யப்பட்டுள்ளது.",
        },
    },
    "security.session_revoked": {
        "en": {
            "title": "Security Notice: Session Revoked",
            "body": "Your active session was terminated from IP {ip_address} on {timestamp}.",
            "lock_title": "AICTE FDR Portal — Security Alert",
            "lock_body": "A security change occurred on your account. Log in to verify.",
        },
        "hi": {
            "title": "सुरक्षा सूचना: सत्र समाप्त",
            "body": "आपका सत्र IP {ip_address} द्वारा {timestamp} पर समाप्त कर दिया गया।",
            "lock_title": "एआईसीटीई एफडीआर पोर्टल — सुरक्षा चेतावनी",
            "lock_body": "आपके खाते में सुरक्षा परिवर्तन हुआ है।",
        },
        "ta": {
            "title": "பாதுகாப்பு அறிவிப்பு: அமர்வு ரத்து செய்யப்பட்டது",
            "body": "உங்கள் அமர்வு IP {ip_address} வழியாக {timestamp} அன்று ரத்து செய்யப்பட்டது.",
            "lock_title": "AICTE FDR போர்டல் — பாதுகாப்பு எச்சரிக்கை",
            "lock_body": "உங்கள் கணக்கில் பாதுகாப்பு மாற்றம் ஏற்பட்டுள்ளது.",
        },
    },
    "operations.alert": {
        "en": {
            "title": "Operational Notice: {subject}",
            "body": "System component alert: {details}. Timestamp: {timestamp}.",
            "lock_title": "AICTE FDR Portal — System Notice",
            "lock_body": "A system operations notice has been logged.",
        },
        "hi": {
            "title": "परिचालन सूचना: {subject}",
            "body": "सिस्टम घटक चेतावनी: {details}। समय: {timestamp}।",
            "lock_title": "एआईसीटीई एफडीआर पोर्टल — सिस्टम सूचना",
            "lock_body": "एक सिस्टम परिचालन सूचना दर्ज की गई है।",
        },
        "ta": {
            "title": "இயக்க அறிவிப்பு: {subject}",
            "body": "கணினி எச்சரிக்கை: {details}. நேரம்: {timestamp}.",
            "lock_title": "AICTE FDR போர்டல் — கணினி அறிவிப்பு",
            "lock_body": "ஒரு கணினி இயக்க அறிவிப்பு பதிவு செய்யப்பட்டுள்ளது.",
        },
    },
}

DEFAULT_FALLBACK = {
    "title": "AICTE Notification: {event_type}",
    "body": "An official compliance event occurred regarding your record.",
    "lock_title": "AICTE FDR Portal — Action Needed",
    "lock_body": "A compliance update is available. Open the application to view.",
}


class SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return ""


def render_template(
    template_key: str,
    context: dict[str, Any],
    locale: str = "en",
) -> tuple[str, str, str, str]:
    """Renders versioned template strings into rich in-app (title, body) and generic lock-screen (lock_title, lock_body).

    Guarantees that lock-screen outputs never expose confidential business values.
    """
    loc = locale if locale in ("en", "hi", "ta") else "en"
    template_group = TEMPLATES.get(template_key, {})
    localized_template = template_group.get(loc) or template_group.get("en")

    if not localized_template:
        title = DEFAULT_FALLBACK["title"].format(event_type=template_key)
        body = DEFAULT_FALLBACK["body"]
        lock_title = DEFAULT_FALLBACK["lock_title"]
        lock_body = DEFAULT_FALLBACK["lock_body"]
    else:
        # Safe format for in-app body with context
        safe_ctx = SafeDict(
            {k: str(v) if v is not None else "" for k, v in context.items()}
        )
        try:
            title = localized_template["title"].format_map(safe_ctx)
        except (KeyError, ValueError, TypeError):
            title = localized_template["title"]
        try:
            body = localized_template["body"].format_map(safe_ctx)
        except (KeyError, ValueError, TypeError):
            body = localized_template["body"]

        # Lock-screen title and body are strictly generic static phrases per SPEC §10.4
        lock_title = localized_template["lock_title"]
        lock_body = localized_template["lock_body"]

    return title, body, lock_title, lock_body
