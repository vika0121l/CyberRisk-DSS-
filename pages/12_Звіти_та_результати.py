"""Підсумкові звіти CyberRisk DSS на основі наявних записів SQLite."""
import base64
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from html import escape
from io import BytesIO
from threading import RLock

import pandas as pd
import streamlit as st

from components import render_footer
from database import initialize_database
from experiment_store import (
    all_experiments, initialize_experiments, report_measures, report_risks,
    tests_for_experiment,
)


LEVELS = (
    (4, "Дуже низький", "very-low"),
    (9, "Низький", "low"),
    (14, "Середній", "medium"),
    (19, "Високий", "high"),
    (25, "Критичний", "critical"),
)
ALL_LEVELS = "Усі рівні"
ALL_COVERAGE = "Усі ризики"
NO_MEASURES = "Без заходів"
WITH_MEASURES = "Із заходами"
NO_EVIDENCE = "Ще не перевірено"
NO_EXPERIMENTAL_DATA = "Немає експериментальних даних"
EXPERIMENTAL_CHECK = "Експериментальна перевірка"
_PDF_LOCK = RLock()

ICONS = {
    "report": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 17v2m4-5v5m4-8v8"/>',
    "risk": '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M8 15v2m4-5v5m4-9v9"/>',
    "priority": '<path d="M12 3 2.5 20h19L12 3zM12 9v5m0 3h.01"/>',
    "measure": '<path d="M12 3 4 7v5c0 4 3 7.5 8 9 5-1.5 8-5 8-9V7zM8.5 12l2.3 2.4 4.7-5"/>',
    "experiment": '<path d="M9 3h6m-5 0v7l-6 8.5A1.6 1.6 0 0 0 5.3 21h13.4a1.6 1.6 0 0 0 1.3-2.5L14 10V3M7.2 16h9.6"/>',
    "bars": '<path d="M3 11h4v10H3zm7-5h4v15h-4zm7-4h4v19h-4z" fill="currentColor" stroke="none"/>',
    "eye": '<path d="M2 12s3.5-6.5 10-6.5 10 6.5 10 6.5-3.5 6.5-10 6.5S2 12 2 12z"/><circle cx="12" cy="12" r="2.6"/>',
    "filter": '<path d="M3 4h18l-7 8v6l-4 2v-8z"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6"/><path d="m15 15 5 5"/>',
    "asset": '<rect x="3" y="4" width="18" height="6" rx="1.5"/><rect x="3" y="14" width="18" height="6" rx="1.5"/><path d="M7 7h.01M7 17h.01M11 7h6m-6 10h6"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 2.5 2.5L16 9"/>',
    "down": '<path d="M12 4v15m-5-5 5 5 5-5"/>',
    "up": '<path d="M12 20V5m-5 5 5-5 5 5"/>',
    "flat": '<path d="M5 12h14"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5m0-8h.01"/>',
}

