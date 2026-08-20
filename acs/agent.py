"""
SHIELD fall-risk demonstration agent (Phase 3).

A simple branching agent: it only calls send_patient_data and
external_analytics if get_fall_risk succeeded, and only escalates to
send_patient_data if the computed risk score crosses a threshold.

Governance is applied entirely from the outside via control.run_tool() /
control.agent_startup() -- tools.py has no awareness of ACS at all, per
Stage 6. Every denial's citation is looked up from the reviewed SHIELD
Policy Record at run time via citations.py, per Stage 7.
"""

import asyncio
from agent_control_specification import AgentControl, AgentControlBlocked

import tools
from citations import load_citation_index, format_citation

RISK_ESCALATION_THRESHOLD = 0.5


async def run_agent(scenario_name: str, governance_flags: dict) -> None:
    print(f"\n{'=' * 70}\nSCENARIO: {scenario_name}\n{'=' * 70}")

    control = AgentControl.from_path("manifest.yaml")
    citation_index = load_citation_index()

    def report_block(e: AgentControlBlocked) -> None:
        reason = e.result.verdict.reason
        record = citation_index.get(reason)
        if record:
            print(f"  -> DENIED. {format_citation(record)}")
            print(f"     \"{record['obligation']['citation_text'].strip()}\"")
        else:
            print(f"  -> DENIED. (no matching record for reason: {reason})")

    # --- agent_startup: foundational MDR classification, informational ---
    startup_result = await control.agent_startup({"agent_id": "fall-risk-demo-agent"})
    if startup_result.verdict.reason:
        record = citation_index.get(startup_result.verdict.reason)
        print(f"[startup:{startup_result.verdict.decision}] {format_citation(record)}")

    # --- Step 1: get_patient_record ---
    print("\nStep 1: get_patient_record")
    try:
        patient_record = await control.run_tool(
            "get_patient_record",
            {"patient_id": "P123", "lawful_basis_present": governance_flags["lawful_basis_present"]},
            lambda args: tools.get_patient_record(args["patient_id"]),
        )
        print(f"  -> ALLOWED. {patient_record.value}")
    except AgentControlBlocked as e:
        report_block(e)
        print("Agent halts: cannot proceed without a patient record.")
        return

    # --- Step 2: get_fall_risk ---
    print("\nStep 2: get_fall_risk")
    try:
        fall_risk = await control.run_tool(
            "get_fall_risk",
            {"patient_id": "P123", "human_reviewed": governance_flags["human_reviewed"]},
            lambda args: tools.get_fall_risk(args["patient_id"], patient_record.value),
        )
        print(f"  -> ALLOWED. {fall_risk.value}")
    except AgentControlBlocked as e:
        report_block(e)
        print("Agent halts: fall-risk score cannot be computed or used downstream.")
        return

    score = fall_risk.value["fall_risk_score"]

    # --- Branch: only escalate to send_patient_data if risk is high ---
    if score < RISK_ESCALATION_THRESHOLD:
        print(f"\nRisk score {score} below threshold ({RISK_ESCALATION_THRESHOLD}); "
              f"agent takes no further action.")
        return

    print(f"\nRisk score {score} at/above threshold; escalating.")

    # --- Step 3: send_patient_data ---
    print("\nStep 3: send_patient_data")
    try:
        send_result = await control.run_tool(
            "send_patient_data",
            {
                "patient_id": "P123",
                "payload": fall_risk.value,
                "destination": "care-team-dashboard",
                "external_destination": True,
                "purpose_authorised": governance_flags["purpose_authorised"],
            },
            lambda args: tools.send_patient_data(args["patient_id"], args["payload"], args["destination"]),
        )
        print(f"  -> ALLOWED. {send_result.value}")
    except AgentControlBlocked as e:
        report_block(e)
        print("Agent skips downstream analytics: sending patient data was denied.")
        return

    # --- Step 4: external_analytics ---
    print("\nStep 4: external_analytics")
    try:
        analytics_result = await control.run_tool(
            "external_analytics",
            {
                "patient_id": "P123",
                "payload": fall_risk.value,
                "human_oversight_assigned": governance_flags["human_oversight_assigned"],
            },
            lambda args: tools.external_analytics(args["patient_id"], args["payload"]),
        )
        print(f"  -> ALLOWED. {analytics_result.value}")
    except AgentControlBlocked as e:
        report_block(e)


async def main():
    # Scenario A: fully compliant -- every governance flag satisfied,
    # everything allowed end to end.
    await run_agent(
        "A -- fully compliant run (ALLOW case)",
        {
            "lawful_basis_present": True,
            "human_reviewed": True,
            "purpose_authorised": True,
            "human_oversight_assigned": True,
        },
    )

    # Scenario B: no human review of the fall-risk score -- denied at
    # Step 2, agent halts, never reaches send_patient_data or
    # external_analytics (DENY case, with real branching).
    await run_agent(
        "B -- no human review of fall-risk score (DENY case)",
        {
            "lawful_basis_present": True,
            "human_reviewed": False,
            "purpose_authorised": True,
            "human_oversight_assigned": True,
        },
    )


asyncio.run(main())
