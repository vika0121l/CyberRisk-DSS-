from pathlib import Path
from html import escape
import streamlit as st
from database import initialize_database, get_connection
from components import render_footer

initialize_database()
css_path = Path(__file__).resolve().parents[1] / 'styles' / 'matrix.css'
if css_path.exists():
    st.markdown(f'<style>{css_path.read_text(encoding="utf-8")}</style>', unsafe_allow_html=True)

LEVELS = [(4, 'Дуже низький', 'very-low'), (9, 'Низький', 'low'),
          (14, 'Середній', 'medium'), (19, 'Високий', 'high'),
          (25, 'Критичний', 'critical')]

def risk_level(score):
    return next((name, css) for maximum, name, css in LEVELS if score <= maximum)

with get_connection() as conn:
    risks = conn.execute('''
        SELECT r.id, a.name, t.name, v.name, r.probability,
               r.impact, r.risk_score, r.assessment_date
        FROM risks r
        JOIN assets a ON a.id = r.asset_id
        JOIN threats t ON t.id = r.threat_id
        JOIN vulnerabilities v ON v.id = r.vulnerability_id
        ORDER BY r.id DESC
    ''').fetchall()

valid = [r for r in risks if r[4] is not None and r[5] is not None
         and 1 <= r[4] <= 5 and 1 <= r[5] <= 5]
counts = {(p, i): sum(r[4] == p and r[5] == i for r in valid)
          for p in range(1, 6) for i in range(1, 6)}
high_count = sum(15 <= r[6] <= 19 for r in valid)
critical_count = sum(r[6] >= 20 for r in valid)
max_score = max((r[6] for r in valid), default=0)
max_level_css = risk_level(max_score)[1] if max_score else 'none'
high_class = 'mx-stat-high' if high_count else 'mx-stat-neutral'
critical_class = 'mx-stat-critical' if critical_count else 'mx-stat-neutral'
max_class = 'mx-stat-max'
max_label = escape(risk_level(max_score)[0]) if max_score else 'Немає оцінок'
max_badge = f'<span class="mx-max-status {max_level_css}">{max_label}</span>' if max_score else '<span class="mx-max-status none">Немає оцінок</span>'
# Маркери збережених оцінок: крапка для однієї, числовий бейдж для кількох.
# Позначення не змінює бал P × I усередині клітинки.
def matrix_marker_rule(p_value, i_value, count):
    cell = f'.st-key-mx_matrix_grid .st-key-mx_cell_{p_value}_{i_value} button::after'
    if count == 1:
        return (f'{cell} {{content:"";position:absolute;top:4px;right:5px;'
                'width:8px;height:8px;border-radius:50%;background:#153b78;'
                'box-shadow:0 0 0 2px rgba(255,255,255,.85);'
                'z-index:2;pointer-events:none;}')
    return (f'{cell} {{content:"{count}";position:absolute;top:2px;right:3px;'
            'height:18px;min-width:18px;box-sizing:border-box;padding:0 4px;'
            'display:flex;align-items:center;justify-content:center;'
            'border-radius:10px;background:#153b78;color:#fff;'
            'font-size:10px;font-weight:800;line-height:1;'
            'box-shadow:0 0 0 2px rgba(255,255,255,.9);'
            'z-index:2;pointer-events:none;}')

occupied_css = '\n'.join(
    matrix_marker_rule(pp, ii, n)
    for (pp, ii), n in counts.items() if n > 0
)
st.markdown(f'<style>{occupied_css}</style>', unsafe_allow_html=True)

