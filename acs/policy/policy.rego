# Combined Rego bundle for the SHIELD demo scenario.
# Each rule below corresponds to one reviewed SHIELD Policy Record in
# records/. Comments cite the record_id and source article for traceability.

package shield_demo

# --- tool_verdict: dispatches pre_tool_call / post_tool_call by tool name ---

default tool_verdict := {"decision": "allow"}

# SHIELD-GDPR-022 -- GDPR Art.22(1) -- get_fall_risk
tool_verdict := {
    "decision": "deny",
    "reason": "gdpr_art22_solely_automated_decision",
    "message": "SHIELD-GDPR-022: get_fall_risk output would drive a significant decision via solely automated processing, with no human review step present. Denied under GDPR Article 22(1)."
} if {
    input.snapshot.tool_call.name == "get_fall_risk"
    not input.snapshot.tool_call.args.human_reviewed
}

# SHIELD-GDPR-009 -- GDPR Art.9(1) -- get_patient_record
tool_verdict := {
    "decision": "deny",
    "reason": "gdpr_art9_no_lawful_basis",
    "message": "SHIELD-GDPR-009: get_patient_record touches special category health data with no lawful basis flag present. Denied under GDPR Article 9(1)."
} if {
    input.snapshot.tool_call.name == "get_patient_record"
    not input.snapshot.tool_call.args.lawful_basis_present
}

# SHIELD-GDPR-005 -- GDPR Art.5(1)(b) -- send_patient_data
tool_verdict := {
    "decision": "deny",
    "reason": "gdpr_art5_purpose_not_authorised",
    "message": "SHIELD-GDPR-005: send_patient_data targets an external destination with no authorised-purpose flag present. Denied under GDPR Article 5(1)(b)."
} if {
    input.snapshot.tool_call.name == "send_patient_data"
    input.snapshot.tool_call.args.external_destination == true
    not input.snapshot.tool_call.args.purpose_authorised
}

# SHIELD-AIACT-ANNEXIII -- EU AI Act Annex III point 5(d) -- external_analytics
# Informational classification flag, non-blocking.
tool_verdict := {
    "decision": "warn",
    "reason": "aiact_annexiii_high_risk_classification",
    "message": "SHIELD-AIACT-ANNEXIII: external_analytics output is used for emergency healthcare triage, classified high-risk under EU AI Act Annex III point 5(d)."
} if {
    input.snapshot.tool_call.name == "external_analytics"
    input.snapshot.tool_call.args.human_oversight_assigned
}

# SHIELD-AIACT-026 -- EU AI Act Art.26(2) -- external_analytics
# Deny takes precedence over the warn case above when oversight is missing.
tool_verdict := {
    "decision": "deny",
    "reason": "aiact_art26_no_human_oversight",
    "message": "SHIELD-AIACT-026: external_analytics call on a high-risk-classified output has no human oversight assigned. Denied under EU AI Act Article 26(2)."
} if {
    input.snapshot.tool_call.name == "external_analytics"
    not input.snapshot.tool_call.args.human_oversight_assigned
}

# --- startup_verdict: agent_startup, always fires once per agent session ---

# SHIELD-MDR-002 -- EU MDR Art.2(1) -- foundational classification, informational
startup_verdict := {
    "decision": "warn",
    "reason": "mdr_art2_medical_device_classification",
    "message": "SHIELD-MDR-002: this agent's fall-risk prediction software has an intended medical purpose and qualifies as a medical device under EU MDR Article 2(1)."
}