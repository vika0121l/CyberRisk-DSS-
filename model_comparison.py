
from risk_model import calculate_advanced_risk


def compare_risk_models(
    base_probability,
    base_impact,
    threat_activity,
    vulnerability_severity,
    asset_criticality
):
    # Перевірка значень базової моделі
    for name, value in [
        ("Базова ймовірність", base_probability),
        ("Базовий вплив", base_impact)
    ]:
        if type(value) is not int or not 1 <= value <= 5:
            raise ValueError(
                f"{name} має бути цілим числом від 1 до 5."
            )

    # Базова модель
    base_score = base_probability * base_impact

    # Вдосконалена модель
    advanced = calculate_advanced_risk(
        threat_activity=threat_activity,
        vulnerability_severity=vulnerability_severity,
        asset_criticality=asset_criticality
    )

    advanced_score = advanced["risk_score"]

    # Різниця між результатами
    difference = advanced_score - base_score

    # Відносна різниця щодо базової оцінки
    difference_percent = round(
        difference / base_score * 100,
        2
    )

    return {
        "base_probability": base_probability,
        "base_impact": base_impact,
        "base_score": base_score,
        "advanced_probability": advanced["probability"],
        "advanced_impact": advanced["impact"],
        "advanced_score": advanced_score,
        "advanced_level": advanced["risk_level"],
        "difference": difference,
        "difference_percent": difference_percent
    }


if __name__ == "__main__":
    result = compare_risk_models(
        base_probability=4,
        base_impact=5,
        threat_activity=3,
        vulnerability_severity=4,
        asset_criticality=5
    )

    for key, value in result.items():
        print(f"{key}: {value}")
