/**
 * JUPITER DISCOVERY ENGINE
 * Risk Queue Data Structure + Session State
 *
 * BOOT PHASE  — runs once when a discovery session is initialized.
 * TURN PHASE  — runs once per user message (single ADK agent call).
 */


// ─────────────────────────────────────────────────────────────────────────────
// 1. RISK QUEUE ITEM — the atomic unit in the queue
//    One item per leaf field that needs to be discovered.
//    Pre-calculated at boot. Never changes during the session.
// ─────────────────────────────────────────────────────────────────────────────

const RiskQueueItem = {
  // Stable key — dot-path into the schema, e.g. "data_assets.pii_sent_to_external_llm"
  key: "data_assets.pii_sent_to_external_llm",

  // Human-readable label for the question generator
  label: "PII sent to external LLM provider",

  // Section this key belongs to — used to group questions naturally
  section: "data_assets",

  // Pre-calculated priority score (0–100). Higher = ask sooner.
  // Formula: risk_weight + required_bonus + section_order_weight
  // risk_weight:      CRITICAL=40, HIGH=25, MEDIUM=10, LOW=0
  // required_bonus:   required=10, optional=0
  // section_order:    system_profile=15, architecture=12, models=10,
  //                   tooling=10, data_assets=12, knowledge_sources=8,
  //                   security=13, compliance=11, users=9, operational=5, risk=10
  priority_score: 62,  // 40 + 10 + 12

  // Risk level — used by question generator to know how to phrase the question
  risk_level: "CRITICAL",  // "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"

  // Whether this field is mandatory for discovery to be considered complete
  required: true,

  // Hint to the question generator: what kind of answer to expect
  // Drives how the LLM parses the answer back
  answer_type: "boolean",  // "boolean" | "enum" | "multi_enum" | "free_text" | "number" | "url"

  // If answer_type is enum or multi_enum, what are the valid values
  allowed_values: null,  // or ["value1", "value2", ...]

  // Fields that become relevant only if this field has a specific value
  // Used to dynamically insert follow-up items into the queue
  unlocks_on: {
    true: ["data_assets.pii_categories", "security.ai_specific_security.data_leakage_protection"]
  },

  // Context given to LLM question generator — what we already know that's relevant
  // Populated at question-generation time, not at boot
  context_hint: null
}


// ─────────────────────────────────────────────────────────────────────────────
// 2. THE PRIORITY QUEUE — sorted array, pre-built at boot
//    Treated as a queue: always pop from index 0.
//    Items with the same priority_score keep schema section order.
//    This replaces your gap analyzer + risk prioritizer completely.
// ─────────────────────────────────────────────────────────────────────────────

