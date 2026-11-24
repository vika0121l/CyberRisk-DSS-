from pathlib import Path
from html import escape
import streamlit as st
from database import initialize_database, get_assets, add_vulnerability, get_connection
from components import render_footer

initialize_database()
css_path = Path(__file__).resolve().parents[1] / 'styles' / 'vulnerabilities.css'
if css_path.exists():
    st.markdown(f'<style>{css_path.read_text(encoding="utf-8")}</style>', unsafe_allow_html=True)

LEVELS = {1: ('Дуже низька', 'very-low'), 2: ('Низька', 'low'), 3: ('Середня', 'medium'), 4: ('Висока', 'high'), 5: ('Критична', 'critical')}

if 'vuln_action' not in st.session_state:
    st.session_state.vuln_action = None

def toggle_action(action):
    st.session_state.vuln_action = None if st.session_state.vuln_action == action else action

assets = get_assets()
asset_choices = {f'ID {a[0]} — {a[1]}': a[0] for a in assets}
with get_connection() as conn:
    vulnerabilities = conn.execute('''
        SELECT v.id, v.asset_id, a.name, v.name, v.severity, v.description
        FROM vulnerabilities v
        LEFT JOIN assets a ON a.id = v.asset_id
        ORDER BY v.id
    ''').fetchall()

asset_count = len({v[1] for v in vulnerabilities})
high_count = sum(int(v[4]) == 4 for v in vulnerabilities)
critical_count = sum(int(v[4]) == 5 for v in vulnerabilities)
critical_card_class = ' vu-stat-critical' if critical_count else ''

st.html('''<div class="vu-hero"><div><div class="vu-eyebrow">CYBERRISK DSS / СИСТЕМА ПІДТРИМКИ ПРИЙНЯТТЯ РІШЕНЬ</div><h1>Вразливості</h1><p>Реєстрація, аналіз та облік вразливостей інформаційних активів підприємства</p></div><div class="vu-hero-icon" aria-hidden="true"></div></div>''')
st.html('''<style>
@media (min-width: 901px) {
    .vu-stats.vu-stats-split { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (min-width: 1200px) {
    .vu-stats.vu-stats-split { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}
.vu-stats-split .vu-stat-critical {
    background: linear-gradient(120deg, #FFF9F9 0%, #FFF0F1 100%) !important;
    border-color: #F4B4BF !important;
}
.vu-stats-split .vu-stat-critical span,
.vu-stats-split .vu-stat-critical strong { color: #AA2639; }
.vu-stats-split .vu-stat-critical small { color: #8D4955; }
.vu-stats-split .vu-icon-critical {
    color: #2267CC;
}
.vu-stats-split .vu-icon-critical::before {
    content: "";
    display: block;
    width: 26px;
    height: 26px;
    background: currentColor;
    mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 2 3 6v6c0 5 3.5 8 9 10 5.5-2 9-5 9-10V6l-9-4Z'/%3E%3Cpath d='M12 7v6M12 17h.01'/%3E%3C/svg%3E") center / contain no-repeat;
}
.vu-stats-split .vu-stat-critical .vu-icon-critical {
    background-color: #FDE4E8 !important;
    color: #C02F43;
}
</style>''')
st.html(f'''<div class="vu-stats vu-stats-split">
<div class="vu-stat"><div class="vu-stat-icon vu-icon-total" aria-hidden="true"></div><div><span>Усього вразливостей</span><strong>{len(vulnerabilities)}</strong><small>Зареєстровано в системі</small></div></div>
<div class="vu-stat"><div class="vu-stat-icon vu-icon-assets" aria-hidden="true"></div><div><span>Активи із вразливостями</span><strong>{asset_count}</strong><small>Із {len(assets)} зареєстрованих активів</small></div></div>
<div class="vu-stat"><div class="vu-stat-icon vu-icon-high" aria-hidden="true"></div><div><span>Високі</span><strong>{high_count}</strong><small>Серйозність 4 із 5</small></div></div>
<div class="vu-stat{critical_card_class}"><div class="vu-stat-icon vu-icon-critical" aria-hidden="true"></div><div><span>Критичні</span><strong>{critical_count}</strong><small>Серйозність 5 із 5</small></div></div>
</div>''')
# Заголовок і керування реєстром — у стилі сторінки «Інформаційні активи».
st.html('<div class="vu-register-heading"><h2>▤ Реєстр вразливостей</h2></div>')

filter_search_col, filter_severity_col, filter_sort_col = st.columns([1.65, 1.0, 1.05], gap="small")
with filter_search_col:
    search_query = st.text_input(
        "Пошук вразливості",
        placeholder="Назва, актив, серйозність, опис або ID...",
        key="vu_registry_search",
    ).strip().casefold()
