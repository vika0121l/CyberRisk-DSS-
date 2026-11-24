"""Зберігання протоколів Cisco Packet Tracer у тій самій SQLite базі."""
import sqlite3
from database import DB_PATH


def connection():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    return con


def initialize_experiments():
    with connection() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            scenario TEXT NOT NULL,
            risk_id INTEGER NOT NULL REFERENCES risks(id),
            measure_id INTEGER NOT NULL REFERENCES security_measures(id),
            topology_file TEXT,
            hypothesis TEXT NOT NULL,
            conclusion TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )''')
        con.execute('''CREATE TABLE IF NOT EXISTS experiment_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
            phase TEXT NOT NULL CHECK(phase IN ('До заходу','Після заходу')),
            source_device TEXT NOT NULL,
            target_device TEXT NOT NULL,
            service TEXT NOT NULL,
            expected TEXT NOT NULL,
            observed TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT ''
        )''')


def risk_options():
    with connection() as con:
        return [dict(r) for r in con.execute('''
            SELECT r.id, a.name AS asset, t.name AS threat, r.risk_score,
                   r.probability, r.impact
            FROM risks r JOIN assets a ON a.id=r.asset_id
            JOIN threats t ON t.id=r.threat_id ORDER BY r.id DESC''')]


def measures_for_risk(risk_id):
    with connection() as con:
        return [dict(r) for r in con.execute('''
            SELECT id, name, implementation_cost, probability_reduction, impact_reduction
            FROM security_measures WHERE risk_id=? ORDER BY id DESC''', (risk_id,))]


def add_experiment(title, scenario, risk_id, measure_id, topology_file, hypothesis, conclusion, tests):
    if not title.strip() or not hypothesis.strip():
        raise ValueError('Заповни назву та гіпотезу.')
    if not tests:
        raise ValueError('Додай хоча б один фактично проведений тест.')
    with connection() as con:
        exists = con.execute('SELECT 1 FROM security_measures WHERE id=? AND risk_id=?',
                             (measure_id, risk_id)).fetchone()
        if not exists:
            raise ValueError('Захід не належить вибраному ризику.')
        cur = con.execute('''INSERT INTO experiments
            (title,scenario,risk_id,measure_id,topology_file,hypothesis,conclusion)
            VALUES (?,?,?,?,?,?,?)''',
            (title.strip(), scenario, risk_id, measure_id, topology_file.strip(),
             hypothesis.strip(), conclusion.strip()))
        exp_id = cur.lastrowid
        for test in tests:
            con.execute('''INSERT INTO experiment_tests
                (experiment_id,phase,source_device,target_device,service,expected,observed,notes)
                VALUES (?,?,?,?,?,?,?,?)''',
                (exp_id, test['phase'], test['source'], test['target'], test['service'],
                 test['expected'], test['observed'], test['notes']))
    return exp_id


def all_experiments():
    with connection() as con:
        return [dict(r) for r in con.execute('''
            SELECT e.*, a.name AS asset, t.name AS threat, m.name AS measure,
                   r.risk_score AS initial_score, r.probability, r.impact,
                   m.probability_reduction, m.impact_reduction, m.implementation_cost
            FROM experiments e JOIN risks r ON r.id=e.risk_id
            JOIN assets a ON a.id=r.asset_id JOIN threats t ON t.id=r.threat_id
            JOIN security_measures m ON m.id=e.measure_id
            ORDER BY e.id DESC''')]


def tests_for_experiment(experiment_id):
    with connection() as con:
        return [dict(r) for r in con.execute('''SELECT phase,source_device,target_device,
            service,expected,observed,notes FROM experiment_tests
            WHERE experiment_id=? ORDER BY id''', (experiment_id,))]


def summary_counts():
    with connection() as con:
        return {name: con.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]
                for name in ('assets','threats','vulnerabilities','risks','security_measures','experiments')}


def report_risks():
    with connection() as con:
        return [dict(r) for r in con.execute('''SELECT r.id, a.name AS asset,
            t.name AS threat, v.name AS vulnerability, r.probability, r.impact,
            r.risk_score, r.assessment_date
            FROM risks r JOIN assets a ON a.id=r.asset_id
            JOIN threats t ON t.id=r.threat_id
            JOIN vulnerabilities v ON v.id=r.vulnerability_id
            ORDER BY r.risk_score DESC, r.id DESC''')]


def report_measures():
    with connection() as con:
        return [dict(r) for r in con.execute('''SELECT m.id, m.risk_id,
            m.name AS measure, m.implementation_cost, m.probability_reduction,
            m.impact_reduction, r.probability, r.impact, r.risk_score
            FROM security_measures m JOIN risks r ON r.id=m.risk_id ORDER BY m.id DESC''')]
