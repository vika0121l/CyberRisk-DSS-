"""Сторінка реєстрації заходів захисту CyberRisk DSS."""
from pathlib import Path
from html import escape
from decimal import Decimal, InvalidOperation
import base64
import sqlite3
import streamlit as st
from database import initialize_database
from measure_repository import (list_measures,list_risks,create_measure,
                                update_measure,delete_measure)
from risk_constraints import initialize_risk_constraints, load_risk_constraints, save_risk_constraints

initialize_database()
initialize_risk_constraints()
css = Path(__file__).resolve().parents[1] / 'styles' / 'measures.css'
if css.exists():
    st.html(f'<style>{css.read_text(encoding="utf-8")}</style>')

# Стилі лише для картки бюджету. Штатні віджети й збереження лишаються в Streamlit.
st.html("""<style>
.st-key-sm_budget_card {
    --sm-card-pad: clamp(15px, 2vw, 25px);
    --sm-card-ink: #183964;
}
.st-key-sm_budget_card [data-testid="stExpander"] > details {
    background: linear-gradient(165deg, #fff, #fbfdff);
    border: 1px solid #bcd5fa !important;
    border-radius: 13px;
    box-shadow: 0 4px 15px rgba(26, 74, 138, .08);
}
.st-key-sm_budget_card [data-testid="stExpander"] summary {
    position: relative;
    display: flex;
    align-items: center;
    min-height: 76px;
    padding: 14px 47px 14px calc(var(--sm-card-pad) + 62px) !important;
    border-bottom: 0 !important;
    color: var(--sm-card-ink);
    cursor: pointer;
}
.st-key-sm_budget_card [data-testid="stExpander"] summary::before {
    content: "";
    position: absolute;
    width: 46px;
    height: 46px;
    left: var(--sm-card-pad);
    top: 50%;
    transform: translateY(-50%);
    border-radius: 12px;
    background: #e2edff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%231b62c0' stroke-width='1.9' stroke-linecap='round'%3E%3Cpath d='M3 5h7m5 0h6M3 12h2m5 0h11M3 19h10m5 0h3'/%3E%3Ccircle cx='12.5' cy='5' r='2.5'/%3E%3Ccircle cx='7.5' cy='12' r='2.5'/%3E%3Ccircle cx='15.5' cy='19' r='2.5'/%3E%3C/svg%3E") center / 25px no-repeat;
    pointer-events: none;
}
.st-key-sm_budget_card summary :is([data-testid="stIconMaterial"], [data-testid="stExpanderToggleIcon"], svg) {
    display: none !important;
}
.st-key-sm_budget_card summary::after {
    content: "";
    position: absolute;
    width: 9px;
    height: 9px;
    right: calc(var(--sm-card-pad) + 5px);
    top: 50%;
    border-right: 2px solid currentColor;
    border-bottom: 2px solid currentColor;
    transform: translateY(-70%) rotate(45deg);
    pointer-events: none;
}
.st-key-sm_budget_card details[open] > summary::after {
    transform: translateY(-25%) rotate(225deg);
}
.st-key-sm_budget_card summary p {
    margin: 0 !important;
    color: var(--sm-card-ink) !important;
    font-size: 1.22rem !important;
    line-height: 1.22;
    font-weight: 750 !important;
}
.st-key-sm_budget_card summary p::after {
    display: block;
    content: "Обмеження для порівняння заходів";
    margin-top: 4px;
    color: #587394;
    font-size: .8rem;
    font-weight: 450;
}
.st-key-sm_budget_card [data-testid="stExpanderDetails"] {
    padding: 1px var(--sm-card-pad) var(--sm-card-pad) !important;
    border-top: 0 !important;
}
.st-key-sm_budget_card [data-testid="stForm"] {
    border: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
}
.st-key-sm_budget_card [data-testid="stWidgetLabel"] p {
    color: var(--sm-card-ink);
    font-weight: 670;
}
.st-key-sm_budget_card [data-testid="stSelectbox"] :is([data-baseweb="select"] > div, [role="group"]:has(input)) {
    background: #edf4ff !important;
    border: 1px solid #c9dcf9 !important;
    border-radius: 9px;
    min-height: 45px;
}
.st-key-sm_budget_card [data-testid="stSelectbox"] button {
    background: transparent !important;
    border: 0 !important;
    min-height: 0 !important;
    box-shadow: none !important;
    color: var(--sm-card-ink) !important;
}
.st-key-sm_budget_card [data-testid="stSelectbox"] button svg {
    fill: currentColor;
}
.st-key-sm_budget_card [data-testid="stSelectbox"] input[role="combobox"] {
    color: var(--sm-card-ink) !important;
    font-size: .95rem !important;
}
.st-key-sm_budget_card [data-testid="stTextInput"] {
    position: relative;
    --sm-unit: "/ 25";
}
.st-key-sm_budget_amount [data-testid="stTextInput"] { --sm-unit: "ум. од."; }
.st-key-sm_budget_card [data-testid="stTextInput"]::after {
    content: var(--sm-unit);
    position: absolute;
    right: 14px;
    bottom: 0;
    height: 48px;
    display: flex;
    align-items: center;
    color: #496689;
    font-size: .88rem;
    font-weight: 650;
    pointer-events: none;
}
.st-key-sm_budget_card [data-testid="stTextInput"] :is([data-baseweb="input"], [data-testid="stTextInputRootElement"]) {
    background: #e9f2ff !important;
    border: 1px solid #c9dcf9 !important;
    border-radius: 9px;
}
.st-key-sm_budget_card [data-testid="stTextInput"] input {
    height: 46px;
    padding: 0 79px 0 13px !important;
    background: transparent !important;
    color: var(--sm-card-ink) !important;
    font-size: 1.14rem !important;
    font-weight: 720;
}
.st-key-sm_budget_card :is(
    [data-testid="stTextInputRootElement"], [data-baseweb="input"],
    [data-baseweb="select"] > div, [role="group"]:has(input)
):focus-within {
    outline: 2px solid #2c6dc6;
    outline-offset: 1px;
}
.st-key-sm_budget_footer {
    border-top: 1px solid #d5e4f8;
    margin-top: 3px;
    padding-top: 13px;
}
.st-key-sm_budget_footer :is(
    [data-testid="stElementContainer"]:has([data-testid="stFormSubmitButton"]),
    [data-testid="stFormSubmitButton"]
) {
    width: 100% !important;
}
.st-key-sm_budget_footer [data-testid="stFormSubmitButton"] {
    display: flex !important;
    justify-content: flex-end;
}
.st-key-sm_budget_footer [data-testid="stCaptionContainer"] p { color: #587394; }
.st-key-sm_budget_footer button {
    min-height: 42px;
    margin-left: auto;
    padding: 0 16px !important;
    background: linear-gradient(115deg, #174580, #2166ca) !important;
    border: 1px solid #1f59af !important;
    border-radius: 9px !important;
    color: #fff !important;
    font-weight: 700;
    white-space: nowrap;
}
.st-key-sm_budget_footer button:hover { filter: brightness(1.1); }
</style>""")

