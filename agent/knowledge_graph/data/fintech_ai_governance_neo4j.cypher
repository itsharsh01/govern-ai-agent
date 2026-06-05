// ============================================================
//  FinTech AI Governance Ontology — Neo4j Cypher
//  Generated from structured ontology covering:
//    Banking / Payment / KYC / Loan / Investment / Support agents
//  Entities: Assets · Tools · Risks · Controls · Regulations
//  Relationships: 62 typed graph edges
// ============================================================


// ────────────────────────────────────────────────────────────
//  CONSTRAINTS & INDEXES
// ────────────────────────────────────────────────────────────

CREATE CONSTRAINT unique_node_name IF NOT EXISTS
  FOR (n:OntologyNode) REQUIRE n.name IS UNIQUE;

CREATE INDEX node_risk_index IF NOT EXISTS
  FOR (n:OntologyNode) ON (n.risk);

CREATE INDEX node_category_index IF NOT EXISTS
  FOR (n:OntologyNode) ON (n.category);


// ────────────────────────────────────────────────────────────
//  LABEL LEGEND
//  :SensitiveFinancialData  — financial data assets
//  :PersonalInformation     — customer PII assets
//  :AgentTool               — APIs / processing pipelines
//  :AISecurityRisk          — attack vectors
//  :PrivacyRisk             — privacy-specific risks
//  :ComplianceControl       — mitigating controls
//  :BankingRegulation       — statutes and standards
//  :GovernanceRequirement   — frameworks and requirements
//  :AIAgent                 — the six agent archetypes
// ────────────────────────────────────────────────────────────


// ============================================================
//  SECTION 1 — SENSITIVE FINANCIAL DATA ASSETS
// ============================================================

CREATE (:SensitiveFinancialData:OntologyNode {
  name:        'Account balance & transaction history',
  category:    'Sensitive financial data',
  risk:        'Critical',
  description: 'Real-time and historical balances, credits, debits, timestamps, merchant codes. Core data accessed by banking and payment agents.',
  sub_types:   ['real_time_balance','ledger_history','spending_patterns','scheduled_payments','transfer_corridors'],
  data_classifications: ['PII','financial_confidential','behavioural'],
  encryption_required: true,
  agents_with_access: ['banking_assistant','payment_agent','customer_support_agent']
});

CREATE (:SensitiveFinancialData:OntologyNode {
  name:        'Credit score & risk profile',
  category:    'Sensitive financial data',
  risk:        'Critical',
  description: 'FICO/VantageScore, debt-to-income ratios, credit utilisation, derogatory marks. Primary input for loan and investment agents.',
  sub_types:   ['credit_score','dti_ratio','credit_utilisation','derogatory_marks','repayment_history'],
  data_classifications: ['financial_confidential','regulated_FCRA'],
  encryption_required: true,
  agents_with_access: ['loan_agent','investment_assistant']
});

CREATE (:SensitiveFinancialData:OntologyNode {
  name:        'Payment card data (PAN, CVV)',
  category:    'Sensitive financial data',
  risk:        'Critical',
  description: 'Primary account numbers, card verification values, expiry dates. Handled by payment agents during authorisation flows.',
  sub_types:   ['PAN','CVV','expiry_date','cardholder_name'],
  data_classifications: ['PCI_DSS_CHD','financial_confidential'],
  encryption_required: true,
  tokenisation_required: true,
  agents_with_access: ['payment_agent']
});

CREATE (:SensitiveFinancialData:OntologyNode {
  name:        'Wire & ACH transfer instructions',
  category:    'Sensitive financial data',
  risk:        'Critical',
  description: 'Beneficiary account details, routing numbers, SWIFT/IBAN codes, transfer amounts and scheduling.',
  sub_types:   ['routing_number','account_number','SWIFT_IBAN','beneficiary_name','transfer_amount'],
  data_classifications: ['financial_confidential','payment_sensitive'],
  encryption_required: true,
  agents_with_access: ['payment_agent','banking_assistant']
});

CREATE (:SensitiveFinancialData:OntologyNode {
  name:        'Investment portfolio holdings',
  category:    'Sensitive financial data',
  risk:        'High',
  description: 'Securities positions, unrealised P&L, asset allocation, trading history, dividend records.',
  sub_types:   ['securities_positions','unrealised_PnL','asset_allocation','trade_history'],
  data_classifications: ['financial_confidential','MiFID_regulated'],
  encryption_required: true,
  agents_with_access: ['investment_assistant']
});

CREATE (:SensitiveFinancialData:OntologyNode {
  name:        'Loan application & repayment data',
  category:    'Sensitive financial data',
  risk:        'High',
  description: 'Loan purpose, collateral details, repayment schedule, payment history, default flags. Used by loan agents for underwriting decisions.',
  sub_types:   ['loan_purpose','collateral','repayment_schedule','default_history','outstanding_balance'],
  data_classifications: ['financial_confidential','ECOA_regulated','FCRA_regulated'],
  encryption_required: true,
  agents_with_access: ['loan_agent']
});


// ============================================================
//  SECTION 2 — CUSTOMER PERSONAL INFORMATION ASSETS
// ============================================================

CREATE (:PersonalInformation:OntologyNode {
  name:        'KYC documents',
  category:    'Personal information',
  risk:        'Critical',
  description: 'Government-issued IDs, utility bills, biometric selfies, proof of address. Uploaded and processed by KYC agents.',
  sub_types:   ['government_ID','utility_bill','biometric_selfie','proof_of_address','tax_identification'],
  data_classifications: ['PII','biometric','GDPR_special_category'],
  encryption_required: true,
  retention_policy: 'jurisdiction_specific_minimum_5yr',
  agents_with_access: ['kyc_agent']
});

CREATE (:PersonalInformation:OntologyNode {
  name:        'Customer PII',
  category:    'Personal information',
  risk:        'Critical',
  description: 'Full legal name, date of birth, SSN/NIN, email, phone number, residential address.',
  sub_types:   ['full_name','date_of_birth','SSN_NIN','email','phone','address'],
  data_classifications: ['PII','GDPR_personal_data','CCPA_personal_information'],
  encryption_required: true,
  agents_with_access: ['customer_support_agent','kyc_agent','banking_assistant','loan_agent']
});

CREATE (:PersonalInformation:OntologyNode {
  name:        'Behavioural & biometric data',
  category:    'Personal information',
  risk:        'High',
  description: 'Typing cadence, voice prints, facial recognition templates, device fingerprints used for continuous authentication.',
  sub_types:   ['typing_cadence','voice_print','facial_template','device_fingerprint','geolocation'],
  data_classifications: ['biometric','GDPR_special_category','CCPA_sensitive'],
  encryption_required: true,
  purpose_limitation: 'authentication_only',
  agents_with_access: ['kyc_agent','customer_support_agent']
});

CREATE (:PersonalInformation:OntologyNode {
  name:        'Chat & interaction history',
  category:    'Personal information',
  risk:        'High',
  description: 'Full conversation logs between customers and AI agents. Contains inferred intent, sensitive disclosures, and potentially other customers PII.',
  sub_types:   ['conversation_logs','intent_signals','session_metadata','agent_reasoning_traces'],
  data_classifications: ['PII','behavioural','potentially_sensitive'],
  encryption_required: true,
  training_use_requires_consent: true,
  agents_with_access: ['banking_assistant','customer_support_agent','payment_agent','loan_agent']
});


// ============================================================
//  SECTION 3 — BANKING & PAYMENT AGENT TOOLS
// ============================================================

CREATE (:AgentTool:OntologyNode {
  name:        'Account inquiry API',
  category:    'Agent tool',
  risk:        'High',
  description: 'Read-only API returning current balances, recent transactions, statements. Scoped per agent session.',
  access_type: 'read_only',
  scope:       ['balance','transactions','statements'],
  auth_method: 'OAuth2_scoped_token',
  rate_limited: true,
  agents_using: ['banking_assistant','customer_support_agent']
});

