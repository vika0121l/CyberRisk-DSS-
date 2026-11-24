"""CyberRisk DSS — прогнозований залишковий ризик після одного заходу."""

from pathlib import Path
from html import escape
import base64

import streamlit as st

from database import initialize_database
from measure_repository import list_risks, list_measures
from risk_constraints import (
    LAST_COMPARED_RISK_KEY, amount, compare_options,
    initialize_risk_constraints, load_risk_constraints, score_of,
)


# ============================================================
# 1. ІНІЦІАЛІЗАЦІЯ ТА СТИЛІ
# ============================================================

initialize_database()
initialize_risk_constraints()

css = Path(__file__).resolve().parents[1] / "styles" / "residual.css"

if css.exists():
    st.html(
        "<style>"
        + css.read_text(encoding="utf-8")
        + "</style>"
    )


# Точкове перевизначення стилю четвертої картки (інші стилі без змін).
st.html("<style>" + '/* Тільки четверта KPI-картка: синій фон, динамічний колір рівня */\n.rr-kpis .rr-kpi.rr-level-card {\n    background: linear-gradient(110deg, #112f60 0%, #2463b5 100%) !important;\n    border: 1px solid #285ba0 !important;\n    box-shadow: 0 5px 15px rgba(19, 55, 111, 0.13);\n}\n.rr-kpis .rr-kpi.rr-level-card .rr-kpi-label {\n    color: #ffffff !important;\n}\n.rr-kpis .rr-kpi.rr-level-card strong {\n    color: var(--rr-level-color, #65E6A0) !important;\n}\n' + "</style>")

# Уточнене оформлення таблиці розрахунків (без зміни формул).
st.html("""<style>
.rr-panel.rr-calc table { width:100%; margin-top:18px; border-collapse:separate; border-spacing:0; font-size:14px; }
.rr-panel.rr-calc thead th { background:#dceafe !important; color:#103a79 !important; font-size:12px !important; font-weight:850 !important; padding:15px 10px !important; border-bottom:2px solid #b9d2f5; }
.rr-panel.rr-calc tbody td { padding:16px 10px !important; color:#123b77 !important; font-weight:750 !important; border-bottom:1px solid #d6e5f7 !important; }
.rr-panel.rr-calc tbody td:not(:first-child) { font-size:15px; font-weight:850 !important; }
.rr-panel.rr-calc tbody tr.rr-total td { background:#e8f2ff !important; font-weight:900 !important; border-top:1px solid #b8d1f5 !important; }
.rr-panel.rr-calc .rr-pill { display:inline-block; min-width:34px; text-align:center; font-size:13px; font-weight:850; }
.rr-panel.rr-calc .rr-equation { margin-top:12px !important; padding:9px 11px !important; min-height:0 !important; line-height:1.4 !important; font-size:clamp(10px, .82vw, 12px) !important; white-space:nowrap; overflow-x:auto; background:#edf5ff; border:1px solid #e2edfb; }
.rr-panel.rr-calc .rr-equation b { font-weight:900; color:#0f3c7c; }
</style>""")

