"""CyberRisk DSS — економічний аналіз. Без змін структури бази даних."""
from html import escape
import streamlit.components.v1 as components
import streamlit as st
from database import initialize_database, get_connection

initialize_database()

def money(value):
    return f"{value:,.2f}".replace(",", " ").replace(".", ",")

def percent(value):
    return f"{value:.0f}%"

def payback_label(years):
    if years is None:
        return "Не окупається"
    if years == 0:
        return "Одразу"
    months = years * 12
    if months < 1:
        return f"{round(years * 365):d} дн. (орієнтовно)"
    if months < 12:
        return f"{months:.1f}".replace(".", ",") + " міс."
    rounded = round(years, 1)
    number = f"{rounded:.1f}".replace(".", ",") if rounded != int(rounded) else str(int(rounded))
    if rounded == int(rounded):
        n = int(rounded)
        unit = "рік" if n % 10 == 1 and n % 100 != 11 else "роки" if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else "років"
    else:
        unit = "року"
    return f"{number} {unit}"

def safe(value):
    return escape(str(value), quote=True)

st.html("""
<style>
/* Єдина фонова сітка, як на головній панелі CyberRisk DSS. */
.stApp {
 background-color: #ffffff !important;
 background-image:
   linear-gradient(to bottom, rgba(54, 110, 184, 0.055) 1px, transparent 1px),
   linear-gradient(to right, rgba(54, 110, 184, 0.055) 1px, transparent 1px) !important;
 background-size: 58px 58px !important;
 background-position: 0 0 !important;
}
section.main .block-container, [data-testid="stMainBlockContainer"] {
 max-width:none!important;width:100%!important;
 padding:1.35rem 1.25rem 2.5rem!important;
}
.ec-hero {position:relative;display:flex;align-items:center;justify-content:space-between;gap:16px;
 background:linear-gradient(112deg,#0c2855,#0752ad 60%,#0870cc);color:white;padding:20px 24px;
 border-radius:13px;box-shadow:0 6px 18px #173b731c;margin-bottom:19px;min-height:118px;}
.ec-kicker {font-size:11px;letter-spacing:1.6px;color:#c8dbf8;font-weight:800;}
.ec-hero h1 {color:white!important;font-size:28px!important;line-height:1.2;margin:9px 0!important;font-weight:800;}
.ec-hero p {color:#e4edfb!important;font-size:14px;margin:0;}
.ec-hero-brand {display:flex;align-items:center;gap:17px;}
.ec-symbol {font-weight:800;width:68px;height:68px;border:1px solid #ffffff55;background:#ffffff20;border-radius:16px;
 display:flex;align-items:center;justify-content:center;font-size:36px;color:#fff;flex-shrink:0;}
.ec-chart-callout {text-align:center;margin:-3px auto 4px;max-width:220px;border:1px solid #a3e0b4;background:#e8faee;border-radius:8px;padding:8px;color:#08733a;font-size:14px;font-weight:800;}
.ec-panel {background:#fff;border:1px solid #d4e4f9;border-radius:13px;padding:18px 20px;
 box-shadow:0 3px 11px #1948780a;margin:7px 0 12px;}
.ec-panel h3 {font-size:17px;color:#163e78;margin:0 0 14px;font-weight:800;}
.ec-selector-head {background:#f7faff;border:1px solid #d4e4f9;border-radius:13px;
 padding:13px 15px 0;margin-bottom:13px;min-height:100px;}
.ec-selector-title {text-align:center;color:#163d79;font-size:15px;font-weight:800;margin-bottom:8px;}
.ec-section-title {font-size:19px;font-weight:800;color:#163e78;margin:5px 0 13px;}
.ec-input-panel {background:white;border:1px solid #d4e4f9;border-radius:13px;padding:15px 19px 8px;margin:8px 0 17px;}
.ec-input-panel label {color:#173e77!important;font-weight:650!important;font-size:14px!important;}
.ec-input-panel [data-testid="stNumberInput"] {margin-bottom:0!important;}
.ec-input-panel [data-testid="stVerticalBlock"] {gap:0.55rem!important;}
.ec-kpi {border:1px solid #d9e7f8;border-radius:12px;padding:16px 12px;min-height:125px;
 text-align:center;background:#eaf2fe;display:flex;flex-direction:column;align-items:center;justify-content:center;}
.ec-kpi.green {background:#e8f9ef;}
.ec-kpi.navy {background:linear-gradient(110deg,#15376c,#2865b5);border-color:#285ca4;}
.ec-kpi .label {color:#244775;font-size:14px;font-weight:750;line-height:1.35;min-height:37px;}
.ec-kpi .value {font-size:27px;font-weight:850;color:#153d7d;margin-top:7px;line-height:1.2;}
.ec-kpi.green .value {color:#087534;}
.ec-kpi.navy .label {color:#fff;}
.ec-kpi.navy .value {color:#77e7a2;}
.ec-two-panel {min-height:390px;display:flex;flex-direction:column;}
.ec-chart-wrap {height:345px;display:flex;align-items:center;justify-content:center;}
.ec-chart-wrap svg {width:100%;height:100%;max-width:760px;}
.ec-note {background:#f0f6ff;color:#3e6494;border-radius:9px;padding:10px 12px;font-size:13px;margin-top:8px;}
.ec-table {width:100%;border-collapse:collapse;color:#173e78;font-size:14px;table-layout:fixed;}
.ec-table th:nth-child(1){width:42%}.ec-table th:nth-child(2){width:37%}.ec-table th:nth-child(3){width:21%}
.ec-table th {background:#dceafd;text-align:left;padding:12px 9px;font-weight:800;border-bottom:2px solid #bad3f6;}
.ec-table td {padding:11px 9px;border-bottom:1px solid #dce8f7;vertical-align:top;}
.ec-table td:last-child {text-align:right;font-weight:800;white-space:nowrap;}
.ec-table tr:last-child td {background:#eaf3ff;font-weight:800;}
.ec-result {background:linear-gradient(110deg,#14366b,#1255ac);padding:18px 20px;border-radius:13px;margin-top:13px;color:white;}
.ec-result h3 {color:white;font-size:19px;margin:0 0 12px;}
.ec-result-inner {background:#eaf3ff;border-radius:11px;padding:18px;display:flex;align-items:center;gap:17px;color:#163d78;line-height:1.65;font-size:14px;}
.ec-status {height:48px;width:48px;border-radius:50%;background:#cbf6dd;display:flex;
 align-items:center;justify-content:center;color:#07833b;font-size:29px;flex-shrink:0;}
.ec-status.bad {background:#fff0dc;color:#b96000;}
.ec-result-inner strong {color:#087535;font-size:17px;}
/* Колір лише заголовка висновку; зовнішній синій фон не змінюємо. */
.ec-result-inner strong.ec-conclusion-positive {color:#087535!important;}
.ec-result-inner strong.ec-conclusion-negative {color:#d12b43!important;}
.ec-result-inner strong.ec-conclusion-neutral {color:#28578f!important;}
.ec-result-inner strong.bad {color:#d12b43!important;}
.ec-footnote {color:#7c90ab;font-size:12px;margin:13px 0 22px;line-height:1.6;}
.ec-footer {border-top:1px solid #d8e6f6;text-align:center;padding:23px 10px 14px;color:#8094ae;font-size:11px;}
.ec-footer strong {display:block;color:#173d79;font-size:17px;margin-bottom:8px;}
@media(max-width:900px) {
 [data-testid="stMainBlockContainer"] {padding:1rem!important;}
 .ec-hero h1 {font-size:23px!important;}
 .ec-symbol {width:50px;height:50px;font-size:26px;}
 .ec-kpi .value {font-size:21px;}
 .ec-panel {padding:14px;}
}

/* v5: одна рамка на картку — селектори адресуються за унікальними ключами,
   а не через :has(), який помилково стилізував вкладені батьківські блоки. */
.ec-hero {min-height:148px!important;padding:26px 30px!important;margin-bottom:22px!important;
 background:linear-gradient(112deg,#112d59 0%,#1c4b89 57%,#2867b9 100%)!important;}
.ec-hero-brand {gap:0!important;}
.ec-symbol {width:72px!important;height:72px!important;}
.st-key-ec_risk_selector, .st-key-ec_measure_selector {
 background:#f6f9ff!important;border:1px solid #cfe0fb!important;border-radius:13px!important;
 box-shadow:0 2px 8px #18467b08!important;
 padding:13px 16px 14px!important;
}
.st-key-ec_risk_selector .ec-selector-title,
.st-key-ec_measure_selector .ec-selector-title {
 text-align:center!important;color:#153d78!important;font-size:15px!important;
 font-weight:800!important;margin:0 0 10px!important;
}
.st-key-ec_risk_selector [data-baseweb="select"] > div,
.st-key-ec_measure_selector [data-baseweb="select"] > div {
 background:#eef4ff!important;border:1px solid #d6e4fa!important;
 border-radius:8px!important;min-height:44px!important;
}
/* Параметри: не стилізуємо предків через :has() — тільки окрему картку. */
.st-key-ec_parameters {
 background:#fff!important;border:1px solid #d4e3f8!important;
 border-radius:13px!important;padding:17px 19px 13px!important;
}
.st-key-ec_parameters .ec-params-title {
 font-size:18px!important;font-weight:800!important;color:#173e78!important;margin:0 0 12px!important;
}
.st-key-ec_parameters [data-testid="stNumberInput"] {
 background:#f6f9ff!important;border:1px solid #e0eaf8!important;
 border-radius:10px!important;padding:8px 11px 9px!important;
}
.st-key-ec_parameters [data-testid="stNumberInput"] label {
 color:#153b73!important;font-weight:700!important;font-size:13px!important;
}
.st-key-ec_parameters [data-testid="stNumberInput"] [data-baseweb="input"] {
 background:#edf3ff!important;border-radius:7px!important;
}
@media(max-width:900px){.ec-hero{min-height:126px!important;padding:20px!important}}



/* v6: один власний контур замість стандартного Streamlit border=True */
.ec-hero {min-height:168px!important;padding:32px 34px!important;box-sizing:border-box!important;}
.ec-hero .ec-kicker {font-size:12px!important;}
.ec-hero h1 {font-size:30px!important;line-height:1.3!important;margin:10px 0!important;}
.ec-hero p {font-size:14px!important;line-height:1.5!important;}
.ec-symbol {width:72px!important;height:72px!important;border-radius:15px!important;background:#ffffff1c!important;}
.st-key-ec_risk_selector,.st-key-ec_measure_selector {
  background:#f6f9ff!important;border:1px solid #cfe0fb!important;
  border-radius:12px!important;padding:20px 20px 22px!important;
  min-height:120px!important;box-shadow:none!important;
}
.st-key-ec_risk_selector [data-baseweb="select"] > div,
.st-key-ec_measure_selector [data-baseweb="select"] > div {
  min-height:54px!important;background:#eaf2ff!important;border:1px solid #d1e1fa!important;
  border-radius:9px!important;
}
.st-key-ec_parameters {background:#fff!important;border:1px solid #d4e3f8!important;
 border-radius:12px!important;padding:23px 22px 20px!important;margin-top:14px!important;box-shadow:none!important;}
.st-key-ec_parameters .ec-params-title {margin-bottom:18px!important;}
.st-key-ec_parameters [data-testid="stNumberInput"] {
 min-height:75px!important;background:#f6f9ff!important;border:1px solid #dbe7f9!important;
 border-radius:10px!important;padding:10px 12px!important;box-sizing:border-box!important;}
.st-key-ec_parameters [data-testid="stNumberInput"] [data-baseweb="input"] {
 min-height:34px!important;background:#edf3ff!important;}
.st-key-ec_parameters [data-testid="stNumberInput"] label {line-height:1.4!important;}
@media(max-width:900px){.ec-hero{min-height:145px!important;padding:23px!important;}}


/* v7: надійна CSS-іконка (без SVG, який не відображався) */
.ec-symbol {display:flex!important;align-items:center!important;justify-content:center!important;flex:none!important;}
.ec-bars {display:flex;align-items:flex-end;justify-content:center;gap:5px;width:42px;height:42px;border-bottom:3px solid #fff;padding:0 3px 3px;box-sizing:border-box;}
.ec-bars i {display:block;width:7px;border:2px solid #fff;border-radius:3px 3px 0 0;background:#ffffff2b;box-sizing:border-box;}
.ec-bars i:nth-child(1){height:14px}.ec-bars i:nth-child(2){height:25px}.ec-bars i:nth-child(3){height:19px}.ec-bars i:nth-child(4){height:35px}
/* Контрастна блакитна секція параметрів із білими полями */
.st-key-ec_parameters {
 background:#edf4ff!important;border:1px solid #cbdffc!important;
 border-radius:13px!important;padding:24px 23px 20px!important;
}
.st-key-ec_parameters [data-testid="stNumberInput"] {
 background:#ffffff!important;border:1px solid #cbdcf6!important;
 min-height:78px!important;border-radius:10px!important;
 padding:10px 12px!important;
}
.st-key-ec_parameters [data-testid="stNumberInput"] [data-baseweb="input"] {
 background:#f7faff!important;border:1px solid #e1eafa!important;border-radius:7px!important;
}
.st-key-ec_parameters [data-testid="stNumberInput"] input {color:#15386b!important;font-weight:700!important;}
.st-key-ec_parameters [data-testid="stNumberInput"] label {color:#163b72!important;font-weight:600!important;}
.st-key-ec_parameters .ec-params-title {color:#12376c!important;}


/* v8 — compact unified KPI design, matching approved reference */
.ec-kpi-heading {font-size:17px;font-weight:800;color:#123d78;margin:13px 0 12px;padding:10px 14px 0;}
.ec-kpi {min-height:108px!important;padding:12px 9px!important;border-radius:11px!important;
 background:linear-gradient(135deg,#f2f7ff,#e7f0ff)!important;border:1px solid #d9e7fa!important;
 box-shadow:none!important;}
.ec-kpi.green {background:linear-gradient(135deg,#f0fcf4,#e5f8eb)!important;border-color:#d7f0df!important;}
.ec-kpi.payback {background:linear-gradient(135deg,#f1f7ff,#e7f0ff)!important;border-color:#d9e7fa!important;}
.ec-kpi .label {font-size:12px!important;min-height:30px!important;line-height:1.3!important;color:#173f78!important;}
.ec-kpi .value {font-size:24px!important;margin-top:5px!important;color:#113d7e!important;}
.ec-kpi.green .value {color:#087d35!important;}
.ec-kpi.payback .value {color:#153d79!important;}
@media(max-width:1100px){.ec-kpi .label{font-size:11px!important}.ec-kpi .value{font-size:20px!important}}

.st-key-ec_kpi_panel {background:#f8fbff!important;border:1px solid #d8e6fa!important;
 border-radius:13px!important;padding:5px 14px 15px!important;margin:10px 0 16px!important;}
.st-key-ec_kpi_panel [data-testid="stHorizontalBlock"] {gap:12px!important;}

/* v10 — затверджений варіант: світла панель, виразні картки */
.st-key-ec_kpi_panel {
  background:linear-gradient(125deg,#ffffff 0%,#fbfdff 50%,#f5f9ff 100%)!important;
  border:1px solid #c9dcf8!important;
  border-radius:17px!important;
  box-shadow:0 6px 19px rgba(22,64,121,.07)!important;
  padding:19px 20px 24px!important;
  margin:15px 0 20px!important;
}
.st-key-ec_kpi_panel [data-testid="stHorizontalBlock"] {gap:13px!important;}
.ec-kpi-heading {
  color:#123b77!important;font-size:20px!important;font-weight:800!important;
  margin:0 0 19px!important;padding:0!important;
}
.ec-kpi {
  min-height:132px!important;padding:19px 11px!important;border-radius:13px!important;
  background:linear-gradient(130deg,#ffffff 0%,#e0edff 100%)!important;
  border:1px solid #c3d9fa!important;
  box-shadow:0 5px 13px rgba(26,71,132,.11)!important;
  display:flex!important;align-items:center!important;justify-content:center!important;
  flex-direction:column!important;box-sizing:border-box!important;
}
.ec-kpi.green {
  background:linear-gradient(130deg,#f7fff9 0%,#d8f6e4 100%)!important;
  border-color:#b8e8cb!important;
}
.ec-kpi.payback {
  background:linear-gradient(110deg,#12305d 0%,#1d4b8d 55%,#2866b7 100%)!important;
  border-color:#2d65b2!important;
  box-shadow:0 7px 18px rgba(13,48,100,.22)!important;
}
.ec-kpi .label {
  color:#173e77!important;font-size:13px!important;font-weight:750!important;
  min-height:36px!important;line-height:1.4!important;
}
.ec-kpi .value {
  color:#123d7d!important;font-size:clamp(19px,1.7vw,27px)!important;
  font-weight:850!important;margin-top:9px!important;
}
.ec-kpi.green .value {color:#078341!important;}
.ec-kpi.payback .label {color:#ffffff!important;}
.ec-kpi.payback .value {color:#7af3b5!important;}
/* Колір змінюється лише для тексту; синій фон картки незмінний. */
.ec-kpi.payback .value.ec-positive {color:#7af3b5!important;}
.ec-kpi.payback .value.ec-negative {color:#ff858e!important;}
.ec-kpi.payback .value.ec-neutral {color:#e3edff!important;}
.ec-kpi.payback .value.ec-warning {color:#ffbf72!important;}
.ec-kpi.payback .ec-payback-hint {font-size:11px;line-height:1.3;color:#ffe0b6!important;margin-top:6px;font-weight:650;}
.ec-kpi.green .value.ec-negative {color:#c92b42!important;}
.ec-kpi .value.ec-negative {color:#c92b42!important;}
@media(max-width:1100px){
  .ec-kpi .label{font-size:11px!important;}
  .ec-kpi .value{font-size:20px!important;}
}

/* Пояснення ROI та зменшення втрат: світла смуга під KPI-картками */
.ec-kpi-explainer {
  margin-top:15px;padding:12px 16px;
  border:1px solid #d4e5f8;border-radius:11px;
  background:linear-gradient(110deg,#f8fbff,#eef6ff);
  color:#36587f;font-size:14px;line-height:1.65;
  display:flex;align-items:flex-start;gap:11px;
}
.ec-kpi-explainer strong {color:#143d78;font-weight:800;}
.ec-kpi-explainer-icon {color:#2565b4;font-size:19px;line-height:1.2;flex-shrink:0;}
.ec-kpi-explainer-divider {color:#9bb3d1;padding:0 6px;}

/* Окрема ніжно-блакитна панель графіка — непрозора поверх сітки сторінки */
.st-key-ec_chart_panel {
  background:linear-gradient(135deg,#f3f8ff 0%,#eaf3ff 100%)!important;
  border:1px solid #bad4f4!important;
  border-radius:16px!important;
  box-shadow:0 6px 18px rgba(20,66,126,.10)!important;
  padding:21px 18px 18px!important;
  overflow:hidden!important;
}
.st-key-ec_chart_panel .ec-section-title {
  color:#123d78!important;
  margin:0 0 12px!important;
}
.st-key-ec_chart_panel .ec-note {
  background:#e0edff!important;
  border:1px solid #c8dcf9!important;
  border-radius:10px!important;
  color:#315c95!important;
}

/* Final: white chart panel with delicate blue gradient and border */
.st-key-ec_chart_panel {
  background:#ffffff!important;
  border:1px solid #a9c9f3!important;
  border-radius:16px!important;
  padding:20px 18px 17px!important;
  box-shadow:0 7px 22px rgba(25,70,133,.10)!important;
  overflow:hidden!important;
}
/* Both adjacent panels use a matching minimum height. */
.st-key-ec_chart_panel, .st-key-ec_details_panel {
  min-height:485px!important;
  box-sizing:border-box!important;
}
.st-key-ec_details_panel {
  background:#ffffff!important;
  border:1px solid #a9c9f3!important;
  border-radius:16px!important;
  padding:20px 18px 17px!important;
  box-shadow:0 7px 22px rgba(25,70,133,.10)!important;
}
.st-key-ec_chart_panel .ec-section-title {margin:2px 0 12px!important;}
.st-key-ec_chart_panel .ec-note {
  background:#eef5ff!important;
  border:1px solid #e1ebfa!important;
  border-radius:9px!important;
  margin-top:8px!important;
}

.st-key-ec_details_panel .ec-row-icon {display:inline-block;width:19px;margin-right:6px;color:#1259a0;font-weight:900;font-size:15px;vertical-align:middle;}
.st-key-ec_details_panel .ec-table tbody tr:last-child .ec-row-icon{color:#fff;}
/* vNext: two compact, equal-height report cards */
.st-key-ec_chart_panel, .st-key-ec_details_panel {
  min-height:485px!important;
  background:#ffffff!important;
  border:1px solid #8fbdf8!important;
  border-radius:17px!important;
  box-shadow:0 5px 16px rgba(21,68,128,.08)!important;
  padding:0 16px 14px!important;
  overflow:hidden!important;
  box-sizing:border-box!important;
}
.st-key-ec_chart_panel .ec-section-title,
.st-key-ec_details_panel .ec-section-title {
  background:linear-gradient(90deg,#edf5ff,#e4f0ff)!important;
  color:#0e3674!important;
  font-size:18px!important;
  font-weight:800!important;
  margin:0 -16px 9px!important;
  padding:16px 17px!important;
  min-height:56px!important;
  box-sizing:border-box!important;
}
.st-key-ec_chart_panel .ec-note {
  margin-top:4px!important;
  background:#eaf3ff!important;
  border:1px solid #c3dafa!important;
  padding:10px 12px!important;
  border-radius:10px!important;
  font-size:12px!important;
  line-height:1.4!important;
}
.st-key-ec_details_panel .ec-table {
  width:100%!important;
  border-collapse:separate!important;
  border-spacing:0!important;
  table-layout:fixed!important;
  font-size:12.5px!important;
  border:1px solid #c6dbf7!important;
  border-radius:10px!important;
  overflow:hidden!important;
}
.st-key-ec_details_panel .ec-table th:nth-child(1){width:44%!important}
.st-key-ec_details_panel .ec-table th:nth-child(2){width:34%!important}
.st-key-ec_details_panel .ec-table th:nth-child(3){width:22%!important}
.st-key-ec_details_panel .ec-table thead th {
  background:linear-gradient(180deg,#1461a7,#0c3977)!important;
  color:#fff!important;
  border:0!important;
  border-right:1px solid #ffffff44!important;
  padding:12px 9px!important;
  font-weight:800!important;
}
.st-key-ec_details_panel .ec-table th:last-child {text-align:right!important;border-right:0!important}
.st-key-ec_details_panel .ec-table tbody td {
  padding:10px 9px!important;
  border-bottom:1px solid #d5e3f6!important;
  color:#163b72!important;
  line-height:1.25!important;
  vertical-align:middle!important;
  overflow-wrap:anywhere!important;
}
.st-key-ec_details_panel .ec-table tbody tr:nth-child(even):not(:last-child) td {background:#f5f9ff!important}
.st-key-ec_details_panel .ec-table tbody tr:not(:last-child) td:last-child {
  background:#eaf3ff!important;
  font-weight:800!important;
  text-align:right!important;
  white-space:nowrap!important;
}
.st-key-ec_details_panel .ec-table tbody tr:nth-child(even):not(:last-child) td:last-child {background:#e1eeff!important}
.st-key-ec_details_panel .ec-table tbody tr:last-child td {
  background:linear-gradient(180deg,#2369b0,#11447f)!important;
  color:#fff!important;
  border-bottom:0!important;
  font-weight:800!important;
}
.st-key-ec_details_panel .ec-table tbody tr:last-child td:last-child {text-align:right!important;white-space:nowrap!important}
/* Фінальне вирівнювання: однакова фактична висота двох панелей.
   470 px замість попереднього min-height:485px; без змін графіка й таблиці. */
.st-key-ec_chart_panel,
.st-key-ec_details_panel {
  height: 470px !important;
  min-height: 470px !important;
  max-height: 470px !important;
  box-sizing: border-box !important;
}

/* На вузькому екрані вміст визначає висоту, щоб не обрізати дані. */
@media (max-width: 900px) {
  .st-key-ec_chart_panel,
  .st-key-ec_details_panel {
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
  }
}


/* Підпис залишається у звичайному потоці Streamlit.
   Не використовуємо absolute: воно ховало підпис через вкладену структуру st.html. */
.st-key-ec_chart_panel .ec-note {
  position:static!important;
  margin-top:-25px!important;
  margin-bottom:0!important;
  background:#eaf3ff!important;
  border:1px solid #c3dafa!important;
  border-radius:10px!important;
  padding:10px 12px!important;
  box-sizing:border-box!important;
}
@media (max-width:900px) {
  .st-key-ec_chart_panel .ec-note {margin-top:8px!important;}
}

</style>
""")