CREATE (:AgentTool:OntologyNode {
  name:        'Payment initiation API',
  category:    'Agent tool',
  risk:        'Critical',
  description: 'Submits ACH, wire, card payments. Irreversible side-effects make this the highest-risk tool in payment agent architecture.',
  access_type: 'write',
  supported_rails: ['ACH','wire','SWIFT','card_push'],
  requires_step_up_auth: true,
  reversible: false,
  agents_using: ['payment_agent']
});

CREATE (:AgentTool:OntologyNode {
  name:        'KYC document processing pipeline',
  category:    'Agent tool',
  risk:        'Critical',
  description: 'OCR, liveness detection, ID document verification, PEP/watchlist screening. Core tool for KYC agents.',
  components:  ['OCR_engine','liveness_detector','ID_verifier','watchlist_screener'],
  requires_human_review_threshold: 'medium_confidence',
  biometric_processing: true,
  agents_using: ['kyc_agent']
});

CREATE (:AgentTool:OntologyNode {
  name:        'Credit decisioning engine',
  category:    'Agent tool',
  risk:        'Critical',
  description: 'Runs ML scoring models to approve, decline, or counter-offer loans and credit products. Loan and investment agents call this API.',
  model_types: ['gradient_boosting','logistic_regression','neural_network'],
  explainability_required: true,
  fairness_testing_required: true,
  adverse_action_notice: true,
  agents_using: ['loan_agent','investment_assistant']
});

CREATE (:AgentTool:OntologyNode {
  name:        'Portfolio management API',
  category:    'Agent tool',
  risk:        'High',
  description: 'Reads holdings, executes trades, rebalances allocations. Used by investment assistants within suitability guardrails.',
  access_type: 'read_write',
  supported_instruments: ['equities','bonds','ETFs','mutual_funds'],
  requires_suitability_check: true,
  agents_using: ['investment_assistant']
});

CREATE (:AgentTool:OntologyNode {
  name:        'AML / sanctions screening tool',
  category:    'Agent tool',
  risk:        'High',
  description: 'Screens counterparties and transactions against OFAC, EU, UN, and domestic watchlists in real time.',
  watchlists:  ['OFAC_SDN','EU_consolidated','UN_consolidated','domestic_PEP'],
  real_time:   true,
  mandatory_filing: true,
  agents_using: ['payment_agent','kyc_agent']
});

CREATE (:AgentTool:OntologyNode {
  name:        'Customer authentication API',
  category:    'Agent tool',
  risk:        'High',
  description: 'Step-up MFA, biometric re-authentication, and session token validation required before sensitive operations.',
  auth_methods: ['TOTP','SMS_OTP','biometric','hardware_key'],
  step_up_triggers: ['payment_above_threshold','account_change','data_export'],
  agents_using: ['banking_assistant','customer_support_agent','payment_agent']
});

CREATE (:AgentTool:OntologyNode {
  name:        'Regulatory reporting API',
  category:    'Agent tool',
  risk:        'High',
  description: 'Generates CTR, SAR, and other mandatory regulatory filings triggered by agent-detected suspicious activity.',
  report_types: ['CTR','SAR','FBAR','form_8300'],
  filing_deadlines_enforced: true,
  agents_using: ['kyc_agent','payment_agent']
});


// ============================================================
//  SECTION 4 — AI SECURITY RISKS
// ============================================================

CREATE (:AISecurityRisk:OntologyNode {
  name:        'Prompt injection attack',
  category:    'AI security risk',
  risk:        'Critical',
  description: 'Malicious instructions embedded in user input or external data override the agents intended behaviour, causing unauthorised tool calls or data exfiltration.',
  attack_vectors: ['user_input','merchant_memo_fields','retrieved_documents','API_responses'],
  impact:      ['unauthorised_payment','data_exfiltration','session_takeover'],
  owasp_llm:  'LLM01'
});

CREATE (:AISecurityRisk:OntologyNode {
  name:        'Goal hijacking',
  category:    'AI security risk',
  risk:        'Critical',
  description: 'Attacker manipulates multi-turn conversation context to redirect an agent toward unintended objectives such as transferring funds or approving fraudulent loans.',
  attack_vectors: ['multi_turn_manipulation','context_window_overflow','role_confusion'],
  impact:      ['fraudulent_payment','loan_approval_bypass','account_takeover'],
  owasp_llm:  'LLM01'
});

CREATE (:AISecurityRisk:OntologyNode {
  name:        'Indirect prompt injection (tool output)',
  category:    'AI security risk',
  risk:        'Critical',
  description: 'Malicious payloads hidden in external content (emails, PDFs, web pages) retrieved by an agent are injected into its context window.',
  attack_vectors: ['email_content','PDF_documents','web_scraping','third_party_API_responses'],
  impact:      ['data_exfiltration','unauthorised_actions','agent_manipulation'],
  owasp_llm:  'LLM02'
});

CREATE (:AISecurityRisk:OntologyNode {
  name:        'Training data poisoning',
  category:    'AI security risk',
  risk:        'High',
  description: 'Adversary corrupts training or fine-tuning data to introduce biased or backdoored behaviour in production AI models.',
  attack_vectors: ['interaction_log_manipulation','synthetic_data_injection','feedback_loop_gaming'],
  impact:      ['biased_decisions','backdoor_triggers','model_degradation'],
  owasp_llm:  'LLM03'
});

CREATE (:AISecurityRisk:OntologyNode {
  name:        'Credential & session theft',
  category:    'AI security risk',
  risk:        'Critical',
  description: 'Exfiltration of OAuth tokens, API keys, or session cookies from agent memory, logs, or tool outputs.',
  attack_vectors: ['prompt_injection_exfiltration','log_scraping','memory_dump','insecure_storage'],
  impact:      ['persistent_account_access','lateral_movement','data_breach'],
  owasp_llm:  'LLM06'
});

CREATE (:AISecurityRisk:OntologyNode {
  name:        'Model inversion / membership inference',
  category:    'AI security risk',
  risk:        'High',
  description: 'Attacker queries the model repeatedly to reconstruct training records or determine whether specific individuals data was used in training.',
  attack_vectors: ['repeated_adversarial_queries','confidence_score_analysis','shadow_model_attacks'],
  impact:      ['PII_reconstruction','privacy_breach','regulatory_violation'],
  owasp_llm:  'LLM06'
});

CREATE (:AISecurityRisk:OntologyNode {
  name:        'Adversarial inputs to KYC models',
  category:    'AI security risk',
  risk:        'Critical',
  description: 'Manipulated identity documents, deepfake video, or printed photo attacks bypass biometric liveness detection and document verification.',
  attack_vectors: ['deepfake_video','printed_photo','adversarial_perturbations','document_forgery'],
  impact:      ['identity_fraud','AML_bypass','account_takeover'],
  owasp_llm:  'LLM09'
});

CREATE (:AISecurityRisk:OntologyNode {
  name:        'Excessive agency / autonomous action',
  category:    'AI security risk',
  risk:        'High',
  description: 'Agent takes high-impact irreversible actions (large transfers, account closures, loan approvals) beyond its authorised scope or risk threshold.',
  attack_vectors: ['missing_confirmation_gates','scope_creep','cascading_agent_calls'],
  impact:      ['financial_loss','regulatory_violation','customer_harm'],
  owasp_llm:  'LLM08'
});


// ============================================================
//  SECTION 5 — PRIVACY RISKS
// ============================================================

CREATE (:PrivacyRisk:OntologyNode {
  name:        'PII leakage via model output',
  category:    'Privacy risk',
  risk:        'Critical',
  description: 'Agent inadvertently includes another customers personal data in a response due to context bleed, retrieval errors, or insufficient output filtering.',
  triggers:    ['retrieval_augmented_generation_errors','context_window_bleed','insufficient_filtering'],
  regulations_violated: ['GDPR','CCPA','GLBA']
});

