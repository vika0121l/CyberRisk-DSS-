"""Головна аналітична панель CyberRisk DSS.

Візуалізація читає наявні записи SQLite і не змінює схему/дані.
Графік фільтрується за всіма ризиками, окремим активом або одним ризиком.
Верхній банер збережений; стилі застосовуються лише до цієї сторінки.
Не потребує plotly, matplotlib чи numpy.
"""
from collections import Counter, defaultdict
from html import escape
from pathlib import Path
import base64

import streamlit as st

from database import (
    get_assets,
    get_threats,
    get_vulnerabilities,
    get_risks,
    get_security_measures,
    get_connection,
)
from components import render_footer


# Залишаємо наявний CSS: у ньому міститься оригінальний стиль синього банера.
css_path = Path(__file__).resolve().parent.parent / "styles" / "dashboard.css"
if css_path.exists():
    st.html(f"<style>{css_path.read_text(encoding='utf-8')}</style>")


def h(value):
    """Екранування рядків із БД перед вставленням в HTML."""
    return escape(str(value if value is not None else "—"), quote=True)


def score_label(value):
    """Бал зі шкали 1–25: без зайвих .0, з комою для дробових середніх."""
    value = float(value)
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value))}/25"
    return f"{value:.1f}".replace(".", ",") + "/25"


def risk_category(score):
    if score <= 4:
        return "Дуже низький"
    if score <= 9:
        return "Низький"
    if score <= 14:
        return "Середній"
    if score <= 19:
        return "Високий"
    return "Критичний"


LEVELS = (
    ("Критичний", "#e63946"),
    ("Високий", "#fb760c"),
    ("Середній", "#e9b617"),
    ("Низький", "#2f87e7"),
    ("Дуже низький", "#1fa76b"),
)


ICON_PATHS = {
    "server": '<rect x="4" y="4" width="16" height="6" rx="1.5"/><rect x="4" y="14" width="16" height="6" rx="1.5"/><path d="M7 7h.01M7 17h.01"/>',
    "layers": '<path d="m12 2 9 5-9 5-9-5 9-5ZM3 12l9 5 9-5M3 17l9 5 9-5"/>',
    "alert": '<path d="M12 3 2 20h20L12 3Z"/><path d="M12 9v5M12 17.5h.01"/>',
    "bug": '<rect x="8" y="7" width="8" height="14" rx="4"/><path d="M9 7 7 4m8 3 2-3M5 10h3m8 0h3M4 15h4m8 0h4M12 9v10"/>',
    "checklist": '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 7h.01M11 7h5M8 12h.01M11 12h5M8 17h.01M11 17h5"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-8M22 20V7"/>',
    "trend": '<path d="m3 17 7-7 5 4 6-8"/><path d="M16 6h5v5"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 4 18 4 18 0V5M3 12c0 4 18 4 18 0"/>',
    "bell": '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',
    "shield": '<path d="M12 2 20 6v6c0 5-3.5 8-8 10-4.5-2-8-5-8-10V6l8-4Z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
}


def svg_img(svg_source, css_class="cd-svg-icon", alt=""):
    """SVG як data:image у тегу IMG: Streamlit st.html не викидає іконки/графіки."""
    encoded = base64.b64encode(svg_source.encode("utf-8")).decode("ascii")
    return (
        f'<img class="{css_class}" '
        f'src="data:image/svg+xml;base64,{encoded}" '
        f'alt="{h(alt)}" loading="eager">'
    )


def icon(name, size=25, color="#1b579f"):
    """Кросбраузерна іконка з явно заданими кольорами (не inline SVG)."""
    path = ICON_PATHS.get(name, ICON_PATHS["shield"])
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        f'{path}</svg>'
    )
    return svg_img(svg, css_class="cd-svg-icon", alt="")


