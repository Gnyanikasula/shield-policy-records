import asyncio
from agent_control_specification import AgentControl, AgentControlBlocked

async def main():
    control = AgentControl.from_path("manifest.yaml")

    # --- agent_startup: SHIELD-MDR-002 (warn, non-blocking) ---
    print("=== agent_startup: SHIELD-MDR-002 ===")
    startup_result = await control.agent_startup({"agent_id": "fall-risk-demo-agent"})
    print("decision:", startup_result.verdict.decision, "| reason:", startup_result.verdict.reason)
    print()

    async def echo(args):
        return {"ok": True, "args": args}

    async def fall_risk_exec(args):
        return {"patient_id": args.get("patient_id"), "fall_risk_score": 0.78}

    cases = [
        # (label, tool_name, args, expect_blocked)
        ("SHIELD-GDPR-022 deny", "get_fall_risk", {"patient_id": "P1"}, True),
        ("SHIELD-GDPR-022 allow", "get_fall_risk", {"patient_id": "P1", "human_reviewed": True}, False),

        ("SHIELD-GDPR-009 deny", "get_patient_record", {"patient_id": "P1"}, True),
        ("SHIELD-GDPR-009 allow", "get_patient_record", {"patient_id": "P1", "lawful_basis_present": True}, False),

        ("SHIELD-GDPR-005 deny", "send_patient_data", {"patient_id": "P1", "external_destination": True}, True),
        ("SHIELD-GDPR-005 allow", "send_patient_data", {"patient_id": "P1", "external_destination": True, "purpose_authorised": True}, False),

        ("SHIELD-AIACT-026 deny", "external_analytics", {"patient_id": "P1"}, True),
        ("SHIELD-AIACT-026/ANNEXIII allow+warn", "external_analytics", {"patient_id": "P1", "human_oversight_assigned": True}, False),
    ]

    for label, tool_name, args, expect_blocked in cases:
        print(f"=== {label} ===")
        exec_fn = fall_risk_exec if tool_name == "get_fall_risk" else echo
        try:
            result = await control.run_tool(tool_name, args, exec_fn)
            status = "ALLOWED"
            pre = result.pre_tool_call_result.verdict
            post = result.post_tool_call_result.verdict
            print(f"{status} | pre: {pre.decision} ({pre.reason}) | post: {post.decision} ({post.reason})")
            if expect_blocked:
                print("!! EXPECTED BLOCK, GOT ALLOW !!")
        except AgentControlBlocked as e:
            print("BLOCKED |", e)
            if not expect_blocked:
                print("!! EXPECTED ALLOW, GOT BLOCK !!")
        print()

asyncio.run(main())