CREATE (:PrivacyRisk:OntologyNode {
  name:        'Unlawful purpose limitation breach',
  category:    'Privacy risk',
  risk:        'High',
  description: 'Data collected for one regulated purpose (KYC onboarding) is subsequently used to train AI models without explicit customer consent.',
  triggers:    ['consent_not_obtained','purpose_scope_creep','third_party_sharing'],
  regulations_violated: ['GDPR_Art5','CCPA','GLBA']
});

CREATE (:PrivacyRisk:OntologyNode {
  name:        'Biometric data misuse',
  category:    'Privacy risk',
  risk:        'High',
  description: 'Biometric templates retained beyond necessity, shared with third-party model vendors, or used for purposes beyond initial authentication consent.',
  triggers:    ['excessive_retention','vendor_sharing','scope_expansion'],
  regulations_violated: ['GDPR_Art9','CCPA_sensitive','BIPA']
});

CREATE (:PrivacyRisk:OntologyNode {
  name:        'Discriminatory AI decisions',
  category:    'Privacy risk',
  risk:        'High',
  description: 'Credit, loan, or KYC models produce outcomes that correlate with protected characteristics, causing disparate impact on protected groups.',
  protected_characteristics: ['race','gender','age','national_origin','religion','disability'],
  regulations_violated: ['ECOA','Fair_Housing_Act','GDPR_Art22']
});


// ============================================================
//  SECTION 6 — COMPLIANCE CONTROLS
// ============================================================

CREATE (:ComplianceControl:OntologyNode {
  name:        'Prompt injection detection',
  category:    'Compliance control',
  risk:        'High',
  description: 'Real-time classifier that flags and blocks adversarial instruction patterns before they reach the agent reasoning loop.',
  implementation: ['rule_based_patterns','ML_classifier','semantic_similarity_check'],
  placement:   'pre_reasoning',
  applies_to:  ['all_agents']
});

CREATE (:ComplianceControl:OntologyNode {
  name:        'Transaction authorisation control',
  category:    'Compliance control',
  risk:        'Critical',
  description: 'Step-up confirmation (OTP, biometric, human approval) required for high-value or irreversible financial actions above defined thresholds.',
  threshold_types: ['amount_based','velocity_based','beneficiary_novelty','risk_score'],
  applies_to:  ['payment_agent','banking_assistant']
});

CREATE (:ComplianceControl:OntologyNode {
  name:        'Human-in-the-loop review',
  category:    'Compliance control',
  risk:        'High',
  description: 'Mandatory human approval gate for actions above defined risk thresholds including transfer limits, loan approvals, and SAR filing decisions.',
  trigger_conditions: ['high_risk_score','large_transaction','adverse_credit_decision','SAR_filing'],
  applies_to:  ['kyc_agent','loan_agent','payment_agent']
});

CREATE (:ComplianceControl:OntologyNode {
  name:        'Access control & least privilege',
  category:    'Compliance control',
  risk:        'Critical',
  description: 'Agents granted only the minimum API scopes needed for their specific task. Token-scoped credentials rotated per session.',
  mechanisms:  ['OAuth2_scoped_tokens','role_based_access_control','per_session_rotation','scope_validation'],
  applies_to:  ['all_agents']
});

CREATE (:ComplianceControl:OntologyNode {
  name:        'Audit logging & monitoring',
  category:    'Compliance control',
  risk:        'High',
  description: 'Immutable append-only logs of all agent actions, tool calls, and data accesses. SIEM integration for real-time anomaly alerting.',
  log_fields:  ['agent_id','customer_id','timestamp','tool_called','data_fields_accessed','triggering_utterance'],
  immutability: 'WORM_compliant',
  retention_years: 7,
  applies_to:  ['all_agents']
});

CREATE (:ComplianceControl:OntologyNode {
  name:        'Data encryption control',
  category:    'Compliance control',
  risk:        'Critical',
  description: 'AES-256 encryption at rest, TLS 1.3 in transit for all data assets. Key management via HSM with quarterly rotation.',
  encryption_at_rest: 'AES_256',
  encryption_in_transit: 'TLS_1_3',
  key_management: 'HSM',
  key_rotation_days: 90,
  applies_to:  ['all_agents']
});

CREATE (:ComplianceControl:OntologyNode {
  name:        'Data minimisation',
  category:    'Compliance control',
  risk:        'High',
  description: 'Agents receive only the data fields necessary for the specific task. PII fields stripped from prompts wherever functionally possible.',
  techniques:  ['field_level_filtering','PII_redaction_in_prompts','need_to_know_scoping'],
  applies_to:  ['all_agents']
});

CREATE (:ComplianceControl:OntologyNode {
  name:        'Consent management',
  category:    'Compliance control',
  risk:        'High',
  description: 'Granular opt-in and opt-out tracking for each data processing purpose, propagated to all downstream AI systems and model training pipelines.',
  consent_types: ['data_processing','marketing','model_training','third_party_sharing','biometric_use'],
  applies_to:  ['kyc_agent','customer_support_agent','banking_assistant']
});

CREATE (:ComplianceControl:OntologyNode {
  name:        'Algorithmic fairness audit',
  category:    'Compliance control',
  risk:        'High',
  description: 'Periodic disparate impact testing of credit scoring and KYC models across protected classes including race, gender, age, and national origin.',
  test_types:  ['disparate_impact_ratio','equal_opportunity','calibration','counterfactual_fairness'],
  frequency:   'quarterly',
  applies_to:  ['loan_agent','kyc_agent','investment_assistant']
});

CREATE (:ComplianceControl:OntologyNode {
  name:        'Output filtering & guardrails',
  category:    'Compliance control',
  risk:        'High',
  description: 'Post-generation filters that redact PII, block policy violations, enforce response format constraints, and prevent cross-customer data leakage.',
  filter_types: ['PII_redaction','policy_violation_detection','format_enforcement','cross_customer_check'],
  placement:   'post_reasoning',
  applies_to:  ['all_agents']
});

CREATE (:ComplianceControl:OntologyNode {
  name:        'Model governance & versioning',
  category:    'Compliance control',
  risk:        'High',
  description: 'Controlled model registry with version pinning, automated rollback capability, change approval workflows, and drift monitoring.',
  components:  ['model_registry','version_pinning','rollback_automation','drift_monitoring','approval_workflow'],
  applies_to:  ['credit_decisioning_engine','kyc_document_processing_pipeline']
});

CREATE (:ComplianceControl:OntologyNode {
  name:        'Input validation & sanitisation',
  category:    'Compliance control',
  risk:        'High',
  description: 'Strict schema validation and allowlist-based sanitisation of all external data before it enters any agent context window.',
  techniques:  ['schema_validation','allowlist_filtering','encoding_normalisation','length_limits'],
  applies_to:  ['all_agents']
});

CREATE (:ComplianceControl:OntologyNode {
  name:        'Rate limiting & anomaly detection',
  category:    'Compliance control',
  risk:        'Medium',
  description: 'Per-user and per-agent API rate limits combined with ML-based behavioural anomaly detection using rolling baselines.',
  limits:      ['per_user_per_minute','per_agent_per_hour','burst_detection'],
  anomaly_methods: ['statistical_baseline','isolation_forest','velocity_checks'],
  applies_to:  ['all_agents']
});

CREATE (:ComplianceControl:OntologyNode {
  name:        'Data retention & deletion policy',
  category:    'Compliance control',
  risk:        'High',
  description: 'Defined retention schedules per data type with automated deletion jobs and right-to-erasure (RTBF) fulfilment workflows.',
  retention_schedules: '{"transaction_history":"7_years","kyc_documents":"5_years_post_relationship","biometric_data":"delete_on_purpose_completion","chat_logs":"2_years"}',
  applies_to:  ['customer_support_agent','kyc_agent','banking_assistant']
});

