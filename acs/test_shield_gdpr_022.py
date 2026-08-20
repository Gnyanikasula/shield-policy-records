import asyncio
from agent_control_specification import AgentControl, AgentControlBlocked

async def main():
    control = AgentControl.from_path("manifest.yaml")

    async def compute_fall_risk(args):
        return {"patient_id": args.get("patient_id"), "fall_risk_score": 0.78}

    print("--- Case 1: get_fall_risk with no human_reviewed flag ---")
    try:
        result = await control.run_tool(
            "get_fall_risk",
            {"patient_id": "P123"},
            compute_fall_risk,
        )
        print("UNEXPECTED: was not blocked:", result.value)
    except AgentControlBlocked as e:
        print("BLOCKED as expected:", e)

    print()
    print("--- Case 2: get_fall_risk with human_reviewed=True ---")
    result2 = await control.run_tool(
        "get_fall_risk",
        {"patient_id": "P123", "human_reviewed": True},
        compute_fall_risk,
    )
    print(
        "ALLOWED as expected -> pre:", result2.pre_tool_call_result.verdict.decision,
        "| post:", result2.post_tool_call_result.verdict.decision,
        "| value:", result2.value,
    )

asyncio.run(main())