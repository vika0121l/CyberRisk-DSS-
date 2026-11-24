
import csv
from pathlib import Path

from risk_model import calculate_advanced_risk


def run_experiments():
    results = []

    for threat in range(1, 6):
        for vulnerability in range(1, 6):
            for criticality in range(1, 6):
                result = calculate_advanced_risk(
                    threat_activity=threat,
                    vulnerability_severity=vulnerability,
                    asset_criticality=criticality
                )

                results.append({
                    "T": threat,
                    "V": vulnerability,
                    "C": criticality,
                    "P": result["probability"],
                    "I": result["impact"],
                    "R": result["risk_score"],
                    "Risk_Level": result["risk_level"]
                })

    return results


if __name__ == "__main__":
    results = run_experiments()

    output_dir = Path("experiment_results")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "risk_model_125_scenarios.csv"

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(results[0].keys())
        )

        writer.writeheader()
        writer.writerows(results)

    print(f"Кількість сценаріїв: {len(results)}")
    print(f"Мінімальна оцінка: {min(r['R'] for r in results)}")
    print(f"Максимальна оцінка: {max(r['R'] for r in results)}")
    print(f"Результати збережено: {output_file}")