CREATE (:ComplianceControl:OntologyNode {
  name:        'Differential privacy controls',
  category:    'Compliance control',
  risk:        'Medium',
  description: 'Mathematically calibrated noise injection into model training and aggregate query responses to prevent membership inference attacks.',
  epsilon_budget: 1.0,
  mechanism:   'Gaussian_Laplace',
  applies_to:  ['credit_decisioning_engine','kyc_document_processing_pipeline']
});

CREATE (:ComplianceControl:OntologyNode {
  name:        'Tokenisation',
  category:    'Compliance control',
  risk:        'Critical',
  description: 'PAN and sensitive card data replaced with opaque cryptographic tokens throughout all agent workflows. Vault-based detokenisation only at settlement.',
  token_format: 'format_preserving_encryption',
  vault_type:  'HSM_backed',
  detokenisation_restricted_to: ['settlement_system'],
  applies_to:  ['payment_agent']
});


// ============================================================
//  SECTION 7 — BANKING REGULATIONS & GOVERNANCE REQUIREMENTS
// ============================================================

CREATE (:BankingRegulation:OntologyNode {
  name:        'GDPR / CCPA',
  category:    'Banking regulation',
  risk:        'Critical',
  description: 'EU General Data Protection Regulation and California Consumer Privacy Act governing collection, processing, deletion, and portability of personal data.',
  jurisdictions: ['EU','EEA','California_US'],
  key_articles: ['Art5_purpose_limitation','Art6_lawful_basis','Art9_special_categories','Art17_right_erasure','Art22_automated_decisions'],
  max_fine_EUR: 20000000,
  max_fine_pct: 4,
  applies_to:  ['all_agents']
});

CREATE (:BankingRegulation:OntologyNode {
  name:        'PCI-DSS',
  category:    'Banking regulation',
  risk:        'Critical',
  description: 'Payment Card Industry Data Security Standard v4.0. Mandates encryption, access control, audit logging, and tokenisation for all systems handling card data.',
  version:     '4.0',
  requirements: ['Req1_network_controls','Req3_stored_data','Req7_access_control','Req10_logging','Req11_testing'],
  assessment_frequency: 'annual',
  applies_to:  ['payment_agent']
});

CREATE (:BankingRegulation:OntologyNode {
  name:        'BSA / AML',
  category:    'Banking regulation',
  risk:        'Critical',
  description: 'Bank Secrecy Act and Anti-Money Laundering rules requiring transaction monitoring, suspicious activity report (SAR) filing, and watchlist screening.',
  jurisdiction: 'US_federal',
  filing_requirements: ['SAR','CTR','FBAR'],
  monitoring_thresholds: '{"CTR_USD":10000,"SAR_structuring":5000}',
  applies_to:  ['payment_agent','kyc_agent']
});

CREATE (:BankingRegulation:OntologyNode {
  name:        'GLBA',
  category:    'Banking regulation',
  risk:        'High',
  description: 'Gramm-Leach-Bliley Act requiring financial institutions to protect customer financial information and maintain a written information security program.',
  jurisdiction: 'US_federal',
  key_rules:   ['Safeguards_Rule','Privacy_Rule','Pretexting_Provisions'],
  annual_risk_assessment: true,
  applies_to:  ['banking_assistant','customer_support_agent','payment_agent']
});

CREATE (:BankingRegulation:OntologyNode {
  name:        'FCRA',
  category:    'Banking regulation',
  risk:        'High',
  description: 'Fair Credit Reporting Act governing accuracy, privacy, and permissible use of consumer credit information in automated credit decisioning.',
  jurisdiction: 'US_federal',
  key_provisions: ['permissible_purpose','adverse_action_notice','dispute_rights','data_accuracy'],
  adverse_action_notice_days: 30,
  applies_to:  ['loan_agent','credit_decisioning_engine']
});

CREATE (:BankingRegulation:OntologyNode {
  name:        'ECOA / Fair Lending',
  category:    'Banking regulation',
  risk:        'High',
  description: 'Equal Credit Opportunity Act prohibiting discriminatory credit decisions based on race, color, religion, national origin, sex, age, or marital status.',
  jurisdiction: 'US_federal',
  protected_classes: ['race','color','religion','national_origin','sex','age','marital_status','public_assistance'],
  disparate_impact_standard: true,
  applies_to:  ['loan_agent','investment_assistant']
});

CREATE (:BankingRegulation:OntologyNode {
  name:        'MiFID II / SEC regulations',
  category:    'Banking regulation',
  risk:        'High',
  description: 'EU Markets in Financial Instruments Directive II and SEC rules governing investment advice suitability, best execution, and record-keeping for AI-assisted advisory.',
  jurisdictions: ['EU','US'],
  key_requirements: ['suitability_assessment','best_execution','conflicts_of_interest','record_keeping_5yr'],
  applies_to:  ['investment_assistant']
});

CREATE (:GovernanceRequirement:OntologyNode {
  name:        'EU AI Act',
  category:    'Governance requirement',
  risk:        'High',
  description: 'EU regulation classifying credit scoring and biometric identification systems as high-risk AI. Requires conformity assessment, transparency obligations, and human oversight.',
  jurisdiction: 'EU',
  high_risk_categories: ['credit_scoring','biometric_ID','employment','critical_infrastructure'],
  key_obligations: ['conformity_assessment','technical_documentation','human_oversight','accuracy_robustness','transparency'],
  effective_date: '2026-08-02',
  applies_to:  ['credit_decisioning_engine','kyc_document_processing_pipeline']
});

CREATE (:GovernanceRequirement:OntologyNode {
  name:        'SOX',
  category:    'Governance requirement',
  risk:        'High',
  description: 'Sarbanes-Oxley Act requiring audit trails and internal controls over financial reporting systems, including AI-generated outputs that feed into financial statements.',
  jurisdiction: 'US_federal',
  key_sections: ['Sec302_CEO_CFO_certification','Sec404_internal_controls','Sec802_record_retention'],
  applies_to:  ['banking_assistant','loan_agent','investment_assistant']
});

CREATE (:GovernanceRequirement:OntologyNode {
  name:        'NIST AI RMF',
  category:    'Governance requirement',
  risk:        'Medium',
  description: 'NIST AI Risk Management Framework providing a govern-map-measure-manage lifecycle for AI risk applicable to all FinTech agent deployments.',
  functions:   ['GOVERN','MAP','MEASURE','MANAGE'],
  version:     '1.0',
  applies_to:  ['all_agents']
});


// ============================================================
//  SECTION 8 — AI AGENT ARCHETYPES
// ============================================================

CREATE (:AIAgent:OntologyNode {
  name:            'Banking assistant agent',
  category:        'AI agent',
  risk:            'High',
  description:     'Conversational agent handling balance enquiries, transaction look-ups, account alerts, and general banking Q&A.',
  primary_actions: ['balance_enquiry','transaction_lookup','alert_configuration','FAQ_response'],
  human_oversight: 'low_for_reads_high_for_account_changes',
  typical_data_accessed: ['Account balance & transaction history','Customer PII']
});

CREATE (:AIAgent:OntologyNode {
  name:            'Customer support agent',
  category:        'AI agent',
  risk:            'High',
  description:     'Agent handling dispute resolution, complaint triage, product guidance, and escalation to human agents.',
  primary_actions: ['dispute_investigation','complaint_triage','product_explanation','escalation'],
  human_oversight: 'medium',
  typical_data_accessed: ['Account balance & transaction history','Customer PII','Chat & interaction history']
});