# Верхній банер: лише назва та іконка аналітики праворуч.
st.html("""<div class="ec-hero">
 <div class="ec-hero-brand"><div><div class="ec-kicker">CYBERRISK DSS / УПРАВЛІННЯ РИЗИКАМИ</div>
 <h1>Економічний аналіз</h1>
 <p>Оцінка витрат та економічної ефективності заходів захисту для зниження кіберризиків</p></div></div>
 <div class="ec-symbol" aria-label="Економічна аналітика"><span class="ec-bars"><i></i><i></i><i></i><i></i></span></div>
</div>""")

with get_connection() as con:
    risks = con.execute("""SELECT r.id,a.name,t.name,r.risk_score,r.probability,r.impact
      FROM risks r JOIN assets a ON a.id=r.asset_id
      JOIN threats t ON t.id=r.threat_id ORDER BY r.id DESC""").fetchall()
    measures = con.execute("""SELECT id,risk_id,name,implementation_cost,probability_reduction,impact_reduction
      FROM security_measures ORDER BY id""").fetchall()

if not risks:
    st.info("Спочатку створіть оцінку ризику в розділі «Оцінювання ризиків».")
    st.stop()

risk_map = {int(r[0]):r for r in risks}
risk_labels = {int(r[0]):f"№{r[0]} — {r[1]} · {r[2]} · R={r[3]}/25" for r in risks}
col_a, col_b = st.columns(2, gap="medium")
with col_a:
    with st.container(border=False, key="ec_risk_selector"):
        st.html('<div class="ec-selector-title">Оберіть ризик для аналізу</div>')
        risk_id = st.selectbox("Ризик", list(risk_labels),
                               format_func=lambda k: risk_labels[k],
                               label_visibility="collapsed", key="ec_risk")