st.html('''<div class="mx-hero"><div><div class="mx-eyebrow">CYBERRISK DSS / АНАЛІЗ КІБЕРРИЗИКІВ</div><h1>Матриця ризиків</h1><p>Наочне відображення рівня кіберризиків за ймовірністю (P) та впливом (I)</p></div><div class="mx-hero-icon" aria-hidden="true"></div></div>''')
st.html(f'''<div class="mx-stats">
<div class="mx-stat"><div class="mx-stat-icon">▤</div><div><span>Усього оцінок</span><strong>{len(valid)}</strong><small>Зареєстровані ризики</small></div></div>
<div class="mx-stat {high_class}"><div class="mx-stat-icon">⚠</div><div><span>Високі ризики</span><strong>{high_count}</strong><small>15 ≤ R ≤ 19</small></div></div>
<div class="mx-stat {critical_class}"><div class="mx-stat-icon">◇</div><div><span>Критичні ризики</span><strong>{critical_count}</strong><small>20 ≤ R ≤ 25</small></div></div>
<div class="mx-stat {max_class}"><div class="mx-stat-icon">▥</div><div class="mx-max-content"><span>Найвищий бал ризику</span><div class="mx-max-value"><strong>{f"{max_score} / 25" if max_score else "—"}</strong>{max_badge}</div><small>Максимальна збережена оцінка</small></div></div></div>''')

if 'matrix_selected' not in st.session_state or not isinstance(st.session_state.matrix_selected, (tuple, list)) or len(st.session_state.matrix_selected) != 2:
    st.session_state.matrix_selected = (valid[0][4], valid[0][5]) if valid else (3, 5)

left, right = st.columns([1.18, 1], gap='medium')
with left:
    st.html('<div class="mx-panel-title"><span></span><h2>Матриця ризиків 5 × 5</h2></div>')
    st.html('<div class="mx-matrix-hint"><span class="mx-hint-icon">ⓘ</span><span>Оберіть клітинку для перегляду оцінок. Синя крапка — одна оцінка, число на маркері — кількість оцінок.</span></div>')
    with st.container(key='mx_matrix_grid'):
        headers = st.columns(6, gap='small')
        headers[0].html('<div class="mx-axis mx-corner">I / P</div>')
        for p_value in range(1, 6):
            headers[p_value].html(f'<div class="mx-axis">{p_value}</div>')
        for i_value in range(5, 0, -1):
            columns = st.columns(6, gap='small')
            columns[0].html(f'<div class="mx-axis mx-y">{i_value}</div>')
            for p_value in range(1, 6):
                score = p_value * i_value
                count = counts[(p_value, i_value)]
                selected = tuple(st.session_state.matrix_selected) == (p_value, i_value)
                with columns[p_value]:
                    if st.button(str(score), key=f'mx_cell_{p_value}_{i_value}',
                                 use_container_width=True,
                                 type='primary' if selected else 'secondary',
                                 help=f'P={p_value}; I={i_value}; R={score}; кількість оцінок: {count}'):
                        st.session_state.matrix_selected = (p_value, i_value)
                        st.rerun()
    st.html('<div class="mx-axis-caption">P — ймовірність → &nbsp; · &nbsp; I — вплив (вертикальна вісь)</div>')

with right:
    p, i = st.session_state.matrix_selected
    score = p * i
    level_name, level_css = risk_level(score)
    matching = [r for r in valid if r[4] == p and r[5] == i]
    st.html('<div class="mx-detail-heading"><span>◎</span><h2>Ризик у вибраній клітинці</h2></div>')

    st.html(f'''<div class="mx-result {level_css}"><div class="mx-result-numbers"><span>P = {p}</span><span>I = {i}</span><span>R = {score}</span></div><div class="mx-result-status"><span class="mx-result-label">Рівень ризику:</span><strong>{escape(level_name)}</strong></div></div>''')
    st.html(f'<div class="mx-count">Збережених оцінок у вибраній клітинці: <strong>{len(matching)}</strong></div>')
    if matching:
        if len(matching) > 1:
            # Усі записи з вибраної клітинки доступні окремо, новіші — першими.
            matching = sorted(matching, key=lambda r: r[0], reverse=True)
            options = {
                r[0]: f'№{r[0]} — {r[1]} | {r[2]} | {r[3]}'
                for r in matching
            }
            widget_key = f'mx_risk_select_{p}_{i}'
            # Видалена з бази оцінка не повинна залишатися вибраною у віджеті.
            if widget_key in st.session_state and st.session_state[widget_key] not in options:
                del st.session_state[widget_key]
            chosen_id = st.selectbox(
                f'Оберіть оцінку ({len(matching)} у клітинці)',
                list(options),
                format_func=lambda risk_id: options[risk_id],
                key=widget_key,
            )
            chosen = next(r for r in matching if r[0] == chosen_id)
            selected_number = next(
                idx for idx, r in enumerate(matching, 1) if r[0] == chosen_id
            )
            st.html(
                f'<div class="mx-selection-meta">Переглядається оцінка '
                f'<b>{selected_number} із {len(matching)}</b>'
                f'<span>· ID {chosen_id}</span></div>'
            )
        else:
            chosen = matching[0]
        details = [('▤', 'Інформаційний актив', chosen[1]), ('⚠', 'Загроза', chosen[2]),
                   ('◇', 'Вразливість', chosen[3]), ('▣', 'Дата оцінювання', chosen[7]),
                   ('▥', 'Результат', f'{chosen[6]} / 25 — {risk_level(chosen[6])[0]}')]
        details_html = ''.join(f'<div class="mx-detail-row"><span><i class="mx-row-icon">{icon}</i>{escape(str(k))}</span><strong>{escape(str(v))}</strong></div>' for icon, k, v in details)
        st.html(f'<div class="mx-detail-list">{details_html}</div>')
    else:
        st.info('Для цієї комбінації P та I збережених оцінок немає. Оберіть клітинку із синьою крапкою.')