# БАНЕР: той самий текст, логотип та кольорова схема, що й раніше.
shield_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48"
viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="1.8"
stroke-linecap="round" stroke-linejoin="round">
<path d="M12 2 20 6v6c0 5-3.5 8-8 10-4.5-2-8-5-8-10V6l8-4Z"/>
<path d="m8.5 12 2.5 2.5 4.5-5"/></svg>'''
shield_b64 = base64.b64encode(shield_svg.encode("utf-8")).decode("ascii")


# Дані з наявних функцій БД.
assets = get_assets()
threats = get_threats()
vulnerabilities = get_vulnerabilities()
risks = get_risks()
measures = get_security_measures()

# Перевіряємо охоплення за ID, а не за назвою активу: назви можуть збігатися.
with get_connection() as connection:
    assessed_ids = {
        int(r[0]) for r in connection.execute("SELECT DISTINCT asset_id FROM risks").fetchall()
    }
    risk_asset_ids = {
        int(row[0]): int(row[1])
        for row in connection.execute("SELECT id, asset_id FROM risks").fetchall()
    }
asset_ids = {int(asset[0]) for asset in assets}
assessed_count = len(assessed_ids & asset_ids)

# Ризики: get_risks() -> (id, asset_name, threat_name, vuln_name, probability,
# impact, risk_score, assessment_date).
valid_risks = []
for r in risks:
    try:
        record = {
            "id": int(r[0]), "asset_id": risk_asset_ids.get(int(r[0])),
            "asset": str(r[1]), "threat": str(r[2]),
            "p": int(r[4]), "i": int(r[5]), "score": int(r[6]),
        }
        if 1 <= record["p"] <= 5 and 1 <= record["i"] <= 5 and 1 <= record["score"] <= 25:
            valid_risks.append(record)
    except (IndexError, ValueError, TypeError):
        continue

level_counts = Counter(risk_category(r["score"]) for r in valid_risks)
urgent = [r for r in valid_risks if r["score"] >= 15]
protected_risk_ids = {int(m[1]) for m in measures}

# Заходи можуть бути альтернативами. Беремо найкращий окремий захід,
# НЕ підсумовуємо всі зареєстровані заходи як нібито вже впроваджені.
measures_by_risk = defaultdict(list)
for m in measures:
    try:
        measures_by_risk[int(m[1])].append((int(m[5]), int(m[6]), str(m[2])))
    except (IndexError, ValueError, TypeError):
        continue


def projected_score(risk):
    candidates = measures_by_risk.get(risk["id"], [])
    if not candidates:
        return risk["score"]
    return min(
        max(1, risk["p"] - p_red) * max(1, risk["i"] - i_red)
        for p_red, i_red, _ in candidates
    )


# Контекстний режим графіка: дані фільтруються за стабільними ID в SQLite.
# Streamlit автоматично перезапускає скрипт при зміні радіокнопки або списку.
VIEW_ALL = "Уся система"
VIEW_ASSET = "Окремий актив"
VIEW_RISK = "Окремий ризик"
VIEW_OPTIONS = [VIEW_ALL, VIEW_ASSET, VIEW_RISK]
asset_lookup = {int(a[0]): str(a[1]) for a in assets}
asset_option_ids = sorted({r["asset_id"] for r in valid_risks if r["asset_id"] in asset_lookup})
risk_lookup = {r["id"]: r for r in valid_risks}
risk_option_ids = sorted(risk_lookup, reverse=True)
view_mode = st.session_state.get("cd_view_mode", VIEW_ALL)
if view_mode not in VIEW_OPTIONS:
    view_mode = VIEW_ALL
asset_choice = st.session_state.get("cd_selected_asset")
risk_choice = st.session_state.get("cd_selected_risk")
if asset_choice not in asset_option_ids:
    asset_choice = asset_option_ids[0] if asset_option_ids else None
if risk_choice not in risk_option_ids:
    risk_choice = risk_option_ids[0] if risk_option_ids else None

if view_mode == VIEW_ASSET and asset_choice is not None:
    display_risks = [r for r in valid_risks if r["asset_id"] == asset_choice]
    graph_scope = f"Актив: {asset_lookup[asset_choice]}"
elif view_mode == VIEW_RISK and risk_choice is not None:
    display_risks = [risk_lookup[risk_choice]]
    graph_scope = f"Ризик №{risk_choice} · {risk_lookup[risk_choice]['asset']}"
else:
    display_risks = valid_risks
    graph_scope = "Всі оцінені ризики інфраструктури"


def best_measure_for(risk):
    """Повертає один найкращий ОКРЕМИЙ захід, не комбінуючи альтернативи."""
    candidates = measures_by_risk.get(risk["id"], [])
    if not candidates:
        return None
    return min(candidates, key=lambda m: max(1, risk["p"] - m[0]) * max(1, risk["i"] - m[1]))


# Власні стилі із префіксом cd-, щоб жодним чином не змінити бічне меню.
st.html("""<style>
/* Відновлюємо існуючий синій банер без зміни навігації. */
.dash-hero{display:flex!important;align-items:center;justify-content:space-between;
 min-height:126px!important;padding:24px 30px!important;border-radius:13px!important;
 background:linear-gradient(110deg,#122f5d,#245fae)!important;color:#fff!important;
 margin:8px 0 18px!important;overflow:hidden!important}
.dash-hero h1{color:#fff!important;margin:5px 0!important;font-size:30px!important;line-height:1.2!important}
.dash-hero p{color:#e0ebff!important;margin:0!important;max-width:650px;line-height:1.5!important;font-size:14px!important}
.dash-hero .dash-eyebrow{color:#bfd8ff!important;font-size:11px!important;font-weight:700!important;letter-spacing:1.3px}
.dash-hero-symbol{display:flex!important;align-items:center!important;justify-content:center!important;
 min-width:70px!important;min-height:70px!important;border-radius:17px!important;background:#ffffff19!important;
 border:1px solid #ffffff40!important;z-index:1!important}
/* Весь новий інтерфейс ізольований префіксом cd-. */
.cd-body{color:#153a70;font-family:inherit;max-width:100%;font-size:14px}
.cd-body *{box-sizing:border-box}
.cd-svg-icon{display:block!important;width:25px!important;height:25px!important;max-width:none!important;object-fit:contain!important;opacity:1!important;visibility:visible!important}
.cd-kpi-icon .cd-svg-icon{width:29px!important;height:29px!important}
.cd-card-head .cd-svg-icon{width:21px!important;height:21px!important;flex:none!important}
.cd-alert .cd-svg-icon{width:26px!important;height:26px!important;flex:none!important}
.cd-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px;margin-bottom:17px}
.cd-kpi{display:flex;align-items:center;gap:15px;min-height:102px;padding:14px 17px;border:1px solid #c7ddfa;
 background:linear-gradient(135deg,#fff,#edf5ff);border-radius:14px;box-shadow:0 4px 13px rgba(22,64,120,.065)}
.cd-kpi-icon{width:47px;height:47px;flex:none;display:grid;place-items:center;color:#2069bd;
 background:#e9f3ff;border-radius:13px}
.cd-kpi-text{min-width:0}.cd-kpi-label{color:#183b72;font-size:13px;font-weight:750;line-height:1.35}
.cd-kpi-num{color:#102f62;font-size:31px;font-weight:850;line-height:1.2;margin:6px 0 1px}
.cd-kpi-sub{color:#7289a5;font-size:11px}
.cd-upper{display:grid;grid-template-columns:1fr 1fr;gap:17px;margin-bottom:17px;align-items:stretch}
.cd-lower{display:grid;grid-template-columns:1.48fr 1fr;gap:17px;margin-bottom:13px;align-items:stretch}
.cd-card{min-width:0;background:#fff;border:1px solid #bad5f7;border-radius:15px;
 overflow:hidden;box-shadow:0 4px 14px rgba(25,75,135,.07)}
.cd-card-head{display:flex;align-items:center;gap:10px;height:49px;padding:0 17px;
 background:linear-gradient(90deg,#edf5ff,#e2eeff);color:#133b76;font-size:16px;font-weight:800;
 border-bottom:1px solid #dfebfa}
.cd-card-head svg{color:#1b559c;flex:none}
.cd-card-body{padding:14px 16px}
.cd-distribution{min-height:245px;display:flex;align-items:center;justify-content:space-around;gap:18px}
.cd-donut{width:186px;height:186px;max-width:43%;aspect-ratio:1;position:relative;border-radius:50%;flex:none}
.cd-donut::after{content:"";position:absolute;inset:26px;background:#fff;border-radius:50%;box-shadow:inset 0 0 0 1px #edf2f9}
.cd-donut-center{position:absolute;z-index:1;inset:0;display:flex;flex-direction:column;
 align-items:center;justify-content:center;text-align:center;color:#123c78}
.cd-donut-center strong{font-size:35px;line-height:1.1}.cd-donut-center span{font-size:12px;font-weight:700;margin-top:5px}
.cd-legend{flex:1;min-width:145px;max-width:245px}
.cd-legend-row{display:flex;align-items:center;gap:9px;padding:7px 6px;
 font-size:12px;border-radius:7px;color:#28476e}
.cd-legend-row:nth-child(even){background:#f3f7fd}
.cd-dot{width:11px;height:11px;border-radius:50%;flex:none}
.cd-legend-name{flex:1}.cd-legend-count{font-weight:800;color:#123e7b;white-space:nowrap}
.cd-trend-body{padding:12px 14px 9px;min-height:245px;display:flex;flex-direction:column;justify-content:center}
.cd-trend-svg{display:block!important;width:100%!important;height:192px!important;max-width:610px!important;margin:0 auto!important;object-fit:contain!important;opacity:1!important;visibility:visible!important}
.cd-trend-note{text-align:center;color:#7388a4;font-size:11px;line-height:1.45;margin-top:0}
.cd-trend-stats{display:flex;justify-content:center;align-items:center;gap:9px;flex-wrap:wrap;margin:2px auto 6px;font-size:11px;color:#365981}
.cd-trend-stats span{background:#f0f6ff;border:1px solid #dbe8fa;border-radius:7px;padding:4px 8px;white-space:nowrap}
.cd-trend-stats b{color:#153d77}
.cd-trend-stats .cd-trend-reduction{background:#edfaf1;border-color:#cbeed9;color:#117342}
.cd-trend-stats .cd-trend-reduction b{color:#087b40}
.cd-risk-label{display:flex;align-items:center;justify-content:center;gap:15px;color:#375779;font-size:11px}
.cd-risk-label i{display:inline-block;width:12px;height:5px;border-radius:4px;vertical-align:middle;margin-right:5px}
.cd-table-wrap{overflow-x:auto;padding:12px 14px 15px}
.cd-table{width:100%;border-collapse:collapse;font-size:12px;color:#163c72}
.cd-table th{text-align:left;background:linear-gradient(180deg,#1e66ac,#0f4281);color:#fff;
 padding:12px 10px;font-weight:800;white-space:nowrap}
.cd-table th:first-child{border-radius:8px 0 0 0}.cd-table th:last-child{border-radius:0 8px 0 0}
.cd-table td{padding:12px 10px;border-bottom:1px solid #deebfa;vertical-align:middle}
.cd-table tbody tr:nth-child(even){background:#f5f9ff}
.cd-table .cd-asset-name{font-weight:750}.cd-asset-id{color:#718bad}
.cd-level{display:inline-block;border-radius:18px;padding:5px 9px;font-size:11px;font-weight:800;white-space:nowrap}
.cd-level-5{background:#fee7e7;color:#bb2839}.cd-level-4{background:#ffedd8;color:#a85b04}
.cd-level-3{background:#fff5c9;color:#846508}.cd-level-2{background:#e4f0ff;color:#245fa5}
.cd-level-1{background:#e3f6ec;color:#13754a}
.cd-note-box{margin:0 14px 14px;border:1px solid #d7e6fa;background:#f3f8ff;
 border-radius:9px;padding:10px 12px;color:#557292;font-size:11px;line-height:1.45}
.cd-alert-content{padding:12px 14px 10px}
.cd-alert{display:flex;align-items:center;gap:12px;background:#fff0ef;border:1px solid #ffc6c6;
 border-radius:10px;padding:12px 13px;color:#ab2432;min-height:65px}
.cd-alert.ok{background:#edf9f2;border-color:#bce7ca;color:#15804e}
.cd-alert-icon{flex:none}.cd-alert strong{display:block;font-size:13px}.cd-alert span{display:block;font-size:11px;color:#637b97;margin-top:4px}
.cd-task-head{font-size:12px;color:#6f88a5;font-weight:800;letter-spacing:.04em;margin:14px 1px 5px;text-transform:uppercase}
.cd-task{display:flex;gap:10px;align-items:flex-start;border-bottom:1px solid #e2edfa;padding:9px 3px;color:#244c7b}
.cd-task:last-child{border-bottom:none}.cd-task-main{min-width:0;flex:1}
.cd-task-name{font-size:12px;font-weight:700}.cd-task-extra{font-size:10px;color:#7289a5;margin-top:3px;line-height:1.45}
.cd-task-status{flex:none;display:inline-flex;align-items:center;justify-content:center;max-width:125px;
 padding:5px 9px;border-radius:20px;font-size:10px;font-weight:800;line-height:1.3;text-align:center;
 border:1px solid transparent;white-space:normal}
.cd-task-status-done{color:#087744;background:#e6f7ee;border-color:#bbebd1}
.cd-task-status-pending{color:#a54b10;background:#fff1df;border-color:#f4d7b0}
.cd-task-status-neutral{color:#3c638e;background:#edf4ff;border-color:#d4e4fa}
.cd-micro{color:#7088a5;font-size:11px;text-align:center;margin:2px 0 11px}
.cd-empty{padding:35px 14px;color:#7a8fa8;font-size:13px;text-align:center}
@media(max-width:1150px){.cd-kpi{gap:9px;padding:12px}.cd-kpi-icon{width:37px;height:37px}
 .cd-kpi-num{font-size:26px}.cd-distribution{gap:9px}.cd-donut{width:155px}}
@media(max-width:900px){.cd-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}
 .cd-upper,.cd-lower{grid-template-columns:1fr}.dash-hero{padding:18px!important;min-height:100px!important}
 .dash-hero h1{font-size:23px!important}.dash-hero-symbol{display:none!important}}
@media(max-width:500px){.cd-kpis{gap:8px}.cd-kpi{min-height:82px}.cd-kpi-icon{display:none}
 .cd-card-head{font-size:14px}.cd-donut{width:136px}.cd-legend-row{font-size:11px}
 .cd-distribution{padding:10px 8px}.cd-table{font-size:11px}
 .cd-task{flex-wrap:wrap}.cd-task-status{margin-left:auto}}

/* v5: footer at the viewport bottom on short dashboards, after content on long ones.
   Scoped to this page through a unique anchor: other Streamlit pages are untouched. */
@supports selector(:has(*)) {
    [data-testid="stMainBlockContainer"]:has(.cd-footer-anchor) {
        display: flex !important;
        flex-direction: column !important;
        min-height: calc(100dvh - 5rem) !important;
        box-sizing: border-box !important;
    }
    [data-testid="stMainBlockContainer"]:has(.cd-footer-anchor)
       > [data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 0 auto !important;
        width: 100% !important;
    }
    [data-testid="stMainBlockContainer"]:has(.cd-footer-anchor)
       > [data-testid="stVerticalBlock"]
       > [data-testid="stElementContainer"]:has(.cd-footer-anchor) {
        margin-top: auto !important;
    }
}
.cd-footer-anchor {height:0!important;line-height:0!important;font-size:0!important;}

/* v6: компактна панель із фільтром у нижній частині графіка. */
.cd-risk-card {min-height:397px!important;}
.cd-risk-card .cd-distribution{min-height:346px!important;}
.st-key-cd_trend_panel {
 background:#fff!important;border:1px solid #bad5f7!important;border-radius:15px!important;
 overflow:hidden!important;box-shadow:0 4px 14px rgba(25,75,135,.07)!important;
 padding:0 0 12px!important;min-height:397px!important;box-sizing:border-box!important;
}
.st-key-cd_trend_panel [data-testid="stVerticalBlock"] {gap:.35rem!important;}
.st-key-cd_trend_panel .cd-card-head {height:auto!important;min-height:49px!important;padding:12px 14px!important;
 font-size:15px!important;line-height:1.25!important;}
.st-key-cd_trend_panel .cd-trend-body{min-height:0!important;padding:2px 11px 0!important;}
.st-key-cd_trend_panel .cd-trend-svg{height:174px!important;}
.st-key-cd_trend_panel .cd-trend-note{font-size:10px!important;line-height:1.35!important;margin:1px 12px 3px!important;}
.st-key-cd_trend_panel .cd-trend-stats{margin:0 auto 4px!important;}
.st-key-cd_trend_panel .cd-filter-caption {font-size:11px;font-weight:800;color:#1b497e;margin:0 16px 0;}
.st-key-cd_trend_panel [data-testid="stRadio"] {padding:0 14px!important;margin:0!important;}
.st-key-cd_trend_panel [data-testid="stRadio"] label {font-size:12px!important;color:#1a4579!important;}
.st-key-cd_trend_panel [data-testid="stSelectbox"] {margin:0 14px 2px!important;}
.st-key-cd_trend_panel [data-testid="stSelectbox"] [data-baseweb="select"] > div {
 min-height:35px!important;background:#f2f7ff!important;border:1px solid #cfdef5!important;border-radius:8px!important;
}
.st-key-cd_trend_panel .cd-scope-text {font-size:10px;color:#627f9e;margin:2px 16px 0;line-height:1.3;}
@media(max-width:900px){.cd-risk-card,.st-key-cd_trend_panel{min-height:0!important}
 .cd-risk-card .cd-distribution{min-height:235px!important}}
</style>""")


st.html(f'''<div class="dash-hero">
    <div class="dash-hero-content">
        <div class="dash-eyebrow">CYBERRISK DSS / АНАЛІТИЧНА ПАНЕЛЬ</div>
        <h1>Головна панель</h1>
        <p>Моніторинг інформаційних активів, аналіз загроз та оцінювання
           кіберризиків інфраструктури підприємства</p>
    </div>
    <div class="dash-hero-symbol"><img src="data:image/svg+xml;base64,{shield_b64}"
        width="48" height="48" alt="CyberRisk DSS"></div>