CREATE (:AIAgent:OntologyNode {
  name:            'Payment agent',
  category:        'AI agent',
  risk:            'Critical',
  description:     'Agent processing domestic and international payments, fund transfers, and bill payments. Highest risk due to irreversible financial actions.',
  primary_actions: ['domestic_payment','international_wire','bill_payment','scheduled_transfer'],
  human_oversight: 'high_for_large_or_novel_transactions',
  typical_data_accessed: ['Payment card data (PAN, CVV)','Wire & ACH transfer instructions','Account balance & transaction history']
});

CREATE (:AIAgent:OntologyNode {
  name:            'KYC agent',
  category:        'AI agent',
  risk:            'Critical',
  description:     'Agent performing identity verification, document authenticity checks, biometric matching, and AML/PEP screening for onboarding.',
  primary_actions: ['document_verification','biometric_matching','watchlist_screening','risk_scoring'],
  human_oversight: 'mandatory_for_medium_and_high_risk',
  typical_data_accessed: ['KYC documents','Behavioural & biometric data','Customer PII']
});

CREATE (:AIAgent:OntologyNode {
  name:            'Loan agent',
  category:        'AI agent',
  risk:            'Critical',
  description:     'Agent underwriting personal loans, mortgages, and business credit using ML-based credit decisioning with regulatory explainability requirements.',
  primary_actions: ['application_intake','credit_assessment','offer_generation','adverse_action_notice'],
  human_oversight: 'required_for_adverse_decisions',
  typical_data_accessed: ['Credit score & risk profile','Loan application & repayment data','Customer PII']
});

CREATE (:AIAgent:OntologyNode {
  name:            'Investment assistant',
  category:        'AI agent',
  risk:            'High',
  description:     'Agent providing suitability-gated investment recommendations, portfolio analysis, and rebalancing suggestions under MiFID II and SEC constraints.',
  primary_actions: ['suitability_assessment','portfolio_analysis','rebalancing_recommendation','market_insight'],
  human_oversight: 'medium_with_suitability_gate',
  typical_data_accessed: ['Investment portfolio holdings','Credit score & risk profile']
});


// ============================================================
//  SECTION 9 — RELATIONSHIPS (62 typed edges)
// ============================================================

// --- Asset → Agent (ACCESSED_BY) ---

MATCH (a:OntologyNode {name:'Account balance & transaction history'}),
      (b:OntologyNode {name:'Banking assistant agent'})
CREATE (a)-[:ACCESSED_BY {scope:'read_only', auth:'OAuth2_scoped'}]->(b);

MATCH (a:OntologyNode {name:'Account balance & transaction history'}),
      (b:OntologyNode {name:'Payment agent'})
CREATE (a)-[:ACCESSED_BY {scope:'read_only_pre_payment', auth:'OAuth2_scoped'}]->(b);

MATCH (a:OntologyNode {name:'Account balance & transaction history'}),
      (b:OntologyNode {name:'Customer support agent'})
CREATE (a)-[:ACCESSED_BY {scope:'read_only', auth:'OAuth2_scoped'}]->(b);

MATCH (a:OntologyNode {name:'Credit score & risk profile'}),
      (b:OntologyNode {name:'Loan agent'})
CREATE (a)-[:ACCESSED_BY {scope:'underwriting', auth:'service_account'}]->(b);

MATCH (a:OntologyNode {name:'Credit score & risk profile'}),
      (b:OntologyNode {name:'Investment assistant'})
CREATE (a)-[:ACCESSED_BY {scope:'suitability_check', auth:'service_account'}]->(b);

MATCH (a:OntologyNode {name:'Payment card data (PAN, CVV)'}),
      (b:OntologyNode {name:'Payment agent'})
CREATE (a)-[:ACCESSED_BY {scope:'tokenised_only', auth:'PCI_scoped_token'}]->(b);

MATCH (a:OntologyNode {name:'Wire & ACH transfer instructions'}),
      (b:OntologyNode {name:'Payment agent'})
CREATE (a)-[:ACCESSED_BY {scope:'initiation', auth:'OAuth2_step_up'}]->(b);

MATCH (a:OntologyNode {name:'Wire & ACH transfer instructions'}),
      (b:OntologyNode {name:'Banking assistant agent'})
CREATE (a)-[:ACCESSED_BY {scope:'read_only_history', auth:'OAuth2_scoped'}]->(b);

MATCH (a:OntologyNode {name:'Investment portfolio holdings'}),
      (b:OntologyNode {name:'Investment assistant'})
CREATE (a)-[:ACCESSED_BY {scope:'full_portfolio', auth:'OAuth2_scoped'}]->(b);

MATCH (a:OntologyNode {name:'Loan application & repayment data'}),
      (b:OntologyNode {name:'Loan agent'})
CREATE (a)-[:ACCESSED_BY {scope:'underwriting_full', auth:'service_account'}]->(b);

MATCH (a:OntologyNode {name:'KYC documents'}),
      (b:OntologyNode {name:'KYC agent'})
CREATE (a)-[:ACCESSED_BY {scope:'verification_only', auth:'service_account'}]->(b);

MATCH (a:OntologyNode {name:'Customer PII'}),
      (b:OntologyNode {name:'Customer support agent'})
CREATE (a)-[:ACCESSED_BY {scope:'identity_verification', auth:'OAuth2_scoped'}]->(b);

MATCH (a:OntologyNode {name:'Customer PII'}),
      (b:OntologyNode {name:'KYC agent'})
CREATE (a)-[:ACCESSED_BY {scope:'onboarding', auth:'service_account'}]->(b);

MATCH (a:OntologyNode {name:'Behavioural & biometric data'}),
      (b:OntologyNode {name:'KYC agent'})
CREATE (a)-[:ACCESSED_BY {scope:'liveness_and_match', auth:'biometric_service'}]->(b);

MATCH (a:OntologyNode {name:'Chat & interaction history'}),
      (b:OntologyNode {name:'Banking assistant agent'})
CREATE (a)-[:PRODUCED_BY {retention:'2_years', training_use:'consent_required'}]->(b);

MATCH (a:OntologyNode {name:'Chat & interaction history'}),
      (b:OntologyNode {name:'Customer support agent'})
CREATE (a)-[:PRODUCED_BY {retention:'2_years', training_use:'consent_required'}]->(b);

// --- Asset → Control (PROTECTED_BY) ---

MATCH (a:OntologyNode {name:'Account balance & transaction history'}),
      (c:OntologyNode {name:'Data encryption control'})
CREATE (a)-[:PROTECTED_BY]->(c);

MATCH (a:OntologyNode {name:'Account balance & transaction history'}),
      (c:OntologyNode {name:'Access control & least privilege'})
CREATE (a)-[:PROTECTED_BY]->(c);

MATCH (a:OntologyNode {name:'Account balance & transaction history'}),
      (c:OntologyNode {name:'Audit logging & monitoring'})
CREATE (a)-[:PROTECTED_BY]->(c);

MATCH (a:OntologyNode {name:'Credit score & risk profile'}),
      (c:OntologyNode {name:'Access control & least privilege'})
CREATE (a)-[:PROTECTED_BY]->(c);

MATCH (a:OntologyNode {name:'Credit score & risk profile'}),
      (c:OntologyNode {name:'Differential privacy controls'})
CREATE (a)-[:PROTECTED_BY]->(c);

MATCH (a:OntologyNode {name:'Payment card data (PAN, CVV)'}),
      (c:OntologyNode {name:'Tokenisation'})
CREATE (a)-[:PROTECTED_BY]->(c);

MATCH (a:OntologyNode {name:'Payment card data (PAN, CVV)'}),
      (c:OntologyNode {name:'Data encryption control'})
CREATE (a)-[:PROTECTED_BY]->(c);

MATCH (a:OntologyNode {name:'KYC documents'}),
      (c:OntologyNode {name:'Data minimisation'})
CREATE (a)-[:PROTECTED_BY]->(c);

MATCH (a:OntologyNode {name:'Customer PII'}),
      (c:OntologyNode {name:'Data encryption control'})