const PRIORITY_QUEUE_TEMPLATE = [
  // Sorted descending by priority_score.
  // This is the TEMPLATE — cloned per session, not mutated globally.

  // ── CRITICAL + required (score 60+) ──────────────────────────────────────
  { key: "data_assets.pii_sent_to_external_llm",                     priority_score: 62, risk_level: "CRITICAL", required: true,  answer_type: "boolean",    section: "data_assets",       label: "PII sent to external LLM API",           unlocks_on: { true: ["data_assets.pii_categories"] } },
  { key: "tooling.human_approval_config.human_approval_required",    priority_score: 62, risk_level: "CRITICAL", required: true,  answer_type: "boolean",    section: "tooling",           label: "Human approval required for tool calls",  unlocks_on: { true: ["tooling.human_approval_config.approval_for"] } },
  { key: "architecture.agentic.is_agentic",                          priority_score: 57, risk_level: "CRITICAL", required: true,  answer_type: "boolean",    section: "architecture",      label: "Is the system agentic",                   unlocks_on: { true: ["architecture.agentic.autonomy_level", "architecture.agentic.orchestration_pattern"] } },
  { key: "security.authentication_method",                           priority_score: 58, risk_level: "HIGH",     required: true,  answer_type: "enum",       section: "security",          label: "Authentication method",                   allowed_values: ["oauth2","saml","api_key","jwt","mfa","sso","none","mixed"] },
  { key: "security.audit_logging_enabled",                           priority_score: 58, risk_level: "HIGH",     required: true,  answer_type: "boolean",    section: "security",          label: "Audit logging enabled",                   unlocks_on: { false: ["_flag.missing_audit_logging"] } },
  { key: "data_assets.sensitive_financial_data",                     priority_score: 55, risk_level: "CRITICAL", required: true,  answer_type: "free_text",  section: "data_assets",       label: "Sensitive financial data handled",         unlocks_on: null },
  { key: "compliance.applicable_regulations",                        priority_score: 56, risk_level: "HIGH",     required: true,  answer_type: "multi_enum", section: "compliance",        label: "Applicable regulations",                  allowed_values: ["gdpr","ccpa","pci_dss","sox","hipaa","dora","eu_ai_act","rbi_guidelines","sebi_regulations","aml_cft","other"] },

  // ── HIGH + required (score 35–55) ────────────────────────────────────────
  { key: "system_profile.business_purpose",                          priority_score: 50, risk_level: "HIGH",     required: true,  answer_type: "free_text",  section: "system_profile",    label: "Business purpose of the system",          unlocks_on: null },
  { key: "system_profile.primary_use_case",                          priority_score: 48, risk_level: "HIGH",     required: true,  answer_type: "enum",       section: "system_profile",    label: "Primary use case",                        allowed_values: ["banking_assistant","customer_support_agent","kyc_assistant","loan_assistant","investment_advisor","financial_analysis_agent","agentic_rag","multi_agent_system","fraud_detection","risk_scoring","document_processing","other"] },
  { key: "system_profile.industry",                                  priority_score: 46, risk_level: "HIGH",     required: true,  answer_type: "enum",       section: "system_profile",    label: "Industry vertical",                       allowed_values: ["banking","insurance","investment","payments","lending","wealth_management","regtech","fintech_other"] },
  { key: "system_profile.system_description",                        priority_score: 44, risk_level: "HIGH",     required: true,  answer_type: "free_text",  section: "system_profile",    label: "System description",                      unlocks_on: null },
  { key: "models.primary_llm.provider",                              priority_score: 45, risk_level: "HIGH",     required: true,  answer_type: "enum",       section: "models",            label: "LLM provider",                            allowed_values: ["openai","anthropic","google","meta","mistral","cohere","azure_openai","aws_bedrock","huggingface","custom_fine_tuned","open_source_self_hosted","other"] },
  { key: "models.primary_llm.model_name",                            priority_score: 43, risk_level: "HIGH",     required: true,  answer_type: "free_text",  section: "models",            label: "LLM model name",                          unlocks_on: null },
  { key: "models.primary_llm.access_method",                         priority_score: 42, risk_level: "HIGH",     required: true,  answer_type: "enum",       section: "models",            label: "Model access method",                     allowed_values: ["api","self_hosted","fine_tuned_api","bedrock","azure_openai","vertex_ai"] },
  { key: "architecture.system_type",                                 priority_score: 47, risk_level: "HIGH",     required: true,  answer_type: "enum",       section: "architecture",      label: "System architecture type",                allowed_values: ["single_agent","multi_agent","rag_pipeline","agentic_rag","workflow_automation","chatbot_only","hybrid"] },
  { key: "architecture.framework",                                   priority_score: 40, risk_level: "HIGH",     required: true,  answer_type: "enum",       section: "architecture",      label: "AI framework used",                       allowed_values: ["langchain","langgraph","llamaindex","autogen","crewai","semantic_kernel","haystack","custom","none","other"] },
  { key: "architecture.data_flow.user_input_flow",                   priority_score: 38, risk_level: "HIGH",     required: true,  answer_type: "free_text",  section: "architecture",      label: "How user input flows through the system", unlocks_on: null },
  { key: "architecture.data_flow.response_generation_flow",          priority_score: 36, risk_level: "HIGH",     required: true,  answer_type: "free_text",  section: "architecture",      label: "How responses are generated",             unlocks_on: null },
  { key: "data_assets.data_types_processed",                         priority_score: 47, risk_level: "HIGH",     required: true,  answer_type: "multi_enum", section: "data_assets",       label: "Data types processed",                    allowed_values: ["customer_pii","financial_data","transaction_history","credit_data","kyc_documents","aml_data","account_data","investment_portfolio","behavioral_data","biometric_data","health_data","employment_data","internal_documents","market_data","regulatory_filings","audit_logs","communication_data","geolocation_data","device_data"] },
  { key: "data_assets.data_encryption.at_rest",                      priority_score: 40, risk_level: "HIGH",     required: true,  answer_type: "boolean",    section: "data_assets",       label: "Data encrypted at rest",                  unlocks_on: null },
  { key: "data_assets.data_encryption.in_transit",                   priority_score: 40, risk_level: "HIGH",     required: true,  answer_type: "boolean",    section: "data_assets",       label: "Data encrypted in transit",               unlocks_on: null },
  { key: "security.authorization_model",                             priority_score: 43, risk_level: "HIGH",     required: true,  answer_type: "enum",       section: "security",          label: "Authorization model",                     allowed_values: ["rbac","abac","pbac","none","custom"] },
  { key: "security.output_filtering",                                priority_score: 43, risk_level: "HIGH",     required: true,  answer_type: "boolean",    section: "security",          label: "Output filtering / guardrails",           unlocks_on: null },
  { key: "compliance.model_governance_framework",                    priority_score: 43, risk_level: "HIGH",     required: true,  answer_type: "free_text",  section: "compliance",        label: "Model governance framework",              unlocks_on: null },
  { key: "compliance.consent_management",                            priority_score: 43, risk_level: "HIGH",     required: true,  answer_type: "free_text",  section: "compliance",        label: "Consent management process",              unlocks_on: null },
  { key: "knowledge_sources.uses_rag",                               priority_score: 38, risk_level: "HIGH",     required: true,  answer_type: "boolean",    section: "knowledge_sources", label: "Uses RAG",                                unlocks_on: { true: ["knowledge_sources.knowledge_base_description", "knowledge_sources.document_uploads"] } },
  { key: "users_and_customers.description",                          priority_score: 35, risk_level: "HIGH",     required: true,  answer_type: "free_text",  section: "users_and_customers", label: "Who uses the system",                   unlocks_on: null },
  { key: "users_and_customers.geographic_regions",                   priority_score: 34, risk_level: "HIGH",     required: true,  answer_type: "free_text",  section: "users_and_customers", label: "Geographic regions served",             unlocks_on: null },
  { key: "tooling.apis.api_authentication_method",                   priority_score: 38, risk_level: "HIGH",     required: true,  answer_type: "enum",       section: "tooling",           label: "API authentication method",               allowed_values: ["api_key","oauth2","jwt","mtls","none","mixed"] },
  { key: "risk_profile.incident_response_process",                   priority_score: 40, risk_level: "HIGH",     required: true,  answer_type: "free_text",  section: "risk_profile",      label: "Incident response process for AI failures", unlocks_on: null },
  { key: "risk_profile.mitigations_in_place",                        priority_score: 38, risk_level: "HIGH",     required: true,  answer_type: "free_text",  section: "risk_profile",      label: "Risk mitigations currently in place",     unlocks_on: null },

  // ── MEDIUM + required (score 15–34) ──────────────────────────────────────
  { key: "architecture.multi_agent.is_multi_agent",                  priority_score: 30, risk_level: "MEDIUM",   required: true,  answer_type: "boolean",    section: "architecture",      label: "Is multi-agent system",                   unlocks_on: { true: ["architecture.multi_agent.number_of_agents", "architecture.multi_agent.agent_communication_protocol"] } },
  { key: "models.embedding_model",                                   priority_score: 22, risk_level: "MEDIUM",   required: false, answer_type: "free_text",  section: "models",            label: "Embedding model used",                    unlocks_on: null },
  { key: "models.secondary_models",                                  priority_score: 20, risk_level: "MEDIUM",   required: false, answer_type: "free_text",  section: "models",            label: "Secondary models (classifiers, rerankers)", unlocks_on: null },
  { key: "tooling.tools",                                            priority_score: 32, risk_level: "MEDIUM",   required: false, answer_type: "free_text",  section: "tooling",           label: "Tools and capabilities the agent can invoke", unlocks_on: null },
  { key: "data_assets.pii_categories",                               priority_score: 30, risk_level: "MEDIUM",   required: false, answer_type: "multi_enum", section: "data_assets",       label: "PII categories present",                  allowed_values: ["name","email","phone","address","national_id","passport","dob","tax_id","bank_account","card_number","ssn","income","credit_score","ip_address","device_id","cookies","biometric","health","political_views","religious_beliefs"] },
  { key: "knowledge_sources.knowledge_base_description",             priority_score: 25, risk_level: "MEDIUM",   required: false, answer_type: "free_text",  section: "knowledge_sources", label: "Knowledge base and documents description", unlocks_on: null },
  { key: "security.secrets_management",                              priority_score: 28, risk_level: "MEDIUM",   required: true,  answer_type: "free_text",  section: "security",          label: "Secrets management approach",             unlocks_on: null },
  { key: "compliance.data_retention_policy",                         priority_score: 28, risk_level: "MEDIUM",   required: true,  answer_type: "free_text",  section: "compliance",        label: "Data retention policy",                   unlocks_on: null },
  { key: "compliance.cross_border_transfer",                         priority_score: 22, risk_level: "MEDIUM",   required: false, answer_type: "boolean",    section: "compliance",        label: "Cross-border data transfer",              unlocks_on: null },
  { key: "risk_profile.risk_tolerance",                              priority_score: 25, risk_level: "MEDIUM",   required: true,  answer_type: "free_text",  section: "risk_profile",      label: "Risk tolerance level",                    unlocks_on: null },

  // ── OPTIONAL / LOW (score < 15) ──────────────────────────────────────────
  { key: "system_access.entry_point_curl",                           priority_score: 12, risk_level: "LOW",      required: false, answer_type: "url",        section: "system_access",     label: "System entry point / API endpoint",       unlocks_on: null },
  { key: "system_access.authentication_curl",                        priority_score: 10, risk_level: "LOW",      required: false, answer_type: "free_text",  section: "system_access",     label: "Authentication curl example",             unlocks_on: null },
  { key: "knowledge_sources.document_uploads",                       priority_score: 8,  risk_level: "LOW",      required: false, answer_type: "free_text",  section: "knowledge_sources", label: "Policy and document uploads",             unlocks_on: null },
  { key: "policies.internal_ai_policy",                              priority_score: 14, risk_level: "LOW",      required: true,  answer_type: "free_text",  section: "policies",          label: "Internal AI usage policy",                unlocks_on: null },
  { key: "policies.data_handling_policy",                            priority_score: 14, risk_level: "LOW",      required: true,  answer_type: "free_text",  section: "policies",          label: "Data handling policy",                    unlocks_on: null },
]