</div>''')


# 1. KPI — виключно фактичні кількості, без вигаданих змін у відсотках.
kpis = [
    ("Інформаційні активи", len(assets), "layers", "зареєстровано"),
    ("Загрози", len(threats), "alert", "зареєстровано"),
    ("Вразливості", len(vulnerabilities), "bug", "зареєстровано"),
    ("Оцінені ризики", len(valid_risks), "checklist", "оцінок ризиків"),
]
kpi_html = "".join(
    f'<div class="cd-kpi"><div class="cd-kpi-icon">{icon(sym, 28)}</div>'
    f'<div class="cd-kpi-text"><div class="cd-kpi-label">{h(label)}</div>'
    f'<div class="cd-kpi-num">{value}</div><div class="cd-kpi-sub">{h(sub)}</div></div></div>'
    for label, value, sym, sub in kpis
)


# 2. Кільцева діаграма: точні частки всіх п'яти категорій.
total_risks = len(valid_risks)
segments = []
cursor_pct = 0.0
for level, color in LEVELS:
    fraction = level_counts[level] / total_risks * 100 if total_risks else 0
    if fraction:
        segments.append(f"{color} {cursor_pct:.4f}% {cursor_pct+fraction:.4f}%")
        cursor_pct += fraction
ring_bg = f"conic-gradient({', '.join(segments)})" if segments else "#e5edf8"
legend_rows = "".join(
    f'<div class="cd-legend-row"><span class="cd-dot" style="background:{color}"></span>'
    f'<span class="cd-legend-name">{h(level)}</span>'
    f'<span class="cd-legend-count">{level_counts[level]} '
    f'({round(level_counts[level] / total_risks * 100) if total_risks else 0}%)</span></div>'
    for level, color in LEVELS
)


# 3. Для всієї системи / окремого активу — середній P×I; для ризику — його оцінка.
# Альтернативні заходи НЕ сумуються: для кожного ризику вибирається найкращий окремий.
if display_risks:
    mean_initial = sum(r["score"] for r in display_risks) / len(display_risks)
    mean_after = sum(projected_score(r) for r in display_risks) / len(display_risks)

    def chart_y(value):
        return 177 - value / 25 * 139

    y1, y2 = chart_y(mean_initial), chart_y(mean_after)
    ticks = "".join(
        f'<line x1="65" y1="{chart_y(tick):.1f}" x2="485" y2="{chart_y(tick):.1f}" stroke="#e1eafa" stroke-dasharray="4 5"/>'
        f'<text x="53" y="{chart_y(tick)+4:.1f}" text-anchor="end" font-size="11" fill="#7b93b1">{tick}</text>'
        for tick in (0, 5, 10, 15, 20, 25)
    )
    # SVG (viewBox) гарантує компактний розмір незалежно від масштабування браузера.
    chart_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="530" height="220" viewBox="0 0 530 220" role="img"
       aria-label="Середня початкова оцінка ризику {mean_initial:.1f} та прогнозована {mean_after:.1f} з 25">
       <defs><linearGradient id="cdArea" x1="0" x2="0" y1="0" y2="1">
       <stop offset="0%" stop-color="#f99a49" stop-opacity=".31"/>
       <stop offset="100%" stop-color="#f99a49" stop-opacity=".02"/></linearGradient></defs>
       {ticks}
       <line x1="65" y1="177" x2="485" y2="177" stroke="#bed1ea"/>
       <path d="M145 {y1:.1f} L405 {y2:.1f} L405 177 L145 177Z" fill="url(#cdArea)"/>
       <path d="M145 {y1:.1f} L405 {y2:.1f}" fill="none" stroke="#fb7c18" stroke-width="3" stroke-linecap="round"/>
       <circle cx="145" cy="{y1:.1f}" r="6" fill="#fb7c18" stroke="white" stroke-width="2"/>
       <circle cx="405" cy="{y2:.1f}" r="6" fill="#fb7c18" stroke="white" stroke-width="2"/>
       <rect x="108" y="{max(4,y1-33):.1f}" rx="7" width="74" height="25" fill="#f87912"/>
       <text x="145" y="{max(21,y1-16):.1f}" fill="white" text-anchor="middle" font-weight="800" font-size="13">{score_label(mean_initial)}</text>
       <rect x="368" y="{max(4,y2-33):.1f}" rx="7" width="74" height="25" fill="#f87912"/>
       <text x="405" y="{max(21,y2-16):.1f}" fill="white" text-anchor="middle" font-weight="800" font-size="13">{score_label(mean_after)}</text>
       <text x="145" y="198" fill="#264d7d" text-anchor="middle" font-size="12" font-weight="700">Початковий ризик</text>
       <text x="405" y="198" fill="#264d7d" text-anchor="middle" font-size="12" font-weight="700">Після заходу*</text>
       </svg>'''
    # Важливо: вставлення сирого <svg> через st.html приховувало графік.
    # IMG із base64 SVG показує той самий графік, як і логотип у верхньому банері.
    chart_markup = svg_img(
        chart_svg,
        css_class="cd-trend-svg",
        alt=f"Середня оцінка ризику: до заходу {score_label(mean_initial)}; прогнозована {score_label(mean_after)}"
    )
    reduction_pct = (mean_initial - mean_after) / mean_initial * 100 if mean_initial > 0 else 0
    metric_summary = (
        '<div class="cd-trend-stats">'
        f'<span>Початковий: <b>{score_label(mean_initial)}</b></span>'
        f'<span>Прогноз: <b>{score_label(mean_after)}</b></span>'
        f'<span class="cd-trend-reduction">Зменшення: <b>{reduction_pct:.0f}%</b></span>'
        '</div>'
    )
    if view_mode == VIEW_RISK:
        chosen = best_measure_for(display_risks[0])
        if chosen:
            trend_description = (
                f"Прогноз за окремим заходом «{chosen[2]}». "
                "Захід може бути лише запланованим — факт впровадження не підтверджений."
            )
        else:
            trend_description = "Для цього ризику немає заходу: прогноз дорівнює початковій оцінці."
    else:
        trend_description = (
            f"Середні значення для {len(display_risks)} оцінок. "
            "Для кожного ризику враховано один найкращий зареєстрований захід; "
            "це прогноз, а не фактично підтверджене зниження."
        )
    if not any(measures_by_risk.get(r["id"]) for r in display_risks):
        trend_description = "Для вибраних ризиків заходів немає: прогноз дорівнює початковій оцінці."