if 'measure_action' not in st.session_state:
    st.session_state.measure_action = None


def toggle(action):
    st.session_state.measure_action = None if st.session_state.measure_action == action else action

def label_risk(r):
    return f'№{r[0]} · {r[1]} · {r[2]} · R={r[6]}/25'

def label_measure(m):
    return f'№{m[0]} · {m[2]} · {m[10]}'


def format_constraint_budget(value):
    if value is None:
        return ""
    whole, _, fraction = f"{value:,.2f}".partition(".")
    return whole.replace(",", " ") + (f",{fraction}" if fraction != "00" else "")


def parse_constraint_inputs(budget_text, threshold_text):
    budget_text = "".join(budget_text.split()).replace(",", ".")
    threshold_text = threshold_text.strip()
    try:
        budget = Decimal(budget_text) if budget_text else None
        if budget is not None and (
            not budget.is_finite() or budget < 0
            or budget != budget.quantize(Decimal("0.01"))
        ):
            raise ValueError
    except (InvalidOperation, ValueError):
        raise ValueError("Введіть невід’ємну суму бюджету, не більше двох знаків після коми.") from None
    if threshold_text and (not threshold_text.isdecimal() or not 1 <= int(threshold_text) <= 25):
        raise ValueError("Поріг залишкового ризику має бути цілим числом від 1 до 25.")
    return budget, int(threshold_text) if threshold_text else None


