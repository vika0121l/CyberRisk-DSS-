from html import escape
from io import BytesIO
import sqlite3
from threading import RLock

import streamlit as st
import pandas as pd
from database import initialize_database
from experiment_store import (initialize_experiments, risk_options, measures_for_risk,
                              add_experiment, all_experiments, tests_for_experiment,
                              connection as experiment_connection)

initialize_database()
initialize_experiments()

# Спільний футер використовується на інших сторінках проєкту.
from components import render_footer

# Дизайн сторінки — CyberRisk Professional.
# Розміщення обмежено основною частиною сторінки, бічне меню не змінюється.
st.html("""
<style>
/* Зберігаємо ширину та відступаємо від верхньої панелі Streamlit. */
[data-testid="stMainBlockContainer"] {
    width: 100% !important;
    max-width: none !important;
    padding: 2.85rem 1.25rem 1rem !important;
    min-height: 100dvh !important;
    box-sizing: border-box !important;
    display: flex !important;
    flex-direction: column !important;
}

/* Вертикальне компонування: футер опускається вниз, коли вміст короткий. */
[data-testid="stMainBlockContainer"] > div:has(> [data-testid="stVerticalBlock"]),
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"],
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] {
    display: flex !important;
    flex: 1 0 auto !important;
    flex-direction: column !important;
    min-height: 0;
}

/* Маркер перед спільним футером розтягує порожній простір над ним.
   Футер НЕ перекриває форми й залишається в кінці довгої сторінки. */
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:has(.exp-footer-anchor),
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] > div:has(.exp-footer-anchor) {
    margin-top: auto !important;
    margin-bottom: -.75rem;
}
.exp-footer-anchor { display: block; height: 0; }

/* Сітка, така сама за характером, як на інших сторінках. */
.stApp { background: #FFFFFF !important; }
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    background-image:
        linear-gradient(rgba(31, 91, 170, .045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(31, 91, 170, .045) 1px, transparent 1px),
        radial-gradient(circle at 80% 25%, rgba(42, 111, 207, .025), transparent 40%);
    background-size: 60px 60px, 60px 60px, 100% 100%;
    animation: cyberGridMove 35s linear infinite;
}
[data-testid="stMain"] { position: relative; z-index: 1; background: transparent !important; }
@keyframes cyberGridMove {
    from { background-position: 0 0, 0 0, center; }
    to   { background-position: 0 120px, 120px 0, center; }
}
@media (prefers-reduced-motion: reduce) {
    [data-testid="stAppViewContainer"]::before { animation: none !important; }
}

/* Верхній банер — ширший завдяки контейнеру вище, і ближче до верху. */
.exp-hero {
    background: linear-gradient(112deg, #122F5E 0%, #194680 58%, #2867B5 100%);
    border-radius: 16px;
    padding: 24px 30px;
    min-height: 150px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    color: white;
    position: relative;
    overflow: hidden;
    margin: 0 0 17px;
    box-sizing: border-box;
    width: 100%;
}
.exp-hero::after {
    content: "";
    position: absolute;
    width: 240px;
    height: 240px;
    right: -75px;
    top: -100px;
    border: 1px solid rgba(255,255,255,.14);
    border-radius: 50%;
    box-shadow: 0 0 0 38px rgba(255,255,255,.035), 0 0 0 80px rgba(255,255,255,.025);
}
.exp-hero-content { position: relative; z-index: 1; min-width: 0; }
.exp-hero-kicker {
    color: #B9D5F9;
    font-size: 11px;
    font-weight: 750;
    letter-spacing: 1.7px;
    margin-bottom: 12px;
}
.exp-hero h1 {
    color: #FFFFFF !important;
    font-size: clamp(27px, 2.6vw, 38px);
    font-weight: 750;
    margin: 0 0 10px !important;
    line-height: 1.2;
}
.exp-hero p { color: #D9E8FB; font-size: 14px; margin: 0; line-height: 1.6; }
.exp-hero-symbol {
    position: relative;
    z-index: 1;
    width: 80px;
    height: 80px;
    min-width: 80px;
    border-radius: 21px;
    background: rgba(255,255,255,.11);
    border: 1px solid rgba(255,255,255,.22);
    display: flex;
    align-items: center;
    justify-content: center;
}
.exp-hero-symbol img { display: block; width: 47px; height: 47px; }

/* Відступи спільного футера: лінія та текст по центру, внизу. */
.dash-footer { margin: 16px auto 0 !important; padding: 20px 12px 12px !important; width: 100%; }

/* Кнопка збереження у стилі інших модулів. */
div.stButton > button[kind="primary"],
div.stFormSubmitButton > button[kind="primary"] {
    background: #1b467d;
    border-color: #1b467d;
}
@media (max-width: 720px) {
    [data-testid="stMainBlockContainer"] { padding: 4.35rem .8rem 1rem !important; }
    .exp-hero { padding: 22px 20px; min-height: 128px; }
    .exp-hero h1 { font-size: 25px !important; }
    .exp-hero-symbol { width: 60px; height: 60px; min-width: 60px; }
    .exp-hero-symbol img { width: 35px; height: 35px; }
}
/* Картки та поля тільки на сторінці експериментів. */
.st-key-exp_protocol,
.st-key-exp_archive {
    min-width: 0;
}
.st-key-exp_setup,
.st-key-exp_checks,
.st-key-exp_summary,
.st-key-exp_archive {
    border: 1.5px solid #b4cdee !important;
    border-radius: 12px !important;
    background: linear-gradient(180deg, #f5f9ff 0, #fff 80px) !important;
    box-shadow: 0 3px 10px rgba(24, 72, 135, .055);
    padding: 15px 17px !important;
}
.exp-section-head {
    display: flex;
    align-items: center;
    gap: 9px;
    color: #173254;
}
.exp-section-head h2 {
    color: inherit !important;
    font-size: 1.08rem !important;
    line-height: 1.3 !important;
    margin: 0 !important;
    padding: 0 !important;
}
.exp-step {
    display: grid;
    place-items: center;
    flex: 0 0 29px;
    height: 29px;
    border-radius: 8px;
    background: #dce9fb;
    color: #214f89;
    font-size: .75rem;
    font-weight: 750;
}
.exp-note {
    display: flex;
    align-items: center;
    gap: 9px;
    border: 1px solid #d7e7fa;
    border-radius: 9px;
    padding: 9px 12px;
    background: #ecf4ff;
    color: #2d537f;
    font-size: .85rem;
}
.exp-info-mark {
    display: grid;
    place-items: center;
    width: 17px;
    height: 17px;
    flex: none;
    border: 1px solid currentColor;
    border-radius: 50%;
    font-size: .72rem;
    font-weight: 750;
}
.st-key-exp_protocol :is([data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div) {
    background: #f6f9fe;
    border-color: #cbdcf2;
    border-radius: 8px;
}
.st-key-exp_protocol [data-testid="stWidgetLabel"] p {
    color: #2d4a6c;
    font-size: .85rem;
    font-weight: 600;
}
.st-key-exp_setup [data-testid="stVerticalBlock"],
.st-key-exp_summary [data-testid="stVerticalBlock"],
.st-key-exp_checks [data-testid="stVerticalBlock"] { gap: .65rem; }
.st-key-exp_phase_before,
.st-key-exp_phase_after {
    border: 1px solid #bfd4ef !important;
    border-radius: 9px !important;
    background: #fff !important;
    padding: 10px 12px !important;
    overflow-wrap: anywhere;
}
.exp-phase-title {
    background: linear-gradient(90deg, #f2f7fe, #f7faff);
    border-bottom: 1px solid #cbdcf2;
    color: #224c7e;
    font-weight: 750;
    font-size: .88rem;
    margin: -10px -12px 1px;
    padding: 8px 12px;
    border-radius: 8px 8px 0 0;
}
.exp-case-name { font-size: .88rem; font-weight: 650; color: #173254; }
.exp-expected { font-size: .79rem; margin-top: 2px; color: #506987; }
.st-key-exp_checks [data-testid="stExpander"] details {
    background: #f7faff;
    border-color: #d8e5f4;
}
.st-key-exp_summary [data-testid="stButton"] {
    display: flex;
    justify-content: flex-end;
}
.st-key-exp_summary [data-testid="stButton"] button {
    background: #1f56a0 !important;
    color: #fff !important;
    border: 1px solid #1f56a0 !important;
    border-radius: 8px;
    font-weight: 700;
}
.st-key-exp_summary [data-testid="stButton"] button:hover {
    background: #184783 !important;
}
.st-key-exp_summary [data-testid="stButton"] button:focus-visible {
    outline: 2px solid #397ccc;
    outline-offset: 2px;
}
/* Повідомлення про успішне збереження у спільному стилі CyberRisk DSS. */
div[data-testid="stToast"] {
    background: #e8f7ee !important;
    border: 1px solid #a7e3bb !important;
    border-left: 4px solid #16a34a !important;
    border-radius: 11px !important;
    color: #166534 !important;
    box-shadow: 0 5px 17px rgba(22,163,74,.12) !important;
}
div[data-testid="stToast"] * { color: #166534 !important; }

/* Таблиці архіву залишаються всередині картки, довгі тексти переносяться. */
.st-key-exp_archive { box-sizing: border-box; }
.st-key-exp_archive .exp-table-wrap {
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
    overflow-x: auto;
    border: 1px solid #d8e5f4;
    border-radius: 8px;
    background: #fff;
}
.st-key-exp_archive .exp-table {
    width: 100%;
    min-width: 34rem;
    table-layout: fixed;
    border-collapse: collapse;
    border: 0;
    margin: 0;
    font-size: .82rem;
    color: #193758;
}
.st-key-exp_archive .exp-table :is(th, td) {
    border: 0;
    border-bottom: 1px solid #e1eaf5;
    padding: 8px;
    text-align: left;
    vertical-align: top;
    white-space: normal;
    overflow-wrap: anywhere;
}
.st-key-exp_archive .exp-table th { background: #eaf2fc; font-weight: 700; }
.st-key-exp_archive .exp-table tbody tr:last-child td { border-bottom: 0; }
.st-key-exp_archive .exp-index-table th:nth-child(1) { width: 5%; }
.st-key-exp_archive .exp-index-table th:nth-child(2) { width: 16%; }
.st-key-exp_archive .exp-index-table th:nth-child(3) { width: 37%; }
.st-key-exp_archive .exp-index-table th:nth-child(4) { width: 7%; }
.st-key-exp_archive .exp-index-table th:nth-child(5) { width: 25%; }
.st-key-exp_archive .exp-index-table th:nth-child(6) { width: 10%; }
.st-key-exp_archive .exp-index-table :is(th, td):nth-child(1),
.st-key-exp_archive .exp-index-table :is(th, td):nth-child(4) {
    text-align: center;
    vertical-align: middle;
}
.st-key-exp_archive .exp-results-table th:nth-child(4) { width: 8%; }
.st-key-exp_archive .exp-results-table th:nth-child(7) { width: 24%; }
.st-key-exp_actions {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: wrap !important;
    gap: .6rem !important;
}
.st-key-exp_actions > * { flex: 0 0 auto !important; width: auto !important; }
.st-key-exp_actions > :is(.st-key-exp_delete_request, :has(.st-key-exp_delete_request)) {
    margin-inline-start: auto;
}
.st-key-exp_delete_panel {
    background: #f3f7fe;
    border: 1px solid #c5d8f3;
    border-radius: 10px;
    padding: 12px 15px;
}
.exp-delete-summary { margin: 0; color: #173254; overflow-wrap: anywhere; }
.exp-delete-summary small { color: #506987; }
.st-key-exp_delete_controls {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: wrap !important;
    justify-content: flex-end !important;
    gap: .6rem !important;
}
.st-key-exp_delete_controls > * { flex: 0 0 auto !important; width: auto !important; }
.st-key-exp_archive .exp-table-wrap:focus-visible,
:is(.st-key-exp_export, .st-key-exp_export_pdf, .st-key-exp_delete_request,
    .st-key-exp_delete_controls) button:focus-visible {
    outline: 2px solid #397ccc;
    outline-offset: 2px;
}
:is(.st-key-exp_export, .st-key-exp_export_pdf, .st-key-exp_delete_request) button,
.st-key-exp_delete_controls button[kind="primary"] {
    background: #1f56a0 !important;
    color: #fff !important;
    border: 1px solid #1f56a0 !important;
    border-radius: 8px;
    font-weight: 700;
}
:is(.st-key-exp_export, .st-key-exp_export_pdf, .st-key-exp_delete_request) button:hover,
.st-key-exp_delete_controls button[kind="primary"]:hover {
    background: #184783 !important;
}
.exp-archive-empty { margin: 0; font-size: .84rem; color: #506987; }
@media (max-width: 900px) {
    .st-key-exp_checks :is(.st-key-exp_phase_before, .st-key-exp_phase_after)
        [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
    .st-key-exp_checks :is(.st-key-exp_phase_before, .st-key-exp_phase_after)
        [data-testid="stColumn"] { flex: 1 1 135px !important; min-width: 0 !important; }
}
@media (max-width: 680px) {
    .st-key-exp_actions > :is(.st-key-exp_delete_request, :has(.st-key-exp_delete_request)) {
        margin-inline-start: 0;
    }
    .st-key-exp_setup, .st-key-exp_checks, .st-key-exp_summary,
    .st-key-exp_archive { padding: 12px !important; }
    :is(.st-key-exp_checks, .st-key-exp_setup) [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
    :is(.st-key-exp_checks, .st-key-exp_setup) [data-testid="stColumn"] {
        flex: 1 1 100% !important;
        min-width: 0 !important;
    }
}
</style>
""")