related = {int(m[0]): m for m in measures if int(m[1]) == risk_id}
with col_b:
    with st.container(border=False, key="ec_measure_selector"):
        st.html('<div class="ec-selector-title">Оберіть захід захисту</div>')
        if related:
            measure_id = st.selectbox("Захід", list(related),
                                      format_func=lambda k: related[k][2],
                                      label_visibility="collapsed", key="ec_measure")
        else:
            measure_id = None
            st.info("Для цього ризику заходів поки немає.")
if measure_id is None:
    st.stop()

risk = risk_map[risk_id]
measure = related[measure_id]
p0,i0 = int(risk[4]),int(risk[5])
p1 = max(1,p0-int(measure[4]))
i1 = max(1,i0-int(measure[5]))
r0,r1 = p0*i0,p1*i1
cost = float(measure[3])

parameter_card = st.container(border=False, key="ec_parameters")
with parameter_card:
    st.html('<div class="ec-params-title">▤ &nbsp;Економічні параметри</div>')
    a,b,c = st.columns(3,gap="medium")
    with a:
        aro = st.number_input("Очікувана річна частота інцидентів (ARO, разів/рік)",
                              min_value=0.0,value=1.0,step=0.1,format="%.2f")
    with b:
        sle = st.number_input("Оціночні втрати від інциденту (SLE, ум. од.)",
                              min_value=0.0,value=10000.0,step=500.0,format="%.2f")
    with c:
        freq_drop = st.number_input("Прогнозоване зниження частоти інцидентів, %",
                                    min_value=0.0,max_value=100.0,value=50.0,step=5.0)
    d,e,f = st.columns(3,gap="medium")
    with d:
        severity_drop = st.number_input("Прогнозоване зниження збитку від інциденту, %",
                                        min_value=0.0,max_value=100.0,value=0.0,step=5.0)
    with e:
        maintenance = st.number_input("Річні витрати на експлуатацію (O, ум. од./рік)",
                                      min_value=0.0,value=0.0,step=100.0,format="%.2f")
    with f:
        horizon = st.number_input("Горизонт оцінювання (T, роки)",
                                  min_value=1,max_value=30,value=3,step=1)
    st.caption(f"SLE у форматі звіту: **{money(sle)} ум. од.** · Вхідні економічні оцінки є експертними припущеннями; вони не виводяться автоматично з балів ризику P × I.")

