"""FastAPI router for voice call sessions, WebRTC signaling, DTMF, and dialogue turns."""

from datetime import datetime, timezone
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.core import AppUser, CallSession
from app.sim_clock import now as sim_now
from app.voice.calls import (
    CallConsentRequiredError,
    CallSuppressedQuietHoursError,
    mint_room_token,
    start_outbound_call,
    start_pstn_call,
    verify_room_token,
)
from app.voice.dialogue import VoiceDialogueManager

router = APIRouter(prefix="/api/v1/calls", tags=["voice_calls"])


class TriggerCallRequest(BaseModel):
    user_id: uuid.UUID
    reminder_id: uuid.UUID | None = None
    transport: str = "webrtc"


class UtteranceRequest(BaseModel):
    utterance: str


class DTMFRequest(BaseModel):
    digits: str


class WebRTCOfferRequest(BaseModel):
    sdp: str
    token: str


@router.post("/trigger", status_code=status.HTTP_201_CREATED)
def trigger_call(req: TriggerCallRequest, session: Session = Depends(get_db)):
    as_of = sim_now(session)
    try:
        call_session, token = start_outbound_call(
            session=session,
            user_id=req.user_id,
            reminder_id=req.reminder_id,
            transport=req.transport,
            as_of=as_of,
        )
        session.commit()
        return {
            "session_id": str(call_session.id),
            "token": token,
            "status": call_session.status,
            "language": call_session.language,
        }
    except CallConsentRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except CallSuppressedQuietHoursError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{session_id}")
def get_call_session(session_id: uuid.UUID, session: Session = Depends(get_db)):
    call_session = session.get(CallSession, session_id)
    if not call_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CallSession not found")
    return {
        "id": str(call_session.id),
        "status": call_session.status,
        "language": call_session.language,
        "pin_attempts": call_session.pin_attempts,
        "started_at": call_session.started_at.isoformat() if call_session.started_at else None,
        "ended_at": call_session.ended_at.isoformat() if call_session.ended_at else None,
        "transcript": call_session.transcript,
    }


@router.post("/{session_id}/turn")
def dialogue_turn(
    session_id: uuid.UUID,
    req: UtteranceRequest,
    session: Session = Depends(get_db),
):
    call_session = session.get(CallSession, session_id)
    if not call_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CallSession not found")
    user = session.get(AppUser, call_session.app_user_id) if call_session.app_user_id else None
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Callee user not found")

    as_of = sim_now(session)
    dm = VoiceDialogueManager(session, call_session, user, as_of)
    res = dm.handle_input(req.utterance)
    session.commit()
    return res.to_dict()


@router.post("/{session_id}/dtmf")
def dtmf_input(
    session_id: uuid.UUID,
    req: DTMFRequest,
    session: Session = Depends(get_db),
):
    call_session = session.get(CallSession, session_id)
    if not call_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CallSession not found")
    user = session.get(AppUser, call_session.app_user_id) if call_session.app_user_id else None
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Callee user not found")

    as_of = sim_now(session)
    dm = VoiceDialogueManager(session, call_session, user, as_of)
    res = dm.handle_input(req.digits)
    session.commit()
    return res.to_dict()


@router.post("/{session_id}/webrtc/offer")
def webrtc_offer(
    session_id: uuid.UUID,
    req: WebRTCOfferRequest,
    session: Session = Depends(get_db),
):
    valid, token_session_id = verify_room_token(req.token)
    if not valid or token_session_id != str(session_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired room token")

    call_session = session.get(CallSession, session_id)
    if not call_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CallSession not found")

    call_session.status = "in_progress"
    session.commit()

    # SmallWebRTC / Pipecat WebRTC SDP Answer format
    simulated_answer_sdp = (
        f"v=0\r\no=- 0 0 IN IP4 127.0.0.1\r\ns=AICTE Voice WebRTC\r\nt=0 0\r\n"
        f"m=audio 9 UDP/TLS/RTP/SAVPF 111\r\nc=IN IP4 127.0.0.1\r\n"
        f"a=rtpmap:111 opus/48000/2\r\na=sendrecv\r\n"
    )
    return {
        "sdp": simulated_answer_sdp,
        "type": "answer",
        "session_id": str(session_id),
    }


@router.post("/{session_id}/pstn")
def pstn_call(session_id: uuid.UUID, session: Session = Depends(get_db)):
    call_session = session.get(CallSession, session_id)
    if not call_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CallSession not found")
    user = session.get(AppUser, call_session.app_user_id) if call_session.app_user_id else None
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Callee user not found")

    result = start_pstn_call(session, user, call_session)
    return result


@router.post("/{session_id}/hangup")
def hangup(session_id: uuid.UUID, session: Session = Depends(get_db)):
    call_session = session.get(CallSession, session_id)
    if not call_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CallSession not found")
    call_session.status = "completed"
    call_session.ended_at = sim_now(session)
    session.commit()
    return {"session_id": str(session_id), "status": "completed"}