# Узгоджені висоти двох рядів: верхній просторіший для великої діаграми,
# нижній компактніший, з однаковою висотою обох карток.
st.html("""<style>
/* Діаграма та таблиця: симетричні картки з більшим простором. */
.rr-panel.rr-graph, .rr-panel.rr-calc {
    height: 465px !important;
    min-height: 465px !important;
    box-sizing: border-box !important;
}
.rr-panel.rr-graph {
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
}
/* Збільшення діаграми, зокрема підписів і позначок, без зміни даних SVG. */
.rr-panel.rr-graph .rr-step-image {
    display: block !important;
    width: 112% !important;
    max-width: none !important;
    height: 335px !important;
    max-height: none !important;
    min-height: 0 !important;
    flex: 1 1 auto !important;
    object-fit: contain !important;
    margin: 4px 0 5px -6% !important;
}
.rr-panel.rr-graph .rr-chart-explain {
    flex: 0 0 auto !important;
    margin-top: auto !important;
}
/* Застарілі стилі внутрішньої картки перекрито нижче. */
.st-key-rr_accept_card {
    height: 282px !important;
    min-height: 282px !important;
    box-sizing: border-box !important;
    background: #fff !important;
    border: 1px solid #d3e3f8 !important;
    border-radius: 14px !important;
    padding: 18px 20px !important;
    box-shadow: 0 4px 14px #1b4c8210 !important;
    overflow: hidden !important;
}
.st-key-rr_accept_card .rr-accept-title {
    margin: 0 0 14px !important;
}
.st-key-rr_accept_card .rr-accept-result {
    box-sizing: border-box !important;
    margin-top: 10px !important;
    padding: 16px 18px !important;
    min-height: 0 !important;
    height: auto !important;
    max-height: none !important;
}
.st-key-rr_accept_card .rr-accept-result p {
    margin: 7px 0 0 !important;
    line-height: 1.45 !important;
}
.rr-conclusion {
    height: 282px !important;
    min-height: 282px !important;
    box-sizing: border-box !important;
    display: flex !important;
    flex-direction: column !important;
}
.rr-conclusion-body {
    flex: 1 1 auto !important;
    min-height: 0 !important;
    display: flex !important;
    align-items: center !important;
}
.rr-conclusion-body p {
    font-size: 14px !important;
    line-height: 1.6 !important;
    font-weight: 650 !important;
}
@media (max-width: 900px) {
    .rr-panel.rr-graph, .rr-panel.rr-calc,
    .rr-conclusion, .st-key-rr_accept_card {
        height: auto !important;
        min-height: 0 !important;
    }
    .rr-panel.rr-graph .rr-step-image {
        width: 100% !important;
        height: auto !important;
        margin-left: 0 !important;
        max-height: 360px !important;
    }
}
</style>""")

# Виправлення: єдина рамка на колонці Streamlit, а не на вкладеному контейнері.
# Так зникає подвійна рамка незалежно від внутрішньої DOM-обгортки Streamlit.
st.html("""<style>
/* Вимикаємо будь-яку рамку/тінь у внутрішньому контейнері. */
.st-key-rr_accept_card,
.st-key-rr_accept_card [data-testid="stVerticalBlockBorderWrapper"],
.st-key-rr_accept_card [data-testid="stVerticalBlockBorderWrapper"] > div {
    border: 0 !important;
    outline: none !important;
    box-shadow: none !important;
    background: transparent !important;
    border-radius: 0 !important;
}
.st-key-rr_accept_card {
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: visible !important;
}
/* Зовнішня колонка — єдина біла картка. */
div[data-testid="stColumn"]:has(.st-key-rr_accept_card) {
    box-sizing: border-box !important;
    border: 1px solid #d3e3f8 !important;
    background: #ffffff !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 14px #1b4c8210 !important;
    padding: 14px 22px 30px !important;
    min-height: 312px !important;
    height: 312px !important;
}
.st-key-rr_accept_card .rr-accept-title { margin: 0 0 18px !important; }
.st-key-rr_accept_card .rr-accept-result {
    margin-top: 16px !important;
    padding: 18px 20px !important;
    min-height: 105px !important;
    height: auto !important;
    border-radius: 12px !important;
    box-sizing: border-box !important;
}
.rr-conclusion {
    box-sizing: border-box !important;
    height: 312px !important;
    min-height: 312px !important;
    margin: 0 !important;
    display: flex !important;
    flex-direction: column !important;
}
.rr-conclusion-body { flex: 1 1 auto !important; min-height: 0 !important; }
@media (max-width: 900px) {
    div[data-testid="stColumn"]:has(.st-key-rr_accept_card), .rr-conclusion {
        height: auto !important;
        min-height: 0 !important;
    }
}
</style>""")

