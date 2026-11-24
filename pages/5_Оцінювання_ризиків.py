from pathlib import Path
from html import escape
from urllib.parse import quote
import sqlite3
import streamlit as st
from database import initialize_database, get_assets, get_connection, add_automated_risk
from risk_model import calculate_advanced_risk
from components import render_footer

initialize_database()
css_path = Path(__file__).resolve().parents[1] / 'styles' / 'risks.css'
if css_path.exists():
    st.markdown(f'<style>{css_path.read_text(encoding="utf-8")}</style>', unsafe_allow_html=True)

# Локальні стилі сторінки. Панелі залишаються реактивними, як звичайні віджети.
st.html("""
<style>
.ri-stats .ri-stat-icon.ri-stat-icon-svg {
    display: grid;
    place-items: center;
    color: #2468CD;
}
.ri-stats .ri-stat-icon.ri-stat-icon-svg::before {
    content: "";
    display: block;
    width: 25px;
    height: 25px;
    background: currentColor;
    -webkit-mask: var(--ri-stat-mask) center / contain no-repeat;
    mask: var(--ri-stat-mask) center / contain no-repeat;
}
.ri-stats .ri-stat.ri-stat-critical {
    background: linear-gradient(120deg, #FFF9F9 0%, #FFF0F1 100%) !important;
    border-color: #F4B4BF !important;
}
.ri-stats .ri-stat.ri-stat-critical .ri-stat-icon-svg {
    background: #FDE4E8 !important;
    color: #C02F43;
}
.ri-stats .ri-stat.ri-stat-critical span,
.ri-stats .ri-stat.ri-stat-critical strong { color: #AA2639; }
.ri-stats .ri-stat.ri-stat-critical small { color: #8D4955; }

/* Кольорові позначки залишаються видимими й зі старим risks.css. */
.ri-table .ri-risk-cell { white-space: nowrap; }
.ri-table .ri-level-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 9px;
    border: 1px solid var(--ri-badge-border);
    border-radius: 999px;
    color: var(--ri-badge-text);
    background: var(--ri-badge-bg);
    font-weight: 750;
    font-size: 11px;
    line-height: 1.2;
    white-space: nowrap;
}
.ri-table .ri-level-badge i {
    display: block;
    width: 6px;
    height: 6px;
    flex-shrink: 0;
    border-radius: 50%;
    background: currentColor;
}
.ri-table .ri-level-badge.critical { --ri-badge-text: #BF2F43; --ri-badge-border: #F7C9D0; --ri-badge-bg: #FEEAEC; }
.ri-table .ri-level-badge.high     { --ri-badge-text: #A45815; --ri-badge-border: #FFD9A9; --ri-badge-bg: #FFF0DC; }
.ri-table .ri-level-badge.medium   { --ri-badge-text: #936900; --ri-badge-border: #F1DEA5; --ri-badge-bg: #FFF8E2; }
.ri-table .ri-level-badge.low      { --ri-badge-text: #215DB5; --ri-badge-border: #C4D9FA; --ri-badge-bg: #EAF2FF; }
.ri-table .ri-level-badge.very-low { --ri-badge-text: #147C44; --ri-badge-border: #B9E2C9; --ri-badge-bg: #E9F8EF; }

:is(.st-key-ri_live_add, .st-key-ri_live_edit)[data-testid="stVerticalBlock"] {
    background: #fff;
    border: 1px solid #dce8f8;
    border-radius: 15px;
    padding: 22px;
}
@media (max-width: 768px) {
    :is(.st-key-ri_live_add, .st-key-ri_live_edit)[data-testid="stVerticalBlock"] {
        padding: 14px;
    }
}
</style>
""")

LEVELS = [(4, 'Дуже низький', 'very-low'), (9, 'Низький', 'low'),
          (14, 'Середній', 'medium'), (19, 'Високий', 'high'), (25, 'Критичний', 'critical')]
