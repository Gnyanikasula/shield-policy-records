# Rego translation of SHIELD-GDPR-022
# Source record: records/SHIELD-GDPR-022.yaml
# Citation: GDPR Article 22(1) (GDPR_Art22_Para1, gold standard ANN_011)
#
# Models the narrow case only: a decision based solely on automated
# processing, with no human review flag present, is denied at pre_tool_call.
# See the record's scope_note for what is deliberately NOT modeled here.

package shield_gdpr_022

default verdict := {"decision": "allow"}

verdict := {
    "decision": "deny",
    "reason": "gdpr_art22_solely_automated_decision",
    "message": "SHIELD-GDPR-022: get_fall_risk output would drive a significant decision via solely automated processing, with no human review step present. Denied under GDPR Article 22(1)."
} if {
    input.snapshot.tool_call.name == "get_fall_risk"
    not input.snapshot.tool_call.args.human_reviewed
}