ale0 = aro*sle
aro1 = aro*(1-freq_drop/100)
sle1 = sle*(1-severity_drop/100)
ale1 = aro1*sle1
saving = ale0-ale1
annual_net = saving-maintenance
first_net = annual_net-cost
total_cost = cost+maintenance
roi = (first_net/total_cost*100) if total_cost>0 else None
payback = (cost/annual_net) if annual_net>0 else (0.0 if cost==0 and annual_net>0 else None)
horizon_net = annual_net*horizon-cost
# Три сценарії: окупність у горизонті, після горизонту, або відсутня.
if annual_net > 0:
    payback_status = "positive" if payback is not None and payback <= horizon else "warning"
elif cost == 0 and annual_net == 0:
    payback_status = "neutral"
else:
    payback_status = "negative"
payback_display = (
    "Не окупається" if payback_status == "negative"
    else "Не визначено" if payback_status == "neutral"
    else payback_label(payback)
)
payback_hint = (
    f"Поза горизонтом оцінювання ({horizon} р.)" if payback_status == "warning" else ""
)
loss_drop = ((ale0-ale1)/ale0*100) if ale0>0 else 0.0

kpi_panel = st.container(border=False, key="ec_kpi_panel")
with kpi_panel:
    st.html('<div class="ec-kpi-heading">▥ &nbsp;Ключові економічні показники</div>')
    kpis = [
        ("Очікувані річні втрати<br>до заходу (ALE₀)", money(ale0), "", ""),
        ("Очікувані річні втрати<br>після заходу (ALE₁)", money(ale1), "", ""),
        ("Річна економія<br>(ΔALE)", money(saving), "green" if saving > 0 else "",
         "ec-negative" if saving < 0 else ""),
        ("ROI<br>(перший рік)", percent(roi) if roi is not None else "—",
         "green" if roi is not None and roi >= 0 else "",
         "ec-negative" if roi is not None and roi < 0 else ""),
        ("Термін окупності<br>(PP)", payback_display, "payback",
         f"ec-{payback_status}"),
    ]
    kcols = st.columns(5, gap="small")
    for col, (label, value, kind, value_class) in zip(kcols, kpis):
        with col:
            hint_html = ('<div class="ec-payback-hint">' + safe(payback_hint) + '</div>') if kind == "payback" and payback_hint else ""
            st.html(
                f'<div class="ec-kpi {kind}"><div class="label">{label}</div>'
                f'<div class="value {value_class}">{safe(value)}</div>{hint_html}</div>'
            )

    # ROI — відносна чиста вигода, тому показник може перевищувати 100%.
    if roi is None:
        roi_explanation = (
            "ROI не визначено: сумарні витрати на впровадження й підтримку "
            "дорівнюють нулю."
        )
    else:
        multiple = roi / 100
        roi_explanation = (
            f"ROI {percent(roi)} означає, що на кожну 1 ум. од. витрат "
            f"припадає {money(multiple)} ум. од. прогнозованої "
            f"чистої вигоди за перший рік."
        )
    st.html(
        '<div class="ec-kpi-explainer">'
        '<span class="ec-kpi-explainer-icon">ⓘ</span>'
        '<div><strong>Як читати показники:</strong> '
        + safe(roi_explanation)
        + ' <span class="ec-kpi-explainer-divider">•</span> '
        + f'Прогнозоване зменшення річних втрат — <strong>{safe(percent(loss_drop))}</strong> '
        + '(цей показник має межі від 0% до 100%).'
        + '</div></div>'
    )

