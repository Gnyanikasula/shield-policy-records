"""
Plain Python tool functions for the SHIELD fall-risk demonstration agent.

Per the spec (Stage 6): these expose no governance logic of their own.
All interception, allow/deny decisions, and citation evidence come from
ACS wrapping these calls in agent.py -- never from code inside this file.
These are deliberately simple stubs, not real ML or real network calls.
"""


def get_patient_record(patient_id: str) -> dict:
    return {
        "patient_id": patient_id,
        "name": "Demo Patient",
        "age": 78,
        "mobility_score": 3,
    }


def get_fall_risk(patient_id: str, patient_record: dict) -> dict:
    mobility_score = patient_record.get("mobility_score", 5)
    score = 0.78 if mobility_score < 4 else 0.20
    return {"patient_id": patient_id, "fall_risk_score": score}


def send_patient_data(patient_id: str, payload: dict, destination: str) -> dict:
    return {"sent": True, "destination": destination, "patient_id": patient_id}


def external_analytics(patient_id: str, payload: dict) -> dict:
    return {
        "analysed": True,
        "patient_id": patient_id,
        "insight": "elevated_risk_trend",
    }