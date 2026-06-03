"""User-facing copy for discovery chat."""

DISCOVERY_GREETING = (
    "Hi — I'm here to help collect information about your AI system for governance discovery.\n\n"
    "I'll ask a short series of focused questions about how your system works, what data it uses, "
    "and how it is operated. Your answers build a structured profile we can use for risk and "
    "compliance review. Please answer each question as clearly as you can."
)

LLM_UNAVAILABLE_NOTICE = (
    "Our AI wording service (Groq) is temporarily unavailable (rate limit or API key issue). "
    "Discovery will continue with standard questions — your answers are still saved."
)