st.html("""<style>
.rr-selection-note {text-align:center; font-size:12px; color:#526d92;}
.rr-selection-note.is-recommended {color:#0b6830; font-weight:700;}
.rr-selection-note.is-manual {color:#8a4c17; font-weight:650;}
.rr-threshold-summary {
    border-radius:9px; background:#f1f6fd; padding:10px 14px;
    font-size:13px; color:#214578; line-height:1.35;
}
.rr-threshold-metrics {display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); margin:0; padding:0;}
.rr-threshold-metrics > div {min-width:0; padding-inline:12px;}
.rr-threshold-metrics > div:first-child {padding-inline-start:0;}
.rr-threshold-metrics > div + div {border-inline-start:1px solid #d4e1f4;}
.rr-threshold-metrics dt {color:#405d84; font-size:12px;}
.rr-threshold-metrics dd {margin:2px 0 0; font-size:16px; font-weight:750; font-variant-numeric:tabular-nums;}
.rr-threshold-source {display:block; margin-top:7px; color:#526d92; font-size:12px;}
.rr-accept-result.at-limit {background:#fff3d4; color:#714504;}
.rr-accept-result.rejected {background:#fdebec; color:#982633;}
.rr-accept-result.not-assessed {background:#f1f6fd; color:#214578;}
.rr-conclusion-body.at-limit > span {background:#ffe6a4; color:#714504;}
.rr-conclusion-body.rejected > span {background:#fbdde1; color:#982633;}
.rr-conclusion-body.not-assessed > span {background:#d5e6fc; color:#214578;}
.rr-conclusion-verdict {
    display:inline-block; margin:0 0 7px; padding:3px 9px; border-radius:6px;
    background:#daf2e4; color:#0b6830; font-size:12px; font-weight:750;
}
.rr-conclusion-body.at-limit .rr-conclusion-verdict {background:#ffe6a4; color:#714504;}
.rr-conclusion-body.rejected .rr-conclusion-verdict {background:#fbdde1; color:#982633;}
.rr-conclusion-body.not-assessed .rr-conclusion-verdict {background:#d5e6fc; color:#214578;}
@media (max-width: 640px) {
    [data-testid="stHorizontalBlock"]:has(.rr-accept-title):has(.rr-conclusion) {
        flex-wrap:wrap !important;
    }
    [data-testid="stHorizontalBlock"]:has(.rr-accept-title):has(.rr-conclusion) > [data-testid="stColumn"] {
        flex:1 1 100% !important;
        width:100% !important;
    }
    .rr-threshold-metrics > div {padding-inline:6px;}
    .rr-threshold-metrics dt, .rr-threshold-metrics dd {overflow-wrap:anywhere;}
    .rr-threshold-metrics dd {font-size:14px;}
}
</style>""")


def e(value):
    """Безпечне відображення тексту в HTML."""
    return escape(str(value), quote=True)


def level(value):
    """Визначення рівня кіберризику."""
    if value <= 4:
        return "Дуже низький"
    if value <= 9:
        return "Низький"
    if value <= 14:
        return "Середній"
    if value <= 19:
        return "Високий"
    return "Критичний"


def level_css(value):
    if value <= 9:
        return "ok"
    if value <= 14:
        return "mid"
    return "bad"


def signed_change(value):
    """Форматування зміни показника."""
    if value < 0:
        return f"−{abs(value)}"
    if value > 0:
        return f"+{value}"
    return "0"


def change_class(value):
    """Колір зміни показника."""
    return "rr-pill" if value < 0 else "rr-pill neutral"


# ============================================================
# 2. ВЕРХНІЙ БАНЕР
# ============================================================

shield = """
<svg xmlns="http://www.w3.org/2000/svg"
     width="52" height="52" viewBox="0 0 52 52" fill="none">
    <path d="M26 4 43 10v14c0 12-7 19-17 24
             C16 43 9 36 9 24V10L26 4Z"
          stroke="white" stroke-width="2.5"/>
    <path d="M18 18h16M18 24h11M18 30h6"
          stroke="white" stroke-width="2.6"
          stroke-linecap="round"/>
    <path d="m29 28 5 5 7-9"
          stroke="#8EE9D0" stroke-width="3"
          stroke-linecap="round"
          stroke-linejoin="round"/>
</svg>
"""

icon = base64.b64encode(shield.encode("utf-8")).decode("ascii")

st.html(
    f"""
    <div class="rr-hero">
        <div>
            <div class="rr-eyebrow">
                CYBERRISK DSS / УПРАВЛІННЯ РИЗИКАМИ
            </div>
            <h1>Залишковий ризик</h1>
            <p>
                Оцінка прогнозованого рівня ризику після
                застосування обраного заходу захисту
                та перевірка його прийнятності
            </p>
        </div>
        <div class="rr-hero-icon">
            <img src="data:image/svg+xml;base64,{icon}"
                 alt="Захист"/>
        </div>
    </div>
    """
)