def save_constraint_form(risk_id, budget_key, threshold_key):
    try:
        budget, threshold = parse_constraint_inputs(
            st.session_state[budget_key], st.session_state[threshold_key],
        )
        save_risk_constraints(risk_id, budget, threshold)
        st.session_state[budget_key] = format_constraint_budget(budget)
        st.session_state[threshold_key] = "" if threshold is None else str(threshold)
        st.session_state["sm_budget_slot"] = 1 - st.session_state.get("sm_budget_slot", 0)
        st.session_state.sm_success_toast = "Обмеження ризику збережено!"
        st.session_state.pop("sm_constraint_error", None)
    except (ValueError, sqlite3.Error) as exc:
        st.session_state.sm_constraint_error = (risk_id, str(exc))


risks=list_risks()
measures=list_measures()
linked_risks=len(set(m[1] for m in measures))

shield_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="10" width="14" height="11" rx="2.2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/><circle cx="12" cy="15" r="1"/><path d="M12 16v2"/><path d="m19.5 2 .55 1.45L21.5 4l-1.45.55L19.5 6l-.55-1.45L17.5 4l1.45-.55Z"/></svg>"""
shield_b64 = base64.b64encode(shield_svg.encode('utf-8')).decode('ascii')
st.html(f'''<section class="sm-hero"><div class="sm-hero-content"><div class="sm-eyebrow">CYBERRISK DSS / УПРАВЛІННЯ КІБЕРРИЗИКАМИ</div>
<h1>Заходи захисту</h1><p>Формування реєстру заходів зниження кіберризиків інформаційної інфраструктури підприємства</p></div>
<div class="sm-hero-icon"><img src="data:image/svg+xml;base64,{shield_b64}" width="48" height="48" alt="CyberRisk DSS — захист"></div></section>''')

# На сторінці показуємо прогноз для КОЖНОГО заходу окремо.
# Індекси list_measures(): 5/6 — ΔP/ΔI, 7/8 — P/I, 9 — R до заходу.
# Прогноз є експертною моделлю, а не фактичним станом захисту.
RISK_LEVELS = (
    (4, "Дуже низький", "very-low"),
    (9, "Низький", "low"),
    (14, "Середній", "medium"),
    (19, "Високий", "high"),
    (25, "Критичний", "critical"),
)


def risk_level(score):
    score = int(score)
    return next((label, css) for bound, label, css in RISK_LEVELS if score <= bound)


def forecast_after(measure):
    # Прогнозоване P₁=max(1,P−ΔP), I₁=max(1,I−ΔI), R₁=P₁×I₁.
    probability = int(measure[7])
    impact = int(measure[8])
    reduction_p = int(measure[5])
    reduction_i = int(measure[6])
    p1 = max(1, probability - reduction_p)
    i1 = max(1, impact - reduction_i)
    return p1 * i1


def money(value):
    return f"{float(value):,.2f}".replace(",", " ")


def compact_score(score, label):
    """Коротка кольорова позначка без зайвого тексту всередині таблиці."""
    level_name, color_class = risk_level(score)
    return (f'<span class="sm-score-chip {color_class}" '
            f'title="{escape(label)}: {escape(level_name)}">'
            f'{int(score)}/25</span>')


# Картки залишаються вгорі, але вартість рахуємо після вибору фільтра.
stats_slot = st.empty()

