"""Збережені обмеження ризику й спільні правила прогнозу та вибору заходу."""

from decimal import Decimal

from database import get_connection


# Це контекст навігації, а не ключ віджета, тому він живе між сторінками.
LAST_COMPARED_RISK_KEY = "dss_last_compared_risk_id"


def initialize_risk_constraints():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS risk_treatment_constraints (
                risk_id INTEGER PRIMARY KEY REFERENCES risks(id) ON DELETE CASCADE,
                budget_amount TEXT,
                residual_threshold INTEGER CHECK (residual_threshold BETWEEN 1 AND 25)
            )
        """)


def load_risk_constraints(risk_id):
    with get_connection() as connection:
        row = connection.execute(
            """SELECT budget_amount, residual_threshold
               FROM risk_treatment_constraints WHERE risk_id = ?""",
            (int(risk_id),),
        ).fetchone()
    if row is None:
        return None, None
    return (None if row[0] is None else Decimal(row[0])), row[1]


def save_risk_constraints(risk_id, budget, threshold):
    if budget is not None:
        budget = Decimal(str(budget))
        if not budget.is_finite() or budget < 0:
            raise ValueError("Бюджет має бути невід’ємною сумою.")
    if threshold is not None and (int(threshold) != threshold or not 1 <= int(threshold) <= 25):
        raise ValueError("Поріг залишкового ризику має бути цілим числом від 1 до 25.")

    with get_connection() as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        if budget is None and threshold is None:
            connection.execute("DELETE FROM risk_treatment_constraints WHERE risk_id = ?", (int(risk_id),))
        else:
            connection.execute(
                """INSERT INTO risk_treatment_constraints (risk_id, budget_amount, residual_threshold)
                   VALUES (?, ?, ?)
                   ON CONFLICT(risk_id) DO UPDATE SET
                       budget_amount = excluded.budget_amount,
                       residual_threshold = excluded.residual_threshold""",
                (int(risk_id), None if budget is None else format(budget, "f"),
                 None if threshold is None else int(threshold)),
            )


def score_of(measure):
    p = max(1, int(measure[7]) - max(0, int(measure[5])))
    i = max(1, int(measure[8]) - max(0, int(measure[6])))
    r = p * i
    initial = int(measure[9])
    reduction = max(0, initial - r)
    percent = reduction / initial * 100 if initial else 0
    return {"row": measure, "p": p, "i": i, "r": r,
            "delta": reduction, "percent": percent, "cost": Decimal(str(measure[4]))}


def decision_key(item):
    return item["r"], item["cost"], item["row"][0]


def compare_options(items, initial, budget, threshold):
    """Ранжує без обмежень і окремо відбирає варіанти, які виконують умови."""
    ranked = sorted(items, key=decision_key)
    improving = [item for item in ranked if item["r"] < initial]
    affordable = [item for item in improving if budget is None or item["cost"] <= budget]
    eligible = [item for item in affordable if threshold is None or item["r"] <= threshold]
    return (
        improving[0] if improving else None,
        affordable[0] if affordable else None,
        eligible[0] if eligible else None,
    )


def amount(value):
    return f"{value:,.2f}".replace(",", " ").replace(".", ",").removesuffix(",00")