# ============================================================
# 3. ОТРИМАННЯ ДАНИХ
# ============================================================

risks = list_risks()

if not risks:
    st.info(
        "Спочатку додайте оцінку на сторінці "
        "«Оцінювання ризиків»."
    )
    st.stop()

all_measures = list_measures()


# ============================================================
# 4. ВИБІР РИЗИКУ ТА ЗАХОДУ ЗАХИСТУ
# ============================================================

last_risk_id = st.session_state.get(LAST_COMPARED_RISK_KEY)
default_risk_index = next((i for i, risk in enumerate(risks) if int(risk[0]) == last_risk_id), 0)

left, right = st.columns(2, gap="medium")
with left:
    with st.container(key="rr_selector_risk", border=False):
        st.html('<div class="rr-field-title">Виберіть ризик для оцінки</div>')
        selected = st.selectbox(
            "Ризик",
            risks,
            index=default_risk_index,
            format_func=lambda r: f"№{r[0]} — {r[1]} · {r[2]} · R={r[6]}/25",
            label_visibility="collapsed",
            key=f"rr_risk_from_{last_risk_id}",
        )
        st.html('<div class="rr-selection-note">Оцінка для одного ризику</div>')

risk_id = int(selected[0])
p0, i0, r0 = map(int, selected[4:7])
budget, threshold = load_risk_constraints(risk_id)
options = [score_of(m) for m in all_measures if int(m[1]) == risk_id]
_, _, recommended = compare_options(options, r0, budget, threshold)
recommended_id = int(recommended["row"][0]) if recommended is not None else None
options_by_id = {int(item["row"][0]): item for item in options}
measure_ids = list(options_by_id)

with right:
    with st.container(key="rr_selector_measure", border=False):
        st.html('<div class="rr-field-title">Захід захисту</div>')
        measure_id = st.selectbox(
            "Захід",
            measure_ids,
            index=measure_ids.index(recommended_id) if recommended_id is not None else None,
            format_func=lambda mid: str(options_by_id[mid]["row"][2]),
            disabled=not measure_ids,
            placeholder="Виберіть захід для ручного аналізу" if measure_ids else "Немає заходів для цього ризику",
            label_visibility="collapsed",
            key=f"rr_measure_for_{risk_id}_{recommended_id}",
        )
        if measure_id is not None and measure_id == recommended_id:
            note = "Рекомендовано в розділі «Порівняння заходів»"
            note_class = "is-recommended"
        elif measure_id is not None:
            note = "Ручний перегляд альтернативи"
            note_class = "is-manual"
        else:
            note = "Немає рекомендованого заходу"
            note_class = ""
        st.html(f'<div class="rr-selection-note {note_class}">{note}</div>')

if measure_id is None:
    if not options:
        st.info("Додайте захід для обраного ризику на сторінці «Заходи захисту».")
    else:
        st.info(
            "Немає заходу, що знижує ризик і відповідає всім заданим обмеженням. "
            "Оберіть альтернативу, щоб переглянути її прогноз окремо."
        )
    st.stop()


# ============================================================
# 5. РОЗРАХУНОК ЗАЛИШКОВОГО РИЗИКУ
# ============================================================

forecast = options_by_id[measure_id]
measure = forecast["row"]
dp = max(0, int(measure[5]))
di = max(0, int(measure[6]))
p1, i1, r1 = (forecast[key] for key in ("p", "i", "r"))
r_intermediate = p1 * i0
reduction = forecast["delta"]
pct = forecast["percent"]
over_budget = budget is not None and forecast["cost"] > budget

# Фактичні зміни з урахуванням нижньої межі
p_change = p1 - p0
i_change = i1 - i0
r_change = r1 - r0


# ============================================================
# 6. ЧОТИРИ ІНФОРМАЦІЙНІ КАРТКИ
# ============================================================