STAT_ICONS = {
    'all': '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 7h6M9 11h6M9 15h3"/>',
    'high': '<path d="M10.3 3.7 1.9 18.3a1.8 1.8 0 0 0 1.6 2.7h17a1.8 1.8 0 0 0 1.6-2.7L13.7 3.7a2 2 0 0 0-3.4 0Z"/><path d="M12 9v5M12 18h.01"/>',
    'critical': '<path d="M12 2 3 6v6c0 5 3.5 8 9 10 5.5-2 9-5 9-10V6l-9-4Z"/><path d="M12 7v6M12 17h.01"/>',
}

def stat_icon_css(kind, markup):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
           f'stroke="black" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{markup}</svg>')
    return f'.ri-stats .ri-stat-icon-{kind} {{ --ri-stat-mask: url("data:image/svg+xml,{quote(svg, safe="")}"); }}'

st.html('<style>' + '\n'.join(stat_icon_css(kind, markup) for kind, markup in STAT_ICONS.items()) + '</style>')

def risk_level(score):
    return next((name, cls) for limit, name, cls in LEVELS if score <= limit)

def stat_icon(kind):
    return f'<div class="ri-stat-icon ri-stat-icon-svg ri-stat-icon-{kind}" aria-hidden="true"></div>'

def render_risk_preview(activity, severity, criticality):
    preview = calculate_advanced_risk(activity, severity, criticality)
    level, _ = risk_level(preview['risk_score'])
    st.info(
        f"Автоматичний розрахунок: P = {preview['probability']}, "
        f"I = {preview['impact']}, R = {preview['risk_score']}/25 — {level}. "
        f"Активність загрози: {activity}/5."
    )
    return preview

def toggle_action(action):
    st.session_state.risk_action = None if st.session_state.risk_action == action else action

if 'risk_action' not in st.session_state:
    st.session_state.risk_action = None

assets = get_assets()
asset_labels = {a[0]: f'ID {a[0]} — {a[1]}' for a in assets}
with get_connection() as conn:
    threats = conn.execute('SELECT id, asset_id, name FROM threats ORDER BY id').fetchall()
    vulns = conn.execute('SELECT id, asset_id, name, severity FROM vulnerabilities ORDER BY id').fetchall()
    risks = conn.execute('''
        SELECT r.id, r.asset_id, a.name, t.name, v.name, r.threat_activity,
               r.probability, r.impact, r.risk_score, r.assessment_date,
               r.threat_id, r.vulnerability_id
        FROM risks r
        JOIN assets a ON a.id=r.asset_id
        JOIN threats t ON t.id=r.threat_id
        JOIN vulnerabilities v ON v.id=r.vulnerability_id
        ORDER BY r.id DESC
    ''').fetchall()

high_count = sum(risk_level(int(r[8]))[1] == 'high' for r in risks)
critical_count = sum(risk_level(int(r[8]))[1] == 'critical' for r in risks)
critical_card_class = ' ri-stat-critical' if critical_count > 0 else ''
st.html('''<div class="ri-hero"><div><div class="ri-eyebrow">CYBERRISK DSS / СИСТЕМА ПІДТРИМКИ ПРИЙНЯТТЯ РІШЕНЬ</div><h1>Оцінювання ризиків</h1><p>Автоматизований розрахунок та облік кіберризиків інформаційної інфраструктури підприємства</p></div><div class="ri-hero-icon"><svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="15" y="6" width="34" height="52" rx="6"/><rect x="21" y="13" width="22" height="12" rx="2"/><path d="M23 34h5"/><path d="M25.5 31.5v5"/><path d="M36 34h6"/><path d="M23 44h6"/><path d="M36 41l6 6"/><path d="M42 41l-6 6"/></svg></div></div>''')
# ============================================================
# СТАТИСТИЧНІ КАРТКИ: спільний дизайн з «Інформаційними активами»
# ============================================================
st.html(f'''<div class="ri-stats">
<div class="ri-stat">{stat_icon('all')}<div><span>Усього оцінок</span><strong>{len(risks)}</strong><small>Зареєстровано в системі</small></div></div>
<div class="ri-stat ri-stat-high">{stat_icon('high')}<div><span>Високі ризики</span><strong>{high_count}</strong><small>Бал ризику 15–19</small></div></div>
<div class="ri-stat{critical_card_class}">{stat_icon('critical')}<div><span>Критичні ризики</span><strong>{critical_count}</strong><small>Бал ризику 20–25</small></div></div>
</div>''')