# Символ колби відображає саме експериментальне дослідження, а не загальний захист.
st.html("""
<div class="exp-hero">
  <div class="exp-hero-content">
    <div class="exp-hero-kicker">CYBERRISK DSS / РЕЗУЛЬТАТИ ДОСЛІДЖЕННЯ</div>
    <h1>Експериментальне дослідження</h1>
    <p>Протоколи перевірки заходів захисту в Cisco Packet Tracer</p>
  </div>
  <div class="exp-hero-symbol" role="img" aria-label="Лабораторна колба — експериментальне дослідження">
    <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIxLjgiCiAgICAgICAgIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIgYXJpYS1oaWRkZW49InRydWUiPgogICAgICA8cGF0aCBkPSJNOSAzaDYiLz4KICAgICAgPHBhdGggZD0iTTEwIDN2N2wtNi42IDkuM0EyIDIgMCAwIDAgNSAyMmgxNGEyIDIgMCAwIDAgMS42LTIuN0wxNCAxMFYzIi8+CiAgICAgIDxwYXRoIGQ9Ik03LjMgMTZoOS40Ii8+CiAgICAgIDxwYXRoIGQ9Ik0xMCAxOWguMDFNMTQgMTloLjAxIi8+CiAgICA8L3N2Zz4=" width="47" height="47" alt="">
  </div>
</div>
""")