with filter_severity_col:
    severity_choice = st.selectbox(
        "Серйозність",
        [
            "Усі рівні",
            "5 — Критична",
            "4 — Висока",
            "3 — Середня",
            "2 — Низька",
            "1 — Дуже низька",
        ],
        key="vu_registry_severity",
    )
with filter_sort_col:
    sort_choice = st.selectbox(
        "Сортувати за",
        [
            "Серйозність: 5 → 1",
            "Серйозність: 1 → 5",
            "ID: нові спочатку",
            "ID: старі спочатку",
            "Назва: А → Я",
            "Назва: Я → А",
        ],
        key="vu_registry_sort",
    )

selected_severity = None if severity_choice == "Усі рівні" else int(severity_choice[0])
filtered_vulnerabilities = []
for item in vulnerabilities:
    level_label = LEVELS.get(int(item[4]), ("Невідомо", "unknown"))[0]
    searchable = " ".join([
        str(item[0]),
        str(item[2] or ""),
        str(item[3] or ""),
        str(item[4]),
        f"{item[4]}/5",
        level_label,
        str(item[5] or ""),
    ]).casefold()
    if search_query and search_query not in searchable:
        continue
    if selected_severity is not None and int(item[4]) != selected_severity:
        continue
    filtered_vulnerabilities.append(item)

if sort_choice == "Серйозність: 5 → 1":
    filtered_vulnerabilities.sort(key=lambda x: (-int(x[4]), -int(x[0])))
elif sort_choice == "Серйозність: 1 → 5":
    filtered_vulnerabilities.sort(key=lambda x: (int(x[4]), int(x[0])))
elif sort_choice == "ID: нові спочатку":
    filtered_vulnerabilities.sort(key=lambda x: int(x[0]), reverse=True)
elif sort_choice == "ID: старі спочатку":
    filtered_vulnerabilities.sort(key=lambda x: int(x[0]))
elif sort_choice == "Назва: А → Я":
    filtered_vulnerabilities.sort(key=lambda x: str(x[3] or "").casefold())
else:
    filtered_vulnerabilities.sort(key=lambda x: str(x[3] or "").casefold(), reverse=True)

if filtered_vulnerabilities:
    table_rows = []
    for item in filtered_vulnerabilities:
        level, css_class = LEVELS.get(int(item[4]), ("Невідомо", "unknown"))
        table_rows.append(
            '<tr>'
            f'<td class="vu-cell-id">{escape(str(item[0]))}</td>'
            f'<td class="vu-name">{escape(str(item[3] or "—"))}</td>'
            f'<td>{escape(str(item[2] or "Невідомий актив"))}</td>'
            f'<td class="vu-severity-cell"><span class="vu-score">{int(item[4])}/5</span>'
            f'<span class="vu-level-badge {css_class}">'
            f'<span class="vu-badge-dot"></span>{escape(level)}'
            '</span></td>'
            f'<td>{escape(str(item[5] or "—"))}</td>'
            '</tr>'
        )
    st.html(
        '<div class="vu-table-wrap"><table class="vu-table">'
        '<thead><tr><th>ID</th><th>Назва вразливості</th>'
        '<th>Інформаційний актив</th><th>Серйозність</th><th>Опис</th>'
        '</tr></thead><tbody>' + ''.join(table_rows) + '</tbody></table></div>'
    )
elif vulnerabilities:
    st.info("За вибраними параметрами вразливостей не знайдено. Очисть пошук або зміни фільтр.")
else:
    st.info("Вразливості ще не зареєстровані. Натисни «Додати вразливість».")

st.caption(f"Показано вразливостей: {len(filtered_vulnerabilities)} із {len(vulnerabilities)}")
st.html('<div class="vu-rule"></div>')

c1, c2, c3 = st.columns(3, gap='medium')
with c1:
    st.button('＋ Додати вразливість', key='vulnerability_action_add', use_container_width=True,
              type='primary' if st.session_state.vuln_action == 'add' else 'secondary',
              on_click=toggle_action, args=('add',))
with c2:
    st.button('✎ Редагувати вразливість', key='vulnerability_action_edit', use_container_width=True, disabled=not vulnerabilities,
              type='primary' if st.session_state.vuln_action == 'edit' else 'secondary',
              on_click=toggle_action, args=('edit',))
with c3:
    st.button('▣ Видалити вразливість', key='vulnerability_action_delete', use_container_width=True, disabled=not vulnerabilities,
              type='primary' if st.session_state.vuln_action == 'delete' else 'secondary',
              on_click=toggle_action, args=('delete',))

