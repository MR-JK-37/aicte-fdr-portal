"""Release-eligibility agent: runs the Phase 3 rules-engine checklist,
then pauses for a real human decision via LangGraph's `interrupt()` —
per the brief: "Competent authority must approve (LangGraph interrupt)".
This is not a metaphor; the graph genuinely suspends mid-execution at the
approval node and must be resumed with a `Command(resume=...)` carrying
the competent authority's actual decision, which is then checked through
the same maker-checker rule as the direct API path
(app.rules.release.assert_maker_checker) before the lifecycle transition
is applied.

Uses an in-memory checkpointer (MemorySaver) — adequate for one API
process; a production deploy with multiple workers would need a
Postgres-backed checkpointer (langgraph's checkpoint-postgres package)
so a resume can land on a different process than the one that started
it. Not wired up here — flagged, not hidden.
"""

from dataclasses import dataclass
from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command, interrupt

from app.lifecycle import apply_transition
from app.models.enums import InstrumentStatus
from app.rules.release import (
    MakerCheckerViolation,
    assert_maker_checker,
    check_release_eligibility,
)


class ReleaseGraphState(TypedDict):
    instrument_id: str
    eligible: bool
    checklist: list[dict]
    decision: dict | None
    outcome: str


@dataclass
class ApprovalDecision:
    approve: bool
    approver_id: str
    approver_role: str
    reason: str


def _check_node(state: ReleaseGraphState, *, session, instrument) -> ReleaseGraphState:
    result = check_release_eligibility(session, instrument)
    state["eligible"] = result.eligible
    state["checklist"] = [
        {
            "rule_id": i.rule_id,
            "passed": i.passed,
            "detail": i.detail,
            "citation": i.citation,
        }
        for i in result.checklist
    ]
    if not result.eligible:
        state["outcome"] = "not_eligible"
    return state


def _approval_node(
    state: ReleaseGraphState, *, session, instrument, release_request
) -> ReleaseGraphState:
    if not state["eligible"]:
        return state

    # Suspends graph execution here. The caller resumes with
    # Command(resume={"approve": ..., "approver_id": ..., ...}).
    decision_payload = interrupt(
        {"checklist": state["checklist"], "instrument_id": state["instrument_id"]}
    )
    state["decision"] = decision_payload

    try:
        assert_maker_checker(
            approver_id=decision_payload["approver_id"],
            approver_role=decision_payload["approver_role"],
            release_request=release_request,
        )
    except MakerCheckerViolation as exc:
        state["outcome"] = f"rejected_maker_checker: {exc}"
        return state

    if not decision_payload.get("approve"):
        state["outcome"] = "rejected_by_approver"
        return state

    apply_transition(
        session,
        instrument,
        InstrumentStatus.RELEASED,
        actor_role=decision_payload["approver_role"],
        actor_id=decision_payload["approver_id"],
        reason=decision_payload.get(
            "reason", "Release approved via release-eligibility agent"
        ),
    )
    state["outcome"] = "released"
    return state


# One shared, process-wide checkpointer: interrupt() and its matching
# resume MUST land on the same checkpointer instance (it's where the
# paused thread's state actually lives) — a fresh MemorySaver() per call
# would make every resume() look like a thread that was never started.
# See module docstring: this is also why it's in-memory/single-process,
# not yet production-ready for a multi-worker deploy.
_CHECKPOINTER = MemorySaver()


def build_graph(session, instrument, release_request):
    graph = StateGraph(ReleaseGraphState)
    graph.add_node(
        "check_eligibility",
        lambda s: _check_node(s, session=session, instrument=instrument),
    )
    graph.add_node(
        "human_approval",
        lambda s: _approval_node(
            s, session=session, instrument=instrument, release_request=release_request
        ),
    )
    graph.set_entry_point("check_eligibility")
    graph.add_conditional_edges(
        "check_eligibility",
        lambda s: "human_approval" if s["eligible"] else END,
        {"human_approval": "human_approval", END: END},
    )
    graph.add_edge("human_approval", END)
    return graph.compile(checkpointer=_CHECKPOINTER)


def start_release_review(
    session, instrument, release_request, *, thread_id: str
) -> ReleaseGraphState:
    """Runs the graph up to the eligibility check; if eligible, it will be
    paused at the interrupt and this returns the checklist for display.
    If ineligible, returns the final (not_eligible) state directly."""
    app = build_graph(session, instrument, release_request)
    config = {"configurable": {"thread_id": thread_id}}
    result = app.invoke(
        {
            "instrument_id": str(instrument.id),
            "eligible": False,
            "checklist": [],
            "decision": None,
            "outcome": "",
        },
        config=config,
    )
    return result


def resume_release_review(
    session, instrument, release_request, *, thread_id: str, decision: ApprovalDecision
) -> ReleaseGraphState:
    """Resumes a previously-paused graph (same thread_id) with the
    competent authority's actual decision."""
    app = build_graph(session, instrument, release_request)
    config = {"configurable": {"thread_id": thread_id}}
    result = app.invoke(
        Command(
            resume={
                "approve": decision.approve,
                "approver_id": decision.approver_id,
                "approver_role": decision.approver_role,
                "reason": decision.reason,
            }
        ),
        config=config,
    )
    return result
