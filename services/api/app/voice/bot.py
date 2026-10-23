"""Pipecat + Sarvam multilingual voice agent pipeline.

Follows Blueprint.txt §16.8 and §5.3:
- STT: Sarvam Saaras v3 realtime (telephony-optimised 8 kHz / 16 kHz)
- TTS: Sarvam Bulbul v3 with Indic language voices (hi-IN, ta-IN, en-IN)
- Router / LLM: Groq fast model for intent extraction
- Guardrail: LLM never outputs raw numbers, amounts, or dates directly;
  it invokes deterministic portal tools and speaks only their 'say' output.
- Interruption handling enabled (barge-in cancels TTS output).
"""

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.voice.dialogue import DialogueState, VoiceDialogueManager


class SarvamNotConfiguredError(Exception):
    pass


@dataclass
class VoiceBotConfig:
    sarvam_api_key: str | None
    groq_api_key: str | None
    language: str = "en"
    allow_interruptions: bool = True
    stt_model: str = "saaras:v3"
    tts_model: str = "bulbul:v3"


def get_voice_bot_config() -> VoiceBotConfig:
    return VoiceBotConfig(
        sarvam_api_key=os.environ.get("SARVAM_API_KEY"),
        groq_api_key=os.environ.get("GROQ_API_KEY"),
        language=os.environ.get("CALL_LANG", "en"),
        allow_interruptions=True,
    )


def build_portal_tools(dialogue_manager: VoiceDialogueManager) -> dict[str, Callable[..., dict[str, Any]]]:
    """Exposes deterministic portal tools for the Pipecat LLM function-calling loop.
    Each returns a dict containing {"say": rendered_text, "action": action_taken}.
    """
    def verify_pin_tool(pin: str) -> dict[str, Any]:
        res = dialogue_manager.handle_input(pin)
        return res.to_dict()

    def get_brief_tool() -> dict[str, Any]:
        res = dialogue_manager.handle_input("brief")
        return res.to_dict()

    def list_institutions_tool() -> dict[str, Any]:
        res = dialogue_manager.handle_input("institutions")
        return res.to_dict()

    def read_details_tool() -> dict[str, Any]:
        res = dialogue_manager.handle_input("details")
        return res.to_dict()

    def ack_tool(confirm: str = "yes") -> dict[str, Any]:
        if dialogue_manager.state != DialogueState.CONFIRM_ACK:
            dialogue_manager.handle_input("acknowledge")
        res = dialogue_manager.handle_input(confirm)
        return res.to_dict()

    def snooze_tool(days: int = 1) -> dict[str, Any]:
        res = dialogue_manager.handle_input(f"snooze {days} days")
        return res.to_dict()

    def escalate_tool() -> dict[str, Any]:
        res = dialogue_manager.handle_input("escalate")
        return res.to_dict()

    def set_language_tool(lang: str) -> dict[str, Any]:
        res = dialogue_manager.handle_input(f"switch to {lang}")
        return res.to_dict()

    return {
        "verify_pin": verify_pin_tool,
        "get_call_brief": get_brief_tool,
        "list_institutions": list_institutions_tool,
        "read_details": read_details_tool,
        "ack": ack_tool,
        "snooze": snooze_tool,
        "escalate": escalate_tool,
        "set_language": set_language_tool,
    }


def assert_sarvam_configured() -> str:
    key = os.environ.get("SARVAM_API_KEY")
    if not key:
        raise SarvamNotConfiguredError("SARVAM_API_KEY is not set — voice synthesis/recognition requires Sarvam credentials")
    return key
