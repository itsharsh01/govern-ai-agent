from __future__ import annotations

from typing import Any

from agent.discovery.digital_twin import DigitalTwinGenerator
from agent.discovery.fact_extractor import FactExtractionEngine
from agent.discovery.gap_analyzer import GapAnalysisEngine
from agent.discovery.interaction_resolver import resolve_interaction
from agent.discovery.models import (
    DiscoveryProgress,
    DiscoveryTurnResponse,
    StructuredInteractionPayload,
)
from agent.discovery.question_generator import QuestionGenerationEngine
from agent.discovery.repository import DiscoveryRepository
from agent.discovery.risk_prioritizer import RiskPrioritizationEngine
from agent.discovery.state_manager import DiscoveryStateManager
from agent.discovery.structured_interaction import structured_to_facts, structured_to_message


class DiscoveryOrchestrator:
    def __init__(self) -> None:
        self.state_manager = DiscoveryStateManager()
        self.fact_extractor = FactExtractionEngine()
        self.gap_analyzer = GapAnalysisEngine()
        self.risk_prioritizer = RiskPrioritizationEngine()
        self.question_generator = QuestionGenerationEngine()
        self.digital_twin = DigitalTwinGenerator()
        self.repository = DiscoveryRepository()

    def create_session(self, customer_id: str | None = None) -> DiscoveryTurnResponse:
        session = self.repository.create_session(customer_id=customer_id)
        schema = session["schema"]
        self.state_manager.init_session_metadata(schema, session["session_id"])

        ranked = self.risk_prioritizer.prioritize(schema, self.gap_analyzer.analyze(schema))
        target = self.question_generator.select_target(ranked, conversation_turns=0, schema=schema)
        if target is None:
            target = ranked[0] if ranked else None
        if target is None:
            raise RuntimeError("No discovery gaps available for new session")
        question = self.question_generator.generate_question(target, schema)

        session["conversation"].append({"role": "assistant", "content": question})
        self.repository.save_session(session)
        return self._build_response(
            session,
            question,
            completion_outputs=None,
            pending_target=target,
        )

    def process_turn(self, session_id: str, user_message: str) -> DiscoveryTurnResponse:
        return self._run_turn(session_id, user_message=user_message, structured=None)

    def process_structured_turn(
        self,
        session_id: str,
        structured: StructuredInteractionPayload,
    ) -> DiscoveryTurnResponse:
        message = structured_to_message(structured)
        return self._run_turn(session_id, user_message=message, structured=structured)

    def _run_turn(
        self,
        session_id: str,
        *,
        user_message: str,
        structured: StructuredInteractionPayload | None,
    ) -> DiscoveryTurnResponse:
        session = self.repository.load_session(session_id)
        schema = session["schema"]

        session["conversation"].append({"role": "user", "content": user_message})
        self.state_manager.increment_turn(schema)

        if structured is not None:
            facts = structured_to_facts(structured)
            self.state_manager.apply_facts(schema, facts, user_message)
        else:
            facts = self.fact_extractor.extract(schema, user_message)
            self.state_manager.apply_facts(schema, facts, user_message)

        gaps = self.gap_analyzer.analyze(schema)
        ranked = self.risk_prioritizer.prioritize(schema, gaps)
        complete = self.state_manager.check_completion(schema, gaps)

        completion_outputs = None
        pending_target = None
        if complete:
            completion_outputs = self.digital_twin.generate(schema).model_dump(mode="json")
            session["completion_outputs"] = completion_outputs
            assistant_message = self._completion_message(completion_outputs)
        else:
            pending_target = self.question_generator.select_target(
                ranked,
                schema["discovery_state"]["conversation_turns"],
                schema,
            )
            if pending_target is None:
                assistant_message = (
                    "Thank you — I have recorded your responses. Discovery will finalize shortly."
                )
            else:
                assistant_message = self.question_generator.generate_question(pending_target, schema)

        session["conversation"].append({"role": "assistant", "content": assistant_message})
        self.repository.save_session(session)
        return self._build_response(
            session,
            assistant_message,
            completion_outputs,
            pending_target=pending_target,
        )

    def _completion_message(self, outputs: dict[str, Any]) -> str:
        summary = outputs.get("system_summary", "")
        return (
            "Discovery is complete. I now have sufficient confidence to build your Digital Twin.\n\n"
            f"{summary}\n\n"
            "You can retrieve the full Digital Twin, discovered risks, and governance readiness "
            "report from the /digital-twin endpoint."
        )

    def _build_response(
        self,
        session: dict[str, Any],
        assistant_message: str,
        completion_outputs: dict[str, Any] | None,
        *,
        pending_target: Any = None,
    ) -> DiscoveryTurnResponse:
        schema = session["schema"]
        state = schema["discovery_state"]
        ranked_raw = state.get("critical_gaps") or []
        remaining = ranked_raw[:3]

        from agent.discovery.models import GapKind, RankedGap

        remaining_gaps = [
            RankedGap(
                field_path=item["field_path"],
                section=item["section"],
                risk_score=item["risk_score"],
                kind=GapKind(item["kind"]),
                rationale=item["rationale"],
            )
            for item in remaining
        ]

        interaction = None
        if pending_target is not None and not state["discovery_complete"]:
            interaction = resolve_interaction(
                schema,
                pending_target.field_path,
                assistant_message,
            )

        return DiscoveryTurnResponse(
            session_id=session["session_id"],
            assistant_message=assistant_message,
            discovery_progress=DiscoveryProgress(
                overall_completeness=state["overall_completeness"],
                overall_confidence=state["overall_confidence"],
                discovery_phase=state["discovery_phase"]["value"],
                section_progress=state["section_progress"],
                conversation_turns=state["conversation_turns"],
            ),
            current_understanding=self.state_manager.build_understanding_summary(schema),
            remaining_gaps=remaining_gaps,
            discovery_complete=state["discovery_complete"],
            completion_outputs=completion_outputs,
            interaction=interaction,
        )


_orchestrator: DiscoveryOrchestrator | None = None


def _get_orchestrator() -> DiscoveryOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = DiscoveryOrchestrator()
    return _orchestrator


def create_session(customer_id: str | None = None) -> DiscoveryTurnResponse:
    return _get_orchestrator().create_session(customer_id=customer_id)


def process_turn(session_id: str, user_message: str) -> DiscoveryTurnResponse:
    return _get_orchestrator().process_turn(session_id, user_message)


def process_structured_turn(
    session_id: str,
    structured: StructuredInteractionPayload,
) -> DiscoveryTurnResponse:
    return _get_orchestrator().process_structured_turn(session_id, structured)