CSS = """
<style>
/* Стилі звітів не перевизначають спільне меню і верхню панель Streamlit. */
/* Біле тло й тонка сітка збігаються з іншими сторінками CyberRisk DSS. */
.stApp:has(.rep-hero) [data-testid="stAppViewContainer"] [data-testid="stMain"]
    :is([data-testid="stMainBlockContainer"], .block-container) {
    width: 100% !important;
    max-width: none !important;
    padding-top: 2.85rem !important;
    padding-inline: 1.25rem !important;
    box-sizing: border-box;
}
.stApp:has(.rep-hero) { background: #fff !important; }
.stApp:has(.rep-hero) [data-testid="stAppViewContainer"]::before {
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
    animation: rep-grid-move 35s linear infinite;
}
.stApp:has(.rep-hero) [data-testid="stMain"] {
    position: relative;
    z-index: 1;
    background: transparent !important;
}
@keyframes rep-grid-move {
    from { background-position: 0 0, 0 0, center; }
    to { background-position: 0 120px, 120px 0, center; }
}
@media (prefers-reduced-motion: reduce) {
    .stApp:has(.rep-hero) [data-testid="stAppViewContainer"]::before { animation: none; }
}
.rep-hero {
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
.rep-hero::after {
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
.rep-hero-copy { position: relative; z-index: 1; min-width: 0; }
.rep-eyebrow {
    color: #B9D5F9;
    font-size: 11px;
    font-weight: 750;
    letter-spacing: 1.7px;
    margin-bottom: 12px;
}
.rep-hero h1 {
    color: #FFFFFF !important;
    font-size: clamp(27px, 2.6vw, 38px);
    font-weight: 750;
    margin: 0 0 10px !important;
    line-height: 1.2;
}
.rep-hero p { color: #D9E8FB; font-size: 14px; margin: 0; line-height: 1.6; }
.rep-hero-symbol {
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
.rep-hero-symbol img { display: block; width: 47px; height: 47px; }

.rep-kpis {
    display: grid;
    grid-template-columns: repeat(4,minmax(0,1fr));
    gap: clamp(10px,1vw,18px);
}
.rep-kpi {
    display: flex;
    align-items: center;
    gap: clamp(9px,1.08vw,20px);
    min-width: 0;
    min-height: clamp(81px,5.65vw,98px);
    padding: 11px clamp(10px,1.1vw,20px);
    background: linear-gradient(153deg,#fff,#f0f5fc);
    border: 1px solid #e3edfa;
    border-radius: 16px;
    box-shadow: 0 5px 14px #123c7410;
}
.rep-kpi:first-child { background: linear-gradient(150deg,#fff,#e7f1fe); border-color:#d5e5fa; }
.rep-kpi-icon, .rep-heading-icon, .rep-filter-icon {
    display: grid;
    place-items: center;
    flex: 0 0 clamp(37px,3.45vw,58px);
    aspect-ratio: 1;
    background: linear-gradient(135deg,#e5f0ff,#d5e5fb);
    border-radius: 13px;
}
.rep-kpi-icon img, .rep-heading-icon img { display: block; width: 55%; height: 55%; }
.rep-kpi.rep-priority .rep-kpi-icon { background: #fff0dc; }
.rep-kpi-label { display: block; color: #12315f; font-size: clamp(.79rem,1vw,1rem); font-weight: 560; line-height: 1.25; }
.rep-kpi-value { display: block; color: #0a2552; font-size: clamp(1.58rem,1.9vw,2.05rem); line-height: 1.12; font-weight: 800; }
.rep-kpi-label + .rep-kpi-value { margin-top: 5px; }
.rep-kpi-value + .rep-kpi-label { margin-top: 4px; }
.st-key-rep_filters, .st-key-rep_panels :is(.st-key-rep_risks,.st-key-rep_measures,.st-key-rep_experiments) {
    border: 1px solid #c9dffc !important;
    border-radius: 18px !important;
    background: linear-gradient(120deg,#f0f6ff 0%,#fdfefe 58%,#e9f2ff 100%) !important;
    padding: clamp(13px,1vw,18px) !important;
    box-shadow: 0 5px 13px #123c740b;
}
.st-key-rep_filters { gap: 12px !important; }
.rep-filter-header {
    display: flex;
    align-items: center;
    gap: 11px;
    color: #294795;
    margin: 0;
}
.rep-filter-header p { color: #203b67; margin: 0; font-size: .91rem; }
.rep-filter-header strong { color: #0b2a5b; font-size: 1.04rem; }
.rep-filter-icon { flex-basis: 30px; border-radius: 8px; }
.rep-filter-icon img { display:block; width:18px; height:18px; }
.rep-heading { display: flex; align-items: center; gap: 12px; color: #0b2b5a; margin: 0; }
.rep-heading h2 {
    color: inherit !important;
    font-size: clamp(1.05rem,1.47vw,1.5rem) !important;
    line-height: 1.22 !important;
    margin: 0 !important;
    padding: 0 !important;
}
.rep-heading-icon { flex-basis: clamp(36px,3.3vw,55px); }
.rep-empty img { width: 19px; height: 19px; display: block; }
.rep-caption { color: #345279; font-size: .91rem; margin: 3px 0 0; }
.rep-risk-totals {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 5px 16px;
    padding: 8px 11px;
    border-radius: 9px;
    background: #f1f6fd;
    color: #194577;
    font-size: .85rem;
}
.rep-risk-totals > span { font-weight: 650; white-space: nowrap; }
.rep-risk-totals > span strong { margin-left: 4px; }
.rep-risk-levels {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 3px 12px;
    margin: 0 !important;
    padding: 0 !important;
    list-style: none;
    color: #4d6485;
    font-size: .77rem;
}
.rep-risk-levels li { margin: 0; white-space: nowrap; }
.rep-risk-levels li strong { margin-left: 3px; }
.rep-risk-tone { --rep-tone: #426999; --rep-tint: #f1f6fe; }
.rep-risk-tone.very-low { --rep-tone: #24614c; --rep-tint: #edf8f2; }
.rep-risk-tone.low { --rep-tone: #255a89; --rep-tint: #edf6ff; }
.rep-risk-tone.medium { --rep-tone: #795b12; --rep-tint: #fff8e6; }
.rep-risk-tone.high { --rep-tone: #8a420b; --rep-tint: #faebd8; }
.rep-risk-tone.critical { --rep-tone: #94394c; --rep-tint: #fff0f3; }
.rep-risk-levels .is-present, .rep-risk-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    color: var(--rep-tone);
    background: var(--rep-tint);
    border-radius: 6px;
    padding: 3px 7px;
}
.rep-risk-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; flex: none; }
.rep-risk-score { color:#172f51; font-weight:750; }
.rep-risk-score small { color:#58718e; font-size:.79em; font-weight:650; }
.rep-risk-badge { border-radius:999px; padding:6px 8px; font-size:.82rem; font-weight:700; white-space:nowrap; }
/* Приховуємо лише штатний хрестик цього діалогу, не кнопку «Закрити». */
[role="dialog"]:has(.st-key-rep_risk_dialog) :is(
    button[aria-label="Close"],
    button[aria-label="Close dialog"],
    [data-testid="stDialogCloseButton"],
    [data-testid="stModalCloseButton"]
) { display: none !important; }
.st-key-rep_risk_detail_controls [data-testid="stButton"] button,
.st-key-rep_risk_dialog [data-testid="stButton"] button {
    min-height: 40px;
    border-radius: 9px;
    border-color: #c5d8f1;
    background: #f5f9ff;
    color: #16467f;
}
.st-key-rep_risk_detail_controls [data-testid="stButton"] button:hover,
.st-key-rep_risk_dialog [data-testid="stButton"] button:hover {
    background: #e8f1fe;
    border-color: #8db6ea;
}
.st-key-rep_risk_detail_controls [data-testid="stWidgetLabel"] p {
    color:#345279;
    font-size:.85rem;
    font-weight:650;
}
.rep-risk-dialog-heading {
    display:flex;
    flex-wrap:wrap;
    align-items:center;
    justify-content:space-between;
    gap:8px 14px;
    color:#163965;
    padding:12px 14px;
    background:#edf4ff;
    border:1px solid #d6e5f7;
    border-radius:10px;
}
.rep-risk-dialog-heading strong { display:block; overflow-wrap:anywhere; }
.rep-risk-dialog-heading small { color:#4d6686; }
.rep-risk-dialog-values {
    display:grid;
    grid-template-columns:repeat(3,minmax(0,1fr));
    gap:10px;
    margin:0;
    padding:0;
}
.rep-risk-dialog-values div {
    min-width:0;
    padding:10px 13px;
    border-radius:9px;
    border:1px solid #dce8f7;
}
.rep-risk-dialog-values dt { color:#526b8b; font-size:.83rem; }
.rep-risk-dialog-values dd { margin:3px 0 0; color:#12315f; font-weight:750; }
.rep-risk-dialog-date { margin:0; color:#526b8b; font-size:.87rem; }
.rep-risk-dialog-date time { color:#18375d; font-weight:650; white-space:nowrap; }
@media (max-width: 420px) {
    .rep-risk-dialog-values { gap:6px; }
    .rep-risk-dialog-values div { padding:8px; }
    .rep-risk-dialog-values dt { font-size:.77rem; }
}
.rep-empty {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 13px 14px;
    border: 1px solid #d6e5f8;
    border-radius: 9px;
    color: #335677;
    background: #f3f8fe;
    font-size: .85rem;
}
.rep-empty img { flex: none; }
.st-key-rep_filters :is([data-baseweb="input"],[data-baseweb="select"] > div,[data-testid="stTextInputRootElement"],.react-aria-ComboBox > [role="group"]) {
    background: #fbfdff;
    border: 1px solid #c5d8f1;
    border-radius: 10px;
    box-shadow: 0 2px 4px #163c7512;
    color: #112d56;
}
.st-key-rep_filters [data-testid="stWidgetLabel"] { margin-bottom: 2px; min-height: 0; }
.st-key-rep_filters [data-testid="stWidgetLabel"] p { color:#0e2f61; font-weight:700; }
.st-key-rep_filters :is([data-baseweb="input"],[data-testid="stTextInputRootElement"]) { position: relative; }
.st-key-rep_filters :is([data-baseweb="input"],[data-testid="stTextInputRootElement"])::before {
    content: "";
    position: absolute;
    inset: 0 auto 0 12px;
    width: 17px;
    background: var(--rep-search-icon) center / contain no-repeat;
    pointer-events: none;
}
.st-key-rep_filters .st-key-rep_search input { padding-left: 38px !important; }
.st-key-rep_filters :is(input,[data-baseweb="select"] > div) { color:#102d59; font-size: 1rem; }
.st-key-rep_filters :is([data-baseweb="input"],[data-baseweb="select"] > div,[data-testid="stTextInputRootElement"],.react-aria-ComboBox > [role="group"]):focus-within {
    border-color:#3879d0;
}
.st-key-rep_filters .react-aria-ComboBox input { padding-left: 15px; }
.st-key-rep_filters input::placeholder { color:#567097; opacity:1; }
.st-key-rep_panels [data-testid="stTabs"] > :has(> [role="tablist"]) { border:0 !important; box-shadow:none !important; }
.st-key-rep_panels :is([data-baseweb="tab-list"],[role="tablist"]) {
    gap: clamp(7px,.9vw,16px);
    flex-wrap: wrap;
    border: 0 !important;
    border-bottom-color: transparent !important;
    padding: 2px 0 7px min(1vw,16px);
    box-shadow: none !important;
}
.st-key-rep_panels :is([data-baseweb="tab-highlight"], [data-baseweb="tab-border"],.react-aria-SelectionIndicator) { display: none !important; }
.st-key-rep_panels :is([data-baseweb="tab"],[role="tab"]) {
    color: #10315f !important;
    border: 1px solid transparent !important;
    border-radius: 12px !important;
    background: linear-gradient(145deg,#f1f6fe,#e6eef9) !important;
    display:inline-flex; align-items:center; justify-content:center;
    font-weight: 750;
    min-height: clamp(43px,3.3vw,54px);
    height: auto;
    padding-inline: clamp(12px,1.8vw,30px);
    box-shadow: 0 2px 5px #19467f0a;
}
.st-key-rep_panels :is([data-baseweb="tab"],[role="tab"]) p { color: inherit !important; font-size: clamp(.84rem,1.1vw,1.08rem); font-weight: 700; }
.st-key-rep_panels :is([data-baseweb="tab"],[role="tab"])::before {
    content: "";
    display: inline-block;
    flex: 0 0 clamp(16px,1.35vw,22px);
    height: clamp(16px,1.35vw,22px);
    margin-right: 9px;
    background: currentColor;
    mask: var(--rep-tab-icon) center / contain no-repeat;
}
.st-key-rep_panels :is([data-baseweb="tab"],[role="tab"]):nth-of-type(1) { --rep-tab-icon: var(--rep-bars-icon); }
.st-key-rep_panels :is([data-baseweb="tab"],[role="tab"]):nth-of-type(2) { --rep-tab-icon: var(--rep-shield-icon); }
.st-key-rep_panels :is([data-baseweb="tab"],[role="tab"]):nth-of-type(3) { --rep-tab-icon: var(--rep-flask-icon); }
.st-key-rep_panels :is([data-baseweb="tab"],[role="tab"])[aria-selected="true"],
.st-key-rep_panels [data-testid="stDownloadButton"] button {
    color: #fff !important;
    background: linear-gradient(115deg,#154d98,#0a387a) !important;
    border: 1px solid #164d94 !important;
    box-shadow: 0 3px 7px #153c7925;
}
.st-key-rep_panels :is([data-baseweb="tab"],[role="tab"]):not([aria-selected="true"]):hover { background:#d9e8ff !important; }
.st-key-rep_panels [data-testid="stDownloadButton"] button {
    min-height: clamp(40px,2.85vw,48px);
    min-width: clamp(131px, 10.6vw, 176px);
    border-radius: 11px !important;
    padding-inline: clamp(10px,1.03vw,18px);
    font-weight: 700;
    white-space: nowrap;
}
.st-key-rep_panels [data-testid="stDownloadButton"] button p { color: inherit !important; font-weight: inherit; font-size: clamp(.83rem,.99vw,1rem); }
.st-key-rep_panels :is(.st-key-rep_csv_risks,.st-key-rep_csv_measures,.st-key-rep_csv_experiments) button {
    background: #fcfdff !important;
    color: #0f4aa1 !important;
    border-color: #2166bf !important;
    box-shadow: none;
}
.st-key-rep_panels :is(:is([data-baseweb="tab"],[role="tab"]), [data-testid="stDownloadButton"] button):focus-visible {
    outline: 2px solid #397ccc !important;
    outline-offset: 2px;
}
.st-key-rep_panels :is(.st-key-rep_risks,.st-key-rep_measures,.st-key-rep_experiments) {
    container-type: inline-size;
    background: linear-gradient(155deg,#f0f6ff,#fff 56%,#fafdff) !important;
    gap: clamp(12px,1.5vw,25px) !important;
}
[class*="st-key-rep_panel_header_"] [data-testid="stHorizontalBlock"] { align-items:center; }
[class*="st-key-rep_panel_actions_"] {
    display:flex !important;
    flex-direction: row !important;
    flex-wrap:wrap;
    justify-content:flex-end;
    gap: clamp(8px, .8vw, 14px);
}
[class*="st-key-rep_panel_actions_"] > * { flex: 0 0 auto !important; width:auto !important; }
.rep-table-scroll {
    overflow-x: auto;
    border: 1px solid #e2ebf6;
    border-radius: 11px;
    background: #fff;
}
.rep-table-scroll:focus-visible { outline: 2px solid #397ccc; outline-offset: 2px; }
.rep-report-table {
    table-layout: fixed;
    width: 100%;
    min-width: 1000px;
    border: 0;
    border-collapse: collapse;
    color: #112c56;
    font-size: clamp(.77rem,.83vw,.88rem);
    letter-spacing: normal;
    line-height: 1.3;
    font-variant-numeric: tabular-nums;
}
.rep-report-table :is(th,td) {
    text-align: center;
    padding: clamp(8px,.8vw,14px) clamp(5px,.62vw,10px);
    border-right: 1px solid #e7eef7;
    border-bottom: 1px solid #e2eaf5;
    overflow-wrap: anywhere;
}
.rep-report-table :is(th,td).rep-text-cell { text-align:left; }
.rep-report-table.rep-table-risks { min-width:900px; }
.rep-report-table.rep-table-experiments { min-width:1060px; }
.rep-cell-note { display:block; margin-top:4px; color:#506984; font-size:.86em; }
.rep-count { white-space:nowrap; font-variant-numeric:tabular-nums; }
.rep-status { white-space:normal; overflow-wrap:normal; }
.rep-status.pending { background:#fff2dc; color:#795311; }
.rep-status.good, .rep-status.bad { white-space:normal; }
.rep-exp-empty strong { display:block; margin-bottom:3px; color:#12315f; }
.rep-report-table :is(th,td):last-child { border-right: 0; }
.rep-report-table tr:last-child td { border-bottom: 0; }
.rep-report-table thead { background: linear-gradient(#f2f7fe,#dfeafa); }
.rep-report-table th { color: #0c2a59; font-weight: 720; }
.rep-table-measures th:nth-child(7) { white-space:nowrap; }
.rep-report-table tr:nth-child(even) td { background: #fbfdff; }
.rep-report-table.rep-table-measures th.rep-text-cell,
.rep-report-table.rep-table-risks :is(th,td).rep-text-cell { text-align: center; }
.rep-asset, .rep-measure-badge { display:inline-flex; align-items:center; gap:6px; vertical-align:middle; }
.rep-asset img, .rep-measure-badge img { width: 15px; height: 15px; flex: none; }
.rep-measure-badge {
    border-radius: 999px;
    padding: 6px 8px;
    background: #eaf0f7;
    color: #324d72;
    font-weight: 630;
    font-size: clamp(.71rem,.78vw,.81rem);
    letter-spacing: normal;
    line-height: 1.2;
    text-align: left;
}
.rep-measure-badge.good { background:#cff3e0; color:#096843; font-weight:750; white-space:nowrap; }
.rep-measure-badge.bad { background:#fde9e9; color:#962934; white-space:nowrap; }
.rep-measure-badge.flat { white-space:nowrap; }
.rep-measure-badge.observed { background:#deedff; color:#214f89; }
.rep-method-note { color: #536984; font-size:.79rem; margin:0; }
.rep-method-note summary { cursor: pointer; }
.rep-method-note p { margin:6px 0 0; }
.stApp:has(.rep-hero) [data-testid="stMain"] .st-key-cr_global_footer {
    padding-top:0 !important;
}
.stApp:has(.rep-hero) [data-testid="stMain"] .st-key-cr_global_footer :is(.cr-footer,.dash-footer,.ec-footer) {
    background: transparent !important;
    border-top-color: #dfeaf8 !important;
}

@container (max-width: 860px) {
    [class*="st-key-rep_panel_header_"] [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
    [class*="st-key-rep_panel_header_"] [data-testid="stColumn"] { flex: 1 1 100% !important; min-width: 0 !important; }
    [class*="st-key-rep_panel_actions_"] { justify-content:flex-start; }
}
.st-key-rep_panels :is([data-baseweb="tab-panel"], [role="tabpanel"], .st-key-rep_risks,
    .st-key-rep_measures, .st-key-rep_experiments) {
    box-sizing: border-box !important;
    min-width: 0 !important;
    max-width: 100% !important;
}
@media (max-width: 1020px) { .rep-kpis { grid-template-columns: repeat(2,minmax(0,1fr)); } }
@media (max-width: 720px) {
    .stApp:has(.rep-hero) [data-testid="stAppViewContainer"] [data-testid="stMain"]
        :is([data-testid="stMainBlockContainer"], .block-container) {
        padding-top: 4.35rem !important;
        padding-inline: .8rem !important;
    }
    .rep-hero { padding: 22px 20px; min-height: 128px; }
    .rep-hero h1 { font-size: 25px !important; }
    .rep-hero-symbol { width: 60px; height: 60px; min-width: 60px; }
    .rep-hero-symbol img { width: 35px; height: 35px; }
    .st-key-rep_filters [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
    .st-key-rep_filters [data-testid="stColumn"] { flex: 1 1 100% !important; min-width: 0 !important; }
    [class*="st-key-rep_panel_actions_"] { gap: 7px !important; }
}
@media (max-width: 390px) {
    .rep-kpis { grid-template-columns: 1fr; }
    .rep-kpi { min-height: 67px; }
}
</style>
"""