st.html('<div class="ri-register-heading"><h2>▤ Реєстр кіберризиків</h2></div>')

# Пошук і фільтрація не змінюють вихідні записи SQLite, а тільки представлення.
filter_cols = st.columns([1.7, 1.05, 1.15], gap='medium')
with filter_cols[0]:
    search_text = st.text_input(
        'Пошук ризику', placeholder='Актив, загроза, вразливість або ID...',
        key='ri_registry_search',
    ).strip().casefold()
with filter_cols[1]:
    selected_level = st.selectbox(
        'Рівень ризику',
        ['Усі рівні', 'Критичний', 'Високий', 'Середній', 'Низький', 'Дуже низький'],
        key='ri_registry_level',
    )
with filter_cols[2]:
    sort_order = st.selectbox(
        'Сортувати за',
        ['Ризик: 25 → 1', 'Ризик: 1 → 25', 'ID: нові спочатку',
         'ID: старі спочатку', 'Актив: А → Я', 'Актив: Я → А'],
        key='ri_registry_sort',
    )


def matches_registry_filters(record):
    level_name, _ = risk_level(int(record[8]))
    if selected_level != 'Усі рівні' and level_name != selected_level:
        return False
    searchable = ' '.join(str(record[i] or '') for i in (0, 2, 3, 4))
    return search_text in searchable.casefold()


visible_risks = [r for r in risks if matches_registry_filters(r)]
if sort_order == 'Ризик: 25 → 1':
    visible_risks.sort(key=lambda r: (int(r[8]), int(r[0])), reverse=True)
elif sort_order == 'Ризик: 1 → 25':
    visible_risks.sort(key=lambda r: (int(r[8]), int(r[0])))
elif sort_order == 'ID: нові спочатку':
    visible_risks.sort(key=lambda r: int(r[0]), reverse=True)
elif sort_order == 'ID: старі спочатку':
    visible_risks.sort(key=lambda r: int(r[0]))
elif sort_order == 'Актив: А → Я':
    visible_risks.sort(key=lambda r: (str(r[2]).casefold(), int(r[0])))
else:
    visible_risks.sort(key=lambda r: (str(r[2]).casefold(), int(r[0])), reverse=True)

# У таблиці заголовки зліва, а лише ID і числові P/I — по центру.
# Усі значення з SQLite екрануються від HTML-ін'єкцій.
if visible_risks:
    rows = []
    for r in visible_risks:
        level_name, level_class = risk_level(int(r[8]))
        activity = str(r[5]) if r[5] is not None else '—'
        score = int(r[8])
        rows.append(
            '<tr>'
            f'<td class="ri-id">{escape(str(r[0]))}</td>'
            f'<td class="ri-name">{escape(str(r[2] or "—"))}</td>'
            f'<td>{escape(str(r[3] or "—"))}</td>'
            f'<td>{escape(str(r[4] or "—"))}</td>'
            f'<td class="ri-num">{escape(activity)}</td>'
            f'<td class="ri-num">{escape(str(r[6] if r[6] is not None else "—"))}</td>'
            f'<td class="ri-num">{escape(str(r[7] if r[7] is not None else "—"))}</td>'
            f'<td class="ri-risk-cell"><span class="ri-score">{score}/25</span>'
            f'<span class="ri-level-badge {level_class}"><i></i>{escape(level_name)}</span></td>'
            f'<td>{escape(str(r[9] or "—"))}</td>'
            '</tr>'
        )
    table = '''<div class="ri-table-wrap"><table class="ri-table">
        <thead><tr><th>ID</th><th>Актив</th><th>Загроза</th>
        <th>Вразливість</th><th>Активність</th><th>P</th><th>I</th>
        <th>Ризик</th><th>Дата</th></tr></thead><tbody>''' + ''.join(rows) + '</tbody></table></div>'
    st.html(table)