if risks:
    with st.container(key="sm_budget_card"):
        # Після збереження створюємо новий expander в іншій позиції.
        # Інакше Streamlit зберігає стан розкриття вже наявного expander.
        slots = (st.empty(), st.empty())
        with slots[st.session_state.get("sm_budget_slot", 0)].container(), st.expander(
            "Бюджет і поріг", expanded=False,
        ):
            constraint_risk = st.selectbox(
                "Ризик", risks, format_func=lambda r: f"№{r[0]} · {r[1]}",
                key="sm_constraint_risk",
            )
            risk_id = constraint_risk[0]
            saved_budget, saved_threshold = load_risk_constraints(risk_id)
            budget_key = f"sm_budget_text_{risk_id}"
            threshold_key = f"sm_threshold_text_{risk_id}"
            # Для цих віджетів єдине джерело значень — Session State.
            # Початкові дані з бази підставляємо лише до створення віджетів.
            if budget_key not in st.session_state:
                st.session_state[budget_key] = format_constraint_budget(saved_budget)
            if threshold_key not in st.session_state:
                st.session_state[threshold_key] = "" if saved_threshold is None else str(saved_threshold)
            with st.form(f"sm_constraints_form_{risk_id}", border=False):
                budget_col, threshold_col = st.columns(2, gap="medium")
                with budget_col, st.container(key="sm_budget_amount"):
                    st.text_input(
                        "Бюджет впровадження",
                        placeholder="Не задано", max_chars=32, key=budget_key,
                    )
                with threshold_col, st.container(key="sm_budget_threshold"):
                    st.text_input(
                        "Поріг залишкового ризику",
                        placeholder="Не задано", max_chars=2, key=threshold_key,
                    )
                with st.container(key="sm_budget_footer"):
                    note, action = st.columns([2.5, 1], gap="medium", vertical_alignment="center")
                    with note:
                        st.caption("Дані автоматично підтягуються до порівняння.")
                    with action:
                        st.form_submit_button(
                            "Зберегти обмеження", type="primary",
                            on_click=save_constraint_form,
                            args=(risk_id, budget_key, threshold_key),
                        )
            form_error = st.session_state.get("sm_constraint_error")
            if form_error and form_error[0] == risk_id:
                st.error(form_error[1])

st.html('''<div class="sm-heading"><h2><span class="sm-heading-symbol">▤</span> Реєстр заходів захисту</h2><p>Кожний захід пов’язаний із конкретною оцінкою кіберризику</p></div>''')

# Пошук і фільтри впливають лише на видиму таблицю, не на самі записи.
col_search, col_risk, col_sort = st.columns([1.65, 1, 1], gap="small")
with col_search:
    search = st.text_input("Пошук заходу", placeholder="Назва, актив, загроза або опис...", key="sm_search")
with col_risk:
    risk_ids = [None] + [r[0] for r in risks]
    risk_labels = {r[0]: f"№{r[0]} · {str(r[1])} · {r[6]}/25" for r in risks}
    selected_risk = st.selectbox("Пов’язаний ризик", risk_ids,
                                 format_func=lambda rid: "Усі ризики" if rid is None else risk_labels.get(rid, str(rid)),
                                 key="sm_risk_filter")
with col_sort:
    sort_mode = st.selectbox("Сортувати за", ["new", "old", "name", "cost_desc", "cost_asc", "risk_desc"],
                             format_func=lambda option: {
                                 "new": "ID: нові спочатку", "old": "ID: старі спочатку",
                                 "name": "Назва: А–Я", "cost_desc": "Вартість: від більшої",
                                 "cost_asc": "Вартість: від меншої", "risk_desc": "Початковий ризик: 25 → 1"
                             }[option], key="sm_sort")

# Картка вартості враховує всі заходи для вибраного ризику.
# Текстовий пошук і сортування змінюють лише відображення таблиці.
total_cost = sum(
    (Decimal(str(m[4])) for m in measures
     if selected_risk is None or int(m[1]) == int(selected_risk)),
    Decimal(0),
)
cost_scope = ("Сума всіх запропонованих рішень" if selected_risk is None
              else f"Сума заходів для ризику №{int(selected_risk)}")
# Статистичні картки у стилі сторінки «Інформаційні активи».
# Іконки малюються через CSS background-image (data:SVG),
# щоб Streamlit не приховував їх під час санітизації HTML.
stats_slot.html(f'''<section class="sm-stats">
  <div class="sm-stat"><span class="sm-stat-icon sm-icon-measures" aria-hidden="true"></span><div class="sm-stat-copy"><span>Зареєстровані заходи</span><strong>{len(measures)}</strong><small>Запропоновані рішення</small></div></div>
  <div class="sm-stat"><span class="sm-stat-icon sm-icon-coverage" aria-hidden="true"></span><div class="sm-stat-copy"><span>Охоплено ризиків</span><strong>{linked_risks}</strong><small>Із {len(risks)} оцінених</small></div></div>
  <div class="sm-stat"><span class="sm-stat-icon sm-icon-cost" aria-hidden="true"></span><div class="sm-stat-copy"><span>Сумарна вартість заходів</span><strong>{money(total_cost)}</strong><small>{escape(cost_scope)}, ум. од.</small></div></div>
  <div class="sm-stat sm-stat-dark"><span class="sm-stat-icon sm-icon-uncovered" aria-hidden="true"></span><div class="sm-stat-copy"><span>Ризики без заходів</span><strong>{max(0,len(risks)-linked_risks)}</strong><small>Потребують розгляду</small></div></div>
</section>''')