def svg_url(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def icon_url(name, color="#285b9b"):
    return svg_url(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" color="{color}" '
        f'fill="none" stroke="{color}" stroke-width="1.85" stroke-linecap="round" '
        f'stroke-linejoin="round">{ICONS[name]}</svg>'
    )


def icon(name, color="#285b9b"):
    return f'<img src="{icon_url(name, color)}" alt="" aria-hidden="true">'


def level_for(score):
    return next(label for limit, label, _ in LEVELS if score <= limit)


def prepare_report(risk_rows, measure_rows, experiment_rows):
    """Об’єднує наявні дані без запису результатів чи перерахунку моделі ризику."""
    measures_by_risk = Counter(m["risk_id"] for m in measure_rows)
    risks = [
        {**r, "level": level_for(r["risk_score"]), "measure_count": measures_by_risk[r["id"]]}
        for r in risk_rows
    ]
    evidence_by_measure = defaultdict(list)
    experiments = []
    for e in experiment_rows:
        tests = tests_for_experiment(e["id"])
        observed = [t for t in tests if t["observed"] in {"Доступний", "Заблокований"}]
        matches = sum(t["expected"] == t["observed"] for t in observed)
        if not observed:
            status = NO_EVIDENCE
        elif len(observed) < len(tests):
            status = "Неповний протокол"
        elif matches < len(observed):
            status = "Є розбіжності"
        else:
            status = "Усі очікування підтверджено"
        item = {
            **e, "matches": matches, "observed_count": len(observed),
            "test_count": len(tests), "status": status,
        }
        evidence_by_measure[(e["risk_id"], e["measure_id"])].append(item)
        experiments.append(item)
    measures = []
    for m in measure_rows:
        p_after = max(1, m["probability"] - m["probability_reduction"])
        i_after = max(1, m["impact"] - m["impact_reduction"])
        after = p_after * i_after
        initial = m["risk_score"]
        verified = any(
            item["observed_count"]
            for item in evidence_by_measure[(m["risk_id"], m["id"])]
        )
        measures.append({
            **m, "after": after, "drop_pct": round(100 * (initial - after) / initial, 1),
            "has_observations": verified,
        })
    return risks, measures, experiments


def filter_risks(risks, query, level, coverage):
    needle = query.strip().casefold()
    matches = []
    for r in risks:
        fields = (r["id"], r["asset"], r["threat"], r["vulnerability"])
        if needle and not any(needle in str(value).casefold() for value in fields):
            continue
        if level != ALL_LEVELS and r["level"] != level:
            continue
        if coverage == NO_MEASURES and r["measure_count"]:
            continue
        if coverage == WITH_MEASURES and not r["measure_count"]:
            continue
        matches.append(r)
    return matches


def render_hero():
    assets = {
        "--rep-search-icon": icon_url("search", "#10315f"),
        "--rep-bars-icon": icon_url("bars"),
        "--rep-shield-icon": icon_url("measure"),
        "--rep-flask-icon": icon_url("experiment"),
    }
    declarations = "".join(f"{name}:url({url});" for name, url in assets.items())
    st.html(CSS + f"<style>.stApp:has(.rep-hero){{{declarations}}}</style>")
    st.html(f"""
    <section class="rep-hero">
        <div class="rep-hero-copy">
            <div class="rep-eyebrow">CYBERRISK DSS / РЕЗУЛЬТАТИ ДОСЛІДЖЕННЯ</div>
            <h1>Звіти та результати</h1>
            <p>Підсумковий огляд кіберризиків, заходів захисту та експериментальних перевірок</p>
        </div>
        <div class="rep-hero-symbol" aria-hidden="true">{icon("report", "#FFFFFF")}</div>
    </section>
    """)


def render_kpis(risks, experiments):
    scores = [r["risk_score"] for r in risks]
    score_range = "—" if not scores else str(min(scores))
    if scores and min(scores) != max(scores):
        score_range = f"{min(scores)}–{max(scores)}"
    cards = (
        ("Записів у реєстрі", len(risks), "report", "#0c60d8"),
        ("Початковий бал", score_range, "bars", "#cf770d"),
        ("Ризиків без заходів", sum(r["measure_count"] == 0 for r in risks), "measure", "#0c60d8"),
        ("Фактичні спостереження", sum(e["observed_count"] for e in experiments), "eye", "#0c60d8"),
    )
    body = []
    for idx, (name, value, symbol, color) in enumerate(cards):
        label = f'<span class="rep-kpi-label">{escape(name)}</span>'
        value_html = f'<strong class="rep-kpi-value">{escape(str(value))}</strong>'
        body.append(
            f'<article class="rep-kpi{" rep-priority" if idx == 1 else ""}"><span class="rep-kpi-icon">'
            f'{icon(symbol, color)}</span><div>{value_html + label if idx == 0 else label + value_html}</div></article>'
        )
    st.html('<section class="rep-kpis" aria-label="Зведені показники">' + "".join(body) + '</section>')


def empty(message):
    st.html(f'<div class="rep-empty">{icon("info")}<span>{escape(message)}</span></div>')


def render_distribution(risks):
    counts = Counter(r["level"] for r in risks)
    items = []
    for _, label, css in LEVELS:
        count = counts[label]
        tone = " is-present" if count else ""
        dot = '<span class="rep-risk-dot" aria-hidden="true"></span>' if count else ""
        items.append(
            f'<li class="rep-risk-tone {css}{tone}">{dot}{escape(label)} '
            f'<strong>{count}</strong></li>'
        )
    st.html(
        f'<div class="rep-risk-totals"><span>Усього <strong>{len(risks)}</strong></span>'
        '<ul class="rep-risk-levels" aria-label="Розподіл за рівнями ризику">'
        + "".join(items) + '</ul></div>'
    )


def csv_bytes(df):
    # Позначаємо потенційні формули з текстових полів як текст для табличних редакторів.
    safe = df.copy()
    def cell(value):
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value
    for column in safe.select_dtypes(include=["object", "string"]).columns:
        safe[column] = safe[column].map(cell)
    return safe.to_csv(index=False).encode("utf-8-sig")


def render_panel_header(kind, title, subtitle, symbol, rows, pdf_fields, note, text_keys):
    if not rows:
        render_panel_heading(title, subtitle, symbol)
        return
    with st.container(key=f"rep_panel_header_{kind}"):
        title_col, actions_col = st.columns([2.1, 1], gap="small")
        with title_col:
            render_panel_heading(title, subtitle, symbol)
        with actions_col, st.container(key=f"rep_panel_actions_{kind}"):
            st.download_button(
                "Експорт CSV", csv_bytes(pd.DataFrame(rows)), file_name=f"cyberrisk_{kind}.csv",
                mime="text/csv", key=f"rep_csv_{kind}", icon=":material/download:", on_click="ignore",
            )
            st.download_button(
                "Експорт PDF", report_pdf(rows, pdf_fields, title, subtitle, note, text_keys),
                file_name=f"cyberrisk_{kind}.pdf", mime="application/pdf",
                key=f"rep_pdf_{kind}", icon=":material/description:", on_click="ignore",
            )


def render_panel_heading(title, subtitle, symbol):
    st.html(
        f'<div class="rep-heading"><span class="rep-heading-icon">{icon(symbol, "#0e5cc6")}</span>'
        f'<div><h2>{escape(title)}</h2><p class="rep-caption">{escape(subtitle)}</p></div></div>'
    )


def render_table(rows, fields, title, kind, text_keys, format_cell):
    columns = "".join(f'<col style="width:{width}%">' for _, _, width in fields)
    labels = "".join(
        f'<th scope="col" class="{"rep-text-cell" if key in text_keys else ""}">{label}</th>'
        for key, label, _ in fields
    )
    entries = []
    for row in rows:
        values = "".join(
            f'<td class="{"rep-text-cell" if key in text_keys else ""}">{format_cell(key, row)}</td>'
            for key, _, _ in fields
        )
        entries.append(f"<tr>{values}</tr>")
    safe_title = escape(title)
    st.html(
        f'<div class="rep-table-scroll" tabindex="0" role="region" aria-label="Таблиця — {safe_title}">'
        f'<table class="rep-report-table rep-table-{kind}" aria-label="{safe_title}">'
        f'<colgroup>{columns}</colgroup><thead><tr>{labels}</tr></thead>'
        '<tbody>' + "".join(entries) + '</tbody></table></div>'
    )


def cell_text(raw):
    return escape(str(raw)) if raw is not None and raw != "" else "—"


def asset_cell(raw):
    return f'<span class="rep-asset">{icon("asset", "#14386c")}<span>{cell_text(raw)}</span></span>'


def badge(value, glyph, tone="", color="#35567f"):
    return (
        f'<span class="rep-measure-badge {tone}">{icon(glyph, color)}'
        f'<span>{cell_text(value)}</span></span>'
    )


def display_date(raw, time=False):
    try:
        date = datetime.fromisoformat(str(raw))
    except ValueError:
        return cell_text(raw)
    text = f"{date:%d.%m.%Y · %H:%M:%S}" if time else f"{date:%d.%m.%Y}"
    return f'<time datetime="{escape(date.isoformat())}">{text}</time>'


def method_note(label, note):
    st.html(
        f'<details class="rep-method-note"><summary>{escape(label)}</summary>'
        f'<p>{escape(note)}</p></details>'
    )


RISK_TITLE = "Зведення ризиків"
RISK_SUBTITLE = "Інформаційні активи, оцінки ризиків і кількість заходів захисту"
RISK_NOTE = "Початковий бал ризику визначено як добуток імовірності (P) та впливу (I)."
RISK_TEXT = ("Актив", "Загроза", "Вразливість")
RISK_FIELDS = (
    ("№ ризику", "№ ризику", 7), ("Актив", "Актив", 19),
    ("Загроза", "Загроза", 23), ("Вразливість", "Вразливість", 22),
    ("Бал", "Початковий<br>бал", 10), ("Рівень", "Рівень ризику", 12),
    ("Заходів", "Заходів", 7),
)
RISK_PDF_FIELDS = (
    ("№ ризику", "№<br>ризику", 6), ("Актив", "Актив", 13),
    ("Загроза", "Загроза", 16), ("Вразливість", "Вразливість", 15),
    ("P", "P", 4), ("I", "I", 4), ("Бал", "Бал", 6),
    ("Рівень", "Рівень", 10), ("Заходів", "Заходів", 9),
    ("Дата оцінювання", "Дата<br>оцінювання", 17),
)
RISK_TONES = {label: css for _, label, css in LEVELS}


def risk_cell(key, row):
    raw = row[key]
    if key == "Актив":
        return asset_cell(raw)
    if key == "Бал":
        return f'<span class="rep-risk-score">{cell_text(raw)}<small> / 25</small></span>'
    if key == "Рівень":
        return (
            f'<span class="rep-risk-badge rep-risk-tone {RISK_TONES.get(raw, "")}">'
            f'<span class="rep-risk-dot" aria-hidden="true"></span>{cell_text(raw)}</span>'
        )
    return cell_text(raw)


@st.dialog("Деталі оцінки ризику", width="medium")
def show_risk_details(row):
    with st.container(key="rep_risk_dialog"):
        st.html(
            '<div class="rep-risk-dialog-heading"><div>'
            f'<small>Ризик №{cell_text(row["№ ризику"])}</small><strong>{asset_cell(row["Актив"])}</strong>'
            f'</div>{risk_cell("Рівень", row)}</div>'
        )
        st.html(
            '<dl class="rep-risk-dialog-values">'
            f'<div><dt>Імовірність (P)</dt><dd>{cell_text(row["P"])} / 5</dd></div>'
            f'<div><dt>Вплив (I)</dt><dd>{cell_text(row["I"])} / 5</dd></div>'
            f'<div><dt>Початковий бал</dt><dd>{risk_cell("Бал", row)}</dd></div>'
            '</dl>'
        )
        st.html(
            '<p class="rep-risk-dialog-date">Дата оцінювання · '
            f'{display_date(row["Дата оцінювання"], time=True)}</p>'
        )
        if st.button("Закрити", key="rep_close_risk_details"):
            st.rerun()


def render_risk_detail_controls(rows):
    with st.container(key="rep_risk_detail_controls"):
        if len(rows) == 1:
            selected = rows[0]
            actions = st
        else:
            by_id = {row["№ ризику"]: row for row in rows}
            choice, actions = st.columns([3, 2], gap="small", vertical_alignment="bottom")
            risk_id = choice.selectbox(
                "Ризик для перегляду", options=list(by_id),
                format_func=lambda value: f'№{value} · {by_id[value]["Актив"]}',
                key="rep_risk_detail_id",
            )
            selected = by_id.get(risk_id)
        if actions.button("Деталі оцінки", key="rep_open_risk_details",
                          icon=":material/info:", disabled=selected is None):
            show_risk_details(selected)


def render_risk_panel(risks, has_data):
    with st.container(key="rep_risks", border=False):
        rows = [
            {"№ ризику": r["id"], "Актив": r["asset"], "Загроза": r["threat"],
             "Вразливість": r["vulnerability"], "P": r["probability"], "I": r["impact"],
             "Бал": r["risk_score"], "Рівень": r["level"], "Заходів": r["measure_count"],
             "Дата оцінювання": r["assessment_date"]}
            for r in risks
        ]
        render_panel_header("risks", RISK_TITLE, RISK_SUBTITLE, "bars", rows, RISK_PDF_FIELDS, RISK_NOTE, RISK_TEXT)
        if not rows:
            empty("За заданими фільтрами ризиків не знайдено." if has_data else
                  "Поки немає оцінених ризиків. Додай оцінку в розділі «Оцінювання ризиків».")
            return
        render_distribution(risks)
        render_table(rows, RISK_FIELDS, RISK_TITLE, "risks", RISK_TEXT, risk_cell)
        render_risk_detail_controls(rows)


MEASURE_FIELDS = (
    ("№ заходу", "№ заходу", 7),
    ("№ ризику", "№ ризику", 7),
    ("Актив", "Актив", 14),
    ("Захід", "Захід", 18.5),
    ("Початковий бал", "Початковий<br>бал", 9.2),
    ("Прогнозований бал", "Прогнозований<br>бал", 11.5),
    ("Зниження, %", "Зниження, %", 8.6),
    ("Вартість (ум. од.)", "Вартість<br>(ум. од.)", 8.7),
    (EXPERIMENTAL_CHECK, "Експериментальна<br>перевірка", 15.5),
)
MEASURE_TITLE = "Заходи та прогноз залишкового ризику"
MEASURE_SUBTITLE = "Оцінені заходи захисту, очікуване зниження ризику та економічна ефективність"
MEASURE_NOTE = (
    "Кожен захід оцінено окремо. Наявність спостережень не означає, що всі очікування підтвердилися. "
    "Економічні сценарії розраховуються окремо в розділі «Економічний аналіз»."
)


def measure_rows(measures, risk_index):
    return [
        {"№ заходу": m["id"], "№ ризику": m["risk_id"],
         "Актив": risk_index[m["risk_id"]]["asset"], "Захід": m["measure"],
         "Початковий бал": m["risk_score"], "Прогнозований бал": m["after"],
         "Зниження, %": m["drop_pct"], "Вартість (ум. од.)": m["implementation_cost"],
         EXPERIMENTAL_CHECK: "Є спостереження" if m["has_observations"] else NO_EXPERIMENTAL_DATA}
        for m in measures
    ]


def display_cost(value):
    if value is None:
        return "—"
    number = format(Decimal(str(value)), ",f")
    whole, _, decimal = number.partition(".")
    decimal = decimal.rstrip("0")
    return whole.replace(",", " ") + (f".{decimal}" if decimal else "")


MEASURE_TEXT = ("Актив", "Захід")


def measure_cell(key, row):
    raw = row[key]
    if key == "Актив":
        return asset_cell(raw)
    if key == "Зниження, %":
        tone, glyph, color = (
            ("good", "down", "#096843") if raw > 0 else
            ("bad", "up", "#962934") if raw < 0 else ("flat", "flat", "#324d72")
        )
        return f'<span class="rep-measure-badge {tone}">{icon(glyph, color)}{raw:.1f} %</span>'
    if key == "Вартість (ум. од.)":
        return escape(display_cost(raw))
    if key == EXPERIMENTAL_CHECK:
        has_data = raw != NO_EXPERIMENTAL_DATA
        return badge(raw, "check" if has_data else "clock", "observed" if has_data else "")
    return cell_text(raw)


@st.cache_data(show_spinner=False, max_entries=16)
def report_pdf(rows, fields, title, subtitle, note, text_keys):
    """Створює текстовий PDF із вбудованим шрифтом для української мови."""
    # Matplotlib уже є у залежностях CyberRisk DSS.
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.figure import Figure
    from matplotlib.font_manager import FontProperties
    from matplotlib.patches import Rectangle
    from matplotlib.textpath import TextToPath

    return _draw_report_pdf(rows, fields, title, subtitle, note, text_keys,
                            (PdfPages, Figure, FontProperties, Rectangle, TextToPath))


def _draw_report_pdf(rows, fields, title, subtitle, note, text_keys, modules):
    from matplotlib import rc_context
    PdfPages, Figure, FontProperties, Rectangle, TextToPath = modules
    metrics = TextToPath()
    pw, ph, side, bottom = 841.89, 595.28, 34, 50
    widths = [(pw - side * 2) * width / 100 for _, _, width in fields]
    centers = []
    start = side
    for width in widths:
        centers.append((start, start + width / 2))
        start += width

    def wrap(value, width, size, bold=False):
        font = FontProperties(family="DejaVu Sans", size=size, weight="bold" if bold else "normal")
        def fits(text):
            return metrics.get_text_width_height_descent(text, font, False)[0] <= width
        lines, line = [], ""
        for word in str(value).split():
            candidate = f"{line} {word}" if line else word
            if fits(candidate):
                line = candidate
                continue
            if line:
                lines.append(line)
            line = ""
            for char in word:
                if line and not fits(line + char):
                    lines.append(line)
                    line = ""
                line += char
        return lines + [line] if line or not lines else lines

    labels = [
        [line for part in label.split("<br>") for line in wrap(part, width - 12, 8.5, True)]
        for (_, label, _), width in zip(fields, widths)
    ]
    label_height = max(32, 11 + 10.8 * max(map(len, labels)))
    max_lines = int((ph - 118 - label_height - bottom - 11) // 10.8)
    rows_for_pages = []
    for row in rows:
        cells = []
        for (key, _, _), width in zip(fields, widths):
            value = row[key]
            if key == "Зниження, %":
                value = f"{value:.1f} %"
            elif key == "Вартість (ум. од.)":
                value = display_cost(value)
            cells.append(wrap("—" if value is None or value == "" else value, width - 12, 8.5, key == "Зниження, %"))
        # Дуже довгі назви продовжуються на наступному рядку, без обрізання тексту.
        for offset in range(0, max(map(len, cells)), max_lines):
            chunk = [part[offset:offset + max_lines] for part in cells]
            rows_for_pages.append((chunk, row.get("Зниження, %", 0)))

    stream = BytesIO()
    lock = getattr(Figure, "_render_lock", _PDF_LOCK)
    with lock, rc_context({"pdf.fonttype": 42}), PdfPages(stream, metadata={"Title": title, "Author": "CyberRisk DSS"}) as pdf:
        page_no = 0

        def new_page():
            nonlocal page_no
            page_no += 1
            fig = Figure(figsize=(pw / 72, ph / 72), facecolor="#ffffff")
            ax = fig.add_axes([0, 0, 1, 1])
            ax.set(xlim=(0, pw), ylim=(0, ph))
            ax.axis("off")
            ax.add_patch(Rectangle((0, ph - 102), pw, 102, color="#123d78", linewidth=0))
            ax.text(side, ph - 25, "CYBERRISK DSS / ЗВІТ", color="#cfe2ff", fontsize=9, weight="bold", va="center")
            ax.text(side, ph - 53, title, color="white", fontsize=20, weight="bold", va="center")
            ax.text(side, ph - 77, subtitle, color="#e6f0ff", fontsize=10, va="center")
            ax.plot([side, pw-side], [34, 34], color="#d9e5f4", linewidth=.7)
            ax.text(side, 23, "CyberRisk DSS  ·  Дані за вибраними фільтрами", fontsize=8, color="#496282", va="center")
            ax.text(pw - side, 23, f"Сторінка {page_no}", fontsize=8, color="#496282", ha="right", va="center")
            y = ph - 118
            draw_row(ax, labels, y, label_height, "#e5effd", heading=True)
            return fig, ax, y - label_height

        def draw_row(ax, cells, y, height, fill, heading=False, reduction=0):
            for idx, ((left, middle), width, lines) in enumerate(zip(centers, widths, cells)):
                ax.add_patch(Rectangle((left, y-height), width, height, facecolor=fill,
                                       edgecolor="#dbe7f5", linewidth=.5))
                key = fields[idx][0]
                align = "left" if key in text_keys else "center"
                color = "#0d2b58"
                if key == "Зниження, %" and not heading:
                    color = "#097044" if reduction > 0 else "#9d2836" if reduction < 0 else color
                center = y - height / 2 + (len(lines) - 1) * 5.4
                for n, line in enumerate(lines):
                    ax.text(left + 6 if align == "left" else middle, center - n * 10.8, line,
                            size=8.5, color=color, ha=align, va="center",
                            weight="bold" if heading or key == "Зниження, %" else "normal", parse_math=False)

        fig, ax, y = new_page()
        for idx, (cells, reduction) in enumerate(rows_for_pages):
            height = max(29, 11 + 10.8 * max(map(len, cells)))
            if y - height < bottom:
                pdf.savefig(fig)
                fig, ax, y = new_page()
            draw_row(ax, cells, y, height, "#f8fbff" if idx % 2 else "#fff", reduction=reduction)
            y -= height
        note_lines = wrap(note, pw - side * 2, 8)
        if y - 14 - 11 * len(note_lines) < bottom:
            pdf.savefig(fig)
            fig, ax, y = new_page()
        for idx, line in enumerate(note_lines):
            ax.text(side, y - 14 - 11 * idx, line, fontsize=8, color="#496282", va="top")
        pdf.savefig(fig)
    return stream.getvalue()


def render_measure_panel(measures, risk_index, has_data):
    with st.container(key="rep_measures", border=False):
        rows = measure_rows(measures, risk_index)
        render_panel_header("measures", MEASURE_TITLE, MEASURE_SUBTITLE, "measure", rows,
                            MEASURE_FIELDS, MEASURE_NOTE, MEASURE_TEXT)
        if not rows:
            empty("Для відібраних ризиків немає зареєстрованих заходів." if has_data else
                  "Поки немає заходів захисту. Додай їх у розділі «Заходи захисту».")
            return
        render_table(rows, MEASURE_FIELDS, MEASURE_TITLE, "measures", MEASURE_TEXT, measure_cell)
        method_note("Як читати прогноз", MEASURE_NOTE)


EXPERIMENT_TITLE = "Результати експериментальних перевірок"
EXPERIMENT_SUBTITLE = "Демонстраційні сценарії на моделі мережі в Cisco Packet Tracer"
EXPERIMENT_NOTE = (
    "Збіг з очікуванням стосується лише перевірок у моделі мережі. "
    "Він не підтверджує прогнозований бал залишкового ризику."
)
EXPERIMENT_TEXT = ("Експеримент", "Сценарій", "Актив", "Захід")
EXPERIMENT_FIELDS = (
    ("№ протоколу", "№<br>протоколу", 8), ("№ ризику", "№<br>ризику", 6),
    ("Експеримент", "Експеримент", 15), ("Актив", "Актив", 12),
    ("Захід", "Захід", 15), ("Перевірено", "Перевірено", 8),
    ("Збіг з очікуванням", "Збіг з<br>очікуванням", 10), ("Підсумок", "Підсумок", 18),
    ("Дата", "Дата", 8),
)
EXPERIMENT_PDF_FIELDS = (
    ("№ протоколу", "№<br>протоколу", 9), ("№ ризику", "№<br>ризику", 6),
    ("Експеримент", "Експеримент", 13), ("Сценарій", "Сценарій", 10),
    ("Актив", "Актив", 10), ("Захід", "Захід", 12),
    ("Перевірено", "Перевірено", 9), ("Збіг з очікуванням", "Збіг з<br>очікуванням", 10),
    ("Підсумок", "Підсумок", 12), ("Дата", "Дата", 9),
)
EXPERIMENT_STATES = {
    NO_EVIDENCE: ("clock", "", "#35567f"),
    "Неповний протокол": ("clock", "pending", "#795311"),
    "Є розбіжності": ("info", "bad", "#962934"),
    "Усі очікування підтверджено": ("check", "good", "#096843"),
}


def experiment_cell(key, row):
    raw = row[key]
    if key == "Експеримент":
        return f'<strong>{cell_text(raw)}</strong><span class="rep-cell-note">{cell_text(row["Сценарій"])}</span>'
    if key == "Актив":
        return asset_cell(raw)
    if key == "Підсумок":
        glyph, tone, color = EXPERIMENT_STATES.get(raw, ("info", "", "#35567f"))
        return badge(raw, glyph, f"rep-status {tone}", color)
    if key == "Дата":
        return display_date(raw)
    if key in ("Перевірено", "Збіг з очікуванням"):
        return f'<span class="rep-count">{cell_text(raw)}</span>'
    return cell_text(raw)


def render_experiment_panel(experiments, has_data):
    with st.container(key="rep_experiments", border=False):
        rows = [
            {"№ протоколу": e["id"], "№ ризику": e["risk_id"], "Експеримент": e["title"],
             "Сценарій": e["scenario"], "Актив": e["asset"], "Захід": e["measure"],
             "Перевірено": f'{e["observed_count"]}/{e["test_count"]}' if e["test_count"] else "—",
             "Збіг з очікуванням": f'{e["matches"]}/{e["observed_count"]}' if e["observed_count"] else "—",
             "Підсумок": e["status"], "Дата": e["created_at"]}
            for e in experiments
        ]
        render_panel_header("experiments", EXPERIMENT_TITLE, EXPERIMENT_SUBTITLE, "experiment",
                            rows, EXPERIMENT_PDF_FIELDS, EXPERIMENT_NOTE, EXPERIMENT_TEXT)
        if not rows:
            title, message = (
                ("Немає протоколів за вибраними фільтрами", "Зміни фільтри звіту, щоб переглянути інші протоколи.")
                if has_data else
                ("Ще немає збережених протоколів", "Результати з’являться після збереження протоколу на сторінці «Експериментальне дослідження».")
            )
            st.html(
                f'<div class="rep-empty rep-exp-empty">{icon("info")}<div>'
                f'<strong>{escape(title)}</strong><span>{escape(message)}</span></div></div>'
            )
            return
        render_table(rows, EXPERIMENT_FIELDS, EXPERIMENT_TITLE, "experiments", EXPERIMENT_TEXT, experiment_cell)
        method_note("Як читати результати", EXPERIMENT_NOTE)


def main():
    render_hero()
    initialize_database()
    initialize_experiments()
    risks, measures, experiments = prepare_report(report_risks(), report_measures(), all_experiments())
    render_kpis(risks, experiments)
    query, level, coverage = "", ALL_LEVELS, ALL_COVERAGE
    if risks:
        with st.container(key="rep_filters", border=False):
            st.html(
                f'<div class="rep-filter-header"><span class="rep-filter-icon">{icon("filter", "#104387")}</span>'
                '<p><strong>Фільтри звіту</strong> · застосовуються до всіх трьох вкладок</p></div>'
            )
            q_col, l_col, c_col = st.columns([1.65, 1, 1], gap="medium")
            query = q_col.text_input(
                "Пошук ризику", placeholder="Актив, загроза, вразливість або номер",
                key="rep_search",
            )
            level = l_col.selectbox("Рівень ризику", [ALL_LEVELS, *(item[1] for item in LEVELS)], key="rep_level")
            coverage = c_col.selectbox("Наявність заходу", [ALL_COVERAGE, NO_MEASURES, WITH_MEASURES], key="rep_coverage")
    selected_risks = filter_risks(risks, query, level, coverage)
    by_id = {r["id"]: r for r in selected_risks}
    selected_measures = [m for m in measures if m["risk_id"] in by_id]
    selected_experiments = [e for e in experiments if e["risk_id"] in by_id]
    with st.container(key="rep_panels"):
        t1, t2, t3 = st.tabs(["Ризики", "Заходи й прогноз", "Експерименти"])
        with t1:
            render_risk_panel(selected_risks, bool(risks))
        with t2:
            render_measure_panel(selected_measures, by_id, bool(measures))
        with t3:
            render_experiment_panel(selected_experiments, bool(experiments))
    # Актуальна навігація відкладає цей виклик та виводить один спільний футер
    # після сторінки. Зі старою навігацією працює звичайний локальний футер.
    render_footer()


main()