elif risks:
    st.info('За вибраними умовами пошуку та фільтрації ризиків не знайдено.')
else:
    st.info('Оцінок ризиків поки немає. Натисніть «Додати оцінку ризику».')

st.caption(f'Показано оцінок: {len(visible_risks)} із {len(risks)}. Для старих оцінок активність загрози може бути не вказана.')
st.html('<div class="ri-rule"></div>')

c1, c2, c3 = st.columns(3, gap='medium')
with c1:
    st.button('＋ Додати оцінку ризику', key='risk_action_add', use_container_width=True,
              type='primary' if st.session_state.risk_action == 'add' else 'secondary',
              on_click=toggle_action, args=('add',))
with c2:
    st.button('✎ Редагувати оцінку', key='risk_action_edit', use_container_width=True,
              disabled=not risks, type='primary' if st.session_state.risk_action == 'edit' else 'secondary',
              on_click=toggle_action, args=('edit',))
with c3:
    st.button('▣ Видалити оцінку', key='risk_action_delete', use_container_width=True,
              disabled=not risks, type='primary' if st.session_state.risk_action == 'delete' else 'secondary',
              on_click=toggle_action, args=('delete',))

if st.session_state.risk_action == 'add':
    if not assets:
        st.warning('Спочатку додайте інформаційний актив.')
    else:
        selected_asset = st.selectbox('Інформаційний актив', list(asset_labels),
                                      format_func=lambda i: asset_labels[i], key='ri_add_asset')
        ts = [t for t in threats if t[1] == selected_asset]
        vs = [v for v in vulns if v[1] == selected_asset]
        if not ts or not vs:
            st.warning('Для цього активу необхідно зареєструвати щонайменше одну загрозу та одну вразливість.')
        else:
            with st.container(key='ri_live_add'):
                threat = st.selectbox('Загроза', ts, format_func=lambda t: f'ID {t[0]} — {t[2]}',
                                      key=f'ri_add_threat_{selected_asset}')
                vuln = st.selectbox('Вразливість', vs, format_func=lambda v: f'ID {v[0]} — {v[2]} (серйозність {v[3]}/5)',
                                    key=f'ri_add_vulnerability_{selected_asset}')
                activity = st.slider('Активність загрози', 1, 5, 3,
                                     key=f'ri_add_activity_{selected_asset}',
                                     help='Експертна оцінка активності загрози: 1 — мінімальна, 5 — максимальна.')
                render_risk_preview(activity, int(vuln[3]),
                                    int(next(a[5] for a in assets if a[0] == selected_asset)))
                if st.button('Зберегти оцінку', key='ri_live_add_save', type='primary'):
                    try:
                        add_automated_risk(selected_asset, threat[0], vuln[0], activity)
                        st.session_state.ri_success = 'Оцінку кіберризику успішно додано до реєстру.'
                        st.session_state.risk_action = None
                        st.rerun()
                    except (ValueError, sqlite3.Error) as exc:
                        st.error(f'Не вдалося зберегти оцінку: {exc}')