CREATE (a)-[:PROTECTED_BY]->(c);

MATCH (a:OntologyNode {name:'Customer PII'}),
      (c:OntologyNode {name:'Output filtering & guardrails'})
CREATE (a)-[:PROTECTED_BY]->(c);

MATCH (a:OntologyNode {name:'Behavioural & biometric data'}),
      (c:OntologyNode {name:'Data retention & deletion policy'})
CREATE (a)-[:PROTECTED_BY]->(c);

MATCH (a:OntologyNode {name:'Behavioural & biometric data'}),
      (c:OntologyNode {name:'Consent management'})
CREATE (a)-[:PROTECTED_BY]->(c);

// --- Asset → Regulation (REGULATED_BY) ---

MATCH (a:OntologyNode {name:'Account balance & transaction history'}),
      (r:OntologyNode {name:'GLBA'})
CREATE (a)-[:REGULATED_BY]->(r);

MATCH (a:OntologyNode {name:'Credit score & risk profile'}),
      (r:OntologyNode {name:'FCRA'})
CREATE (a)-[:REGULATED_BY]->(r);

MATCH (a:OntologyNode {name:'Payment card data (PAN, CVV)'}),
      (r:OntologyNode {name:'PCI-DSS'})
CREATE (a)-[:REGULATED_BY]->(r);

MATCH (a:OntologyNode {name:'KYC documents'}),
      (r:OntologyNode {name:'BSA / AML'})
CREATE (a)-[:REGULATED_BY]->(r);

MATCH (a:OntologyNode {name:'KYC documents'}),
      (r:OntologyNode {name:'GDPR / CCPA'})
CREATE (a)-[:REGULATED_BY]->(r);

MATCH (a:OntologyNode {name:'Customer PII'}),
      (r:OntologyNode {name:'GDPR / CCPA'})
CREATE (a)-[:REGULATED_BY]->(r);

MATCH (a:OntologyNode {name:'Investment portfolio holdings'}),
      (r:OntologyNode {name:'MiFID II / SEC regulations'})
CREATE (a)-[:REGULATED_BY]->(r);

MATCH (a:OntologyNode {name:'Loan application & repayment data'}),
      (r:OntologyNode {name:'ECOA / Fair Lending'})
CREATE (a)-[:REGULATED_BY]->(r);

// --- Tool → Agent (USED_BY) ---

MATCH (t:OntologyNode {name:'Account inquiry API'}),
      (ag:OntologyNode {name:'Banking assistant agent'})
CREATE (t)-[:USED_BY]->(ag);

MATCH (t:OntologyNode {name:'Account inquiry API'}),
      (ag:OntologyNode {name:'Customer support agent'})
CREATE (t)-[:USED_BY]->(ag);

MATCH (t:OntologyNode {name:'Payment initiation API'}),
      (ag:OntologyNode {name:'Payment agent'})
CREATE (t)-[:USED_BY]->(ag);

MATCH (t:OntologyNode {name:'KYC document processing pipeline'}),
      (ag:OntologyNode {name:'KYC agent'})
CREATE (t)-[:USED_BY]->(ag);

MATCH (t:OntologyNode {name:'Credit decisioning engine'}),
      (ag:OntologyNode {name:'Loan agent'})
CREATE (t)-[:USED_BY]->(ag);

MATCH (t:OntologyNode {name:'Portfolio management API'}),
      (ag:OntologyNode {name:'Investment assistant'})
CREATE (t)-[:USED_BY]->(ag);

MATCH (t:OntologyNode {name:'AML / sanctions screening tool'}),
      (ag:OntologyNode {name:'Payment agent'})
CREATE (t)-[:USED_BY]->(ag);

MATCH (t:OntologyNode {name:'AML / sanctions screening tool'}),
      (ag:OntologyNode {name:'KYC agent'})
CREATE (t)-[:USED_BY]->(ag);

MATCH (t:OntologyNode {name:'Customer authentication API'}),
      (ag:OntologyNode {name:'Banking assistant agent'})
CREATE (t)-[:USED_BY]->(ag);

MATCH (t:OntologyNode {name:'Customer authentication API'}),
      (ag:OntologyNode {name:'Customer support agent'})
CREATE (t)-[:USED_BY]->(ag);

MATCH (t:OntologyNode {name:'Regulatory reporting API'}),
      (ag:OntologyNode {name:'KYC agent'})
CREATE (t)-[:USED_BY]->(ag);

MATCH (t:OntologyNode {name:'Regulatory reporting API'}),
      (ag:OntologyNode {name:'Payment agent'})
CREATE (t)-[:USED_BY]->(ag);

// --- Tool → Regulation (REGULATED_BY) ---

MATCH (t:OntologyNode {name:'Credit decisioning engine'}),
      (r:OntologyNode {name:'ECOA / Fair Lending'})
CREATE (t)-[:REGULATED_BY]->(r);

MATCH (t:OntologyNode {name:'Credit decisioning engine'}),
      (r:OntologyNode {name:'EU AI Act'})
CREATE (t)-[:REGULATED_BY]->(r);

MATCH (t:OntologyNode {name:'KYC document processing pipeline'}),
      (r:OntologyNode {name:'BSA / AML'})
CREATE (t)-[:REGULATED_BY]->(r);

MATCH (t:OntologyNode {name:'AML / sanctions screening tool'}),
      (r:OntologyNode {name:'BSA / AML'})
CREATE (t)-[:REGULATED_BY]->(r);

MATCH (t:OntologyNode {name:'Portfolio management API'}),
      (r:OntologyNode {name:'MiFID II / SEC regulations'})
CREATE (t)-[:REGULATED_BY]->(r);

// --- Risk → Target (TARGETS / EXPLOITS) ---

MATCH (ri:OntologyNode {name:'Prompt injection attack'}),
      (t:OntologyNode {name:'Payment initiation API'})
CREATE (ri)-[:TARGETS {severity:'Critical', reversibility:'irreversible'}]->(t);

MATCH (ri:OntologyNode {name:'Prompt injection attack'}),
      (ag:OntologyNode {name:'Customer support agent'})
CREATE (ri)-[:TARGETS {attack_surface:'external_user_input'}]->(ag);

MATCH (ri:OntologyNode {name:'Goal hijacking'}),
      (ag:OntologyNode {name:'Payment agent'})
CREATE (ri)-[:TARGETS {impact:'fraudulent_transfer'}]->(ag);

MATCH (ri:OntologyNode {name:'Goal hijacking'}),
      (ag:OntologyNode {name:'Loan agent'})
CREATE (ri)-[:TARGETS {impact:'fraudulent_loan_approval'}]->(ag);

MATCH (ri:OntologyNode {name:'Indirect prompt injection (tool output)'}),
      (ag:OntologyNode {name:'Customer support agent'})
CREATE (ri)-[:TARGETS]->(ag);

MATCH (ri:OntologyNode {name:'Training data poisoning'}),
      (a:OntologyNode {name:'Chat & interaction history'})
CREATE (ri)-[:EXPLOITS]->(a);

MATCH (ri:OntologyNode {name:'Training data poisoning'}),
      (t:OntologyNode {name:'Credit decisioning engine'})
CREATE (ri)-[:TARGETS]->(t);

MATCH (ri:OntologyNode {name:'Credential & session theft'}),
      (t:OntologyNode {name:'Customer authentication API'})
CREATE (ri)-[:TARGETS]->(t);

MATCH (ri:OntologyNode {name:'Model inversion / membership inference'}),
      (a:OntologyNode {name:'Customer PII'})
CREATE (ri)-[:EXPOSES]->(a);

MATCH (ri:OntologyNode {name:'Model inversion / membership inference'}),
      (a:OntologyNode {name:'Credit score & risk profile'})
CREATE (ri)-[:EXPOSES]->(a);