BEFORE = "До заходу"
AFTER = "Після заходу"
AVAILABLE = "Доступний"
BLOCKED = "Заблокований"
UNTESTED = "Не перевірено"
ACL = "ACL — доступ до вебсервера"
PORT = "Port Security — сторонній пристрій"
CUSTOM = "Інший сценарій"

SCENARIOS = {
    ACL: {
        "title": "Перевірка ізоляції гостьової мережі",
        "hypothesis": "Після заходу внутрішній сайт доступний працівнику, але недоступний гостю.",
        "target": "Внутрішній вебсервер",
        "service": "HTTP",
        "sources": ("Гостьовий комп’ютер", "Комп’ютер працівника"),
    },
    PORT: {
        "title": "Перевірка захисту порту комутатора",
        "hypothesis": "Після заходу сторонній пристрій не має доступу, а дозволений може працювати.",
        "target": "Внутрішній ресурс",
        "service": "Доступ до мережевого сервісу",
        "sources": ("Сторонній пристрій", "Дозволений пристрій"),
    },
}


def section_title(number, title):
    st.html(
        f'<div class="exp-section-head"><span class="exp-step" aria-hidden="true">'
        f'{number}</span><h2>{escape(title)}</h2></div>'
    )


def phase_tests(phase, preset, prefix, phase_key):
    phase_code = "before" if phase == BEFORE else "after"
    rows = []
    with st.container(key=f"exp_phase_{phase_code}", border=False):
        st.html(f'<div class="exp-phase-title">{phase}</div>')
        for i in range(2):
            key = f"{prefix}_{phase_key}_{i}"
            expected = BLOCKED if phase == AFTER and i == 0 and preset else AVAILABLE
            default_source = preset["sources"][i] if preset else ""
            if i:
                st.divider()
            left, right = st.columns([1.15, 1], gap="small", vertical_alignment="center")
            with right:
                observed = st.selectbox(
                    "Фактично", [UNTESTED, AVAILABLE, BLOCKED], key=f"{key}_observed",
                )
            with st.expander(f"Деталі перевірки {i + 1}"):
                source = st.text_input("Джерело", value=default_source, key=f"{key}_source")
                target = st.text_input(
                    "Призначення", value=preset["target"] if preset else "", key=f"{key}_target",
                )
                service = st.text_input(
                    "Сервіс або спосіб перевірки", value=preset["service"] if preset else "",
                    key=f"{key}_service",
                )
                expected_options = [AVAILABLE, BLOCKED]
                expected_value = st.selectbox(
                    "Очікувано", expected_options, index=expected_options.index(expected),
                    key=f"{key}_expected",
                )
                notes = st.text_input("Примітка", key=f"{key}_notes")
            with left:
                label = source.strip() or default_source or f"Перевірка {i + 1}"
                st.html(f'<div class="exp-case-name">{escape(label)}</div>')
                st.html(f'<div class="exp-expected">Очікувано: {expected_value.lower()}</div>')
            rows.append({
                "phase": phase, "source": source.strip(), "target": target.strip(),
                "service": service.strip(), "expected": expected_value,
                "observed": observed, "notes": notes.strip(),
            })
    return rows