else:
    chart_markup = '<div class="cd-empty">Діаграма з’явиться після першого оцінювання ризику.</div>'
    metric_summary = ""
    trend_description = "Для порівняння необхідні збережені оцінки ризиків."


# 4. Таблиця активів: лише поля, які справді є в SQLite.
criticality_names = {1: "Дуже низька", 2: "Низька", 3: "Середня", 4: "Висока", 5: "Критична"}
asset_rows = "".join(
    '<tr>'
    f'<td class="cd-asset-id">{h(asset[0])}</td>'
    f'<td class="cd-asset-name">{h(asset[1])}</td>'
    f'<td>{h(asset[2])}</td>'
    f'<td>{h(asset[3])}</td>'
    f'<td><span class="cd-level cd-level-{int(asset[5])}">'
    f'{criticality_names.get(int(asset[5]), "Невідома")} ({int(asset[5])})</span></td>'
    '</tr>' for asset in assets[:8]
)
if not asset_rows:
    asset_rows = '<tr><td colspan="5" class="cd-empty">Активів поки немає. Додай їх у розділі «Інформаційні активи».</td></tr>'


# 5. Контекстні оповіщення й реальні наступні кроки.
def risk_count_phrase(n):
    """Правильне українське узгодження: 1 ризик / 2 ризики / 5 ризиків."""
    unit = "ризик" if n % 10 == 1 and n % 100 != 11 else (
        "ризики" if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14)
        else "ризиків"
    )
    return f"{n} {unit} високого або критичного рівня"


