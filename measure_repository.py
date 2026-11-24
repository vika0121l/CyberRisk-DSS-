"""CRUD для заходів захисту. Використовує наявну SQLite CyberRisk DSS."""
from database import get_connection, add_security_measure


def list_measures():
    with get_connection() as conn:
        return conn.execute('''
            SELECT m.id,m.risk_id,m.name,m.description,m.implementation_cost,
                   m.probability_reduction,m.impact_reduction,
                   r.probability,r.impact,r.risk_score,a.name,t.name,v.name
            FROM security_measures m
            JOIN risks r ON r.id=m.risk_id
            JOIN assets a ON a.id=r.asset_id
            JOIN threats t ON t.id=r.threat_id
            JOIN vulnerabilities v ON v.id=r.vulnerability_id
            ORDER BY m.id DESC
        ''').fetchall()


def list_risks():
    with get_connection() as conn:
        return conn.execute('''
            SELECT r.id,a.name,t.name,v.name,r.probability,r.impact,r.risk_score
            FROM risks r JOIN assets a ON a.id=r.asset_id
            JOIN threats t ON t.id=r.threat_id
            JOIN vulnerabilities v ON v.id=r.vulnerability_id
            ORDER BY r.id DESC
        ''').fetchall()


def validate_measure(risk_id,name,description,cost,p_reduction,i_reduction):
    if not isinstance(name,str) or not name.strip():
        raise ValueError('Вкажіть назву заходу захисту.')
    if len(name.strip()) > 180:
        raise ValueError('Назва має містити не більше 180 символів.')
    if not isinstance(description,str):
        raise ValueError('Некоректний опис заходу.')
    if not (0 <= float(cost) < float('inf')):
        raise ValueError('Вартість має бути скінченним невід’ємним числом.')
    if not (isinstance(p_reduction,int) and 0 <= p_reduction <= 4):
        raise ValueError('Зниження ймовірності має бути від 0 до 4.')
    if not (isinstance(i_reduction,int) and 0 <= i_reduction <= 4):
        raise ValueError('Зниження впливу має бути від 0 до 4.')
    with get_connection() as conn:
        row=conn.execute('SELECT id FROM risks WHERE id=?',(risk_id,)).fetchone()
    if row is None:
        raise ValueError('Обраний ризик не існує.')


def create_measure(risk_id,name,description,cost,p_reduction,i_reduction):
    validate_measure(risk_id,name,description,cost,p_reduction,i_reduction)
    return add_security_measure(risk_id,name.strip(),description.strip(),float(cost),p_reduction,i_reduction)


def update_measure(measure_id,risk_id,name,description,cost,p_reduction,i_reduction):
    validate_measure(risk_id,name,description,cost,p_reduction,i_reduction)
    with get_connection() as conn:
        cursor=conn.execute('''UPDATE security_measures
            SET risk_id=?,name=?,description=?,implementation_cost=?,
                probability_reduction=?,impact_reduction=? WHERE id=?''',
            (risk_id,name.strip(),description.strip(),float(cost),p_reduction,i_reduction,measure_id))
        return cursor.rowcount > 0


def delete_measure(measure_id):
    with get_connection() as conn:
        cursor=conn.execute('DELETE FROM security_measures WHERE id=?',(measure_id,))
        return cursor.rowcount > 0
