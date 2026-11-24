"""CyberRisk DSS — порівняння альтернативних заходів захисту."""
from pathlib import Path
from html import escape
import base64
import streamlit as st
from database import initialize_database
from measure_repository import list_measures, list_risks
from risk_constraints import (
    LAST_COMPARED_RISK_KEY, amount, compare_options, decision_key,
    initialize_risk_constraints, load_risk_constraints, score_of,
)

initialize_database()
initialize_risk_constraints()
css_file = Path(__file__).resolve().parents[1] / "styles" / "comparison.css"
if css_file.exists():
    st.html(f"<style>{css_file.read_text(encoding='utf-8')}</style>")

# Спільна сітка вирівнює картки без залежності від обгорток Streamlit.
st.html("""<style>
.cmp-analysis-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 260px), 1fr));
    align-items: stretch;
    gap: 12px;
    margin-top: 20px;
}
.cmp-analysis-grid > :is(.cmp-chart-panel, .cmp-donut-panel, .cmp-recommend) {
    width: 100%;
    height: auto !important;
    min-width: 0;
    margin: 0;
}
.cmp-analysis-grid .cmp-recommend { padding-block: 16px !important; }
.cmp-analysis-grid .cmp-rec-head { margin-bottom: 10px !important; }
.cmp-analysis-grid .cmp-rec-selected { padding-block: 10px !important; }
.cmp-analysis-grid .cmp-rec-facts { margin: 14px 0 10px !important; }
.cmp-analysis-grid .cmp-donut-details { min-width: 0; }
.cmp-analysis-grid .cmp-donut-panel { container-type: inline-size; }
@container (max-width: 305px) {
    .cmp-analysis-grid .cmp-donut-body { flex-wrap: wrap; }
}
.cmp-budget-banner {
    margin: 8px 0 14px; padding: 12px 16px; border: 1px solid #efcb8f;
    border-left: 4px solid #cd780c; border-radius: 10px;
    background: #fff6e6; color: #65420f; line-height: 1.55;
}
.cmp-budget-banner strong { display: block; margin-bottom: 3px; color: #67400a; }
.cmp-budget-chip {
    display: table; margin: 5px auto 0; border-radius: 7px; padding: 2px 6px;
    font-size: 11px; line-height: 1.4; background: #fff0d6; color: #7b4906;
}
.cmp-budget-chip.good { background: #e1f3e9; color: #196044; }
.cmp-rec-selected.cmp-no-choice > span { background: #ffe7bd; color: #704509; }
.cmp-saved-constraints {
    display: flex; flex-wrap: wrap; gap: 7px 20px; align-items: baseline;
    padding: 10px 14px; margin: 0 0 12px; color: #244870;
    background: #f1f6fe; border: 1px solid #d4e4fa; border-radius: 10px;
}
.cmp-saved-constraints small { flex-basis: 100%; }
</style>""")


def risk_level(score):
    if score <= 4: return "Дуже низький"
    if score <= 9: return "Низький"
    if score <= 14: return "Середній"
    if score <= 19: return "Високий"
    return "Критичний"


def level_class(score):
    return ("very-low" if score <= 4 else "low" if score <= 9 else
            "medium" if score <= 14 else "high" if score <= 19 else "critical")


def risk_label(r):
    return f"№{r[0]} — {r[1]} · {r[2]} · R={r[6]}/25"


def safe(text):
    return escape(str(text), quote=True)