MATCH (ri:OntologyNode {name:'Adversarial inputs to KYC models'}),
      (t:OntologyNode {name:'KYC document processing pipeline'})
CREATE (ri)-[:TARGETS]->(t);

MATCH (ri:OntologyNode {name:'Adversarial inputs to KYC models'}),
      (a:OntologyNode {name:'Behavioural & biometric data'})
CREATE (ri)-[:EXPLOITS]->(a);

MATCH (ri:OntologyNode {name:'Excessive agency / autonomous action'}),
      (ag:OntologyNode {name:'Payment agent'})
CREATE (ri)-[:TARGETS]->(ag);

MATCH (ri:OntologyNode {name:'PII leakage via model output'}),
      (a:OntologyNode {name:'Customer PII'})
CREATE (ri)-[:EXPOSES]->(a);

MATCH (ri:OntologyNode {name:'Discriminatory AI decisions'}),
      (ag:OntologyNode {name:'Loan agent'})
CREATE (ri)-[:AFFECTS]->(ag);

MATCH (ri:OntologyNode {name:'Unlawful purpose limitation breach'}),
      (a:OntologyNode {name:'KYC documents'})
CREATE (ri)-[:EXPLOITS]->(a);

// --- Risk → Control (MITIGATED_BY) ---

MATCH (ri:OntologyNode {name:'Prompt injection attack'}),
      (c:OntologyNode {name:'Prompt injection detection'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'High'}]->(c);

MATCH (ri:OntologyNode {name:'Prompt injection attack'}),
      (c:OntologyNode {name:'Output filtering & guardrails'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'Medium'}]->(c);

MATCH (ri:OntologyNode {name:'Goal hijacking'}),
      (c:OntologyNode {name:'Transaction authorisation control'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'High'}]->(c);

MATCH (ri:OntologyNode {name:'Goal hijacking'}),
      (c:OntologyNode {name:'Human-in-the-loop review'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'High'}]->(c);

MATCH (ri:OntologyNode {name:'Indirect prompt injection (tool output)'}),
      (c:OntologyNode {name:'Input validation & sanitisation'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'High'}]->(c);

MATCH (ri:OntologyNode {name:'Indirect prompt injection (tool output)'}),
      (c:OntologyNode {name:'Prompt injection detection'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'Medium'}]->(c);

MATCH (ri:OntologyNode {name:'Training data poisoning'}),
      (c:OntologyNode {name:'Model governance & versioning'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'High'}]->(c);

MATCH (ri:OntologyNode {name:'Training data poisoning'}),
      (c:OntologyNode {name:'Algorithmic fairness audit'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'Medium'}]->(c);

MATCH (ri:OntologyNode {name:'Credential & session theft'}),
      (c:OntologyNode {name:'Access control & least privilege'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'High'}]->(c);

MATCH (ri:OntologyNode {name:'Credential & session theft'}),
      (c:OntologyNode {name:'Audit logging & monitoring'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'Medium'}]->(c);

MATCH (ri:OntologyNode {name:'Model inversion / membership inference'}),
      (c:OntologyNode {name:'Differential privacy controls'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'High'}]->(c);

MATCH (ri:OntologyNode {name:'Model inversion / membership inference'}),
      (c:OntologyNode {name:'Rate limiting & anomaly detection'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'Medium'}]->(c);

MATCH (ri:OntologyNode {name:'Adversarial inputs to KYC models'}),
      (c:OntologyNode {name:'Human-in-the-loop review'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'High'}]->(c);

MATCH (ri:OntologyNode {name:'Excessive agency / autonomous action'}),
      (c:OntologyNode {name:'Transaction authorisation control'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'High'}]->(c);

MATCH (ri:OntologyNode {name:'Excessive agency / autonomous action'}),
      (c:OntologyNode {name:'Human-in-the-loop review'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'High'}]->(c);

MATCH (ri:OntologyNode {name:'PII leakage via model output'}),
      (c:OntologyNode {name:'Output filtering & guardrails'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'High'}]->(c);

MATCH (ri:OntologyNode {name:'PII leakage via model output'}),
      (c:OntologyNode {name:'Data minimisation'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'Medium'}]->(c);

MATCH (ri:OntologyNode {name:'Discriminatory AI decisions'}),
      (c:OntologyNode {name:'Algorithmic fairness audit'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'High'}]->(c);

MATCH (ri:OntologyNode {name:'Unlawful purpose limitation breach'}),
      (c:OntologyNode {name:'Consent management'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'High'}]->(c);

MATCH (ri:OntologyNode {name:'Unlawful purpose limitation breach'}),
      (c:OntologyNode {name:'Data minimisation'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'Medium'}]->(c);

MATCH (ri:OntologyNode {name:'Biometric data misuse'}),
      (c:OntologyNode {name:'Data retention & deletion policy'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'High'}]->(c);

MATCH (ri:OntologyNode {name:'Biometric data misuse'}),
      (c:OntologyNode {name:'Consent management'})
CREATE (ri)-[:MITIGATED_BY {effectiveness:'High'}]->(c);

// --- Control → Regulation (REQUIRED_BY) ---

MATCH (c:OntologyNode {name:'Data encryption control'}),
      (r:OntologyNode {name:'GLBA'})
CREATE (c)-[:REQUIRED_BY]->(r);

MATCH (c:OntologyNode {name:'Data encryption control'}),
      (r:OntologyNode {name:'PCI-DSS'})
CREATE (c)-[:REQUIRED_BY]->(r);

MATCH (c:OntologyNode {name:'Tokenisation'}),
      (r:OntologyNode {name:'PCI-DSS'})
CREATE (c)-[:REQUIRED_BY]->(r);

MATCH (c:OntologyNode {name:'Audit logging & monitoring'}),
      (r:OntologyNode {name:'BSA / AML'})
CREATE (c)-[:REQUIRED_BY]->(r);

MATCH (c:OntologyNode {name:'Audit logging & monitoring'}),
      (r:OntologyNode {name:'PCI-DSS'})
CREATE (c)-[:REQUIRED_BY]->(r);

MATCH (c:OntologyNode {name:'Audit logging & monitoring'}),
      (r:OntologyNode {name:'SOX'})
CREATE (c)-[:REQUIRED_BY]->(r);

MATCH (c:OntologyNode {name:'Access control & least privilege'}),
      (r:OntologyNode {name:'GLBA'})
CREATE (c)-[:REQUIRED_BY]->(r);

MATCH (c:OntologyNode {name:'Access control & least privilege'}),
      (r:OntologyNode {name:'SOX'})
CREATE (c)-[:REQUIRED_BY]->(r);

MATCH (c:OntologyNode {name:'Consent management'}),
      (r:OntologyNode {name:'GDPR / CCPA'})
CREATE (c)-[:REQUIRED_BY]->(r);

MATCH (c:OntologyNode {name:'Data minimisation'}),
      (r:OntologyNode {name:'GDPR / CCPA'})
CREATE (c)-[:REQUIRED_BY]->(r);

MATCH (c:OntologyNode {name:'Data retention & deletion policy'}),
      (r:OntologyNode {name:'GDPR / CCPA'})
CREATE (c)-[:REQUIRED_BY]->(r);

MATCH (c:OntologyNode {name:'Algorithmic fairness audit'}),
      (r:OntologyNode {name:'ECOA / Fair Lending'})
CREATE (c)-[:REQUIRED_BY]->(r);

MATCH (c:OntologyNode {name:'Human-in-the-loop review'}),
      (r:OntologyNode {name:'EU AI Act'})
CREATE (c)-[:REQUIRED_BY]->(r);

MATCH (c:OntologyNode {name:'Model governance & versioning'}),
      (r:OntologyNode {name:'EU AI Act'})
CREATE (c)-[:REQUIRED_BY]->(r);

MATCH (c:OntologyNode {name:'Model governance & versioning'}),
      (r:OntologyNode {name:'NIST AI RMF'})