def validate_tests(rows, preset):
    tests = []
    for row in rows:
        fields = (row["source"], row["target"], row["service"])
        if not preset and not any(fields) and row["observed"] == UNTESTED and not row["notes"]:
            continue
        if not all(fields):
            raise ValueError("У деталях заповни джерело, призначення й сервіс для кожної внесеної перевірки.")
        if row["observed"] == UNTESTED:
            raise ValueError(
                "Заповни фактичний результат усіх чотирьох перевірок."
                if preset else "Заповни фактичний результат кожної внесеної перевірки."
            )
        tests.append(row)
    if not tests:
        raise ValueError("Додай хоча б одну проведену перевірку.")
    return tests


def render_protocol():
    risks = risk_options()
    if not risks:
        with st.container(key="exp_setup", border=False):
            section_title("01", "Налаштування протоколу")
            st.info("Спочатку додай актив, загрозу, вразливість і оціни ризик.")
        return

    risk_labels = {
        r["id"]: f'№{r["id"]} · {r["asset"]} · {r["threat"]} (R={r["risk_score"]})'
        for r in risks
    }
    with st.container(key="exp_protocol"):
        with st.container(key="exp_setup", border=False):
            section_title("01", "Налаштування протоколу")
            title_column, scenario_column = st.columns(2, gap="medium")
            scenario = scenario_column.selectbox(
                "Сценарій", [ACL, PORT, CUSTOM], key="exp_selected_scenario",
            )
            risk_column, measure_column = st.columns(2, gap="medium")
            risk_id = risk_column.selectbox(
                "Пов’язаний ризик", list(risk_labels), format_func=risk_labels.__getitem__,
                key="exp_selected_risk",
            )
            measures = measures_for_risk(risk_id)
            if not measures:
                measure_column.info("Для цього ризику спочатку додай захід на сторінці «Заходи захисту».")
                return
            measure_labels = {m["id"]: m["name"] for m in measures}
            measure_id = measure_column.selectbox(
                "Перевірюваний захід", list(measure_labels), format_func=measure_labels.__getitem__,
                key=f"exp_selected_measure_{risk_id}",
            )
            preset = SCENARIOS.get(scenario)
            generation = st.session_state.get("exp_form_generation", 0)
            prefix = f"exp_data_{generation}_{risk_id}_{measure_id}_{[ACL, PORT, CUSTOM].index(scenario)}"
            title_example = preset["title"] if preset else "Перевірка доступу до внутрішнього сервісу"
            hypothesis_example = preset["hypothesis"] if preset else "Після заходу сервіс доступний лише дозволеним пристроям."
            title = title_column.text_input(
                "Назва експерименту", placeholder=f"Наприклад — {title_example}",
                key=f"{prefix}_title",
            )
            file_column, hypothesis_column = st.columns(2, gap="medium")
            topology = file_column.text_input(
                "Файл моделі (.pkt)", placeholder="Наприклад, enterprise_after.pkt",
                key=f"{prefix}_file",
            )
            hypothesis = hypothesis_column.text_input(
                "Гіпотеза", placeholder=f"Наприклад — {hypothesis_example}",
                key=f"{prefix}_hypothesis",
            )
        with st.container(key="exp_checks", border=False):
            section_title("02", "Перевірки до й після заходу")
            if preset:
                st.caption("Фактичні результати заповнюй після перевірки. Джерело, сервіс і примітку можна уточнити в деталях.")
            else:
                st.caption("Відкрий деталі, щоб описати тест. Повністю порожні перевірки не зберігаються.")
            before_column, after_column = st.columns(2, gap="medium")
            with before_column:
                before = phase_tests(BEFORE, preset, prefix, "0")
            with after_column:
                after = phase_tests(AFTER, preset, prefix, "1")
        with st.container(key="exp_summary", border=False):
            section_title("03", "Висновок")
            conclusion = st.text_area(
                "Висновок експерименту", label_visibility="collapsed",
                placeholder="Що змінилося після заходу? Чи зберігся дозволений доступ?",
                height=80, key=f"{prefix}_conclusion",
            )
            submitted = st.button("Зберегти протокол", type="primary", key="exp_save")

        if submitted:
            try:
                tests = validate_tests(before + after, preset)
                exp_id = add_experiment(
                    title, scenario, risk_id, measure_id, topology,
                    hypothesis, conclusion, tests,
                )
            except ValueError as exc:
                st.error(str(exc))
            except sqlite3.Error:
                st.error("Не вдалося зберегти протокол у базі. Спробуй ще раз.")
            else:
                st.session_state["exp_saved_protocol"] = exp_id
                st.session_state["exp_form_generation"] = generation + 1
                st.rerun()