cards = [
    (
        "Початковий ризик (R)",
        f"{r0}/25",
        "orange"
    ),
    (
        "Прогнозований залишковий ризик (R′)",
        f"{r1}/25",
        "blue"
    ),
    (
        "Зниження ризику",
        f"{pct:.1f}%".replace(".", ","),
        "green"
    ),
    (
        "Рівень ризику після заходу",
        level(r1),
        "green" if r1 <= 9 else "orange"
    ),
]

# Колір напису залежить від прогнозованого рівня ризику.
def risk_text_color(value):
    if value <= 9:
        return "#65E6A0"  # Дуже низький / низький
    if value <= 14:
        return "#FFE082"  # Середній
    if value <= 19:
        return "#FFB347"  # Високий
    return "#FF626B"      # Критичний


cards_html = ""
for index, (title, value, color) in enumerate(cards):
    # Лише четверта картка отримує темно-синій фон.
    extra_class = " rr-level-card" if index == 3 else ""
    text_style = (
        f' style="--rr-level-color: {risk_text_color(r1)};"'
        if index == 3 else ""
    )
    cards_html += (
        f'<div class="rr-kpi {color}{extra_class}"{text_style}>'
        '<div class="rr-kpi-content">'
        f'<div class="rr-kpi-label">{e(title)}</div>'
        f'<strong>{e(value)}</strong>'
        '</div></div>'
    )

st.html('<div class="rr-kpis">' + cards_html + '</div>')

# ============================================================
# 7. СТУПІНЧАСТА ДІАГРАМА
# ============================================================

# Чотири стани:
# 1. Початковий ризик
# 2. Після зміни ймовірності
# 3. Після зміни впливу
# 4. Підсумковий залишковий ризик

values = [
    r0,
    r_intermediate,
    r1,
    r1
]

xs = [90, 250, 410, 570]

ys = [
    236 - value / 25 * 188
    for value in values
]

# Побудова ступінчастої лінії
path = f"M {xs[0]} {ys[0]:.1f}"

for j in range(1, 4):
    mid = (xs[j - 1] + xs[j]) / 2

    path += (
        f" H {mid:.1f}"
        f" V {ys[j]:.1f}"
        f" H {xs[j]}"
    )

# Горизонтальна шкала
lines = "".join(
    f"""
    <line x1="70"
          y1="{236 - v / 25 * 188:.1f}"
          x2="620"
          y2="{236 - v / 25 * 188:.1f}"
          stroke="#dbe6f5"
          stroke-dasharray="3 4"/>
    <text x="51"
          y="{241 - v / 25 * 188:.1f}"
          text-anchor="end"
          font-size="12"
          fill="#506c94">{v}</text>
    """
    for v in [0, 5, 10, 15, 20, 25]
)

# Точки на графіку
dots = ""

for j, (x, y) in enumerate(zip(xs, ys)):
    if j == 0:
        color = "#f97316"
    elif j == 3:
        color = "#16a34a"
    else:
        color = "#2878e6"

    risk_symbol = "R′" if j == 3 else "R"

    dots += f"""
    <circle cx="{x}"
            cy="{y:.1f}"
            r="7"
            fill="{color}"
            stroke="white"
            stroke-width="3"/>
    <text x="{x}"
          y="{y - 17:.1f}"
          text-anchor="middle"
          font-size="14"
          font-weight="800"
          fill="#153d7b">
        {risk_symbol} = {values[j]}
    </text>
    """

labels = [
    ("Початковий", "ризик (R)"),
    ("Після зміни", "ймовірності"),
    ("Після зміни", "впливу"),
    ("Залишковий", "ризик (R′)")
]

xlabels = "".join(
    f"""
    <text x="{x}"
          y="270"
          text-anchor="middle"
          font-size="12"
          font-weight="650"
          fill="#173b73">
        <tspan x="{x}">{e(line1)}</tspan>
        <tspan x="{x}" dy="16">{e(line2)}</tspan>
    </text>
    """
    for x, (line1, line2) in zip(xs, labels)
)

svg = f"""
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 650 312"
     role="img"
     aria-label="Ступінчаста діаграма ризику від {r0} до {r1}">
    <text x="39" y="28"
          font-size="12"
          fill="#6883a4">
        Рівень ризику (R)
    </text>

    {lines}

    <path d="{path}"
          fill="none"
          stroke="#2674e5"
          stroke-width="4"
          stroke-linejoin="round"
          stroke-linecap="round"/>

    {dots}
    {xlabels}
</svg>
"""