def budget_notice(best, affordable, winner, items, initial, budget, threshold):
    if best is None:
        return "Немає заходу, що знижує ризик", "Жоден із доданих заходів не дає прогнозованого бала нижче за початковий."

    reason = ""
    if budget is not None and best["cost"] > budget:
        reason = (
            f"«{best['row'][2]}» дає найнижчий прогнозований ризик ({best['r']}/25), "
            f"але коштує {amount(best['cost'])} ум. од. і перевищує бюджет "
            f"{amount(budget)} ум. од. на {amount(best['cost'] - budget)} ум. од. "
        )
    if winner is not None and reason:
        target = f" та відповідає порогу ≤ {threshold}/25" if threshold is not None else ""
        return "Найнижчий бал поза бюджетом", (
            reason + f"Система пропонує «{winner['row'][2]}» — {winner['r']}/25 "
            f"за {amount(winner['cost'])} ум. од. Цей захід вкладається в бюджет{target}."
        )
    if winner is None and affordable is None:
        minimum = min(item["cost"] for item in items if item["r"] < initial)
        return "У межах бюджету немає придатного заходу", (
            reason + f"Заходи, що знижують ризик, коштують від {amount(minimum)} ум. од. "
            "Потрібно переглянути бюджет або додати інший захід."
        )
    if winner is None:
        scope = "у межах бюджету" if budget is not None else "серед доданих заходів"
        return "Немає заходу, що відповідає заданим умовам", (
            reason + f"Найнижчий прогнозований бал {scope} — {affordable['r']}/25. "
            f"Він перевищує поріг {threshold}/25. Потрібно розглянути інші заходи або переглянути обмеження."
        )
    return None


balance_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18M5 21h14M3 7h18M6 7l-4 8h8L6 7ZM18 7l-4 8h8l-4-8Z"/></svg>'''
balance = base64.b64encode(balance_svg.encode()).decode()
st.html(f'''<section class="cmp-hero">
  <div><div class="cmp-eyebrow">CYBERRISK DSS / УПРАВЛІННЯ РИЗИКАМИ</div>
  <h1>Порівняння заходів</h1>
  <p>Аналіз альтернативних заходів захисту для зниження кіберризику та обґрунтування доцільного рішення</p></div>
  <div class="cmp-hero-icon"><img src="data:image/svg+xml;base64,{balance}" width="52" height="52" alt="Порівняння заходів"></div>
</section>''')

risks = list_risks()
measures = list_measures()
if not risks:
    st.info("Спочатку створіть оцінку на сторінці «Оцінювання ризиків».")
    st.stop()

# One selector, one concise context summary: no redundant KPI tiles.
left, right = st.columns([1.0, 1.0], gap="medium")
last_risk_id = st.session_state.get(LAST_COMPARED_RISK_KEY)
default_risk_index = next((i for i, risk in enumerate(risks) if int(risk[0]) == last_risk_id), 0)
with left:
    st.html('<div class="cmp-field-title">Виберіть ризик для аналізу</div>')
    selected = st.selectbox("Ризик", risks, format_func=risk_label,
                            index=default_risk_index, label_visibility="collapsed", key="cmp_selected_risk")
    st.session_state[LAST_COMPARED_RISK_KEY] = int(selected[0])
with right:
    st.html(f'''<div class="cmp-risk-context">
      <div class="cmp-risk-name"><span class="cmp-risk-icon">▤</span><strong>Аналізований ризик</strong></div>
      <div class="cmp-metric"><small>P (ймовірність)</small><b>{int(selected[4])}</b></div>
      <div class="cmp-metric"><small>I (вплив)</small><b>{int(selected[5])}</b></div>
      <div class="cmp-metric"><small>R (оцінка)</small><b class="cmp-score">{int(selected[6])}/25</b></div>
      <div class="cmp-metric"><small>Рівень ризику</small><b class="cmp-level {level_class(int(selected[6]))}">{risk_level(int(selected[6]))}</b></div>
    </div>''')

items = [score_of(m) for m in measures if int(m[1]) == int(selected[0])]
items.sort(key=decision_key)
initial_r = int(selected[6])

st.html('''<div class="cmp-heading"><h2>Альтернативні заходи захисту</h2>
<p>Порівняння ефективності, вартості та прогнозованого зниження ризику</p></div>''')
if not items:
    st.info("Для цього ризику поки немає заходів захисту. Додайте їх у розділі «Заходи захисту».")