st.write("")
left,right = st.columns(2,gap="medium")
with left:

    # Адаптивна шкала Y: округлені поділки без обрізаних значень.
    import math
    peak = max(ale0, ale1, 1.0)
    raw_step = peak * 1.2 / 5
    magnitude = 10 ** math.floor(math.log10(raw_step))
    step = next(v * magnitude for v in (1, 2, 2.5, 5, 10) if v * magnitude >= raw_step)
    axis_max = step * 5
    plot_top, plot_bottom = 105, 238
    plot_height = plot_bottom - plot_top
    y0 = plot_bottom - plot_height * ale0 / axis_max
    y1 = plot_bottom - plot_height * ale1 / axis_max
    h0, h1 = plot_bottom - y0, plot_bottom - y1
    grid_lines = []
    for tick in range(6):
        value = step * tick
        y = plot_bottom - plot_height * tick / 5
        grid_lines.append(
            f'<line x1="90" y1="{y:.2f}" x2="645" y2="{y:.2f}" '
            f'stroke="#dce8f7" stroke-width="1" stroke-dasharray="4 5"/>'
            f'<text x="80" y="{y+5:.2f}" text-anchor="end" fill="#56749c" '
            f'font-size="13">{safe(f"{value:,.0f}".replace(",", " "))}</text>'
        )
    grid_svg = "".join(grid_lines)
    # Індикатор закріплений у верхній зоні SVG, окремо від стовпчиків та їхніх підписів.
    chart = f"""<div class="ec-chart-wrap"><div class="ec-chart-badge">↓ Зменшення втрат<br><b>на {safe(percent(loss_drop))}</b></div><svg viewBox="0 0 680 322" role="img" aria-label="Порівняння прогнозованих річних втрат">
      <text x="22" y="142" transform="rotate(-90 22 142)" text-anchor="middle" fill="#496b97" font-size="13">Втрати, ум. од.</text>
      {grid_svg}
      <line x1="90" y1="105" x2="90" y2="238" stroke="#b8cde9" stroke-width="1.4"/>
      <rect x="165" y="{y0:.2f}" width="148" height="{h0:.2f}" rx="5" fill="#438cef"/>
      <rect x="391" y="{y1:.2f}" width="148" height="{h1:.2f}" rx="5" fill="#63c783"/>
      <text x="239" y="{max(90,y0-10):.2f}" text-anchor="middle" fill="#123b77" font-size="18" font-weight="800">{safe(money(ale0))}</text>
      <text x="465" y="{max(90,y1-10):.2f}" text-anchor="middle" fill="#123b77" font-size="18" font-weight="800">{safe(money(ale1))}</text>
      <text x="239" y="260" text-anchor="middle" fill="#173d77" font-size="15" font-weight="700">До впровадження</text>
      <text x="239" y="279" text-anchor="middle" fill="#173d77" font-size="15" font-weight="700">заходу (ALE₀)</text>
      <text x="465" y="260" text-anchor="middle" fill="#173d77" font-size="15" font-weight="700">Після впровадження</text>
      <text x="465" y="279" text-anchor="middle" fill="#173d77" font-size="15" font-weight="700">заходу (ALE₁)</text>
      </svg></div>"""
    note = (f'<div class="ec-note">Прогнозоване зменшення річних втрат: <b>{safe(percent(loss_drop))}</b>. '
            f'Окремо оцінка кіберризику змінюється з <b>{r0}/25</b> до <b>{r1}/25</b>.</div>')
    with st.container(border=False, key="ec_chart_panel"):
        st.html('<div class="ec-section-title">▥ &nbsp;Порівняння прогнозованих річних втрат</div>')
        components.html(
            '<!DOCTYPE html><html lang="uk"><head><meta charset="utf-8">'
            '<style>html,body{margin:0;background:#fff;font-family:Arial,sans-serif}'
            '.ec-chart-wrap{height:303px;display:flex;flex-direction:column;align-items:stretch;justify-content:flex-start;background:#ffffff;border-radius:11px}'
            '.ec-chart-badge{align-self:flex-end;margin:0 18px 0 0;min-width:175px;box-sizing:border-box;text-align:center;background:#eaf3ff;border:1px solid #a9c9f3;border-radius:9px;color:#17467f;font-weight:800;font-size:12px;line-height:1.3;padding:5px 9px;flex:none}' + '.ec-chart-badge b{font-size:15px;color:#0e3c79}' + '.ec-chart-wrap svg{width:100%;height:257px;flex:1;min-height:0;max-width:none}</style>'
            '</head><body>' + chart + '</body></html>',
            height=313, scrolling=False
        )
        st.html(note)
