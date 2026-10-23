"""Localized voice response templates for English, Hindi, and Tamil.

Per Blueprint.txt §5.4:
- Every data fact (amounts, dates, deadlines, counts) is passed from DB fields.
- The LLM never invents numbers, dates, or financial facts.
- Pre-PIN responses never include financial or institution details.
"""

from typing import Any

TEMPLATES = {
    "call.greet_disclose": {
        "en": "Hello, this is the AICTE FDR Assistant, an automated AI voice calling on behalf of the Regulation Bureau. This call may be recorded for audit. To continue, please enter or say your 4-digit call PIN.",
        "hi": "नमस्ते, मैं एआईसीटीई एफडीआर सहायक हूँ — यह रेगुलेशन ब्यूरो की ओर से एक स्वचालित एआई कॉल है। ऑडिट के लिए यह कॉल रिकॉर्ड की जा सकती है। आगे बढ़ने के लिए कृपया अपना 4 अंकों का कॉल पिन बोलें या दबाएँ।",
        "ta": "வணக்கம், நான் AICTE FDR உதவியாளர் — இது ஒழுங்குமுறை பணியகத்தின் சார்பில் அழைக்கும் தானியங்கி AI அழைப்பு. தணிக்கைக்காக இந்த அழைப்பு பதிவு செய்யப்படலாம். தொடர, உங்கள் 4 இலக்க அழைப்பு PIN-ஐ சொல்லுங்கள் அல்லது அழுத்துங்கள்.",
    },
    "call.pin_prompt": {
        "en": "Please enter or say your 4-digit call PIN.",
        "hi": "कृपया अपना 4 अंकों का कॉल पिन बोलें या दबाएँ।",
        "ta": "தயவுசெய்து உங்கள் 4 இலக்க அழைப்பு PIN-ஐ சொல்லுங்கள் அல்லது அழுத்துங்கள்.",
    },
    "call.pin_incorrect": {
        "en": "Incorrect PIN. You have {remaining} attempt(s) remaining. Please try again.",
        "hi": "गलत पिन। आपके पास {remaining} प्रयास शेष हैं। कृपया पुनः प्रयास करें।",
        "ta": "தவறான PIN. உங்களிடம் {remaining} வாய்ப்புகள் மீதமுள்ளன. மீண்டும் முயற்சிக்கவும்.",
    },
    "call.pin_locked": {
        "en": "Your PIN was entered incorrectly 3 times. For your security, this voice channel is locked for 24 hours. Goodbye.",
        "hi": "पिन 3 बार गलत दर्ज किया गया है। आपकी सुरक्षा के लिए यह वॉइस चैनल 24 घंटे के लिए लॉक कर दिया गया है। धन्यवाद।",
        "ta": "PIN 3 முறை தவறாக உள்ளிடப்பட்டது. உங்கள் பாதுகாப்பிற்காக இந்த அழைப்பு வசதி 24 மணி நேரத்திற்கு முடக்கப்பட்டுள்ளது. நன்றி.",
    },
    "call.privacy_refusal": {
        "en": "For security, financial details and institution names cannot be disclosed before PIN verification. Please enter your 4-digit call PIN.",
        "hi": "सुरक्षा कारणों से, पिन सत्यापन से पहले वित्तीय विवरण या संस्थाओं के नाम नहीं बताए जा सकते। कृपया अपना 4 अंकों का पिन दर्ज करें।",
        "ta": "பாதுகாப்பு காரணங்களுக்காக, PIN சரிபார்ப்புக்கு முன் நிதி விவரங்களை வெளியிட முடியாது. தயவுசெய்து உங்கள் 4 இலக்க PIN-ஐ உள்ளிடவும்.",
    },
    "call.social_eng_refusal": {
        "en": "AICTE will never ask for your OTP or password on this call, and bank details cannot be changed by phone.",
        "hi": "एआईसीटीई इस कॉल पर कभी भी आपका ओटीपी या पासवर्ड नहीं मांगेगा, और बैंक विवरण फोन पर नहीं बदले जा सकते।",
        "ta": "AICTE இந்த அழைப்பில் உங்கள் OTP அல்லது கடவுச்சொல்லை எப்போதும் கேட்காது, மேலும் வங்கி விவரங்களை தொலைபேசி மூலம் மாற்ற முடியாது.",
    },
    "call.brief": {
        "en": "Thank you, {officer_first_name}. You have {expiring_count} FDRs expiring in the next {window_days} days, and {discrepancy_count} records with open discrepancies. Would you like to hear the institutions, acknowledge, or snooze?",
        "hi": "धन्यवाद, {officer_first_name} जी। अगले {window_days} दिनों में {expiring_count} एफडीआर की परिपक्वता है और {discrepancy_count} रिकॉर्ड में विसंगति है। क्या आप संस्थानों के नाम सुनना चाहेंगे, स्वीकार करना चाहेंगे, या याद दिलाना बाद में करें?",
        "ta": "நன்றி, {officer_first_name}. அடுத்த {window_days} நாட்களில் {expiring_count} FDR-கள் முதிர்வடைகின்றன; {discrepancy_count} பதிவுகளில் முரண்பாடுகள் உள்ளன. நிறுவனங்களின் பெயர்களைக் கேட்க வேண்டுமா, ஒப்புதல் தர வேண்டுமா, அல்லது பின்னர் நினைவூட்ட வேண்டுமா?",
    },
    "call.institutions_item": {
        "en": "{inst_name}, FDR {last4_digits}, maturing on {maturity_date}.",
        "hi": "{inst_name}, एफडीआर {last4_digits}, परिपक्वता तिथि {maturity_date}।",
        "ta": "{inst_name}, FDR {last4_digits}, முதிர்வு தேதி {maturity_date}.",
    },
    "call.institutions_prompt": {
        "en": "Say 'details' for amounts, or 'acknowledge'.",
        "hi": "राशि जानने के लिए 'विवरण' कहें, या 'स्वीकार करें'।",
        "ta": "தொகை விவரங்களுக்கு 'விவரங்கள்' அல்லது 'ஒப்புதல்' என்று கூறவும்.",
    },
    "call.fdr_detail": {
        "en": "FDR {last4_digits} for {inst_name}: amount is {spoken_amount}, maturing on {maturity_date}.",
        "hi": "{inst_name} के लिए एफडीआर {last4_digits}: राशि {spoken_amount} है, परिपक्वता तिथि {maturity_date}।",
        "ta": "{inst_name}-ன் FDR {last4_digits}: தொகை {spoken_amount}, முதிர்வு தேதி {maturity_date}.",
    },
    "call.ack_prompt": {
        "en": "To confirm, you are acknowledging {expiring_count} expiring FDRs. Say yes or no.",
        "hi": "पुष्टि करें: आप {expiring_count} एफडीआर को स्वीकार कर रहे हैं — हाँ या नहीं?",
        "ta": "உறுதிப்படுத்தவும்: {expiring_count} FDR-களுக்கு ஒப்புதல் தருகிறீர்களா — ஆம் அல்லது இல்லை?",
    },
    "call.ack_done": {
        "en": "Done. Your acknowledgement is recorded at {time}. Goodbye.",
        "hi": "सफलतापूर्वक दर्ज किया गया। आपकी पावती {time} पर रिकॉर्ड की गई है। धन्यवाद।",
        "ta": "பதிவு செய்யப்பட்டது. உங்கள் ஒப்புதல் {time}-ல் பதிவு செய்யப்பட்டுள்ளது. நன்றி.",
    },
    "call.ack_cancelled": {
        "en": "Acknowledgement cancelled. You can ask for institutions, snooze, or escalate.",
        "hi": "पावती रद्द कर दी गई। आप संस्थानों के नाम, बाद में याद दिलाना, या उच्च स्तर पर भेजना चुन सकते हैं।",
        "ta": "ஒப்புதல் ரத்து செய்யப்பட்டது. நீங்கள் நிறுவனங்கள், தாமதப்படுத்துதல் அல்லது புகாரளிக்கலாம்.",
    },
    "call.snooze_done": {
        "en": "Reminder snoozed for {days} day(s). You will be notified on {snooze_until}. Goodbye.",
        "hi": "{days} दिन के लिए याद दिलाना स्थगित किया गया। आपको {snooze_until} पर पुनः सूचित किया जाएगा। धन्यवाद।",
        "ta": "{days} நாட்களுக்கு நினைவூட்டல் ஒத்திவைக்கப்பட்டது. {snooze_until} அன்று மீண்டும் தெரிவிக்கப்படும். நன்றி.",
    },
    "call.snooze_invalid": {
        "en": "Snooze duration must be between 1 and 7 days. How many days would you like to snooze?",
        "hi": "स्थगन अवधि 1 से 7 दिनों के बीच होनी चाहिए। आप कितने दिन के लिए स्थगित करना चाहते हैं?",
        "ta": "ஒத்திவைப்பு காலம் 1 முதல் 7 நாட்களுக்குள் இருக்க வேண்டும். எத்தனை நாட்களுக்கு ஒத்திவைக்க வேண்டும்?",
    },
    "call.escalate_done": {
        "en": "This matter has been escalated to the Regulation Bureau supervising dashboard. Goodbye.",
        "hi": "यह मामला रेगुलेशन ब्यूरो के पर्यवेक्षी डैशबोर्ड को भेज दिया गया है। धन्यवाद।",
        "ta": "இந்த விவகாரம் ஒழுங்குமுறை பணியக மேற்பார்வை டாஷ்போர்டிற்கு அனுப்பப்பட்டுள்ளது. நன்றி.",
    },
    "call.stop_calls_done": {
        "en": "Automated voice calls have been stopped per your request. You will receive updates via in-app notifications and email. Goodbye.",
        "hi": "आपके अनुरोध के अनुसार स्वचालित वॉइस कॉल बंद कर दी गई हैं। आपको इन-ऐप और ईमेल द्वारा अपडेट मिलेंगे। धन्यवाद।",
        "ta": "உங்கள் கோரிக்கையின்படி தானியங்கி AI அழைப்புகள் நிறுத்தப்பட்டுள்ளன. உங்களுக்கு செயலி மற்றும் மின்னஞ்சல் மூலம் தகவல்கள் வரும். நன்றி.",
    },
    "call.language_changed": {
        "en": "Language switched to English. How can I assist you?",
        "hi": "भाषा बदलकर हिंदी कर दी गई है। मैं आपकी क्या सहायता कर सकता हूँ?",
        "ta": "மொழி தமிழுக்கு மாற்றப்பட்டது. நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?",
    },
    "call.repeat": {
        "en": "Repeating: {text}",
        "hi": "दोहरा रहा हूँ: {text}",
        "ta": "மீண்டும் கூறுகிறேன்: {text}",
    },
    "call.fallback": {
        "en": "I did not understand. You can say 'institutions', 'details', 'acknowledge', 'snooze', or 'escalate'.",
        "hi": "मैं समझ नहीं पाया। आप 'संस्थान', 'विवरण', 'स्वीकार', 'स्थगित', या 'उच्च स्तर' कह सकते हैं।",
        "ta": "புரியவில்லை. 'நிறுவனங்கள்', 'விவரங்கள்', 'ஒப்புதல்', 'ஒத்திவைப்பு' என்று கூறலாம்.",
    },
}


def render_voice_template(key: str, lang: str = "en", **kwargs: Any) -> str:
    """Renders a voice response template with exact keyword substitutions."""
    base_lang = "en"
    if lang.startswith("hi"):
        base_lang = "hi"
    elif lang.startswith("ta"):
        base_lang = "ta"

    template_dict = TEMPLATES.get(key)
    if not template_dict:
        return f"[{key}]"

    tmpl = template_dict.get(base_lang, template_dict.get("en", ""))
    try:
        return tmpl.format(**kwargs)
    except KeyError:
        return tmpl