# Компактна легенда пояснює кольори матриці, не дублюючи KPI.
# Діапазони відповідають LEVELS та використовуються для кольорів клітинок.
st.html('''<section class="mx-scale" aria-label="Шкала рівнів кіберризику">
  <div class="mx-scale-title"><span class="mx-scale-icon" aria-hidden="true">▧</span><h3>Шкала рівнів кіберризику</h3></div>
  <div class="mx-scale-level"><i class="mx-scale-swatch very-low"></i><div><strong>Дуже низький</strong><span>1 ≤ R ≤ 4</span></div></div>
  <div class="mx-scale-level"><i class="mx-scale-swatch low"></i><div><strong>Низький</strong><span>5 ≤ R ≤ 9</span></div></div>
  <div class="mx-scale-level"><i class="mx-scale-swatch medium"></i><div><strong>Середній</strong><span>10 ≤ R ≤ 14</span></div></div>
  <div class="mx-scale-level"><i class="mx-scale-swatch high"></i><div><strong>Високий</strong><span>15 ≤ R ≤ 19</span></div></div>
  <div class="mx-scale-level"><i class="mx-scale-swatch critical"></i><div><strong>Критичний</strong><span>20 ≤ R ≤ 25</span></div></div>
  <div class="mx-scale-formula">R = P × I</div>
</section>''')
st.html('''<section class="mx-guide" aria-label="Інструкція з використання матриці ризиків">
  <div class="mx-guide-title">
    <span class="mx-guide-title-icon" aria-hidden="true">☷</span>
    <h3>Інструкція з використання<br>матриці ризиків</h3>
  </div>
  <div class="mx-guide-step">
    <span class="mx-guide-number">1</span>
    <div class="mx-guide-copy"><h4>Оберіть клітинку</h4>
      <p>Крапка означає одну збережену оцінку, число — кілька оцінок.</p></div>
  </div>
  <div class="mx-guide-step">
    <span class="mx-guide-number">2</span>
    <div class="mx-guide-copy"><h4>Перегляньте оцінки</h4>
      <p>Проаналізуйте актив, загрозу та вразливість у вибраній клітинці.</p></div>
  </div>
  <div class="mx-guide-step">
    <span class="mx-guide-number">3</span>
    <div class="mx-guide-copy"><h4>Оцініть ризик</h4>
      <p>Бал R = P × I визначає підсумковий рівень ризику.</p></div>
  </div>
  <div class="mx-guide-step">
    <span class="mx-guide-number">4</span>
    <div class="mx-guide-copy"><h4>Визначте заходи реагування</h4>
      <p>На основі результатів оберіть пріоритетні заходи захисту.</p></div>
  </div>
</section>''')
render_footer()