with right:

    rows=[
        ("Річні втрати до заходу (ALE₀)","ARO × SLE",money(ale0)),
        ("Річні втрати після заходу (ALE₁)","ARO₁ × SLE₁",money(ale1)),
        ("Річна економія (ΔALE)","ALE₀ − ALE₁",money(saving)),
        ("Вартість впровадження (C)","Дані заходу",money(cost)),
        ("Річна підтримка (O)","Експертна оцінка",money(maintenance)),
        ("ROI першого року","(ΔALE − C − O) / (C + O)",percent(roi) if roi is not None else "—"),
        ("Термін окупності (PP)","C / (ΔALE − O)",payback_display),
        (f"Чистий ефект за {horizon} р.","(ΔALE − O) × T − C",money(horizon_net)),
    ]
    row_icons = ["▱", "▱", "▥", "◈", "⚙", "%", "◷", "↗"]
    trs = "".join(
        f'<tr><td><span class="ec-row-icon" aria-hidden="true">{icon}</span>{safe(name)}</td>'
        f'<td>{safe(formula)}</td><td>{safe(value)}</td></tr>'
        for icon, (name, formula, value) in zip(row_icons, rows)
    )
    with st.container(border=False, key="ec_details_panel"):
        st.html('<div class="ec-section-title">▤ &nbsp;Деталізація розрахунків</div>')
        st.html('<table class="ec-table"><thead><tr><th>Показник</th><th>Формула</th><th>Значення</th></tr></thead>'
                f'<tbody>{trs}</tbody></table>')

