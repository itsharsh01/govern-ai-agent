from __future__ import annotations

import os

from typing import Any

from agent.discovery.llm_config import discovery_llm_enabled
from agent.discovery.models import GapKind, RankedGap
from agent.discovery.schema_utils import field_is_empty, get_at_path, is_schema_field
from agent.discovery.templates import DEFAULT_QUESTION_TEMPLATE, QUESTION_TEMPLATES

ANSWERED_CONFIDENCE = 0.7


def _phrasing_llm():
    if not discovery_llm_enabled():
        return None

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    model_name = os.getenv("DISCOVERY_LLM_MODEL", "gemini-2.0-flash")
    llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=0.4)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a senior AI governance consultant conducting a discovery interview. "
                "Rewrite the provided question template into one concise, professional question. "
                "Briefly explain why the information is needed. Ask exactly ONE question. "
                "Do not ask multiple questions.",
            ),
            (
                "human",
                "Target field: {field_path}\nRationale: {rationale}\nTemplate:\n{template}",
            ),
        ]
    )
    return prompt | llm


def _field_label(field_path: str) -> str:
    return field_path.split(".")[-1].replace("_", " ")


class QuestionGenerationEngine:
    OPENING_FIELD = "system_profile.business_purpose"

    def _field_is_answered(self, schema: dict[str, Any], field_path: str) -> bool:
        try:
            field = get_at_path(schema, field_path)
        except KeyError:
            return False
        if not is_schema_field(field):
            return False
        if field_is_empty(field):
            return False
        return field.get("confidence", 0) >= ANSWERED_CONFIDENCE

    def select_target(
        self,
        ranked_gaps: list[RankedGap],
        conversation_turns: int,
        schema: dict[str, Any],
    ) -> RankedGap | None:
        if conversation_turns == 0 or not ranked_gaps:
            if self._field_is_answered(schema, self.OPENING_FIELD):
                unanswered = [g for g in ranked_gaps if not self._field_is_answered(schema, g.field_path)]
                if unanswered:
                    return unanswered[0]
            else:
                return RankedGap(
                    field_path=self.OPENING_FIELD,
                    section="system_profile",
                    risk_score=1.0,
                    kind=GapKind.MISSING,
                    rationale="Opening discovery question",
                )

        for gap in ranked_gaps:
            if not self._field_is_answered(schema, gap.field_path):
                return gap

        return ranked_gaps[0] if ranked_gaps else None

    def generate_question(self, target: RankedGap, schema: dict) -> str:
        template = QUESTION_TEMPLATES.get(
            target.field_path,
            DEFAULT_QUESTION_TEMPLATE.format(field_label=_field_label(target.field_path)),
        )
        if target.kind == GapKind.INFERRED_UNVALIDATED:
            template = (
                f"I inferred {target.field_path} from your earlier response. "
                f"Can you confirm or correct this: {template}"
            )

        phrased = self._phrase(template, target)
        context = schema["discovery_state"]["next_question_context"]
        context["target_section"] = target.section
        context["target_field"] = target.field_path
        context["rationale"] = target.rationale
        context["question_text"] = phrased
        return phrased

    def _phrase(self, template: str, target: RankedGap) -> str:
        if not discovery_llm_enabled():
            return template

        chain = _phrasing_llm()
        if chain is None:
            return template

        try:
            response = chain.invoke(
                {
                    "field_path": target.field_path,
                    "rationale": target.rationale,
                    "template": template,
                }
            )
            content = getattr(response, "content", response)
            text = str(content).strip()
            return text or template
        except Exception:
            return template