urgent_count = len(urgent)
if urgent_count:
    first = max(urgent, key=lambda r: r["score"])
    alert_html = (f'<div class="cd-alert">{icon("alert", 26, "#bf3444")}'
                  f'<div><strong>{risk_count_phrase(urgent_count)}</strong>'
                  f'<span>Найвища оцінка: {h(first["asset"])} — {first["score"]}/25</span></div></div>')
else:
    alert_html = (f'<div class="cd-alert ok">{icon("shield", 26, "#16814e")}'
                  '<div><strong>Високих і критичних оцінок немає</strong>'
                  '<span>Це не виключає неперевірених загроз і вразливостей.</span></div></div>')

urgent_covered = sum(r["id"] in protected_risk_ids for r in urgent)
all_assets_assessed = bool(assets) and assessed_count == len(assets)
all_urgent_covered = bool(urgent) and urgent_covered == len(urgent)


def task_markup(status, status_text, label, detail):
    """Статуси, а не чекбокси: ці елементи не редагують записи БД."""
    return (
        '<div class="cd-task">'
        f'<div class="cd-task-main"><div class="cd-task-name">{h(label)}</div>'
        f'<div class="cd-task-extra">{h(detail)}</div></div>'
        f'<span class="cd-task-status cd-task-status-{status}" '
        f'aria-label="Статус: {h(status_text)}">{h(status_text)}</span></div>'
    )