chart_img = (
    "data:image/svg+xml;base64,"
    + base64.b64encode(
        svg.encode("utf-8")
    ).decode("ascii")
)


# ============================================================
# 8. ДІАГРАМА ТА ТАБЛИЦЯ РОЗРАХУНКІВ
# ============================================================

a, b = st.columns(2, gap="medium")

with a:
    if di == 0:
        explanation = (
            "Вплив не змінюється (ΔI = 0), "
            "тому після другого етапу ризик "
            f"залишається на рівні {r1}/25."
        )
    else:
        explanation = (
            "Зміна ймовірності та впливу "
            "врахована послідовно; "
            f"підсумковий прогноз — {r1}/25."
        )

    st.html(
        f"""
        <div class="rr-panel rr-graph">
            <h3>
                <span>▥</span>
                Етапи розрахунку залишкового ризику
            </h3>
            <p>
                Послідовна зміна оцінки ризику
                за параметрами P та I
            </p>

            <img class="rr-step-image"
                 src="{chart_img}"
                 alt="Ступінчаста діаграма залишкового ризику"/>

            <div class="rr-chart-explain">
                <span class="rr-chart-dot"></span>
                {e(explanation)}
            </div>
        </div>
        """
    )

with b:
    st.html(
        f"""
        <div class="rr-panel rr-calc">
            <h3>
                <span>▤</span>
                Розрахунок залишкового ризику
            </h3>

            <table>
                <thead>
                    <tr>
                        <th>Показник</th>
                        <th>Початкове значення</th>
                        <th>Після заходу</th>
                        <th>Зміна</th>
                    </tr>
                </thead>

                <tbody>
                    <tr>
                        <td>Ймовірність (P)</td>
                        <td>{p0}</td>
                        <td>{p1}</td>
                        <td>
                            <b class="{change_class(p_change)}">
                                {signed_change(p_change)}
                            </b>
                        </td>
                    </tr>

                    <tr>
                        <td>Вплив (I)</td>
                        <td>{i0}</td>
                        <td>{i1}</td>
                        <td>
                            <b class="{change_class(i_change)}">
                                {signed_change(i_change)}
                            </b>
                        </td>
                    </tr>

                    <tr class="rr-total">
                        <td>Ризик (R = P × I)</td>
                        <td>{r0}</td>
                        <td>{r1}</td>
                        <td>
                            <b class="{change_class(r_change)}">
                                {signed_change(r_change)}
                            </b>
                        </td>
                    </tr>
                </tbody>
            </table>

            <div class="rr-equation">
                ⓘ &nbsp;
                Прогноз:
                P′ = max(1, {p0} − {dp}) = {p1};
                I′ = max(1, {i0} − {di}) = {i1}; R′ = {p1} × {i1} = <b>{r1}</b>.
            </div>
        </div>
        """
    )


# ============================================================
# 9. ПЕРЕВІРКА ПОРОГУ ПРИЙНЯТНОСТІ
# ============================================================

threshold_label = f"≤ {threshold}/25" if threshold is not None else "Не задано"
margin = threshold - r1 if threshold is not None else None
margin_name = "Перевищення" if margin is not None and margin < 0 else "Запас"
margin_value = "—"
if margin is not None:
    n = abs(margin)
    unit = "бал" if n % 10 == 1 and n % 100 != 11 else (
        "бали" if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else "балів"
    )
    margin_value = f"{n} {unit}"

if threshold is None:
    status_class = "not-assessed"
    status_title = "Поріг не задано"
    verdict = "Не оцінено"
    assessment = "Збережіть поріг для цього ризику в розділі «Заходи захисту», щоб оцінити прийнятність прогнозу."
    decision = "Поріг для цього ризику не задано, тому прийнятність прогнозу не оцінено."
elif margin == 0:
    status_class = "at-limit"
    status_title = "На межі прийнятності"
    verdict = "На межі"
    assessment = "Прогноз дорівнює встановленому порогу. Він допустимий, але без запасу."
    decision = f"Прогноз відповідає порогу {threshold}/25 без запасу."