// ─────────────────────────────────────────────────────────────────────────────
// 3. PRIORITY SCORE FORMULA
//    Run this at boot to build the queue from the schema.
//    No magic numbers in the schema itself — computed here.
// ─────────────────────────────────────────────────────────────────────────────

const RISK_WEIGHTS = {
  CRITICAL: 40,
  HIGH:     25,
  MEDIUM:   10,
  LOW:       0
}

const SECTION_WEIGHTS = {
  security:            13,
  data_assets:         12,
  architecture:        12,
  compliance:          11,
  system_profile:      15,  // reduced: asked early but not highest risk
  models:              10,
  tooling:             10,
  risk_profile:        10,
  knowledge_sources:    8,
  users_and_customers:  9,
  policies:             7,
  system_access:        5,
  operational:          5
}

function computePriorityScore(schemaField) {
  const risk     = RISK_WEIGHTS[schemaField.risk_level ?? "LOW"]
  const required = schemaField.required ? 10 : 0
  const section  = SECTION_WEIGHTS[schemaField.section] ?? 5
  return risk + required + section
}

// Build and sort the queue (called once at session start)
function buildPriorityQueue(schemaFields) {
  return schemaFields
    .map(field => ({ ...field, priority_score: computePriorityScore(field) }))
    .sort((a, b) => b.priority_score - a.priority_score)
}


