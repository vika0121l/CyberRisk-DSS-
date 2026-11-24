
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "cyberrisk.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                ip_address TEXT,
                network_segment TEXT,
                criticality INTEGER NOT NULL
                    CHECK (criticality BETWEEN 1 AND 5),
                description TEXT
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS threats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(id)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                severity INTEGER NOT NULL
                    CHECK (severity BETWEEN 1 AND 5),
                description TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(id)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS risks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                threat_id INTEGER NOT NULL,
                vulnerability_id INTEGER NOT NULL,
                probability INTEGER NOT NULL
                    CHECK (probability BETWEEN 1 AND 5),
                impact INTEGER NOT NULL
                    CHECK (impact BETWEEN 1 AND 5),
                risk_score INTEGER NOT NULL
                    CHECK (risk_score BETWEEN 1 AND 25),
                assessment_date TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asset_id) REFERENCES assets(id),
                FOREIGN KEY (threat_id) REFERENCES threats(id),
                FOREIGN KEY (vulnerability_id)
                    REFERENCES vulnerabilities(id)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS security_measures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                risk_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                implementation_cost REAL NOT NULL DEFAULT 0
                    CHECK (implementation_cost >= 0),
                probability_reduction INTEGER NOT NULL DEFAULT 0
                    CHECK (probability_reduction BETWEEN 0 AND 4),
                impact_reduction INTEGER NOT NULL DEFAULT 0
                    CHECK (impact_reduction BETWEEN 0 AND 4),
                FOREIGN KEY (risk_id) REFERENCES risks(id)
            )
        """)



        # Безпечне оновлення схеми для автоматизованого оцінювання ризиків.
        # Старі записи зберігаються; для них threat_activity залишається NULL.
        columns = [
            row[1]
            for row in connection.execute("PRAGMA table_info(risks)").fetchall()
        ]
        if "threat_activity" not in columns:
            connection.execute("""
                ALTER TABLE risks
                ADD COLUMN threat_activity INTEGER
                    CHECK (threat_activity IS NULL OR threat_activity BETWEEN 1 AND 5)
            """)

    print("Базу даних успішно ініціалізовано!")


def add_asset(
    name, asset_type, ip_address,
    network_segment, criticality, description
):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO assets (
                name, asset_type, ip_address,
                network_segment, criticality, description
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name, asset_type, ip_address,
                network_segment, criticality, description
            )
        )


def get_assets():
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT id, name, asset_type, ip_address,
                   network_segment, criticality, description
            FROM assets
            ORDER BY id
            """
        )
        return cursor.fetchall()

def update_asset(
    asset_id, name, asset_type, ip_address,
    network_segment, criticality, description
):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE assets
            SET name = ?,
                asset_type = ?,
                ip_address = ?,
                network_segment = ?,
                criticality = ?,
                description = ?
            WHERE id = ?
            """,
            (
                name, asset_type, ip_address,
                network_segment, criticality,
                description, asset_id
            )
        )
        return cursor.rowcount > 0


def delete_asset(asset_id):
    with get_connection() as connection:

        dependencies = connection.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM threats
                 WHERE asset_id = ?) +
                (SELECT COUNT(*) FROM vulnerabilities
                 WHERE asset_id = ?) +
                (SELECT COUNT(*) FROM risks
                 WHERE asset_id = ?)
            """,
            (asset_id, asset_id, asset_id)
        ).fetchone()[0]

        if dependencies > 0:
            raise ValueError(
                "Неможливо видалити актив, оскільки з ним "
                "пов'язані загрози, вразливості або ризики."
            )

        cursor = connection.execute(
            "DELETE FROM assets WHERE id = ?",
            (asset_id,)
        )

        return cursor.rowcount > 0

def asset_ip_exists(ip_address, exclude_id=None):
    if not ip_address:
        return False

    with get_connection() as connection:
        if exclude_id is None:
            cursor = connection.execute(
                """
                SELECT 1 FROM assets
                WHERE ip_address = ?
                LIMIT 1
                """,
                (ip_address,)
            )
        else:
            cursor = connection.execute(
                """
                SELECT 1 FROM assets
                WHERE ip_address = ? AND id != ?
                LIMIT 1
                """,
                (ip_address, exclude_id)
            )

        return cursor.fetchone() is not None