elif margin > 0:
    status_class = "accepted"
    status_title = "Прогноз нижче порогу"
    verdict = "Нижче порогу"
    assessment = "Прогнозований залишковий ризик відповідає порогу із запасом."
    decision = f"Прогнозований ризик нижчий за поріг {threshold}/25."
else:
    status_class = "rejected"
    status_title = "Прогноз перевищує поріг"
    verdict = "Понад поріг"
    assessment = "Прогнозований залишковий ризик не відповідає встановленому порогу."
    decision = f"Прогнозований ризик {r1}/25 перевищує поріг {threshold}/25. Розгляньте інший захід."

if over_budget:
    overage = amount(forecast["cost"] - budget)
    decision += f" Захід перевищує збережений бюджет на {overage} ум. од. і не є рекомендацією системи."

c, d = st.columns(2, gap="medium")

with c:
    with st.container(key="rr_accept_card", border=False):
        st.html(
            f"""
            <div class="rr-accept-title">◎ &nbsp; Перевірка порогу прийнятності</div>
            <div class="rr-threshold-summary">
                <dl class="rr-threshold-metrics">
                    <div><dt>Прогноз</dt><dd>{r1}/25</dd></div>
                    <div><dt>Поріг</dt><dd>{e(threshold_label)}</dd></div>
                    <div><dt>{margin_name}</dt><dd>{margin_value}</dd></div>
                </dl>
                <small class="rr-threshold-source">Джерело порогу — «Заходи захисту»</small>
            </div>
            <div class="rr-accept-result {status_class}" role="status">
                <strong>{status_title}</strong>
                <p>{assessment}</p>
            </div>
            """
        )

# ============================================================
# 10. АВТОМАТИЧНИЙ ВИСНОВОК СИСТЕМИ
# ============================================================

with d:
    measure_name = str(measure[2])
    effect = (
        f"за прогнозом знижує ризик з {r0}/25 до {r1}/25 "
        f"на {reduction} балів ({pct:.1f}%)."
        if reduction else f"за прогнозом не знижує ризик ({r0}/25 → {r1}/25)."
    )
    conclusion = (
        f"Для ризику №{risk_id} захід «{measure_name}» {effect} "
        f"Ймовірність {p0} → {p1}, вплив {i0} → {i1}. "
        f"{decision} Після впровадження перевірте результат повторно."
    )
    conclusion_status = "rejected" if over_budget else status_class
    conclusion_verdict = "Понад бюджет" if over_budget else verdict
    conclusion_icon = {
        "accepted": "✓", "at-limit": "=", "rejected": "!", "not-assessed": "ⓘ",
    }[conclusion_status]

    st.html(
        f"""
        <div class="rr-conclusion">
            <h3>◎ &nbsp; Висновок системи</h3>
            <div class="rr-conclusion-body {conclusion_status}">
                <span aria-hidden="true">{conclusion_icon}</span>
                <div>
                    <strong class="rr-conclusion-verdict">{e(conclusion_verdict)}</strong>
                    <p>{e(conclusion)}</p>
                </div>
            </div>
        </div>
        """
    )


# ============================================================
# 11. ОБМЕЖЕННЯ П'ЯТИБАЛЬНОЇ ШКАЛИ
# ============================================================

if dp > p0 - 1 or di > i0 - 1:
    st.html(
        """
        <div class="rr-caveat">
            <b>
                ⓘ Особливість п’ятибальної шкали.
            </b>

            Значення P′ та I′ не можуть бути
            нижчими за 1. Частина експертно
            оціненого зниження обмежується
            нижньою межею шкали, тому різні
            заходи можуть мати однаковий
            прогнозований результат.
        </div>
        """
    )


# ============================================================
# 12. ПРИМІТКА ТА ПІДВАЛ СТОРІНКИ
# ============================================================

st.caption(
    "Результат є прогнозом для одного обраного заходу, "
    "а не підтвердженням його фактичної ефективності. "
    "Збережений поріг застосовується лише до прогнозу для вибраного ризику. "
    "Поєднання кількох заходів тут не моделюється."
)

try:
    from components import render_footer
    render_footer()
except ImportError:
    pass
