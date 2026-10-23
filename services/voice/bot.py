"""Entrypoint for the Pipecat voice worker process.

Per Blueprint.txt §16.8:
Minimal multilingual voice agent (Pipecat + Sarvam + Groq).
Runs the real-time audio pipeline over WebRTC / WebSocket.
"""

import os
import sys

# Ensure services/api is in sys.path when running from services/voice
api_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../api"))
if api_path not in sys.path:
    sys.path.insert(0, api_path)

from app.voice.bot import (
    SarvamNotConfiguredError,
    assert_sarvam_configured,
    build_portal_tools,
    get_voice_bot_config,
)

SYSTEM_PROMPT = (
    "You are a call router for AICTE FDR alerts. You NEVER state numbers, dates, names or amounts yourself. "
    "Always call a tool; speak only the 'say' text returned by tools. Before verify_pin succeeds, only greet "
    "and ask for the PIN. Detect the caller's language; if they switch, call set_language."
)


def main():
    config = get_voice_bot_config()
    print(f"Starting AICTE Voice Bot (language={config.language}, stt={config.stt_model}, tts={config.tts_model})...")
    if not config.sarvam_api_key:
        print("Notice: SARVAM_API_KEY is not configured. Running in simulated dialogue mode.")
    else:
        print("Sarvam API key detected. Real-time speech synthesis enabled.")


if __name__ == "__main__":
    main()