// ─────────────────────────────────────────────────────────────────────────────
// 4. SESSION STATE — one instance per active discovery conversation
//    Cloned from PRIORITY_QUEUE_TEMPLATE at session start.
//    All mutations happen here. Never touch the template.
// ─────────────────────────────────────────────────────────────────────────────

const SessionState = {
  session_id: "uuid-here",
  started_at: "2025-01-01T00:00:00Z",
  last_updated_at: "2025-01-01T00:00:00Z",

  // ── The live queue ────────────────────────────────────────────────────────
  // Mutable copy of the sorted PRIORITY_QUEUE_TEMPLATE.
  // Items are REMOVED (shift/splice) when their field is filled with
  // confidence >= 0.75. Never re-added — monotonically shrinks.
  queue: [
    /* [...copy of PRIORITY_QUEUE_TEMPLATE sorted by priority_score...] */
  ],

  // ── What we know so far ───────────────────────────────────────────────────
  // Flat dict: schema dot-path → { value, confidence, source, turn_discovered }
  // Built up turn by turn by parse_answer tool.
  discovered: {
    // "system_profile.business_purpose": {
    //   value: "An AI assistant for retail banking customers",
    //   confidence: 0.9,
    //   source: "customer_stated",
    //   turn_discovered: 1
    // }
  },

  // ── Cross-question tracking ────────────────────────────────────────────────
  // If the last answer had confidence < 0.75, the SAME queue item stays at
  // index 0 and we cross-question. Track how many times we've cross-questioned
  // a single key so we don't loop more than 2 times before moving on.
  current_key: null,         // dot-path of the key being asked about right now
  cross_question_count: 0,   // resets to 0 every time current_key changes
  max_cross_questions: 2,    // after 2 cross-questions, accept what we have and pop

  // ── Progress counters (pre-computed, no scan needed) ──────────────────────
  total_keys: 0,             // set at boot: PRIORITY_QUEUE_TEMPLATE.length
  filled_keys: 0,            // increments each time an item is removed from queue
  remaining_keys: 0,         // total_keys - filled_keys (your gap counter)
  completion_pct: 0.0,       // filled_keys / total_keys

  // ── Risk flags (set by parse_answer when a high-risk pattern is found) ────
  high_risk_flags_triggered: [],
  // e.g. ["pii_to_llm", "missing_audit_logging", "payment_api", "autonomous_actions"]

  // ── Turn history (for LLM context window) ─────────────────────────────────
  // Keep last 6 turns only — enough for follow-up context, small enough for <2s
  turn_history: [
    // { turn: 1, question_asked: "...", user_answer: "...", keys_filled: ["..."] }
  ],
  max_history_turns: 6,

  // ── Completion criteria ───────────────────────────────────────────────────
  discovery_complete: false,
  completion_criteria: {
    all_required_filled: false,     // all items where required=true are filled
    all_critical_gaps_resolved: false,  // no CRITICAL items left in queue
    confidence_met: false,          // avg confidence of discovered{} >= 0.80
    minimum_confidence: 0.80
  }
}