search_text = search.strip().casefold()
filtered = []
for measure in measures:
    if selected_risk is not None and int(measure[1]) != int(selected_risk):
        continue
    haystack = " ".join(str(x or "") for x in (
        measure[0], measure[1], measure[2], measure[3], measure[10], measure[11], measure[12]
    )).casefold()
    if search_text and search_text not in haystack:
        continue
    filtered.append(measure)

sort_modes = {
    "new": (lambda m: int(m[0]), True),
    "old": (lambda m: int(m[0]), False),
    "name": (lambda m: (str(m[2]).casefold(), int(m[0])), False),
    "cost_desc": (lambda m: (float(m[4]), int(m[0])), True),
    "cost_asc": (lambda m: (float(m[4]), int(m[0])), False),
    "risk_desc": (lambda m: (int(m[9]), int(m[0])), True),
}
key_function, descending = sort_modes[sort_mode]
filtered.sort(key=key_function, reverse=descending)

if filtered:
    rows = []
    for m in filtered:
        start_score = int(m[9])
        forecast_score = forecast_after(m)
        start_level, _ = risk_level(start_score)
        forecast_level, _ = risk_level(forecast_score)
        delta_p = f"−{int(m[5])}" if m[5] else "0"
        delta_i = f"−{int(m[6])}" if m[6] else "0"
        change = start_score - forecast_score
        # 2 останні стовпці об'єднані: прогноз не губиться,
        # але таблиця залишається читабельною при масштабі 90%.
        if change > 0:
            change_label = f'−{change} балів'
            change_class = 'improved'
        elif change == 0:
            change_label = 'Без змін'
            change_class = 'unchanged'
        else:
            change_label = f'+{abs(change)} балів'
            change_class = 'worsened'
        rows.append(f'''<tr>
          <td class="sm-id">{int(m[0])}</td>
          <td class="sm-strong">{escape(str(m[2]))}</td>
          <td>№{int(m[1])} · {escape(str(m[10] or "—"))}</td>
          <td>{escape(str(m[11] or "—"))}</td>
          <td class="sm-num">{money(m[4])}</td>
          <td class="sm-effect">
            <span class="sm-effect-chip">ΔP <b>{delta_p}</b></span>
            <span class="sm-effect-chip">ΔI <b>{delta_i}</b></span>
          </td>
          <td class="sm-risk-change">
            <div class="sm-change-scores">
              {compact_score(start_score, "Початковий ризик")}
              <span class="sm-change-arrow" aria-label="переходить у">→</span>
              {compact_score(forecast_score, "Прогнозований ризик")}
            </div>
            <div class="sm-change-levels">{escape(start_level)} → {escape(forecast_level)}</div>
            <div class="sm-change-delta {change_class}">{change_label}</div>
          </td>
        </tr>''')
    st.html('''<div class="sm-table-scroll"><table class="sm-table sm-table-compact">
      <colgroup>
        <col style="width:4.5%"><col style="width:19.5%"><col style="width:16.5%">
        <col style="width:24%"><col style="width:9%"><col style="width:10%"><col style="width:16.5%">
      </colgroup>
      <thead><tr>
        <th>ID</th><th>Захід захисту</th><th>Актив / ризик</th>
        <th>Загроза</th><th>Вартість</th><th>Ефект</th><th>Зміна ризику*</th>
      </tr></thead><tbody>''' + "".join(rows) + '</tbody></table></div>')
elif measures:
    st.info("За вибраними умовами заходів не знайдено. Спробуйте змінити пошук або фільтр.")
else:
    st.info("Заходів захисту ще немає. Додайте перший захід для зареєстрованого ризику.")
st.caption(f"Показано заходів: {len(filtered)} із {len(measures)}")
st.html('''<div class="sm-model-note"><strong>* Прогноз, не фактичний результат.</strong> P₁ = max(1, P − ΔP), I₁ = max(1, I − ΔI), R₁ = P₁ × I₁. ΔP та ΔI — експертні оцінки зниження ймовірності та впливу. Економічна ефективність розраховується в окремому розділі.</div>''')
c1,c2,c3=st.columns(3,gap='medium')
with c1:
    st.button('＋ Додати захід',use_container_width=True,key='sm_add_btn',
              type='primary' if st.session_state.measure_action=='add' else 'secondary',
              on_click=toggle,args=('add',),disabled=not risks)