def add_threat(asset_id, name, category, description):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO threats (
                asset_id, name, category, description
            )
            VALUES (?, ?, ?, ?)
            """,
            (asset_id, name, category, description)
        )
        return cursor.lastrowid


def get_threats():
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                threats.id,
                assets.name,
                threats.name,
                threats.category,
                threats.description
            FROM threats
            JOIN assets ON threats.asset_id = assets.id
            ORDER BY threats.id
            """
        )
        return cursor.fetchall()
def add_vulnerability(asset_id, name, severity, description):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO vulnerabilities (
                asset_id, name, severity, description
            )
            VALUES (?, ?, ?, ?)
            """,
            (asset_id, name, severity, description)
        )
        return cursor.lastrowid


def get_vulnerabilities():
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                vulnerabilities.id,
                assets.name,
                vulnerabilities.name,
                vulnerabilities.severity,
                vulnerabilities.description
            FROM vulnerabilities
            JOIN assets
                ON vulnerabilities.asset_id = assets.id
            ORDER BY vulnerabilities.id
            """
        )
        return cursor.fetchall()

def calculate_risk(probability, impact):
    if not 1 <= probability <= 5:
        raise ValueError("Імовірність повинна бути від 1 до 5.")

    if not 1 <= impact <= 5:
        raise ValueError("Наслідки повинні бути від 1 до 5.")

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

    return risk_score, risk_level

def add_risk(
    asset_id,
    threat_id,
    vulnerability_id,
    probability=None,
    impact=None,
    *,
    threat_activity=None
):
    """Зберігає ризик у старому або автоматизованому режимі.

    Автоматизований режим: add_risk(asset_id, threat_id, vulnerability_id,
                                     threat_activity=4)
    Старий режим: add_risk(asset_id, threat_id, vulnerability_id, 4, 5)
    """
    with get_connection() as connection:
        asset = connection.execute(
            "SELECT criticality FROM assets WHERE id = ?", (asset_id,)
        ).fetchone()
        threat = connection.execute(
            "SELECT id FROM threats WHERE id = ? AND asset_id = ?",
            (threat_id, asset_id)
        ).fetchone()
        vulnerability = connection.execute(
            "SELECT severity FROM vulnerabilities WHERE id = ? AND asset_id = ?",
            (vulnerability_id, asset_id)
        ).fetchone()

        if asset is None:
            raise ValueError("Вибраний інформаційний актив не існує.")
        if threat is None:
            raise ValueError("Загроза не належить вибраному активу.")
        if vulnerability is None:
            raise ValueError("Вразливість не належить вибраному активу.")

        if threat_activity is not None:
            if probability is not None or impact is not None:
                raise ValueError(
                    "Для автоматичного розрахунку передавайте лише threat_activity."
                )
            from risk_model import calculate_advanced_risk

            result = calculate_advanced_risk(
                threat_activity=threat_activity,
                vulnerability_severity=int(vulnerability[0]),
                asset_criticality=int(asset[0])
            )
            probability = result["probability"]
            impact = result["impact"]
            risk_score = result["risk_score"]
        else:
            if probability is None or impact is None:
                raise ValueError(
                    "Вкажіть threat_activity для автоматичного розрахунку "
                    "або probability та impact для старого режиму."
                )
            risk_score, _ = calculate_risk(probability, impact)

        cursor = connection.execute(
            """
            INSERT INTO risks (
                asset_id, threat_id, vulnerability_id,
                probability, impact, risk_score, threat_activity
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                asset_id, threat_id, vulnerability_id,
                probability, impact, risk_score, threat_activity
            )
        )
        return cursor.lastrowid


def add_automated_risk(asset_id, threat_id, vulnerability_id, threat_activity):
    """Зручний виклик автоматизованого оцінювання для сторінки Streamlit."""
    return add_risk(
        asset_id, threat_id, vulnerability_id,
        threat_activity=threat_activity
    )


def get_risks():
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                risks.id,
                assets.name,
                threats.name,
                vulnerabilities.name,
                risks.probability,
                risks.impact,
                risks.risk_score,
                risks.assessment_date
            FROM risks
            JOIN assets
                ON risks.asset_id = assets.id
            JOIN threats
                ON risks.threat_id = threats.id
            JOIN vulnerabilities
                ON risks.vulnerability_id = vulnerabilities.id
            ORDER BY risks.id DESC
            """
        )

        return cursor.fetchall()

