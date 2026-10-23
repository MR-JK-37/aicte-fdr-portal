"""Deterministic dialogue manager and state machine for voice bot.

Follows Blueprint.txt §5.4 & §5.5:
  GREET_DISCLOSE -> VERIFY_PIN -> BRIEF -> MENU_QA -> CONFIRM_ACK -> CLOSE
- Financial details and institution names are withheld until PIN is verified.
- Social engineering attempts (requesting OTPs, altering bank details) are rejected.
- Successful acknowledgement writes an immutable audit_log row.
- Snooze is bounded to 1-7 days.
- Language switching applies immediately across en, hi, ta.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.models.core import (
    AppUser,
    CallSession,
    ConsentRecord,
    Discrepancy,
    Escalation,
    Institution,
    Instrument,
    Reminder,
)
from app.voice.formatters import speak_amount, speak_date, speak_fdr_digits
from app.voice.security import verify_user_call_pin
from app.voice.templates import render_voice_template


class DialogueState(str, Enum):
    GREET_DISCLOSE = "GREET_DISCLOSE"
    VERIFY_PIN = "VERIFY_PIN"
    BRIEF = "BRIEF"
    MENU_QA = "MENU_QA"
    CONFIRM_ACK = "CONFIRM_ACK"
    CLOSE = "CLOSE"


class DialogueTurnResult:
    def __init__(
        self,
        say: str,
        state: DialogueState,
        action_taken: str | None = None,
        data: dict[str, Any] | None = None,
    ):
        self.say = say
        self.state = state
        self.action_taken = action_taken
        self.data = data or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "say": self.say,
            "state": self.state.value,
            "action_taken": self.action_taken,
            "data": self.data,
        }


class VoiceDialogueManager:
    """Manages the lifecycle, security, and state transitions of an active call."""

    def __init__(
        self,
        session: Session,
        call_session: CallSession,
        user: AppUser,
        as_of: datetime,
    ):
        self.session = session
        self.call_session = call_session
        self.user = user
        self.as_of = as_of
        self.lang = call_session.language or user.preferred_language or "en"
        self.state = DialogueState(
            call_session.transcript.get("state", DialogueState.VERIFY_PIN.value)
        )
        self.last_say = call_session.transcript.get("last_say", "")
        self._history = list(call_session.transcript.get("turns", []))

    def _record_turn(self, role: str, content: str) -> None:
        self._history.append({"role": role, "content": content, "timestamp": self.as_of.isoformat()})
        self.call_session.transcript = {
            "state": self.state.value,
            "last_say": self.last_say,
            "turns": self._history,
        }
        self.session.add(self.call_session)

    def _get_officer_first_name(self) -> str:
        name_parts = (self.user.full_name or "Officer").split()
        return name_parts[0]

    def _get_context_records(self) -> tuple[list[Instrument], int]:
        """Fetches instruments and discrepancies relevant to this call session."""
        inst_id = self.call_session.institution_id or self.user.institution_id
        if not inst_id and self.call_session.reminder_id:
            rem = self.session.get(Reminder, self.call_session.reminder_id)
            if rem:
                inst_id = rem.institution_id

        instruments: list[Instrument] = []
        discrepancy_count = 0
        if inst_id:
            instruments = list(
                self.session.execute(
                    select(Instrument).where(Instrument.institution_id == inst_id)
                ).scalars().all()
            )
            discrepancy_count = len(
                list(
                    self.session.execute(
                        select(Discrepancy).where(Discrepancy.institution_id == inst_id)
                    ).scalars().all()
                )
            )
        return instruments, discrepancy_count

    def start_call(self) -> DialogueTurnResult:
        """Emits the initial greeting and automated AI assistant disclosure."""
        say = render_voice_template("call.greet_disclose", self.lang)
        self.state = DialogueState.VERIFY_PIN
        self.last_say = say
        self._record_turn("assistant", say)
        return DialogueTurnResult(say=say, state=self.state, action_taken="greet_disclose")

    def handle_input(self, user_utterance: str) -> DialogueTurnResult:
        """Processes a spoken user utterance or DTMF input."""
        cleaned = user_utterance.strip().lower()
        self._record_turn("user", user_utterance)

        # 1. Check for social engineering cues regardless of state
        if any(w in cleaned for w in ["otp", "password", "bank account", "change ifsc", "new account", "update bank"]):
            say = render_voice_template("call.social_eng_refusal", self.lang)
            self.last_say = say
            self._record_turn("assistant", say)
            return DialogueTurnResult(say=say, state=self.state, action_taken="refuse_social_engineering")

        # 2. Language switching command
        if "tamil" in cleaned or "தமிழ்" in cleaned:
            self.lang = "ta"
            self.call_session.language = "ta"
            self.user.preferred_language = "ta"
            self.session.add(self.call_session)
            self.session.add(self.user)
            say = render_voice_template("call.language_changed", self.lang)
            self.last_say = say
            self._record_turn("assistant", say)
            return DialogueTurnResult(say=say, state=self.state, action_taken="change_language", data={"lang": "ta"})

        if "hindi" in cleaned or "हिंदी" in cleaned or "हिन्दी" in cleaned:
            self.lang = "hi"
            self.call_session.language = "hi"
            self.user.preferred_language = "hi"
            self.session.add(self.call_session)
            self.session.add(self.user)
            say = render_voice_template("call.language_changed", self.lang)
            self.last_say = say
            self._record_turn("assistant", say)
            return DialogueTurnResult(say=say, state=self.state, action_taken="change_language", data={"lang": "hi"})

        if "english" in cleaned:
            self.lang = "en"
            self.call_session.language = "en"
            self.user.preferred_language = "en"
            self.session.add(self.call_session)
            self.session.add(self.user)
            say = render_voice_template("call.language_changed", self.lang)
            self.last_say = say
            self._record_turn("assistant", say)
            return DialogueTurnResult(say=say, state=self.state, action_taken="change_language", data={"lang": "en"})

        # 3. Stop calls / opt-out
        if any(w in cleaned for w in ["stop calls", "stop calling", "do not call", "கால் நிறுத்தவும்", "कॉल बंद करें"]):
            return self._handle_stop_calls()

        # 4. Repeat command
        if any(w in cleaned for w in ["repeat", "say again", "दोबारा", "மீண்டும்"]):
            say = self.last_say or render_voice_template("call.fallback", self.lang)
            self._record_turn("assistant", say)
            return DialogueTurnResult(say=say, state=self.state, action_taken="repeat")

        # 5. Pre-PIN Guardrail: If not authenticated, prevent access to financial facts
        if self.state in (DialogueState.GREET_DISCLOSE, DialogueState.VERIFY_PIN):
            # Check if input is digits (PIN attempt)
            digits = "".join(c for c in cleaned if c.isdigit())
            if len(digits) >= 4:
                return self._handle_pin_entry(digits[:6])

            # If user asks for institutions, amounts, details before PIN:
            if any(w in cleaned for w in ["institution", "amount", "detail", "fdr", "which", "money", "संस्थान", "राशि", "நிறுவனம்"]):
                say = render_voice_template("call.privacy_refusal", self.lang)
                self.last_say = say
                self._record_turn("assistant", say)
                return DialogueTurnResult(say=say, state=self.state, action_taken="privacy_refusal")

            # Fallback in PIN state: repeat PIN prompt
            say = render_voice_template("call.pin_prompt", self.lang)
            self.last_say = say
            self._record_turn("assistant", say)
            return DialogueTurnResult(say=say, state=self.state, action_taken="prompt_pin")

        # 6. Post-PIN State Machine: MENU_QA / CONFIRM_ACK
        if self.state == DialogueState.CONFIRM_ACK:
            return self._handle_ack_confirmation(cleaned)

        if self.state in (DialogueState.BRIEF, DialogueState.MENU_QA):
            return self._handle_menu_qa(cleaned)

        # Closed state
        say = "Call ended. Goodbye."
        return DialogueTurnResult(say=say, state=DialogueState.CLOSE, action_taken="closed")

    def _handle_pin_entry(self, pin: str) -> DialogueTurnResult:
        verified, reason = verify_user_call_pin(
            self.session, self.user, self.call_session, pin, self.as_of
        )
        if verified:
            self.state = DialogueState.MENU_QA
            instruments, disc_count = self._get_context_records()
            brief = render_voice_template(
                "call.brief",
                self.lang,
                officer_first_name=self._get_officer_first_name(),
                expiring_count=len(instruments) or 1,
                window_days=30,
                discrepancy_count=disc_count,
            )
            self.last_say = brief
            self._record_turn("assistant", brief)
            return DialogueTurnResult(
                say=brief,
                state=self.state,
                action_taken="pin_verified",
                data={"verified": True},
            )

        if reason == "locked":
            self.state = DialogueState.CLOSE
            say = render_voice_template("call.pin_locked", self.lang)
            self.last_say = say
            self._record_turn("assistant", say)
            return DialogueTurnResult(
                say=say,
                state=self.state,
                action_taken="channel_locked",
                data={"locked": True},
            )

        # Incorrect PIN with attempts remaining
        remaining = 3 - self.call_session.pin_attempts
        say = render_voice_template("call.pin_incorrect", self.lang, remaining=remaining)
        self.last_say = say
        self._record_turn("assistant", say)
        return DialogueTurnResult(
            say=say,
            state=self.state,
            action_taken="pin_incorrect",
            data={"remaining_attempts": remaining},
        )

    def _handle_menu_qa(self, utterance: str) -> DialogueTurnResult:
        instruments, _ = self._get_context_records()

        # Acknowledge intent
        if any(w in utterance for w in ["acknowledge", "ack", "स्वीकार", "ஒப்புதல்"]):
            self.state = DialogueState.CONFIRM_ACK
            say = render_voice_template(
                "call.ack_prompt",
                self.lang,
                expiring_count=len(instruments) or 1,
            )
            self.last_say = say
            self._record_turn("assistant", say)
            return DialogueTurnResult(say=say, state=self.state, action_taken="prompt_ack_confirm")

        # List institutions intent
        if any(w in utterance for w in ["institution", "which", "list", "संस्थान", "நிறுவனம்"]):
            items = []
            for inst in instruments[:3]:
                inst_obj = self.session.get(Institution, inst.institution_id) if inst.institution_id else None
                inst_name = inst_obj.name if inst_obj else "Primary Institution"
                last4 = speak_fdr_digits(inst.instrument_number, self.lang)
                mat_date = speak_date(inst.maturity_date or self.as_of.date(), self.lang)
                items.append(
                    render_voice_template(
                        "call.institutions_item",
                        self.lang,
                        inst_name=inst_name,
                        last4_digits=last4,
                        maturity_date=mat_date,
                    )
                )
            items_str = " ".join(items) if items else "No records found."
            prompt = render_voice_template("call.institutions_prompt", self.lang)
            say = f"{items_str} {prompt}".strip()
            self.last_say = say
            self._record_turn("assistant", say)
            return DialogueTurnResult(say=say, state=self.state, action_taken="list_institutions")

        # Read details intent
        if any(w in utterance for w in ["detail", "amount", "विवरण", "விவரங்கள்"]):
            inst = instruments[0] if instruments else None
            if inst:
                inst_obj = self.session.get(Institution, inst.institution_id) if inst.institution_id else None
                inst_name = inst_obj.name if inst_obj else "Institution"
                last4 = speak_fdr_digits(inst.instrument_number, self.lang)
                spk_amt = speak_amount(inst.amount, self.lang)
                mat_date = speak_date(inst.maturity_date or self.as_of.date(), self.lang)
                say = render_voice_template(
                    "call.fdr_detail",
                    self.lang,
                    last4_digits=last4,
                    inst_name=inst_name,
                    spoken_amount=spk_amt,
                    maturity_date=mat_date,
                )
            else:
                say = render_voice_template("call.fallback", self.lang)
            self.last_say = say
            self._record_turn("assistant", say)
            return DialogueTurnResult(say=say, state=self.state, action_taken="read_details")

        # Snooze intent
        if any(w in utterance for w in ["snooze", "later", "स्थगित", "ஒத்திவை"]):
            # Extract requested days if present
            days = 1
            digits = [int(c) for c in utterance if c.isdigit()]
            if digits:
                days = digits[0]
            if days < 1 or days > 7:
                say = render_voice_template("call.snooze_invalid", self.lang)
                self.last_say = say
                self._record_turn("assistant", say)
                return DialogueTurnResult(say=say, state=self.state, action_taken="snooze_invalid")

            snooze_until = self.as_of + timedelta(days=days)
            if self.call_session.reminder_id:
                rem = self.session.get(Reminder, self.call_session.reminder_id)
                if rem:
                    rem.scheduled_for = snooze_until
                    self.session.add(rem)

            append_audit_entry(
                self.session,
                action="voice_snooze",
                entity_type="reminder",
                entity_id=str(self.call_session.reminder_id or self.call_session.id),
                before={"status": "due"},
                after={"snoozed_days": days, "snooze_until": snooze_until.isoformat()},
                actor_id=str(self.user.id),
                institution_id=str(self.user.institution_id) if self.user.institution_id else None,
            )
            self.state = DialogueState.CLOSE
            self.call_session.status = "completed"
            self.call_session.ended_at = self.as_of
            self.session.add(self.call_session)

            say = render_voice_template(
                "call.snooze_done",
                self.lang,
                days=days,
                snooze_until=speak_date(snooze_until.date(), self.lang),
            )
            self.last_say = say
            self._record_turn("assistant", say)
            return DialogueTurnResult(say=say, state=self.state, action_taken="snooze_applied")

        # Escalate intent
        if any(w in utterance for w in ["escalate", "supervisor", "उच्च स्तर", "மேற்பார்வை"]):
            inst_id = self.call_session.institution_id or self.user.institution_id
            if inst_id and instruments:
                self.session.add(
                    Escalation(
                        institution_id=inst_id,
                        instrument_id=instruments[0].id,
                        level="regulation_bureau",
                        escalated_to="Bureau Officer",
                        status="open",
                    )
                )
            append_audit_entry(
                self.session,
                action="voice_escalate",
                entity_type="call_session",
                entity_id=str(self.call_session.id),
                before={"escalated": False},
                after={"escalated": True, "level": "regulation_bureau"},
                actor_id=str(self.user.id),
                institution_id=str(self.user.institution_id) if self.user.institution_id else None,
            )
            self.state = DialogueState.CLOSE
            self.call_session.status = "completed"
            self.call_session.ended_at = self.as_of
            self.session.add(self.call_session)

            say = render_voice_template("call.escalate_done", self.lang)
            self.last_say = say
            self._record_turn("assistant", say)
            return DialogueTurnResult(say=say, state=self.state, action_taken="escalated")

        # Fallback
        say = render_voice_template("call.fallback", self.lang)
        self.last_say = say
        self._record_turn("assistant", say)
        return DialogueTurnResult(say=say, state=self.state, action_taken="fallback")

    def _handle_ack_confirmation(self, utterance: str) -> DialogueTurnResult:
        is_yes = any(w in utterance for w in ["yes", "yeah", "confirm", "हाँ", "ஆம்", "சரி"])
        is_no = any(w in utterance for w in ["no", "cancel", "नहीं", "இல்லை"])

        if is_yes:
            # Mark reminder acknowledged if linked
            if self.call_session.reminder_id:
                rem = self.session.get(Reminder, self.call_session.reminder_id)
                if rem:
                    rem.acknowledged_at = self.as_of
                    self.session.add(rem)

            append_audit_entry(
                self.session,
                action="voice_acknowledgement",
                entity_type="reminder" if self.call_session.reminder_id else "call_session",
                entity_id=str(self.call_session.reminder_id or self.call_session.id),
                before={"acknowledged": False},
                after={
                    "acknowledged": True,
                    "channel": "voice",
                    "call_session_id": str(self.call_session.id),
                    "acknowledged_at": self.as_of.isoformat(),
                },
                actor_id=str(self.user.id),
                institution_id=str(self.user.institution_id) if self.user.institution_id else None,
            )
            self.state = DialogueState.CLOSE
            self.call_session.status = "completed"
            self.call_session.ended_at = self.as_of
            self.session.add(self.call_session)

            say = render_voice_template("call.ack_done", self.lang, time=self.as_of.strftime("%H:%M UTC"))
            self.last_say = say
            self._record_turn("assistant", say)
            return DialogueTurnResult(say=say, state=self.state, action_taken="acknowledged")

        if is_no:
            self.state = DialogueState.MENU_QA
            say = render_voice_template("call.ack_cancelled", self.lang)
            self.last_say = say
            self._record_turn("assistant", say)
            return DialogueTurnResult(say=say, state=self.state, action_taken="ack_cancelled")

        say = render_voice_template("call.ack_prompt", self.lang, expiring_count=1)
        self.last_say = say
        self._record_turn("assistant", say)
        return DialogueTurnResult(say=say, state=self.state, action_taken="prompt_ack_confirm_retry")

    def _handle_stop_calls(self) -> DialogueTurnResult:
        # Revoke consent in ConsentRecord
        consents = list(
            self.session.execute(
                select(ConsentRecord)
                .where(
                    ConsentRecord.app_user_id == self.user.id,
                    ConsentRecord.consent_type == "automated_voice_calls",
                    ConsentRecord.revoked_at.is_(None),
                )
            ).scalars().all()
        )
        for c in consents:
            c.revoked_at = self.as_of
            self.session.add(c)

        append_audit_entry(
            self.session,
            action="voice_consent_revoked",
            entity_type="consent_record",
            entity_id=str(consents[0].id) if consents else str(self.user.id),
            before={"consent_granted": True},
            after={"consent_granted": False, "revoked_at": self.as_of.isoformat()},
            actor_id=str(self.user.id),
            institution_id=str(self.user.institution_id) if self.user.institution_id else None,
        )

        self.state = DialogueState.CLOSE
        self.call_session.status = "completed"
        self.call_session.ended_at = self.as_of
        self.session.add(self.call_session)

        say = render_voice_template("call.stop_calls_done", self.lang)
        self.last_say = say
        self._record_turn("assistant", say)
        return DialogueTurnResult(say=say, state=self.state, action_taken="consent_revoked")