if not assets:
    asset_status = ("neutral", "Немає активів")
elif all_assets_assessed:
    asset_status = ("done", "Охоплено")
else:
    asset_status = ("pending", "Не завершено")

if not urgent:
    protection_status = ("neutral", "Не потрібно")
elif all_urgent_covered:
    protection_status = ("done", "Заходи є")
else:
    protection_status = ("pending", "Потребує уваги")

tasks = "".join([
    task_markup(*asset_status, "Оцінити ризики інформаційних активів",
                f"Охоплено {assessed_count} із {len(assets)} активів"),
    task_markup(*protection_status, "Призначити заходи для підвищених ризиків",
                f"Зареєстровані заходи є для {urgent_covered} із {len(urgent)} високих/критичних оцінок"),
    task_markup("neutral", "Перевірка вручну", "Перевірити економічну ефективність заходів",
                "Оцінювання виконується в розділі «Економічний аналіз»; факт перевірки тут не зберігається"),
])


# Загальні KPI та розподіл завжди відображають поточні дані всієї системи.
st.html(f'<div class="cd-body"><section class="cd-kpis" aria-label="Ключові показники">{kpi_html}</section></div>')

left_col, right_col = st.columns(2, gap="medium")
with left_col:
    st.html(f'''<div class="cd-body">
      <div class="cd-card cd-risk-card">
        <div class="cd-card-head">{icon("chart", 21)} Розподіл оцінених ризиків</div>
        <div class="cd-card-body cd-distribution">
          <div class="cd-donut" style="background:{ring_bg}">
            <div class="cd-donut-center"><strong>{total_risks}</strong><span>оцінок ризику</span></div>
          </div>
          <div class="cd-legend">{legend_rows}</div>
        </div>
      </div></div>''')