with c2:
    st.button('✎ Редагувати',use_container_width=True,key='sm_edit_btn',disabled=not measures,
              type='primary' if st.session_state.measure_action=='edit' else 'secondary',
              on_click=toggle,args=('edit',))
with c3:
    st.button('▣ Видалити',use_container_width=True,key='sm_delete_btn',disabled=not measures,
              type='primary' if st.session_state.measure_action=='delete' else 'secondary',
              on_click=toggle,args=('delete',))

if not risks:
    st.warning('Для додавання заходів спочатку створіть хоча б одну оцінку на сторінці «Оцінювання ризиків».')

if st.session_state.measure_action in ('add','edit') and risks:
    editing=st.session_state.measure_action=='edit'
    chosen=None
    if editing and measures:
        chosen=st.selectbox('Захід для редагування',measures,format_func=label_measure,key='sm_choose_edit')
    if not editing or chosen:
        initial_risk=chosen[1] if chosen else risks[0][0]
        index=next((i for i,r in enumerate(risks) if r[0]==initial_risk),0)
        with st.form('sm_edit_form' if editing else 'sm_add_form',clear_on_submit=not editing):
            risk=st.selectbox('Пов’язана оцінка ризику',risks,index=index,format_func=label_risk)
            name=st.text_input('Назва заходу *',value=chosen[2] if chosen else '',max_chars=180,
                               placeholder='Наприклад, багатофакторна автентифікація')
            description=st.text_area('Опис та призначення',value=chosen[3] or '' if chosen else '',
                                     placeholder='Опишіть, як саме захід впливає на обраний ризик')
            a,b,c=st.columns(3)
            with a:
                cost=st.number_input('Орієнтовна вартість (ум. од.)',min_value=0.0,
                                     value=float(chosen[4]) if chosen else 0.0,step=100.0,format='%.2f')
            with b:
                pr=st.number_input('Очікуване зниження P',min_value=0,max_value=4,
                                   value=int(chosen[5]) if chosen else 0,step=1)
            with c:
                ir=st.number_input('Очікуване зниження I',min_value=0,max_value=4,
                                   value=int(chosen[6]) if chosen else 0,step=1)
            st.caption('Оцінки зниження задаються експертно. Вони використовуватимуться для подальшого порівняння заходів і моделювання залишкового ризику.')
            submitted=st.form_submit_button('Зберегти зміни' if editing else 'Додати захід захисту',type='primary',use_container_width=True)
        if submitted:
            try:
                if editing:
                    ok=update_measure(chosen[0],risk[0],name,description,cost,int(pr),int(ir))
                    if not ok:
                        raise ValueError('Захід уже не існує.')
                else:
                    create_measure(risk[0],name,description,cost,int(pr),int(ir))
                st.session_state.sm_success_toast = (
                    'Зміни успішно збережено!' if editing
                    else 'Захід захисту успішно додано!'
                )
                st.session_state.measure_action=None
                st.rerun()
            except (ValueError,TypeError) as exc:
                st.error(str(exc))

if st.session_state.measure_action=='delete' and measures:
    selected=st.selectbox('Оберіть захід',measures,format_func=label_measure,key='sm_choose_delete')
    confirm=st.checkbox(f'Підтверджую видалення заходу №{selected[0]}',key='sm_confirm_delete')
    if st.button('Видалити захід',type='primary',disabled=not confirm,key='sm_delete_confirm'):
        if delete_measure(selected[0]):
            st.session_state.sm_success_toast = 'Захід захисту успішно видалено!'
            st.session_state.measure_action=None
            st.rerun()
        else:
            st.warning('Захід не знайдено.')

if 'sm_success_toast' in st.session_state:
    st.toast(st.session_state.pop('sm_success_toast'), icon=':material/check_circle:')

st.html('''<div class="sm-note"><strong>Призначення модуля</strong><span>Тут реєструються запропоновані заходи. Порівняння альтернатив, моделювання залишкового ризику та економічне обґрунтування виконуватимуться в окремих розділах системи.</span></div>''')
from components import render_footer
render_footer()