else:
    budget, threshold = load_risk_constraints(selected[0])
    budget_text = f"{amount(budget)} ум. од." if budget is not None else "не задано"
    threshold_text = f"≤ {threshold}/25" if threshold is not None else "не задано"
    st.html(f'''<div class="cmp-saved-constraints">
      <span>Бюджет впровадження · <strong>{safe(budget_text)}</strong></span>
      <span>Поріг залишкового ризику · <strong>{safe(threshold_text)}</strong></span>
      <small>{'Бюджет не збережено. Рекомендація не враховує витрат як обмеження. Ліміт можна зберегти в розділі «Заходи захисту».'
              if budget is None else 'Вартість заходів і збережені обмеження завантажено з розділу «Заходи захисту».'}</small>
    </div>''')
    best, affordable, winner = compare_options(items, initial_r, budget, threshold)
    notice = budget_notice(best, affordable, winner, items, initial_r, budget, threshold)
    if notice:
        title, detail = notice
        st.html(f'<aside class="cmp-budget-banner" role="status"><strong>{safe(title)}</strong>{safe(detail)}</aside>')

    trs = []
    for x in items:
        m = x["row"]
        cls = level_class(x["r"])
        budget_badge = ""
        if budget is not None:
            budget_badge = ('<small class="cmp-budget-chip good">У межах бюджету</small>'
                            if x["cost"] <= budget else
                            '<small class="cmp-budget-chip">Понад бюджет</small>')
        threshold_badge = ('<small class="cmp-budget-chip">Понад поріг</small>'
                           if threshold is not None and x["r"] > threshold else "")
        trs.append(f'''<tr>
        <td>{m[0]}</td><td class="cmp-name">{safe(m[2])}</td>
        <td class="cmp-number">{x['cost']:,.2f}{budget_badge}</td>
        <td class="cmp-number">{"−" + str(int(m[5])) if int(m[5]) else "0"}</td><td class="cmp-number">{"−" + str(int(m[6])) if int(m[6]) else "0"}</td>
        <td class="cmp-number">{x['p']}</td><td class="cmp-number">{x['i']}</td>
        <td class="cmp-number"><span class="cmp-r-score">{x['r']}</span>{threshold_badge}</td>
        <td class="cmp-number">{x['delta']}</td><td class="cmp-number">{x['percent']:.1f}%</td>
        <td><span class="cmp-level {cls}">{risk_level(x['r'])}</span></td>
        </tr>''')
    st.html('''<div class="cmp-table-wrap"><table class="cmp-table">
    <colgroup>
      <col style="width:4%"><col style="width:29%"><col style="width:10%">
      <col style="width:6%"><col style="width:6%"><col style="width:6%">
      <col style="width:6%"><col style="width:6%"><col style="width:8%">
      <col style="width:8%"><col style="width:11%">
    </colgroup><thead>
    <tr><th rowspan="2">№</th><th rowspan="2">Захід захисту</th>
    <th rowspan="2">Вартість, од.</th><th rowspan="2">ΔP<small>(зниження P)</small></th><th rowspan="2">ΔI<small>(зниження I)</small></th>
    <th colspan="3">Прогнозовані значення</th>
    <th colspan="2">Зниження ризику</th><th rowspan="2">Рівень після впровадження</th></tr>
    <tr><th>P′</th><th>I′</th><th>R′</th><th>абсолютне</th><th>%</th></tr>
    </thead><tbody>''' + ''.join(trs) + '</tbody></table></div>')
    st.caption("R′ — прогнозований ризик після одного заходу. Ефекти різних заходів автоматично не підсумовуються.")

    bars = [("Початковий ризик", initial_r, "initial")]
    bars.extend((str(x["row"][2]), x["r"], "predicted") for x in items)
    html_bars = []
    for label, value, kind in bars:
        # Keep the full title in the tooltip, but use a readable compact chart label.
        # No change to measure names stored in the database or displayed in the table.
        if kind == "initial":
            display_label = label
        elif "(MFA)" in label.upper():
            display_label = "MFA"
        elif len(label) > 22:
            display_label = label[:19].rstrip() + "…"
        else:
            display_label = label
        html_bars.append(f'''<div class="cmp-bar-item"><div class="cmp-bar-label" title="{safe(label)}">{safe(display_label)}</div>
        <div class="cmp-bar-track"><div class="cmp-bar-fill {kind}" style="width:{value / 25 * 100:.1f}%"></div></div>
        <b>{value}</b></div>''')
    chart_card = ('<div class="cmp-panel cmp-chart-panel"><div class="cmp-panel-heading"><span class="cmp-panel-icon">▥</span> Порівняння рівня ризику</div><div class="cmp-bars">'+''.join(html_bars)+'</div><div class="cmp-axis-note">Шкала оцінки ризику: 1–25</div></div>')

    best_effect = winner or best or items[0]
    donut_note = ("Прогноз для рекомендованого заходу" if winner else
                  "Найнижчий прогнозований бал без урахування обмежень · не рекомендація")
    p = best_effect["percent"]
    delta = best_effect["delta"]
    delta_unit = ("балів" if 11 <= delta % 100 <= 14 else
                  "бал" if delta % 10 == 1 else "бали" if 2 <= delta % 10 <= 4 else "балів")
    donut_card = (f'''<div class="cmp-panel cmp-donut-panel"><div class="cmp-panel-heading"><span class="cmp-panel-icon">◎</span> Розподіл зниження ризику</div><div class="cmp-donut-body"><div class="cmp-donut" style="--pct:{p:.2f}%">
    <div class="cmp-donut-center"><strong>{p:.1f}%</strong><span>зниження</span></div></div>
    <div class="cmp-donut-details"><span><i class="cmp-dot forecast"></i>Зниження — <b>{delta} {delta_unit}</b></span>
    <span><i class="cmp-dot original"></i>Залишковий бал — <b>{best_effect['r']}</b></span>
    <small>Початковий бал — {initial_r}<br>{safe(donut_note)}</small></div></div></div>''')

    recommendation_heading = '<div class="cmp-recommend"><div class="cmp-rec-head"><span class="cmp-rec-award">♙</span> Рекомендація системи</div>'
    if winner:
        constraints = []
        if budget is not None:
            constraints.append(f"бюджет ≤ {amount(budget)} ум. од.")
        if threshold is not None:
            constraints.append(f"поріг ≤ {threshold}/25")
        limit_note = (f"Враховано {', '.join(constraints)}." if constraints
                      else "Бюджет і поріг не задано. Вибір зроблено за прогнозованим балом і вартістю.")
        recommendation_card = recommendation_heading + f'''
    <div class="cmp-rec-selected"><span>✓</span><div><small>Рекомендований захід</small>
    <strong>{safe(winner['row'][2])}</strong></div></div>
    <div class="cmp-rec-facts"><div><span class="cmp-fact-icon">▤</span><small>Вартість</small><strong>{winner['cost']:,.2f}</strong></div>
    <div><span class="cmp-fact-icon">↘</span><small>Зниження ризику</small><strong>{winner['percent']:.1f}%</strong></div>
    <div><span class="cmp-fact-icon">♢</span><small>Ризик після заходу</small><strong>{winner['r']}/25</strong></div></div>
    <p>{safe(limit_note)}</p></div>'''
    else:
        recommendation_card = recommendation_heading + '''
    <div class="cmp-rec-selected cmp-no-choice"><span>!</span><div>
    <strong>Немає придатного заходу</strong></div></div>
    <p>Жоден варіант не знижує ризик із дотриманням усіх заданих умов.</p></div>'''
    st.html('<div class="cmp-analysis-grid">' + chart_card + donut_card + recommendation_card + '</div>')


st.html('''<div class="cmp-method"><div class="cmp-method-title">ⓘ &nbsp; Логіка оцінювання</div>
<div class="cmp-method-step"><b>1</b><span>Прогноз P′ та I′<small>P′ = max(1, P − ΔP), I′ = max(1, I − ΔI)</small></span></div>
<div class="cmp-method-arrow">›</div>
<div class="cmp-method-step"><b>2</b><span>Оцінка нового ризику<small>R′ = P′ × I′</small></span></div>
<div class="cmp-method-arrow">›</div>
<div class="cmp-method-step"><b>3</b><span>Аналіз ефективності<small>ΔR = R − R′; % = ΔR / R × 100</small></span></div>
<div class="cmp-method-arrow">›</div>
<div class="cmp-method-step"><b>4</b><span>Формування рекомендації<small>Відбір за заданими умовами → мінімум R′ → мінімум вартості</small></span></div></div>''')
st.caption("Прогнози базуються на експертних оцінках ΔP та ΔI, не є доказом фактичного впровадження чи результативності. Для комбінованих заходів потрібна окрема модель взаємодії.")
try:
    from components import render_footer
    render_footer()
except ImportError:
    pass