is_positive=horizon_net>0
conclusion_class = (
    "ec-conclusion-positive" if horizon_net > 0
    else "ec-conclusion-negative" if horizon_net < 0
    else "ec-conclusion-neutral"
)
if is_positive:
    headline="Захід є економічно доцільним за заданих припущень"
elif horizon_net==0:
    headline="За обраний період економічний результат є нульовим"
else:
    headline=f"За обраний період ({horizon} р.) сукупні витрати перевищують прогнозовану економію"
details=(f'Захід «{measure[2]}» прогнозовано зменшує річні втрати '
         f'з {money(ale0)} до {money(ale1)} ум. од. ({percent(loss_drop)}). '
         f'Очікувана річна економія — {money(saving)} ум. од.; '
         f'ROI першого року — {percent(roi) if roi is not None else "не визначено"}; '
         f'термін окупності — {payback_display}'
         f'{f" (поза горизонтом оцінювання {horizon} р.)" if payback_status == "warning" else ""}. '
         f'За {horizon} р. прогнозований чистий економічний ефект — {money(horizon_net)} ум. од. '
         'Результати потрібно перевірити після впровадження заходу.')
st.html(f'<div class="ec-result"><h3>◉ &nbsp;Висновок системи</h3>'
        f'<div class="ec-result-inner"><div class="ec-status {" " if is_positive else "bad"}">'
        f'{"✓" if is_positive else "!"}</div><div>'
        f'<strong class="{conclusion_class}" style="color:{"#087535" if horizon_net > 0 else "#d12b43" if horizon_net < 0 else "#28578f"} !important;display:block;font-weight:800">{safe(headline)}</strong>'
        f'<div>{safe(details)}</div></div></div></div>')
st.html('<div class="ec-footnote">Методика: ALE = ARO × SLE. ROI першого року враховує вартість впровадження та річну підтримку. '
        'Окупність = початкові витрати / (річна економія − річна підтримка). '
        'Модель не враховує дисконтування, інфляцію та часовий розподіл витрат. '
        'Це прогноз на основі експертних припущень, а не підтверджені фактичні збитки.</div>')
try:
    from components import render_footer
    render_footer()
except ImportError:
    st.caption("© 2026 CyberRisk DSS · Усі права захищено")