with right_col:
    with st.container(border=False, key="cd_trend_panel"):
        st.html(f'''<div class="cd-body">
          <div class="cd-card-head">{icon("trend", 21)} Порівняння початкового та прогнозованого ризику</div>
          <div class="cd-trend-body">{chart_markup}
            {metric_summary}
            <div class="cd-trend-note">{h(trend_description)}</div>
          </div></div>''')
        st.html('<div class="cd-filter-caption">Перегляд показників:</div>')
        selected_mode = st.radio(
            "Перегляд показників", VIEW_OPTIONS, horizontal=True,
            label_visibility="collapsed", key="cd_view_mode"
        )
        if selected_mode == VIEW_ASSET:
            if asset_option_ids:
                st.selectbox(
                    "Оберіть актив", asset_option_ids,
                    format_func=lambda aid: f"{asset_lookup[aid]} · {sum(r['asset_id']==aid for r in valid_risks)} оцінок",
                    label_visibility="collapsed", key="cd_selected_asset"
                )
            else:
                st.caption("Немає активів зі збереженими оцінками ризику.")
        elif selected_mode == VIEW_RISK:
            if risk_option_ids:
                st.selectbox(
                    "Оберіть ризик", risk_option_ids,
                    format_func=lambda rid: (
                        f"№{rid} · {risk_lookup[rid]['asset']} · {risk_lookup[rid]['threat']} "
                        f"· {risk_lookup[rid]['score']}/25"
                    ),
                    label_visibility="collapsed", key="cd_selected_risk"
                )
            else:
                st.caption("Збережених ризиків немає.")
        st.html(f'<div class="cd-scope-text">{h(graph_scope)}</div>')