def render_archive_table(frame, label, table_class):
    table = frame.to_html(index=False, escape=True, border=0, classes=["exp-table", table_class])
    st.html(
        f'<div class="exp-table-wrap" role="region" aria-label="{escape(label)}" tabindex="0">'
        + table + '</div>'
    )


_EXP_PDF_LOCK = RLock()


@st.cache_data(show_spinner=False, max_entries=16)
def experiment_pdf(protocol, tests):
    """Створює PDF вибраного протоколу з вбудованим кириличним шрифтом."""
    from matplotlib import rc_context
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.figure import Figure
    from matplotlib.font_manager import FontProperties
    from matplotlib.patches import Rectangle
    from matplotlib.textpath import TextToPath

    page_width, page_height = 841.89, 595.28  # A4, альбомна орієнтація
    margin, bottom = 34, 54
    content_width = page_width - 2 * margin
    top = page_height - 104
    navy, body, muted, line_color = "#123d78", "#193758", "#496282", "#d8e5f4"
    tests_columns = [
        ("phase", "Етап", 0.10), ("source_device", "Джерело", 0.15),
        ("target_device", "Призначення", 0.16), ("service", "Сервіс", 0.09),
        ("expected", "Очікувано", 0.12), ("observed", "Фактично", 0.13),
        ("notes", "Примітка", 0.25),
    ]
    metrics = TextToPath()

    def wrap(value, width, size, weight="normal"):
        font = FontProperties(family="DejaVu Sans", size=size, weight=weight)
        def fits(text):
            return metrics.get_text_width_height_descent(text, font, False)[0] <= width

        lines = []
        for paragraph in str(value or "—").split("\n"):
            current = ""
            for word in paragraph.split():
                trial = f"{current} {word}" if current else word
                if fits(trial):
                    current = trial
                    continue
                if current:
                    lines.append(current)
                    current = ""
                for char in word:
                    if current and not fits(current + char):
                        lines.append(current)
                        current = ""
                    current += char
            lines.append(current)
        return lines

    stream = BytesIO()
    lock = getattr(Figure, "_render_lock", _EXP_PDF_LOCK)
    pdf_title = f"Протокол експерименту №{protocol['id']}"
    with lock, rc_context({"pdf.fonttype": 42, "font.family": "DejaVu Sans"}), PdfPages(
        stream, metadata={"Title": pdf_title, "Author": "CyberRisk DSS"},
    ) as pdf:
        page_no = 0
        fig, ax = None, None
        y = top

        def write(x, at, value, size=10, color=body, weight="normal", **kwargs):
            ax.text(x, at, value, fontsize=size, color=color, weight=weight,
                    va="top", parse_math=False, **kwargs)

        def new_page():
            nonlocal fig, ax, y, page_no
            if fig is not None:
                pdf.savefig(fig)
            page_no += 1
            fig = Figure(figsize=(page_width / 72, page_height / 72), facecolor="white")
            ax = fig.add_axes([0, 0, 1, 1])
            ax.set(xlim=(0, page_width), ylim=(0, page_height))
            ax.axis("off")
            ax.add_patch(Rectangle((0, page_height - 82), page_width, 82,
                                   facecolor=navy, edgecolor="none"))
            write(margin, page_height - 20, "CYBERRISK DSS / ЕКСПЕРИМЕНТАЛЬНЕ ДОСЛІДЖЕННЯ",
                  9, "#cfe2ff", "bold")
            write(margin, page_height - 39, pdf_title, 23, "white", "bold")
            ax.plot([margin, page_width - margin], [39, 39], color=line_color, linewidth=.7)
            write(margin, 29, "CyberRisk DSS  ·  Збережений протокол", 8, muted)
            write(page_width - margin, 29, f"Сторінка {page_no}", 8, muted, ha="right")
            y = top

        def paragraph(value, size=10, weight="normal", color=body, gap=6):
            nonlocal y
            step = size * 1.36
            for text_line in wrap(value, content_width, size, weight):
                if y - step < bottom:
                    new_page()
                write(margin, y, text_line, size, color, weight)
                y -= step
            y -= gap

        def heading(label):
            nonlocal y
            if y - 39 < bottom:
                new_page()
            y -= 5
            paragraph(label, 12, "bold", navy, gap=5)

        widths = [content_width * fraction for _, _, fraction in tests_columns]
        header = [[label] for _, label, _ in tests_columns]
        step, padding = 11.5, 6.0

        def draw_row(cells, height, background, is_header=False):
            nonlocal y
            x = margin
            for cell, width in zip(cells, widths):
                ax.add_patch(Rectangle((x, y - height), width, height,
                                       facecolor=background, edgecolor=line_color, linewidth=.55))
                for idx, text_line in enumerate(cell):
                    write(x + padding, y - padding - idx * step, text_line, 8.5,
                          navy if is_header else body, "bold" if is_header else "normal")
                x += width
            y -= height

        def table_heading():
            heading("Результати перевірок")
            draw_row(header, 25, "#e5effd", is_header=True)

        new_page()
        paragraph(protocol["title"], 17, "bold", navy, gap=10)
        paragraph(f"Сценарій: {protocol['scenario']}   ·   Ризик №{protocol['risk_id']}   ·   "
                  f"Дата: {protocol['created_at']}", color=muted)
        paragraph(f"Захід: {protocol['measure']}")
        paragraph(f"Файл моделі: {protocol['topology_file'] or 'Не вказано'}", gap=10)
        heading("Гіпотеза")
        paragraph(protocol["hypothesis"])
        heading("Висновок")
        paragraph(protocol["conclusion"] or "Не вказаний", gap=12)

        if y - 74 < bottom:
            new_page()
        table_heading()
        if not tests:
            paragraph("Збережених перевірок немає.", color=muted)
        for index, row in enumerate(tests):
            cells = [wrap(row.get(key), width - padding * 2, 8.5)
                     for (key, _, _), width in zip(tests_columns, widths)]
            count = max(map(len, cells))
            # Не залишаємо заголовок без результатів. Довгі примітки
            # продовжуємо на наступних сторінках без обрізання.
            fresh_capacity = int((top - 52 - bottom - padding * 2) // step)
            capacity = int((y - bottom - padding * 2) // step)
            if capacity < 1 or (index > 0 and capacity < count <= fresh_capacity):
                new_page()
                table_heading()
            offset = 0
            while offset < count:
                capacity = int((y - bottom - padding * 2) // step)
                take = min(capacity, count - offset)
                draw_row([cell[offset:offset + take] for cell in cells],
                         take * step + padding * 2, "#f6faff" if index % 2 else "white")
                offset += take
                if offset < count:
                    new_page()
                    table_heading()
        pdf.savefig(fig)
    return stream.getvalue()


def clear_pending_delete():
    st.session_state.pop("exp_pending_delete", None)


def delete_protocol(protocol_id):
    # Сховище вмикає зовнішні ключі: пов'язані перевірки видаляються каскадно.
    with experiment_connection() as con:
        return con.execute("DELETE FROM experiments WHERE id = ?", (protocol_id,)).rowcount == 1


def render_archive():
    with st.container(key="exp_archive", border=False):
        section_title("▤", "Збережені протоколи")
        experiments = all_experiments()
        if not experiments:
            clear_pending_delete()
            st.html('<p class="exp-archive-empty">Поки немає збережених протоколів.</p>')
            return
        render_archive_table(
            pd.DataFrame([
                {"№": e["id"], "Сценарій": e["scenario"], "Назва": e["title"],
                 "Ризик": e["risk_id"], "Захід": e["measure"], "Дата": e["created_at"]}
                for e in experiments
            ]),
            "Список збережених протоколів", "exp-index-table",
        )
        protocols = {e["id"]: e for e in experiments}
        selection_key = "exp_archive_selected"
        if st.session_state.get(selection_key) not in protocols:
            st.session_state.pop(selection_key, None)
        selected = st.selectbox(
            "Переглянути протокол", list(protocols),
            format_func=lambda value: f'№{value} — {protocols[value]["title"]}',
            key=selection_key, on_change=clear_pending_delete,
        )
        item = protocols[selected]
        st.text(f'Гіпотеза: {item["hypothesis"]}')
        st.text(f'Висновок: {item["conclusion"] or "Не вказаний"}')
        st.text(f'Файл моделі: {item["topology_file"] or "Не вказано"}')
        rows = tests_for_experiment(selected)
        df = pd.DataFrame(rows).rename(columns={
            "phase": "Етап", "source_device": "Джерело", "target_device": "Призначення",
            "service": "Сервіс", "expected": "Очікувано", "observed": "Фактично",
            "notes": "Примітка",
        })
        render_archive_table(df, "Результати перевірок вибраного протоколу", "exp-results-table")
        with st.container(key="exp_actions"):
            st.download_button(
                "Експорт протоколу CSV", df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"experiment_{selected}.csv", mime="text/csv",
                key="exp_export", type="primary",
            )
            st.download_button(
                "Експорт протоколу PDF", experiment_pdf(item, rows),
                file_name=f"experiment_{selected}.pdf", mime="application/pdf",
                key="exp_export_pdf", type="primary", on_click="ignore",
            )
            if st.button("Видалити протокол", icon=":material/delete_outline:",
                         type="primary", key="exp_delete_request"):
                st.session_state["exp_pending_delete"] = selected

        if st.session_state.get("exp_pending_delete") != selected:
            return
        with st.container(key="exp_delete_panel"):
            st.html(
                f'<p class="exp-delete-summary"><strong>Видалити протокол №{selected} '
                f'«{escape(item["title"])}»?</strong><br>'
                '<small>Результати його перевірок також буде видалено. '
                'Файл Cisco Packet Tracer (.pkt) залишиться без змін.</small></p>'
            )
            with st.container(key="exp_delete_controls"):
                st.button("Скасувати", key="exp_delete_cancel", on_click=clear_pending_delete)
                confirmed = st.button("Підтвердити видалення", type="primary",
                                      key=f"exp_delete_confirm_{selected}")
            if confirmed:
                try:
                    removed = delete_protocol(selected)
                except sqlite3.Error:
                    st.error("Не вдалося видалити протокол. Спробуй ще раз.")
                else:
                    clear_pending_delete()
                    if removed:
                        st.session_state["exp_deleted_protocol"] = selected
                    else:
                        st.session_state["exp_archive_notice"] = "Цей протокол уже видалено."
                    st.rerun()


st.html(
    '<div class="exp-note"><span class="exp-info-mark" aria-hidden="true">i</span>'
    '<span>Прогноз ризику й фактичні результати перевірок фіксуються окремо.</span></div>'
)
if (saved_id := st.session_state.pop("exp_saved_protocol", None)) is not None:
    st.toast(f"Протокол №{saved_id} успішно збережено", icon=":material/check_circle:")
if (deleted_id := st.session_state.pop("exp_deleted_protocol", None)) is not None:
    st.toast(f"Протокол №{deleted_id} видалено", icon=":material/check_circle:")
if (archive_notice := st.session_state.pop("exp_archive_notice", None)) is not None:
    st.info(archive_notice)

render_protocol()
render_archive()
st.html('<span class="exp-footer-anchor" aria-hidden="true"></span>')
render_footer()