// ─────────────────────────────────────────────────────────────────────────────
// 5. ADK TOOL CONTRACTS — what each tool receives and returns
//    These are the 4 tools registered on your ADK agent.
//    The agent calls them in sequence within a single turn.
// ─────────────────────────────────────────────────────────────────────────────

// Tool 1: parse_answer
// Input: user's raw answer text + current session state
// Output: array of fact patches + confidence scores
// The agent calls this FIRST every turn.
const ParseAnswerInput = {
  user_answer: "We use GPT-4o via the OpenAI API directly, no fine-tuning",
  current_key: "models.primary_llm.provider",
  session_state_snapshot: { /* SessionState */ }
}
const ParseAnswerOutput = {
  patches: [
    { key: "models.primary_llm.provider",   value: "openai",     confidence: 0.98, source: "customer_stated" },
    { key: "models.primary_llm.model_name",  value: "gpt-4o",     confidence: 0.98, source: "customer_stated" },
    { key: "models.primary_llm.access_method", value: "api",      confidence: 0.95, source: "customer_stated" },
    // Note: the answer also implicitly tells us is_fine_tuned = false
    // but confidence is lower since it was stated negatively
    { key: "models.primary_llm.is_fine_tuned", value: false,      confidence: 0.85, source: "inferred" }
  ],
  risk_flags_detected: [],   // e.g. ["pii_to_llm"] if relevant
  needs_cross_question: false,
  cross_question_reason: null
}