elif st.session_state.risk_action == 'edit':
    selected = st.selectbox('Оберіть оцінку', risks, format_func=lambda r: f'ID {r[0]} — {r[2]} — {r[8]}/25', key='ri_edit_choice')
    asset_id = selected[1]
    ts = [t for t in threats if t[1] == asset_id]
    vs = [v for v in vulns if v[1] == asset_id]
    if not ts or not vs:
        st.error('Для пов’язаного активу відсутні загрози або вразливості.')
    else:
        t_ids = [t[0] for t in ts]
        v_ids = [v[0] for v in vs]
        with st.container(key='ri_live_edit'):
            st.text_input('Інформаційний актив', value=selected[2], disabled=True)
            threat = st.selectbox('Загроза', ts, index=t_ids.index(selected[10]) if selected[10] in t_ids else 0,
                                  format_func=lambda t: f'ID {t[0]} — {t[2]}',
                                  key=f'ri_edit_threat_{selected[0]}')
            vuln = st.selectbox('Вразливість', vs, index=v_ids.index(selected[11]) if selected[11] in v_ids else 0,
                                format_func=lambda v: f'ID {v[0]} — {v[2]} (серйозність {v[3]}/5)',
                                key=f'ri_edit_vulnerability_{selected[0]}')
            activity = st.slider('Активність загрози', 1, 5,
                                 int(selected[5]) if selected[5] is not None else 3,
                                 key=f'ri_edit_activity_{selected[0]}')
            preview = render_risk_preview(activity, int(vuln[3]),
                                          int(next(a[5] for a in assets if a[0] == asset_id)))
            if st.button('Зберегти зміни', key='ri_live_edit_save', type='primary'):
                try:
                    with get_connection() as conn:
                        cursor = conn.execute('''UPDATE risks SET threat_id=?, vulnerability_id=?, threat_activity=?,
                                                 probability=?, impact=?, risk_score=? WHERE id=?''',
                                              (threat[0], vuln[0], activity, preview['probability'],
                                               preview['impact'], preview['risk_score'], selected[0]))
                        if cursor.rowcount != 1:
                            raise ValueError('Оцінку не знайдено.')
                    st.session_state.ri_success = 'Зміни оцінки кіберризику успішно збережено.'
                    st.session_state.risk_action = None
                    st.rerun()
                except (ValueError, sqlite3.Error) as exc:
                    st.error(f'Не вдалося оновити оцінку: {exc}')

elif st.session_state.risk_action == 'delete':
    selected = st.selectbox('Оберіть оцінку для видалення', risks,
                            format_func=lambda r: f'ID {r[0]} — {r[2]} — {r[8]}/25', key='ri_delete_choice')
    with get_connection() as conn:
        linked = conn.execute('SELECT COUNT(*) FROM security_measures WHERE risk_id=?', (selected[0],)).fetchone()[0]
    st.html('<div class="ri-delete-heading"><strong>Видалення оцінки ризику</strong><span>Перевірка пов’язаних заходів захисту та підтвердження</span></div>')
    if linked:
        st.error(f'Видалення заблоковано: з оцінкою пов’язано {linked} захід(заходів) захисту.')
    else:
        st.warning('Після підтвердження оцінку буде остаточно видалено.')
        confirmed = st.checkbox('Підтверджую видалення вибраної оцінки', key=f'ri_confirm_{selected[0]}')
        if st.button('Остаточно видалити', key='ri_confirm_delete', type='primary', disabled=not confirmed):
            try:
                with get_connection() as conn:
                    linked_now = conn.execute('SELECT COUNT(*) FROM security_measures WHERE risk_id=?', (selected[0],)).fetchone()[0]
                    if linked_now:
                        raise ValueError('Видалення заблоковано: оцінка вже пов’язана із заходом захисту.')
                    cursor = conn.execute('DELETE FROM risks WHERE id=?', (selected[0],))
                    if cursor.rowcount != 1:
                        raise ValueError('Оцінку не знайдено.')
                st.session_state.ri_success = 'Оцінку кіберризику успішно видалено.'
                st.session_state.risk_action = None
                st.rerun()
            except (ValueError, sqlite3.Error) as exc:
                st.error(f'Не вдалося видалити оцінку: {exc}')

if 'ri_success' in st.session_state:
    st.toast(st.session_state.pop('ri_success'), icon=':material/check_circle:')
st.html('<div class="ri-bottom-rule"></div>')
render_footer()