def add_security_measure(
    risk_id,
    name,
    description,
    implementation_cost,
    probability_reduction,
    impact_reduction
):
    if not name.strip():
        raise ValueError("Вкажіть назву заходу захисту.")

    if implementation_cost < 0:
        raise ValueError("Вартість не може бути від'ємною.")

    if not 0 <= probability_reduction <= 4:
        raise ValueError(
            "Зниження ймовірності має бути від 0 до 4."
        )

    if not 0 <= impact_reduction <= 4:
        raise ValueError(
            "Зниження наслідків має бути від 0 до 4."
        )

    with get_connection() as connection:
        risk = connection.execute(
            "SELECT id FROM risks WHERE id = ?",
            (risk_id,)
        ).fetchone()

        if risk is None:
            raise ValueError("Вибраний ризик не існує.")

        cursor = connection.execute(
            """
            INSERT INTO security_measures (
                risk_id,
                name,
                description,
                implementation_cost,
                probability_reduction,
                impact_reduction
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                risk_id,
                name.strip(),
                description.strip(),
                implementation_cost,
                probability_reduction,
                impact_reduction
            )
        )

        return cursor.lastrowid


def get_security_measures():
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                security_measures.id,
                security_measures.risk_id,
                security_measures.name,
                security_measures.description,
                security_measures.implementation_cost,
                security_measures.probability_reduction,
                security_measures.impact_reduction,
                risks.risk_score
            FROM security_measures
            JOIN risks
                ON security_measures.risk_id = risks.id
            ORDER BY security_measures.id DESC
            """
        )

        return cursor.fetchall()

def calculate_residual_risk(risk_id):
    with get_connection() as connection:
        risk = connection.execute(
            """
            SELECT probability, impact
            FROM risks
            WHERE id = ?
            """,
            (risk_id,)
        ).fetchone()

        if risk is None:
            raise ValueError("Вибраний ризик не існує.")

        probability, impact = risk

        measures = connection.execute(
            """
            SELECT probability_reduction, impact_reduction
            FROM security_measures
            WHERE risk_id = ?
            """,
            (risk_id,)
        ).fetchall()

    total_probability_reduction = sum(
        measure[0] for measure in measures
    )

    total_impact_reduction = sum(
        measure[1] for measure in measures
    )

    residual_probability = max(
        1, probability - total_probability_reduction
    )

    residual_impact = max(
        1, impact - total_impact_reduction
    )

    initial_score, initial_level = calculate_risk(
        probability, impact
    )

    residual_score, residual_level = calculate_risk(
        residual_probability, residual_impact
    )

    return {
        "initial_score": initial_score,
        "initial_level": initial_level,
        "residual_probability": residual_probability,
        "residual_impact": residual_impact,
        "residual_score": residual_score,
        "residual_level": residual_level,
        "reduction_percent": round(
            (initial_score - residual_score) / initial_score * 100,
            2
        )
    }

def calculate_economic_analysis(risk_id):
    result = calculate_residual_risk(risk_id)

    with get_connection() as connection:
        measures = connection.execute(
            """
            SELECT
                name,
                implementation_cost
            FROM security_measures
            WHERE risk_id = ?
            ORDER BY id
            """,
            (risk_id,)
        ).fetchall()

    total_cost = sum(
        measure[1] for measure in measures
    )

    initial_score = result["initial_score"]
    residual_score = result["residual_score"]

    risk_reduction = initial_score - residual_score

    if risk_reduction > 0:
        cost_per_point = total_cost / risk_reduction
    else:
        cost_per_point = None

    return {
        "risk_id": risk_id,
        "initial_score": initial_score,
        "residual_score": residual_score,
        "risk_reduction": risk_reduction,
        "reduction_percent": result["reduction_percent"],
        "total_cost": round(total_cost, 2),
        "cost_per_point": (
            round(cost_per_point, 2)
            if cost_per_point is not None
            else None
        ),
        "measures": measures
    }

if __name__ == "__main__":
    initialize_database()