// Tool 2: peek_queue
// Input: current queue (just reads, no mutation)
// Output: next item to ask about (after applying patches above)
// The agent calls this SECOND to know what topic comes next.
const PeekQueueOutput = {
  next_item: { /* RiskQueueItem */ },
  remaining_count: 31,
  section_changed: true,  // true if next item is in a different section than current
  section_intro_needed: "models"  // if section_changed, agent should intro the new section naturally
}

// Tool 3: generate_question
// Input: next queue item + last 6 turns of history + any newly discovered context
// Output: natural language question string
// The LLM generates this — NOT a template lookup.
const GenerateQuestionInput = {
  target_item: { /* RiskQueueItem */ },
  context: {
    already_known: {
      "models.primary_llm.provider": "openai",
      "architecture.system_type": "agentic_rag"
    },
    last_user_statement: "We use GPT-4o via the OpenAI API directly",
    section_intro_needed: false
  },
  instruction: "Generate a single, natural, conversational question to discover the value of the target field. Reference what the user already told us where relevant. Do not ask a yes/no question for free_text fields. Do not reveal the field name or schema structure. Max 2 sentences."
}
const GenerateQuestionOutput = {
  question: "Since you're calling GPT-4o directly via the OpenAI API — does any customer data or PII end up in the prompts you send to OpenAI, or do you sanitize that before it leaves your environment?",
  is_cross_question: false
}

// Tool 4: check_confidence
// Input: current session state after patches applied
// Output: whether to pop the current key off the queue or cross-question
const CheckConfidenceOutput = {
  should_pop: true,           // confidence >= 0.75 for current_key
  should_cross_question: false,
  discovery_complete: false,
  completion_pct: 0.18        // 18% done
}


// ─────────────────────────────────────────────────────────────────────────────
// 6. TURN EXECUTION FLOW — pseudo-code
//    This is what your ADK agent orchestrates in a single turn.
//    Target: < 2s wall time (one LLM call, tool calls are local/fast)
// ─────────────────────────────────────────────────────────────────────────────

/*

ON SESSION START:
  queue    = buildPriorityQueue(SCHEMA_FIELDS)  // sort once
  state    = clone(SessionState)
  state.total_keys = queue.length
  state.remaining_keys = queue.length
  state.current_key = queue[0].key
  → send opening question (generated by LLM with no prior context)

ON EACH USER MESSAGE:
  1. parse_answer(user_answer, state.current_key, state)
     → patches[]                      // may contain 1..N facts
     → risk_flags_detected[]
     → needs_cross_question: bool

  2. Apply patches to state.discovered{}
     For each patched key:
       if key exists in queue → remove it (shift if index 0, splice otherwise)
       state.filled_keys++
       state.remaining_keys--

  3. Apply risk flags to state.high_risk_flags_triggered[]

  4. if needs_cross_question AND state.cross_question_count < max_cross_questions:
       state.cross_question_count++
       → generate_question({ target_item: queue[0], is_cross_question: true })
       → return cross-question to user

  5. else:
       state.cross_question_count = 0
       next_item = peek_queue(state.queue)   // just reads queue[0]
       state.current_key = next_item.key

  6. check_confidence(state)
       if discovery_complete → return completion summary

  7. generate_question({ target_item: next_item, context: state })
     → question string

  8. Append to turn_history (trim to last 6)

  9. Return question to user

*/