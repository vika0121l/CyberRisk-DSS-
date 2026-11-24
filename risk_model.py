
import math


def validate_score(value, name):
    if type(value) is not int or not 1 <= value <= 5:
        raise ValueError(
            f"{name} має бути цілим числом від 1 до 5."
        )


def calculate_advanced_risk(
    threat_activity,
    vulnerability_severity,
    asset_criticality
):
    validate_score(threat_activity, "Активність загрози")
    validate_score(vulnerability_severity, "Серйозність вразливості")
    validate_score(asset_criticality, "Критичність активу")

    probability_raw = (
        0.5 * threat_activity
        + 0.5 * vulnerability_severity
    )

    # Округлення до найближчого цілого,
    # при значенні x.5 — у більший бік.
    probability = math.floor(probability_raw + 0.5)

    impact = asset_criticality
    risk_score = probability * impact

    if risk_score <= 4:
        risk_level = "Дуже низький"
    elif risk_score <= 9:
        risk_level = "Низький"
    elif risk_score <= 14:
        risk_level = "Середній"
    elif risk_score <= 19:
        risk_level = "Високий"
    else:
        risk_level = "Критичний"

    return {
        "threat_activity": threat_activity,
        "vulnerability_severity": vulnerability_severity,
        "asset_criticality": asset_criticality,
        "probability": probability,
        "impact": impact,
        "risk_score": risk_score,
        "risk_level": risk_level
    }


if __name__ == "__main__":
    result = calculate_advanced_risk(
        threat_activity=4,
        vulnerability_severity=5,
        asset_criticality=5
    )

    for key, value in result.items():
        print(f"{key}: {value}")