st.html(f'''<div class="cd-body">
    <section class="cd-lower" aria-label="Активи та сповіщення">
        <div class="cd-card">
            <div class="cd-card-head">{icon("database", 21)} Інформаційні активи підприємства</div>
            <div class="cd-table-wrap"><table class="cd-table">
                <thead><tr><th>№</th><th>Назва активу</th><th>Тип</th><th>IP-адреса</th><th>Критичність</th></tr></thead>
                <tbody>{asset_rows}</tbody>
            </table></div>
            <div class="cd-note-box">Відображено {min(len(assets),8)} із {len(assets)} активів. Повний перелік — у розділі «Інформаційні активи».</div>
        </div>
        <div class="cd-card">
            <div class="cd-card-head">{icon("bell", 21)} Оповіщення та завдання</div>
            <div class="cd-alert-content">{alert_html}
                <div class="cd-task-head">Наступні кроки</div>{tasks}
            </div>
        </div>
    </section>
    <p class="cd-micro">Загальні показники — з поточних записів SQLite. Перемикач змінює лише правий графік; прогнозні оцінки не підтверджують фактичного усунення ризиків.</p>
</div>''')

# Окремий якір переміщує спільний футер до низу короткої сторінки.
# На довгих сторінках він лишається у звичайному потоці документа.
st.html('<div class="cd-footer-anchor" aria-hidden="true"></div>')
render_footer()