if st.session_state.vuln_action == 'add':
    if not assets:
        st.warning('Спочатку зареєструйте інформаційний актив.')
    else:
        with st.form('vu_add_form', clear_on_submit=True):
            asset_label = st.selectbox('Інформаційний актив', list(asset_choices))
            name = st.text_input('Назва вразливості')
            severity = st.slider('Серйозність вразливості', 1, 5, 3,
                                 help='1 — дуже низька, 2 — низька, 3 — середня, 4 — висока, 5 — критична')
            description = st.text_area('Опис вразливості')
            if st.form_submit_button('Зберегти вразливість', type='primary'):
                if not name.strip():
                    st.error('Вкажіть назву вразливості.')
                else:
                    add_vulnerability(asset_choices[asset_label], name.strip(), severity, description.strip())
                    st.session_state.vu_success = 'Вразливість успішно додано до реєстру.'
                    st.session_state.vuln_action = None
                    st.rerun()

elif st.session_state.vuln_action == 'edit':
    choices = {f'ID {v[0]} — {v[3]}': v[0] for v in vulnerabilities}
    chosen_id = choices[st.selectbox('Оберіть вразливість', list(choices))]
    with get_connection() as conn:
        record = conn.execute('SELECT asset_id, name, severity, description FROM vulnerabilities WHERE id=?', (chosen_id,)).fetchone()
    if record and asset_choices:
        asset_ids = list(asset_choices.values())
        with st.form(f'vu_edit_form_{chosen_id}'):
            asset_label = st.selectbox('Інформаційний актив', list(asset_choices), index=asset_ids.index(record[0]) if record[0] in asset_ids else 0)
            name = st.text_input('Назва вразливості', value=record[1])
            severity = st.slider('Серйозність вразливості', 1, 5, int(record[2]))
            description = st.text_area('Опис вразливості', value=record[3] or '')
            if st.form_submit_button('Зберегти зміни', type='primary'):
                if not name.strip():
                    st.error('Назва вразливості не може бути порожньою.')
                else:
                    new_asset_id = asset_choices[asset_label]
                    with get_connection() as conn:
                        linked = conn.execute('SELECT COUNT(*) FROM risks WHERE vulnerability_id=?', (chosen_id,)).fetchone()[0]
                    if linked and new_asset_id != record[0]:
                        st.error('Не можна змінити актив вразливості, яка вже використовується в оцінюванні ризику.')
                    else:
                        with get_connection() as conn:
                            cursor = conn.execute('UPDATE vulnerabilities SET asset_id=?, name=?, severity=?, description=? WHERE id=?',
                                                  (new_asset_id, name.strip(), severity, description.strip(), chosen_id))
                            changed = cursor.rowcount
                            conn.commit()
                        if changed == 1:
                            st.session_state.vu_success = 'Зміни вразливості успішно збережено.'
                            st.session_state.vuln_action = None
                            st.rerun()
                        else:
                            st.error('Запис не знайдено. Зміни не збережено.')

elif st.session_state.vuln_action == 'delete':
    choices = {f'ID {v[0]} — {v[3]}': v[0] for v in vulnerabilities}
    chosen_id = choices[st.selectbox('Оберіть вразливість для видалення', list(choices), key='vu_delete_choice')]
    with get_connection() as conn:
        linked = conn.execute('SELECT COUNT(*) FROM risks WHERE vulnerability_id=?', (chosen_id,)).fetchone()[0]
    st.html('<div class="vu-delete-heading"><strong>Видалення вразливості</strong><span>Перевірка зв’язків та підтвердження операції</span></div>')
    if linked:
        st.error(f'Видалення заблоковано. Вразливість використовується в {linked} оцінці(ах) кіберризику.')
    else:
        st.warning('Вразливість не використовується в оцінюваннях ризиків. Після підтвердження запис буде остаточно видалено.')
        confirmed = st.checkbox('Підтверджую видалення вибраної вразливості', key=f'vu_confirm_{chosen_id}')
        if st.button('Остаточно видалити', type='primary', disabled=not confirmed, key='vu_confirm_delete'):
            with get_connection() as conn:
                linked_now = conn.execute('SELECT COUNT(*) FROM risks WHERE vulnerability_id=?', (chosen_id,)).fetchone()[0]
                if linked_now:
                    st.error('Видалення скасовано: з’явилися пов’язані оцінки ризиків.')
                    st.stop()
                cursor = conn.execute('DELETE FROM vulnerabilities WHERE id=?', (chosen_id,))
                deleted = cursor.rowcount
                conn.commit()
            if deleted == 1:
                st.session_state.vu_success = 'Вразливість успішно видалено з реєстру.'
                st.session_state.vuln_action = None
                st.rerun()
            else:
                st.error('Вразливість не знайдено. Видалення не виконано.')

if 'vu_success' in st.session_state:
    st.toast(st.session_state.pop('vu_success'), icon=':material/check_circle:')

# Контейнер футера з автоматичним притисканням донизу на коротких сторінках.
with st.container(key="vu_page_footer"):
    st.html('<div class="vu-bottom-rule"></div>')
    render_footer()
