"""AI / Bounded Agents Router (F-26, F-05, F-27 / SPEC §14, §17).

Exposes bounded AI services with strict authorization:
- Policy Q&A (APH citation resolver)
- Gated Case Summaries (Tier S check, post-check validation)
- Machine Translation Drafts (Tier P, ICU placeholder check)
- Gateway Health & Provider Status (kill switch state, active providers)
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.case_summary import generate_case_summary
from app.agents.rag import answer_compliance_question
from app.agents.translation import generate_translation_draft
from app.auth.deps import get_current_principal
from app.authz import Principal
from app.db import get_session
from app.llm_gateway.gateway import is_gateway_disabled
from app.llm_gateway.registry import load_registry, providers_with_keys
from app.llm_gateway.resilience import is_circuit_open
from app.models.core import Instrument

router = APIRouter(prefix="/v1/ai", tags=["ai-gateway"])


class PolicyQARequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class PolicyQAResponse(BaseModel):
    answer: str
    refused: bool
    unavailable: bool
    verified_citations: list[str]
    sources: list[dict[str, Any]]


class TranslationDraftRequest(BaseModel):
    source_text: str = Field(min_length=1, max_length=2000)
    target_language: str = Field(min_length=2, max_length=10)


class TranslationDraftResponse(BaseModel):
    status: str
    source_text: str
    target_language: str
    translated_text: str
    placeholders_preserved: bool
    requires_human_review: bool
    disclaimer: str


class CaseSummaryResponse(BaseModel):
    status: str
    summary: str | None
    key_points: list[str]
    disclaimer: str
    verified_against_record: bool


class ProviderHealthInfo(BaseModel):
    name: str
    verified: bool
    has_key: bool
    circuit_open: bool
    tier_eligibility: list[str]


class GatewayStatusResponse(BaseModel):
    gateway_disabled: bool
    active_providers_count: int
    providers: list[ProviderHealthInfo]


@router.get("/status", response_model=GatewayStatusResponse)
def get_gateway_status(
    principal: Principal = Depends(get_current_principal),
) -> GatewayStatusResponse:
    """Returns gateway operational status and provider health."""
    registry = load_registry()
    providers_info = []
    for p in registry.values():
        providers_info.append(
            ProviderHealthInfo(
                name=p.name,
                verified=p.verified,
                has_key=p.has_key,
                circuit_open=is_circuit_open(p.name),
                tier_eligibility=p.tier_eligibility,
            )
        )
    return GatewayStatusResponse(
        gateway_disabled=is_gateway_disabled(),
        active_providers_count=len(providers_with_keys()),
        providers=providers_info,
    )


@router.post("/policy-qa", response_model=PolicyQAResponse)
def policy_qa(
    payload: PolicyQARequest,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
) -> PolicyQAResponse:
    """Compliance RAG: Q&A over approved APH clauses with citation resolver."""
    rag_answer = answer_compliance_question(session, payload.question)
    return PolicyQAResponse(
        answer=rag_answer.answer,
        refused=rag_answer.refused,
        unavailable=rag_answer.unavailable,
        verified_citations=rag_answer.verified_citations,
        sources=[
            {
                "clause_id": s.clause_id,
                "title": s.title,
                "distance": round(s.distance, 4),
                "synthetic_placeholder": s.synthetic_placeholder,
            }
            for s in rag_answer.sources
        ],
    )


@router.post("/case-summary/{instrument_id}", response_model=CaseSummaryResponse)
def get_case_summary(
    instrument_id: uuid.UUID,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
) -> CaseSummaryResponse:
    """Gated case summary for authorized officers."""
    instrument = session.get(Instrument, instrument_id)
    if not instrument:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instrument not found",
        )

    res = generate_case_summary(session, instrument)
    return CaseSummaryResponse(
        status=res.status,
        summary=res.summary,
        key_points=res.key_points,
        disclaimer=res.disclaimer,
        verified_against_record=res.verified_against_record,
    )


@router.post("/translation-draft", response_model=TranslationDraftResponse)
def create_translation_draft(
    payload: TranslationDraftRequest,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
) -> TranslationDraftResponse:
    """Generates a machine translation draft for public UI strings."""
    res = generate_translation_draft(
        payload.source_text,
        payload.target_language,
        session=session,
    )
    return TranslationDraftResponse(
        status=res.status,
        source_text=res.source_text,
        target_language=res.target_language,
        translated_text=res.translated_text,
        placeholders_preserved=res.placeholders_preserved,
        requires_human_review=res.requires_human_review,
        disclaimer=res.disclaimer,
    )