CREATE (c)-[:REQUIRED_BY]->(r);

// --- Regulation → Agent (GOVERNS) ---

MATCH (r:OntologyNode {name:'GDPR / CCPA'}),
      (ag:OntologyNode {name:'KYC agent'})
CREATE (r)-[:GOVERNS]->(ag);

MATCH (r:OntologyNode {name:'PCI-DSS'}),
      (ag:OntologyNode {name:'Payment agent'})
CREATE (r)-[:GOVERNS]->(ag);

MATCH (r:OntologyNode {name:'BSA / AML'}),
      (ag:OntologyNode {name:'KYC agent'})
CREATE (r)-[:GOVERNS]->(ag);

MATCH (r:OntologyNode {name:'BSA / AML'}),
      (ag:OntologyNode {name:'Payment agent'})
CREATE (r)-[:GOVERNS]->(ag);

MATCH (r:OntologyNode {name:'ECOA / Fair Lending'}),
      (ag:OntologyNode {name:'Loan agent'})
CREATE (r)-[:GOVERNS]->(ag);

MATCH (r:OntologyNode {name:'MiFID II / SEC regulations'}),
      (ag:OntologyNode {name:'Investment assistant'})
CREATE (r)-[:GOVERNS]->(ag);

MATCH (r:OntologyNode {name:'EU AI Act'}),
      (ag:OntologyNode {name:'KYC agent'})
CREATE (r)-[:GOVERNS]->(ag);

MATCH (r:OntologyNode {name:'EU AI Act'}),
      (ag:OntologyNode {name:'Loan agent'})
CREATE (r)-[:GOVERNS]->(ag);

MATCH (r:OntologyNode {name:'NIST AI RMF'}),
      (ag:OntologyNode {name:'Banking assistant agent'})
CREATE (r)-[:GOVERNS]->(ag);

// --- Privacy risk → Regulation (VIOLATES) ---

MATCH (ri:OntologyNode {name:'PII leakage via model output'}),
      (r:OntologyNode {name:'GDPR / CCPA'})
CREATE (ri)-[:VIOLATES]->(r);

MATCH (ri:OntologyNode {name:'Unlawful purpose limitation breach'}),
      (r:OntologyNode {name:'GDPR / CCPA'})
CREATE (ri)-[:VIOLATES]->(r);

MATCH (ri:OntologyNode {name:'Discriminatory AI decisions'}),
      (r:OntologyNode {name:'ECOA / Fair Lending'})
CREATE (ri)-[:VIOLATES]->(r);


// ============================================================
//  SECTION 10 — USEFUL QUERY PATTERNS
// ============================================================

// Q1: Full risk exposure path — asset → risk → control → regulation
// MATCH (a:SensitiveFinancialData)-[:ACCESSED_BY]->(ag:AIAgent),
//       (ri:OntologyNode)-[:TARGETS]->(ag),
//       (ri)-[:MITIGATED_BY]->(c:ComplianceControl),
//       (c)-[:REQUIRED_BY]->(r:BankingRegulation)
// RETURN a.name AS asset, ag.name AS agent, ri.name AS risk,
//        c.name AS control, r.name AS regulation
// ORDER BY a.name, ri.risk;

// Q2: All Critical-risk nodes with no mitigating control
// MATCH (n:OntologyNode {risk:'Critical'})
// WHERE NOT (n)-[:MITIGATED_BY]->()
// RETURN n.name, labels(n) AS type;

// Q3: Controls required by more than one regulation (shared compliance)
// MATCH (c:ComplianceControl)-[:REQUIRED_BY]->(r:OntologyNode)
// WITH c, count(r) AS reg_count
// WHERE reg_count > 1
// RETURN c.name, reg_count ORDER BY reg_count DESC;

// Q4: Attack surface of payment agent — all risks, tools, and assets
// MATCH (ri:OntologyNode)-[:TARGETS]->(ag:AIAgent {name:'Payment agent'}),
//       (t:AgentTool)-[:USED_BY]->(ag),
//       (a:OntologyNode)-[:ACCESSED_BY]->(ag)
// RETURN DISTINCT ri.name AS risk, t.name AS tool, a.name AS asset;

// Q5: Shortest compliance path from a data asset to a regulation
// MATCH path = shortestPath(
//   (a:OntologyNode {name:'Payment card data (PAN, CVV)'})-[*]->
//   (r:OntologyNode {name:'PCI-DSS'})
// )
// RETURN path;

// Q6: Agents that access data regulated by GDPR but lack consent management
// MATCH (a:PersonalInformation)-[:REGULATED_BY]->(r {name:'GDPR / CCPA'}),
//       (a)-[:ACCESSED_BY]->(ag:AIAgent)
// WHERE NOT (ag)<-[:APPLIED_TO]-(:ComplianceControl {name:'Consent management'})
// RETURN ag.name, a.name;

// ============================================================
//  SECTION 3b — CRM / CUSTOMER DATA TOOL TEMPLATE (CAN_ACCESS)
// ============================================================

CREATE (:AgentTool:OntologyNode {
  name:        'CRM Tool',
  category:    'Agent tool',
  risk:        'High',
  description: 'Customer relationship management integration for profile lookup, contact history, and account context.',
  access_type: 'read_only',
  scope:       ['customer_profile','contact_history','account_context'],
  auth_method: 'OAuth2_scoped_token',
  agents_using: ['customer_support_agent','banking_assistant']
});

CREATE (:PersonalInformation:OntologyNode {
  name:        'Customer Email',
  category:    'Personal information',
  risk:        'High',
  description: 'Customer email addresses used for notifications, authentication, and support correspondence.',
  sub_types:   ['email'],
  data_classifications: ['PII','GDPR_personal_data'],
  encryption_required: true
});

CREATE (:PersonalInformation:OntologyNode {
  name:        'Phone Number',
  category:    'Personal information',
  risk:        'High',
  description: 'Customer mobile and landline numbers used for MFA, alerts, and support callbacks.',
  sub_types:   ['phone'],
  data_classifications: ['PII','GDPR_personal_data'],
  encryption_required: true
});

CREATE (:SensitiveFinancialData:OntologyNode {
  name:        'Account Number',
  category:    'Sensitive financial data',
  risk:        'Critical',
  description: 'Primary customer account identifiers used for banking and CRM lookups.',
  sub_types:   ['account_number'],
  data_classifications: ['financial_confidential','PII'],
  encryption_required: true
});

// --- Tool → data (CAN_ACCESS template edges for instance propagation) ---

MATCH (crm:OntologyNode {name:'CRM Tool'}),
      (email:OntologyNode {name:'Customer Email'}),
      (phone:OntologyNode {name:'Phone Number'}),
      (acct:OntologyNode {name:'Account Number'})
CREATE (crm)-[:CAN_ACCESS {scope:'read_only', auth:'OAuth2_scoped'}]->(email),
       (crm)-[:CAN_ACCESS {scope:'read_only', auth:'OAuth2_scoped'}]->(phone),
       (crm)-[:CAN_ACCESS {scope:'read_only', auth:'OAuth2_scoped'}]->(acct);

MATCH (api:OntologyNode {name:'Account inquiry API'}),
      (bal:OntologyNode {name:'Account balance & transaction history'}),
      (pii:OntologyNode {name:'Customer PII'})
CREATE (api)-[:CAN_ACCESS {scope:'read_only', auth:'OAuth2_scoped'}]->(bal),
       (api)-[:CAN_ACCESS {scope:'read_only', auth:'OAuth2_scoped'}]->(pii);


// ============================================================
//  END OF ONTOLOGY
//  Node count:   54  (10 assets · 8 tools · 12 sec risks · 4 priv risks
//                     · 16 controls · 10 regs/gov · 6 agents)
//  Edge count:   62+ typed relationships
// ============================================================
