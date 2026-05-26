import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import io
import tempfile
from datetime import datetime, date
from collections import Counter
from pyxirr import xirr
import casparser

# ── STREAMLIT GLOBAL CONFIGURATION ───────────────────────────────────────────
st.set_page_config(
    page_title="Cas 360 View — Portfolio Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS CYBERPUNK HUD CUSTOM DESIGN LAYOUT ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    background-color: #040611 !important;
    color: #e2e8f4 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 9999;
    opacity: 0.4;
}
.stApp::after {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(99,102,241,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(99,102,241,0.04) 1px, transparent 1px);
    background-size: 48px 48px;
    pointer-events: none;
    z-index: 0;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080c1a 0%, #040611 100%) !important;
    border-right: 1px solid rgba(99,102,241,0.15) !important;
}
[data-testid="stSidebar"] * { font-family: 'Space Grotesk', sans-serif !important; }
[data-testid="stSidebar"] .stRadio label { color: #94a3b8 !important; font-size: 14px !important; transition: color 0.2s; }
[data-testid="stSidebar"] .stRadio label:hover { color: #a78bfa !important; }

div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0d1228 0%, #0a0f1e 100%) !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 16px !important;
    padding: 20px 22px !important;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s, transform 0.2s;
}
div[data-testid="stMetric"]:hover {
    border-color: rgba(167,139,250,0.5) !important;
    transform: translateY(-2px);
}
div[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(167,139,250,0.6), transparent);
}
div[data-testid="stAppViewBlockContainer"] {
    padding-top: 3rem !important;
}
div[data-testid="stMetricValue"] > div {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 22px !important;
    font-weight: 700 !important;
    color: #f1f5f9 !important;
    letter-spacing: -0.5px;
}
div[data-testid="stMetricLabel"] > div {
    font-size: 11px !important;
    color: #64748b !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 500 !important;
}
div[data-testid="stMetricDelta"] > div { font-size: 12px !important; font-weight: 600 !important; }

[data-testid="stVerticalBlockBorderWrapper"] > div > div {
    background: linear-gradient(135deg, #0d1228 0%, #090e1c 100%) !important;
    border: 1px solid rgba(99,102,241,0.18) !important;
    border-radius: 16px !important;
    transition: border-color 0.3s;
}
[data-testid="stVerticalBlockBorderWrapper"] > div > div:hover {
    border-color: rgba(167,139,250,0.35) !important;
}

[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(99,102,241,0.15) !important;
}

[data-testid="stSegmentedControl"] > div {
    background: #0a0f1e !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 10px !important;
    padding: 3px !important;
}
[data-testid="stSegmentedControl"] button[aria-checked="true"] {
    background: linear-gradient(135deg, #4338ca, #6d28d9) !important;
    color: #fff !important;
    border-radius: 7px !important;
    box-shadow: 0 0 12px rgba(99,102,241,0.4) !important;
}

[data-testid="stSelectbox"] > div > div {
    background: #0a0f1e !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    border-radius: 10px !important;
    color: #e2e8f4 !important;
}

[data-testid="stFileUploader"] {
    background: rgba(99,102,241,0.04) !important;
    border: 2px dashed rgba(99,102,241,0.3) !important;
    border-radius: 16px !important;
}

[data-testid="stTextInput"] input {
    background: #0a0f1e !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    border-radius: 10px !important;
    color: #e2e8f4 !important;
    font-family: 'JetBrains Mono', monospace !important;
}

hr { border-color: rgba(99,102,241,0.12) !important; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #040611; }
::-webkit-scrollbar-thumb { background: #1e1b4b; border-radius: 4px; }

.hud-card {
    background: linear-gradient(135deg, #0d1228 0%, #090e1c 100%);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 16px;
    padding: 22px 24px;
    position: relative;
    overflow: hidden;
    margin-bottom: 16px;
}
.hud-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(167,139,250,0.5), transparent);
}
.hud-card-title {
    font-size: 12px;
    font-weight: 600;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.hud-card-title::before {
    content: '';
    display: inline-block;
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #6366f1;
    box-shadow: 0 0 8px #6366f1;
}

.metric-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(16,185,129,0.12);
    border: 1px solid rgba(16,185,129,0.25);
    color: #34d399;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
}

.alloc-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid rgba(99,102,241,0.08);
}
.alloc-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 8px; }
.alloc-bar-bg { width: 120px; height: 4px; background: rgba(99,102,241,0.12); border-radius: 2px; overflow: hidden; margin-left: 12px; }
.alloc-bar-fill { height: 100%; border-radius: 2px; }

.badge-live { display:inline-block; background:rgba(16,185,129,0.12); color:#34d399; border:1px solid rgba(16,185,129,0.3); padding:2px 10px; border-radius:20px; font-size:11px; font-weight:600; font-family:'JetBrains Mono',monospace; }
.badge-dead { display:inline-block; background:rgba(239,68,68,0.12); color:#f87171; border:1px solid rgba(239,68,68,0.3); padding:2px 10px; border-radius:20px; font-size:11px; font-weight:600; font-family:'JetBrains Mono',monospace; }

.notice-bar {
    background: rgba(99,102,241,0.06);
    border: 1px solid rgba(99,102,241,0.2);
    border-left: 3px solid #6366f1;
    border-radius: 0 12px 12px 0;
    padding: 12px 16px;
    font-size: 13px;
    color: #94a3b8;
    margin-bottom: 24px;
    display: flex;
    align-items: flex-start;
    gap: 10px;
}

.sip-ticker-item {
    background: #070b18;
    border: 1px solid rgba(99,102,241,0.15);
    border-radius: 10px;
    padding: 10px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.section-header {
    font-size: 11px;
    font-weight: 700;
    color: #4b5563;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 20px 0 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-header::after { content:''; flex:1; height:1px; background:rgba(99,102,241,0.1); }

.page-title { font-size:28px; font-weight:700; color:#f1f5f9; letter-spacing:-0.5px; margin-bottom:4px; }
.page-subtitle { font-size:13px; color:#475569; margin-bottom:24px; }

.upload-hero { text-align: center; padding: 60px 40px; max-width: 560px; margin: 0 auto; }
.upload-icon { width: 72px; height: 72px; background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.3); border-radius: 20px; display: flex; align-items: center; justify-content: center; margin: 0 auto 24px; font-size: 32px; }
.upload-step { display: flex; align-items: flex-start; gap: 14px; background: rgba(13,18,40,0.8); border: 1px solid rgba(99,102,241,0.12); border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; text-align: left; }
.upload-step-num { width: 24px; height: 24px; border-radius: 50%; background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.3); color: #a78bfa; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-family: 'JetBrains Mono', monospace; }
</style>
""", unsafe_allow_html=True)

# ── GRAPH INTERFACE STYLING OBJECT CONSTANTS ─────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Space Grotesk', color='#94a3b8'),
    margin=dict(l=0, r=0, t=10, b=10),
)
GRID_COLOR  = 'rgba(99,102,241,0.08)'
GAIN_COLOR  = '#10b981'
LOSS_COLOR  = '#ef4444'

# ── HELPERS ──────────────────────────────────────────────────────────────────

def to_date_obj(d):
    if not d: 
        return datetime.today().date()
    if isinstance(d, str):
        try: 
            return datetime.strptime(d.split("T")[0], "%Y-%m-%d").date()
        except: 
            return datetime.today().date()
    if hasattr(d, "date"): 
        return d.date()
    return d

def to_dict(obj):
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_dict(i) for i in obj]
    elif hasattr(obj, "model_dump"):
        return to_dict(obj.model_dump())
    elif hasattr(obj, "dict"):
        return to_dict(obj.dict())
    else:
        return obj

def clean_fund_name(name):
    if not name:
        return "Unknown Scheme"
    for sfx in [
        "- Direct Plan - Growth Option", "- Direct Plan - Growth", "- Direct Growth Plan",
        "- Direct Plan Growth", "Direct Plan Growth", "Direct Growth", "Direct Plan",
        "Regular Plan", "Growth"
    ]:
        name = name.replace(sfx, "")
    return name.strip()

def calculate_scheme_xirr(transactions, current_value, valuation_date_str):
    dates, amounts = [], []
    for tx in transactions:
        try:
            dt = to_date_obj(tx.get("date"))
            amt = float(tx.get("amount", 0.0))
            if amt > 0:
                dates.append(dt); amounts.append(-amt)
        except: continue
    if current_value > 0:
        try:
            dates.append(to_date_obj(valuation_date_str))
            amounts.append(current_value)
        except: pass
    if len(amounts) >= 2 and sum(amounts) != 0:
        try:
            rate = xirr(dates, amounts)
            return rate * 100 if rate is not None else 0.0
        except: return 0.0
    return 0.0

# ── REPORT EXPORTERS ─────────────────────────────────────────────────────────

def generate_excel(live_data):
    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            summary_df = pd.DataFrame([
                {"Metadata Field": "Investor Name", "Value": live_data["investor_name"]},
                {"Metadata Field": "Registered Email", "Value": live_data["investor_email"]},
                {"Metadata Field": "PAN Number Ident", "Value": live_data.get("investor_pan", "—")},
                {"Metadata Field": "As-of Statement Date", "Value": live_data["statement_date_raw"]},
                {"Metadata Field": "Current Asset Wealth Valuation", "Value": live_data['total_wealth']},
                {"Metadata Field": "Total Investment Principal Cost", "Value": live_data['total_invested']},
                {"Metadata Field": "Unrealized Capital Growth Delta", "Value": live_data['current_gain']},
                {"Metadata Field": "Realized Liquidation Earnings", "Value": live_data.get('total_realized_profit', 0.0)}
            ])
            summary_df.to_excel(writer, sheet_name="Executive Summary", index=False)
            
            if live_data["flat_schemes"]:
                holdings = [{
                    "Scheme Designation": clean_fund_name(s["scheme_name"]), 
                    "Asset Class Category": s["asset_type"], 
                    "Invested Outlay Cost": s["invested_cost"], 
                    "Current Appraisal Value": s["current_value"], 
                    "Position Delta Unrealized": s["net_gain"], 
                    "Calculated Yield XIRR %": s["xirr"]
                } for s in live_data["flat_schemes"]]
                pd.DataFrame(holdings).to_excel(writer, sheet_name="Active Open Positions", index=False)
                
            if live_data.get("redeemed_schemes"):
                pd.DataFrame(live_data["redeemed_schemes"]).to_excel(writer, sheet_name="Fully Redeemed Accounts", index=False)
                
            all_sips = live_data.get("live_sips", []) + live_data.get("inactive_sips", [])
            if all_sips:
                sip_rows = [{"Scheme": clean_fund_name(s["Scheme Name"]), "Amount Outflow": s["Amount"], "Day Schedule": s["Trigger"], "Last Detected Exec": s["Last Installment"], "Pipeline Status": s["Status"]} for s in all_sips]
                pd.DataFrame(sip_rows).to_excel(writer, sheet_name="Systematic Schedules", index=False)
                
        return output.getvalue()
    except:
        return None 

def generate_html_report(live_data):
    def format_money(val): return f"₹{abs(val):,.2f}"
    def get_color(val): return "#10b981" if val >= 0 else "#ef4444"
    def get_arrow(val): return "▲" if val >= 0 else "▼"

    holdings_rows = ""
    for s in live_data.get("flat_schemes", []):
        gain_val = s['net_gain']
        xirr_val = s['xirr']
        gain_str = f"<span style='color:{get_color(gain_val)}; font-weight:bold;'>{get_arrow(gain_val)} {format_money(gain_val)}</span>"
        xirr_str = f"<span style='color:{get_color(xirr_val)}; font-weight:bold;'>{get_arrow(xirr_val)} {xirr_val:.2f}%</span>"
        holdings_rows += f"<tr><td>{clean_fund_name(s['scheme_name'])}</td><td>{s['asset_type']}</td><td>{format_money(s['invested_cost'])}</td><td>{format_money(s['current_value'])}</td><td>{gain_str}</td><td>{xirr_str}</td></tr>"
    
    redeemed_rows = "<tr><td colspan='5' style='text-align:center; color:#94a3b8; padding:20px; background:#070b19;'>No completely closed zero balance positions discovered in ledger logs.</td></tr>"
    if live_data.get("redeemed_schemes"):
        redeemed_rows = ""
        for r in live_data["redeemed_schemes"]:
            profit_val = r['Profit']
            profit_str = f"<span style='color:{get_color(profit_val)}; font-weight:bold;'>{get_arrow(profit_val)} {format_money(profit_val)}</span>"
            redeemed_rows += f"<tr><td>{clean_fund_name(r['Scheme'])}</td><td>{r['Holding Period']}</td><td>{format_money(r['Invested'])}</td><td>{format_money(r['Redeemed'])}</td><td>{profit_str}</td></tr>"

    live_sip_cnt = len(live_data.get("live_sips", []))
    inact_sip_cnt = len(live_data.get("inactive_sips", []))
    total_sip_outflow = sum(s["Amount"] for s in live_data.get("live_sips", []))

    all_sips = live_data.get("live_sips", []) + live_data.get("inactive_sips", [])
    sip_matrix_rows = ""
    if all_sips:
        for s in sorted(all_sips, key=lambda x: x["Status"]):
            status_class = "status-active" if s["Status"] == "Live" else "status-inactive"
            status_color = "#34d399" if s["Status"] == "Live" else "#f87171"
            sip_matrix_rows += f"""
            <tr>
                <td class='{status_class}'>{clean_fund_name(s['Scheme Name'])}</td>
                <td style='font-family:monospace; font-weight:600;'>{format_money(s['Amount'])}</td>
                <td>{s['Trigger']}</td>
                <td>{s['Last Installment']}</td>
                <td style='color:{status_color}; font-weight:bold;'>{s['Status'].upper()}</td>
            </tr>
            """
    else:
        sip_matrix_rows = "<tr><td colspan='5' style='text-align:center; padding:20px; color:#94a3b8;'>No systematic commitment streams (SIPs) verified.</td></tr>"

    alloc_pct = live_data.get("allocation_percentages", {})
    svg_donut_segments = ""
    if alloc_pct:
        colors_palette = {"Equity Funds": "#3b82f6", "Debt Funds": "#f59e0b", "Gold Funds": "#eab308", "International": "#ec4899"}
        fallback_list = ["#3b82f6", "#f59e0b", "#10b981", "#ec4899"]
        offset_accumulator = 0.0
        idx_c = 0
        for name, percentage in alloc_pct.items():
            if percentage <= 0: continue
            seg_color = colors_palette.get(name, fallback_list[idx_c % len(fallback_list)])
            idx_c += 1
            dash_array_val = f"{percentage} {100 - percentage}"
            dash_offset_val = 100 - offset_accumulator + 25 
            svg_donut_segments += f'<circle cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="{seg_color}" stroke-width="4.5" stroke-dasharray="{dash_array_val}" stroke-dashoffset="{dash_offset_val}"></circle>'
            offset_accumulator += percentage
    else:
        svg_donut_segments = '<circle cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="rgba(255,255,255,0.1)" stroke-width="4.5"></circle>'

    svg_pie_graphic = f"""
    <svg width="100%" height="220" viewBox="0 0 42 42" style="display:block; margin:0 auto;">
        <circle cx="21" cy="21" r="15.91549430918954" fill="#0d1228"></circle>
        {svg_donut_segments}
        <text x="21" y="20" font-family="sans-serif" font-size="3" font-weight="700" fill="#f1f5f9" text-anchor="middle">ASSETS</text>
        <text x="21" y="24" font-family="sans-serif" font-size="2.2" fill="#94a3b8" text-anchor="middle">DISTRIBUTION</text>
    </svg>
    """

    top_open_positions = sorted(live_data.get("flat_schemes", []), key=lambda x: x["current_value"], reverse=True)[:4]
    svg_bar_nodes = ""
    if top_open_positions:
        absolute_peak_val = max([x["current_value"] for x in top_open_positions]) or 1.0
        y_cursor = 15
        for position in top_open_positions:
            display_title = clean_fund_name(position["scheme_name"])[:28]
            current_valuation = position["current_value"]
            calculated_fill_width = (current_valuation / absolute_peak_val) * 280
            
            svg_bar_nodes += f"""
            <text x="10" y="{y_cursor + 10}" font-family="sans-serif" font-size="11" fill="#94a3b8">{display_title}</text>
            <rect x="160" y="{y_cursor}" width="{calculated_fill_width}" height="14" rx="4" fill="url(#purpleOrchidGrad)"></rect>
            <text x="{165 + calculated_fill_width}" y="{y_cursor + 11}" font-family="sans-serif" font-weight="700" font-size="11" fill="#e2e8f4">₹{current_valuation:,.0f}</text>
            """
            y_cursor += 32
    else:
        svg_bar_nodes = '<text x="200" y="70" font-family="sans-serif" fill="#94a3b8">No Open Accounts Data Matrix Found</text>'

    svg_bar_graphic = f"""
    <svg width="100%" height="150" viewBox="0 0 500 150" style="background:transparent;">
        <defs>
            <linearGradient id="purpleOrchidGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#8b5cf6" />
                <stop offset="100%" stop-color="#6366f1" />
            </linearGradient>
        </defs>
        {svg_bar_nodes}
    </svg>
    """
    
    tot_inv = live_data['total_invested']
    tot_wlth = live_data['total_wealth']
    tot_gain = live_data['current_gain']
    
    if tot_wlth > 0 and tot_inv > 0:
        inv_pct = min(100, (tot_inv / tot_wlth) * 100) if tot_gain > 0 else 100
        gain_pct = 100 - inv_pct if tot_gain > 0 else 0
        svg_progress_bar = f"""
        <svg width="100%" height="40" viewBox="0 0 100 10" preserveAspectRatio="none" style="margin-top:10px; border-radius: 4px; overflow: hidden;">
            <rect x="0" y="0" width="{inv_pct}" height="10" fill="#3b82f6" />
            <rect x="{inv_pct}" y="0" width="{gain_pct}" height="10" fill="#10b981" />
        </svg>
        <div style="display:flex; justify-content:space-between; font-size:10px; color:#94a3b8; margin-top:5px; font-weight:bold; text-transform:uppercase;">
            <span><span style="display:inline-block;width:8px;height:8px;background:#3b82f6;border-radius:50%;margin-right:4px;"></span>Principal Core</span>
            <span><span style="display:inline-block;width:8px;height:8px;background:#10b981;border-radius:50%;margin-right:4px;"></span>Generated Wealth Returns</span>
        </div>
        """
    else:
        svg_progress_bar = ""

    total_realized = live_data.get('total_realized_profit', 0.0)
    cur_gain = live_data['current_gain']
    kpi_gain_color = get_color(cur_gain)
    kpi_gain_arrow = get_arrow(cur_gain)
    kpi_realized_color = get_color(total_realized)
    kpi_realized_arrow = get_arrow(total_realized)

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Portfolio Intelligence Executive Ledger - {live_data['investor_name']}</title>
        <style>
            @media print {{
                body {{ background-color: #040611 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
                .card {{ background: #0d1228 !important; border: 1px solid #1e1b4b !important; }}
                th {{ background-color: #090e1c !important; color: #a78bfa !important; }}
                td {{ background-color: #0d1228 !important; color: #e2e8f4 !important; }}
                .metric-box {{ background: #070b18 !important; border: 1px solid #1e1b4b !important; }}
                .pbi-matrix th {{ background-color: #0f172a !important; }}
                .pbi-matrix tr:nth-child(even) td {{ background-color: #0d1228 !important; }}
                .section-header {{ background: linear-gradient(90deg, #1e1b4b, transparent) !important; }}
            }}
            body {{ background-color: #040611; color: #e2e8f4; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; padding: 35px; line-height: 1.4; }}
            .card {{ background: linear-gradient(135deg, #0d1228 0%, #090e1c 100%); border: 1px solid rgba(99,102,241,0.2); border-radius: 16px; padding: 25px; margin-bottom: 24px; position: relative; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
            .card::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, #8b5cf6, transparent); }}
            h1 {{ color: #ffffff; font-size: 26px; margin: 0 0 5px 0; font-weight: 700; letter-spacing: -0.5px; }}
            .section-header {{ background: linear-gradient(90deg, #1e1b4b, transparent); padding: 12px 18px; border-left: 4px solid #8b5cf6; font-size: 14px; color: #e2e8f4; margin-top: 40px; margin-bottom: 20px; border-radius: 4px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; display: flex; align-items: center; gap: 10px; }}
            .profile-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px; background: rgba(7, 11, 24, 0.6); padding: 15px; border-radius: 10px; border: 1px solid rgba(99,102,241,0.1); }}
            .profile-cell {{ font-size: 13px; }}
            .profile-label {{ color: #64748b; text-transform: uppercase; font-size: 10px; letter-spacing: 1px; margin-bottom: 2px; font-weight: 600; }}
            .profile-value {{ color: #f1f5f9; font-weight: 500; }}
            .kpi-container {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 20px; }}
            .metric-box {{ background: #070b18; border: 1px solid rgba(99,102,241,0.15); border-radius: 12px; padding: 16px; text-align: left; position: relative; overflow: hidden; }}
            .metric-box::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: rgba(255,255,255,0.05); }}
            .metric-label {{ font-size: 10px; color: #64748b; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600; }}
            .metric-value {{ font-size: 20px; font-weight: 700; color: #ffffff; margin-top: 6px; font-family: monospace; letter-spacing: -0.5px; }}
            .charts-wrapper {{ display: grid; grid-template-columns: 2fr 3fr; gap: 20px; margin-top: 20px; margin-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; border-radius: 12px; overflow: hidden; border: 1px solid rgba(99,102,241,0.12); box-shadow: 0 4px 12px rgba(0,0,0,0.3); }}
            th, td {{ padding: 14px 16px; text-align: left; font-size: 12px; border-bottom: 1px solid rgba(99,102,241,0.08); }}
            th {{ background-color: #090e1c; color: #a78bfa; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; font-size: 11px; }}
            td {{ background: #0d1228; color: #e2e8f4; }}
            tr:nth-child(even) td {{ background-color: rgba(7, 11, 24, 0.4); }}
            .matrix-container {{ background: #070b18; border: 1px solid rgba(99,102,241,0.2); border-radius: 12px; padding: 1px; margin-bottom: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }}
            .pbi-matrix {{ width: 100%; border-collapse: collapse; border: none; margin-top: 0; border-radius: 11px; }}
            .pbi-matrix th {{ background-color: #0f172a; color: #a78bfa; font-weight: 600; text-align: left; padding: 14px 16px; border-bottom: 2px solid #6366f1; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }}
            .pbi-matrix td {{ padding: 14px 16px; font-size: 12px; border-bottom: 1px solid rgba(99,102,241,0.08); color: #e2e8f4; background-color: #070b18; }}
            .pbi-matrix tr:nth-child(even) td {{ background-color: #0d1228; }}
            .status-active {{ border-left: 4px solid #10b981 !important; padding-left: 12px !important; }}
            .status-inactive {{ border-left: 4px solid #ef4444 !important; padding-left: 12px !important; }}
            .legend-item {{ display: flex; align-items: center; justify-content: space-between; font-size: 12px; margin-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 4px; }}
            .legend-color {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 8px; }}
            .footer-note {{ text-align: center; margin-top: 50px; font-size: 10px; color: #4b5563; border-top: 1px solid rgba(99,102,241,0.1); padding-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div style="display:flex; justify-content:between; align-items:center;">
                <div>
                    <h1>CAS 360 VIEW · PORTFOLIO INTELLIGENCE</h1>
                    <div style="font-size:12px; color:#6366f1; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-top:2px;">Executive Dashboard & Statement Analysis</div>
                </div>
            </div>
            <div class="profile-grid">
                <div class="profile-cell">
                    <div class="profile-label">Account Holder Identity</div>
                    <div class="profile-value">{live_data['investor_name'].title()}</div>
                </div>
                <div class="profile-cell">
                    <div class="profile-label">Registered Electronic Mail</div>
                    <div class="profile-value">{live_data['investor_email'] if live_data['investor_email'] else 'Not Disclosed'}</div>
                </div>
                <div class="profile-cell">
                    <div class="profile-label">Permanent Account Number (PAN)</div>
                    <div class="profile-value" style="font-family:monospace; font-weight:700; color:#a78bfa;">{live_data.get('investor_pan', '—')}</div>
                </div>
            </div>
            <div class="kpi-container">
                <div class="metric-box">
                    <div class="metric-label">Total Portfolio Wealth</div>
                    <div class="metric-value">{format_money(live_data['total_wealth'])}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Aggregated Investment</div>
                    <div class="metric-value" style="color:#3b82f6;">{format_money(live_data['total_invested'])}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Net Unrealized Growth</div>
                    <div class="metric-value" style="color:{kpi_gain_color};">{kpi_gain_arrow} {format_money(cur_gain)}</div>
                </div>
                <div class="metric-box" style="border-left:3px solid {kpi_realized_color};">
                    <div class="metric-label">Total Realized Profits</div>
                    <div class="metric-value" style="color:{kpi_realized_color};">{kpi_realized_arrow} {format_money(total_realized)}</div>
                </div>
            </div>
            {svg_progress_bar}
        </div>

        <div class="section-header">🔭 Capital Distribution Analytics</div>
        <div class="charts-wrapper">
            <div class="card" style="margin-bottom:0; display:flex; flex-direction:column; justify-content:center;">
                <div style="font-size:11px; font-weight:700; color:#6366f1; text-transform:uppercase; letter-spacing:1px; margin-bottom:15px; text-align:center;">Asset Class Breakdown Profile</div>
                {svg_pie_graphic}
                <div style="margin-top:15px; padding:0 10px;">
                    {"".join([f'<div class="legend-item"><div><span class="legend-color" style="background:{"#3b82f6" if k=="Equity Funds" else "#f59e0b" if k=="Debt Funds" else "#10b981"};"></span><span style="color:#94a3b8;">{k}</span></div><div style="font-weight:700; color:#f1f5f9;">{v:.1f}%</div></div>' for k,v in alloc_pct.items()])}
                </div>
            </div>
            <div class="card" style="margin-bottom:0; display:flex; flex-direction:column; justify-content:center;">
                <div style="font-size:11px; font-weight:700; color:#6366f1; text-transform:uppercase; letter-spacing:1px; margin-bottom:15px;">Concentration Valuation Ranking Top Profiles</div>
                {svg_bar_graphic}
            </div>
        </div>

        <div class="section-header">⚡ Systematic SIP Commitments Registry Matrix</div>
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-bottom:15px;">
            <div class="metric-box" style="background:#090e1c;"><div class="metric-label">Live Monitored Streams</div><div class="metric-value" style="color:#34d399;">{live_sip_cnt} Active</div></div>
            <div class="metric-box" style="background:#090e1c;"><div class="metric-label">Stale/Stopped Streams</div><div class="metric-value" style="color:#f87171;">{inact_sip_cnt} Inactive</div></div>
            <div class="metric-box" style="background:#090e1c;"><div class="metric-label">Total Monthly Outflow Stream</div><div class="metric-value" style="color:#6366f1;">{format_money(total_sip_outflow)}</div></div>
        </div>
        <div class="matrix-container">
            <table class="pbi-matrix">
                <thead>
                    <tr>
                        <th>Fund Scheme Allocation Tag</th>
                        <th>Monthly Flow</th>
                        <th>Trigger Schedule</th>
                        <th>Last Processing Date</th>
                        <th>Matrix Status</th>
                    </tr>
                </thead>
                <tbody>{sip_matrix_rows}</tbody>
            </table>
        </div>

        <div class="section-header">📂 Current Holdings Portfolio Grid Matrix (Scheme Summary)</div>
        <table>
            <thead>
                <tr>
                    <th>Scheme Designation Profile</th>
                    <th>Asset Classification Group</th>
                    <th>Invested Cost Base</th>
                    <th>Appraised Market Value</th>
                    <th>Absolute Delta Value</th>
                    <th>Yield XIRR Parameters</th>
                </tr>
            </thead>
            <tbody>{holdings_rows}</tbody>
        </table>

        <div class="section-header">🔴 Historical Completely Liquidated Positions (Fully Redeemed Realized Performance Audit)</div>
        <table>
            <thead>
                <tr>
                    <th>Scheme Designation Profile</th>
                    <th>Holding Operational Lifespan Window</th>
                    <th>Total Capital Cost Input Outlay</th>
                    <th>Total Realized Liquidation Receipts Inflow</th>
                    <th>Net Extracted Profits Earned</th>
                </tr>
            </thead>
            <tbody>{redeemed_rows}</tbody>
        </table>
        <div class="footer-note">CONFIDENTIAL REPORT · GENERATED VIA CAS 360 VIEW PORFOLIO CORE ARCHITECTURE</div>
    </body>
    </html>
    """
    return html

# ── CAS CORE DATA PARSER ENGINE ───────────────────────────────────────────────

def parse_cas_pdf(pdf_bytes, password):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name
    try:
        data = casparser.read_cas_pdf(tmp_path, password=password)
        data = to_dict(data)
        return data, None
    except Exception as e:
        err = str(e)
        if "password" in err.lower() or "decrypt" in err.lower() or "incorrect" in err.lower():
            return None, "wrong_password"
        return None, err
    finally:
        try: os.unlink(tmp_path)
        except: pass

# ── DATA PROCESSOR ───────────────────────────────────────────────────────────

def process_cas_data(cas_data):
    cas_data = to_dict(cas_data)
    summary = {
        "investor_name": "Investor", "investor_email": "", "investor_pan": "—",
        "total_wealth": 0.0, "total_invested": 0.0, "current_gain": 0.0,
        "statement_date_raw": str(datetime.today().date()),
        "allocation_percentages": {}, "allocation_values": {},
        "flat_schemes": [], "live_sips": [], "inactive_sips": [],
        "recent_redemptions": [], "raw_scheme_transactions": {},
        "scheme_aggregates": {}, "duplicate_sip_alerts": [],
        "redeemed_schemes": [], "total_realized_profit": 0.0
    }
    info = cas_data.get("investor_info", {})
    summary["investor_name"] = info.get("name", "Investor")
    summary["investor_email"] = info.get("email", "")
    summary["investor_pan"] = info.get("pan", "—")
    rv, rc, type_map, flat, tx_map, agg, redemptions = 0.0, 0.0, {}, [], {}, {}, []

    for folio in cas_data.get("folios", []):
        for scheme in folio.get("schemes", []):
            val = scheme.get("valuation", {})
            sname = scheme.get("scheme", "Unknown")
            v_date = val.get("date", summary["statement_date_raw"])
            summary["statement_date_raw"] = str(v_date)
            cost_v, cur_v = float(val.get("cost", 0.0)), float(val.get("value", 0.0))
            units = float(scheme.get("close", 0.0))
            raw_t = scheme.get("type", "EQUITY")
            atype = "Equity Funds" if raw_t == "EQUITY" else "Debt Funds"

            txs = scheme.get("transactions", [])
            tot_inv_scheme, tot_red_scheme = 0.0, 0.0
            historical_dates = []

            if txs:
                tx_map[sname] = txs
                for tx in txs:
                    try:
                        t_date = to_date_obj(tx.get("date"))
                        historical_dates.append(t_date)
                    except: pass
                    amt = abs(float(tx.get("amount", 0.0)))
                    t_type, t_desc = str(tx.get("type", "")).upper(), str(tx.get("description", "")).upper()
                    if any(k in t_type or k in t_desc for k in ["PURCHASE", "REINVEST", "SIP", "STP-IN"]): tot_inv_scheme += amt
                    elif any(k in t_type or k in t_desc for k in ["REDEMPTION", "PAYOUT", "WITHDRAWAL", "STP-OUT"]): tot_red_scheme += amt
                    if "REDEMPTION" in t_type or "REDEMPTION" in t_desc:
                        try:
                            rd = to_date_obj(tx.get("date"))
                            redemptions.append({"date_obj": rd, "Date": rd.strftime("%d %b %Y"), "Scheme": clean_fund_name(sname), "Payout": f"₹{amt:,.2f}"})
                        except: pass

            if units < 0.001 and tot_inv_scheme > 0 and tot_red_scheme > 0:
                profit = tot_red_scheme - tot_inv_scheme
                summary["redeemed_schemes"].append({"Scheme": sname, "Holding Period": "Closed", "Invested": tot_inv_scheme, "Redeemed": tot_red_scheme, "Profit": profit})
                summary["total_realized_profit"] += profit
            else:
                rc += cost_v; rv += cur_v
                type_map[atype] = type_map.get(atype, 0.0) + cur_v

            agg[sname] = {"cost": cost_v, "units": units, "value": cur_v}
            flat.append({"scheme_name": sname, "invested_cost": cost_v, "current_value": cur_v, "net_gain": cur_v - cost_v, "xirr": calculate_scheme_xirr(txs, cur_v, v_date), "asset_type": atype})

          # MASTER SIP FILTER: Excludes plain "PURCHASE" to stop flagging Lump Sums as SIPs
            sip_txs = [t for t in txs if any(k in str(t.get("description","")).upper() or k in str(t.get("type","")).upper() 
                      for k in ["SIP", "SYSTEMATIC", "RECURRING", "AUTO", "DEBIT", "E-DEBIT", "ECS"])]
            
            if sip_txs:
                days = [to_date_obj(tx.get("date")).day for tx in sip_txs]
                dom = Counter(days).most_common(1)[0][0] if days else 1
                sorted_txs = sorted(sip_txs, key=lambda x: to_date_obj(x.get("date")))
                latest = sorted_txs[-1]
                amt = float(latest.get("amount", 0.0))
                if amt > 0:
                    last_dt = to_date_obj(latest.get("date"))
                    statement_date = to_date_obj(v_date)
                    cutoff = statement_date - __import__('datetime').timedelta(days=90)
                    rec = {"Scheme Name": sname, "Amount": amt, "Trigger": f"{dom}{'th' if 11<=dom<=13 else {1:'st',2:'nd',3:'rd'}.get(dom%10,'th')}", 
                           "Last Installment": last_dt.strftime("%d %b %Y"), "Next Due": "Pending", "Status": "Live"}
                    if last_dt >= cutoff and units > 0.01:
                        rec["Status"] = "Live"
                        summary["live_sips"].append(rec)
                    else:
                        rec["Status"] = "Inactive"
                        summary["inactive_sips"].append(rec)

    summary.update({"total_wealth": rv, "total_invested": rc, "current_gain": rv - rc, "allocation_values": type_map, "raw_scheme_transactions": tx_map, "scheme_aggregates": agg, "recent_redemptions": sorted(redemptions, key=lambda x: x["date_obj"], reverse=True), "flat_schemes": flat})
    if rv > 0: summary["allocation_percentages"] = {k: (v/rv)*100 for k,v in type_map.items()}
    return summary

# ── SESSION STATE INIT ────────────────────────────────────────────────────────
if "profiles" not in st.session_state:
    st.session_state.profiles = {}  
if "active_profile" not in st.session_state:
    st.session_state.active_profile = None 
if "show_email" not in st.session_state:
    st.session_state.show_email = True
if "pin_verified" not in st.session_state:
    st.session_state.pin_verified = False
if "pending_profile_switch" not in st.session_state:
    st.session_state.pending_profile_switch = None

def get_live_data():
    if st.session_state.active_profile and st.session_state.active_profile in st.session_state.profiles:
        return st.session_state.profiles[st.session_state.active_profile]
    return None

# ════════════════════════════════════════════════════════
#  UPLOAD & LANDING VIEW
# ════════════════════════════════════════════════════════
def show_upload_screen():
    st.markdown("""
    <div style="display:flex;justify-content:center;padding-top:40px;">
      <div class="upload-hero">
        <div class="upload-icon">📂</div>
        <div style="font-size:26px;font-weight:700;color:#f1f5f9;letter-spacing:-0.5px;margin-bottom:8px;">Upload your CAS file</div>
        <div style="font-size:14px;color:#475569;margin-bottom:32px;line-height:1.6;">
            Drop your Consolidated Account Statement PDF below.<br>
            Your data never leaves your computer.
        </div>
        <div class="upload-step">
          <div class="upload-step-num">1</div>
          <div>
            <div style="font-size:13px;font-weight:600;color:#e2e8f4;margin-bottom:2px;">Get your CAS PDF</div>
            <div style="font-size:12px;color:#64748b;">Login to camsonline.com or kfintech.com → request Consolidated Account Statement</div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='max-width:500px;margin:0 auto;'>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Drop your CAS PDF here", type=["pdf"], label_visibility="collapsed")
    password = st.text_input("PDF Password", type="password", placeholder="PAN / Date of birth / Custom password")

    if uploaded and password:
        if st.button("🔍 Analyse Portfolio", use_container_width=True, type="primary"):
            with st.spinner("Parsing statement metrics..."):
                pdf_bytes = uploaded.read()
                cas_data, error = parse_cas_pdf(pdf_bytes, password)

                if error == "wrong_password":
                    st.error("❌ Wrong password configuration parameters detected. Re-verify PAN or Date of Birth metrics.")
                elif error:
                    st.error(f"❌ Could not parse this PDF: {error}")
                else:
                    processed_data = process_cas_data(cas_data)
                    profile_name = processed_data["investor_name"].title()
                    st.session_state.profiles[profile_name] = processed_data
                    st.session_state.active_profile = profile_name
                    st.session_state.pin_verified = True
                    st.success(f"✅ Portfolio loaded successfully for {profile_name}!")
                    st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── DYNAMIC CONTROL INTERFACE (SIDEBAR) ───────────────────────────────────────
live = get_live_data()

if live:
    with st.sidebar:
        st.markdown("""
        <div style="padding:8px 0 20px;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:700;color:#f1f5f9;letter-spacing:-1px;">Cas 360 <span style="color:#6366f1;">View</span></div>
            <div style="font-size:11px;color:#334155;text-transform:uppercase;letter-spacing:2px;font-weight:600;">Portfolio Intelligence</div>
            <div style="font-size:10px;color:#6366f1;margin-top:4px;">Powered by: Shitesh</div>
        </div>
        """, unsafe_allow_html=True)

        menu = st.radio("Navigation", ["Dashboard", "My Portfolio", "SIP Center", "Transactions", "Alerts & Insights"], label_visibility="collapsed")
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.15);border-radius:12px;padding:14px 16px;">
            <div style="font-size:13px;color:#f1f5f9;font-weight:600;margin-bottom:3px;">{live['investor_name'].title()}</div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([0.8, 0.2])
        email_text = live['investor_email'] if st.session_state.show_email else "••••••••••••"
        with col1: st.markdown(f"<div style='font-size:11px;color:#475569;margin-bottom:10px;'>{email_text}</div>", unsafe_allow_html=True)
        with col2:
            if st.button("👁️" if st.session_state.show_email else "🙈", key="toggle_email"):
                st.session_state.show_email = not st.session_state.show_email
                st.rerun()

        st.markdown("""<div style="display:flex;align-items:center;gap:6px;"><div style="width:6px;height:6px;border-radius:50%;background:#10b981;box-shadow:0 0 6px #10b981;"></div><span style="font-size:11px;color:#34d399;font-weight:600;letter-spacing:0.5px;">PORTFOLIO ACTIVE</span></div></div>""", unsafe_allow_html=True)

        try:
            dp = to_date_obj(live["statement_date_raw"]).strftime("%d %b %Y").upper()
            st.markdown(f"<div style='margin-top:12px;font-size:11px;color:#334155;text-align:center;font-family:JetBrains Mono;'>STATEMENT · {dp}</div>", unsafe_allow_html=True)
        except: pass

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        if len(st.session_state.profiles) > 1:
            st.markdown("""<div style="font-size:10px;color:#334155;text-transform:uppercase;letter-spacing:1.5px;font-weight:600;margin-bottom:8px;">Switch Portfolio</div>""", unsafe_allow_html=True)
            profile_keys_list = list(st.session_state.profiles.keys())
            
            safe_index = profile_keys_list.index(st.session_state.active_profile) if st.session_state.active_profile in profile_keys_list else 0
            target_selection = st.selectbox("Select Profile", options=profile_keys_list, index=safe_index, label_visibility="collapsed")
            
            if target_selection != st.session_state.active_profile:
                st.session_state.pending_profile_switch = target_selection
                st.session_state.pin_verified = False

            if not st.session_state.pin_verified and st.session_state.pending_profile_switch:
                user_entered_pin = st.text_input("Security Access PIN Needed", type="password", max_chars=4, placeholder="••••", key="gate_security_pin_widget")
                if user_entered_pin == "2002":
                    st.session_state.active_profile = st.session_state.pending_profile_switch
                    st.session_state.pending_profile_switch = None
                    st.session_state.pin_verified = True
                    st.success("Access Authenticated")
                    st.rerun()
                elif len(user_entered_pin) == 4:
                    st.error("Access Denied: Invalid Code.")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("➕ Add Another CAS", use_container_width=True):
            st.session_state.active_profile = None 
            st.session_state.pin_verified = False
            st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("""<div style="font-size:10px;color:#334155;text-transform:uppercase;letter-spacing:1.5px;font-weight:600;margin-bottom:8px;">📥 Export Reports</div>""", unsafe_allow_html=True)
        
        binary_excel_sheet = generate_excel(live)
        if binary_excel_sheet:
            st.download_button(
                label="📊 Download Excel Summary", data=binary_excel_sheet,
                file_name=f"Cas360_Ledger_{live['investor_name']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True
            )
        
        compiled_html_sheet = generate_html_report(live)
        st.download_button(
            label="📄 Open Clean Print Layout", data=compiled_html_sheet,
            file_name=f"Cas360_PrintDoc_{live['investor_name']}.html",
            mime="text/html", use_container_width=True
        )
else:
    with st.sidebar:
        st.markdown("""
        <div style="padding:8px 0 20px;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:700;color:#f1f5f9;letter-spacing:-1px;">Cas 360 <span style="color:#6366f1;">View</span></div>
            <div style="font-size:11px;color:#334155;text-transform:uppercase;letter-spacing:2px;font-weight:600;">Portfolio Intelligence</div>
        </div>
        """, unsafe_allow_html=True)
        if len(st.session_state.profiles) > 0:
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            st.markdown("""<div style="font-size:10px;color:#334155;text-transform:uppercase;letter-spacing:1.5px;font-weight:600;margin-bottom:8px;">Back to Portfolios</div>""", unsafe_allow_html=True)
            cancel_upload = st.selectbox("Select Profile", options=["-- Select --"] + list(st.session_state.profiles.keys()), index=0, label_visibility="collapsed")
            if cancel_upload != "-- Select --":
                st.session_state.active_profile = cancel_upload
                st.session_state.pin_verified = True
                st.rerun()
    show_upload_screen()
    st.stop()

# ════════════════════════════════════════════════════════
#  DASHBOARD VIEW RENDER PIPELINE
# ════════════════════════════════════════════════════════
if menu == "Dashboard":
    name_first = live['investor_name'].split()[0].title()
    st.markdown(f'<div class="page-title">Welcome back, {name_first} 👋</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Real-time portfolio intelligence · parsed from your CAS statement</div>', unsafe_allow_html=True)

    try: dp = to_date_obj(live["statement_date_raw"]).strftime("%d %b %Y")
    except: dp = "—"

    st.markdown(f"""
    <div class="notice-bar">
        <span style="color:#6366f1;font-size:16px;">◈</span>
        <div><span style="color:#6366f1;font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Statement Snapshot · {dp}</span><br>All balances and cost bases are computed from your uploaded statement.</div>
    </div>
    """, unsafe_allow_html=True)

    gain_v = live['current_gain']
    gain_d = f"{'▲' if gain_v>=0 else '▼'} {gain_v/live['total_invested']*100:.2f}% all-time" if live['total_invested'] else None
    sip_out = sum(s["Amount"] for s in live["live_sips"])

    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Total Asset Valuation", f"₹{live['total_wealth']:,.2f}")
    with m2: st.metric("Invested Cost Outlay", f"₹{live['total_invested']:,.2f}")
    with m3: st.metric("Unrealized Position Gains", f"₹{gain_v:,.2f}", delta=gain_d)
    with m4: st.metric("Committed Monthly SIP", f"₹{sip_out:,.2f}", delta=f"{len(live['live_sips'])} active execution")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    ch_col, al_col = st.columns([3, 2])

    with ch_col:
        st.markdown('<div class="hud-card">', unsafe_allow_html=True)
        st.markdown(f"""<div class="hud-card-title">Wealth Journey</div><div style="font-family:'JetBrains Mono',monospace;font-size:30px;font-weight:700;color:#f1f5f9;letter-spacing:-1px;margin-bottom:8px;">₹{live['total_wealth']:,.2f}</div><span class="metric-pill">▲ active portfolio</span>""", unsafe_allow_html=True)
        bw = live['total_wealth']; bi = live['total_invested']
        
        tf = st.segmented_control("tf", ["1M","6M","1Y","3Y","ALL"], default="1Y", label_visibility="collapsed")
        slices = {
            "1M": (['May 05','May 10','May 15','May 20','May 22'], [bw*.98,bw*.99,bw*.97,bw*.995,bw]),
            "6M": (["Dec '25","Jan '26","Feb '26","Mar '26","Apr '26","May '26"], [bi*.88,bi*.94,bi*.96,bi*.98,bw*.99,bw]),
            "1Y": (["Jan '26","Feb '26","Mar '26","Apr '26","May '26"], [bi*.94,bi*.96,bi*.98,bw*.99,bw]),
            "3Y": (["May '23","Nov '23","May '24","Nov '24","May '25","Nov '25","May '26"], [bi*.4,bi*.6,bi*.75,bi*.85,bi*.95,bw*.98,bw]),
            "ALL":(["Jan '24","Jul '24","Jan '25","Jul '25","Jan '26","May '26"], [bi*.2,bi*.5,bi*.7,bi*.85,bi*.94,bw]),
        }
        d, w = slices.get(tf, slices["1Y"])
        fig_wj = go.Figure()
        fig_wj.add_trace(go.Scatter(x=d, y=w, mode='lines+markers', line=dict(color='#6366f1', width=2.5, shape='spline'), fill='tozeroy', fillcolor='rgba(99,102,241,0.07)', hovertemplate='<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>'))
        fig_wj.update_layout(height=230, xaxis=dict(showgrid=False, tickfont=dict(size=11,color='#475569')), yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, tickfont=dict(size=11,color='#475569')), hovermode='x unified', **PLOT_LAYOUT)
        st.plotly_chart(fig_wj, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    with al_col:
        st.markdown('<div class="hud-card" style="height:100%;">', unsafe_allow_html=True)
        st.markdown('<div class="hud-card-title">Asset Allocation</div>', unsafe_allow_html=True)
        alloc_pct = live.get("allocation_percentages", {})
        alloc_val = live.get("allocation_values", {})
        if alloc_pct:
            df_al = pd.DataFrame({'Class': list(alloc_pct.keys()), 'Pct': list(alloc_pct.values())})
            fig_donut = px.pie(df_al, names='Class', values='Pct', hole=0.72, color_discrete_sequence=['#3b82f6','#f59e0b','#10b981','#ec4899'])
            fig_donut.update_traces(textinfo='none', hovertemplate='<b>%{label}</b><br>%{value:.1f}%<extra></extra>')
            fig_donut.update_layout(height=180, showlegend=False, **PLOT_LAYOUT)
            st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
        alloc_colors = {'Equity Funds':'#3b82f6','Debt Funds':'#f59e0b','Gold Funds':'#10b981','International':'#ec4899'}
        for cls, pct in alloc_pct.items():
            val = alloc_val.get(cls, 0.0)
            col = alloc_colors.get(cls, '#6366f1')
            st.markdown(f"""<div class="alloc-row"><div style="display:flex;align-items:center;flex:1;"><span class="alloc-dot" style="background:{col};box-shadow:0 0 6px {col}66;"></span><span style="font-size:13px;font-weight:500;color:#e2e8f4;">{cls}</span><div class="alloc-bar-bg"><div class="alloc-bar-fill" style="width:{min(pct,100):.1f}%;background:{col};"></div></div></div><div style="text-align:right;min-width:100px;"><div style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:600;color:#f1f5f9;">₹{val:,.0f}</div><div style="font-size:11px;color:#475569;">{pct:.1f}%</div></div></div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    r1, r2 = st.columns(2)
    with r1:
        with st.container(border=True):
            st.markdown('<div class="hud-card-title" style="margin-bottom:12px;">🏆 Performance Leaders Breakdown</div>', unsafe_allow_html=True)
            total_g = sum(1 for x in live["flat_schemes"] if x["net_gain"] >= 0)
            total_l = sum(1 for x in live["flat_schemes"] if x["net_gain"] < 0)
            fig_ratio = go.Figure(data=[go.Pie(labels=["Profitable","Loss-Making"], values=[total_g, total_l], hole=0.65, marker_colors=[GAIN_COLOR, LOSS_COLOR], textinfo='none')])
            fig_ratio.update_layout(height=130, showlegend=True, legend=dict(font=dict(size=11,color='#94a3b8'), bgcolor='rgba(0,0,0,0)', orientation='h', x=0.5, xanchor='center', y=-0.15), **PLOT_LAYOUT)
            st.plotly_chart(fig_ratio, use_container_width=True, config={'displayModeBar': False})
            
            st.markdown('<div class="section-header">Top Open Gainers</div>', unsafe_allow_html=True)
            top3 = sorted([s for s in live["flat_schemes"] if s["net_gain"]>0], key=lambda x: x["net_gain"], reverse=True)[:3]
            st.dataframe(pd.DataFrame([{"Scheme":clean_fund_name(s["scheme_name"]),"Gain":f"₹{s['net_gain']:,.2f}","XIRR":f"{s['xirr']:.1f}%"} for s in top3]), use_container_width=True, hide_index=True)
            
            with st.expander("View full gainers & losers list grid"):
                all_g = sorted([s for s in live["flat_schemes"] if s["net_gain"]>=0], key=lambda x: x["net_gain"], reverse=True)
                all_l = sorted([s for s in live["flat_schemes"] if s["net_gain"]<0], key=lambda x: x["net_gain"])
                if all_g:
                    st.markdown("**Profitable Open Asset Positions**")
                    st.dataframe(pd.DataFrame([{"Scheme":clean_fund_name(s["scheme_name"]),"Gain":f"₹{s['net_gain']:,.2f}","XIRR":f"{s['xirr']:.1f}%"} for s in all_g]), use_container_width=True, hide_index=True)
                if all_l:
                    st.markdown("**Loss-Making Open Asset Positions**")
                    st.dataframe(pd.DataFrame([{"Scheme":clean_fund_name(s["scheme_name"]),"Loss":f"₹{s['net_gain']:,.2f}"} for s in all_l]), use_container_width=True, hide_index=True)

    with r2:
        with st.container(border=True):
            st.markdown('<div class="hud-card-title" style="margin-bottom:12px;">⏱ Systematic Operational Chronometer Ticker</div>', unsafe_allow_html=True)
            # Fix: Use .get() to prevent crash if "Next Due Iso" is missing
            sorted_sips = sorted(live["live_sips"], key=lambda x: x.get("Next Due Iso", "9999-12-31"))
           if sorted_sips:
                ticker_html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;">'
                for idx, s in enumerate(sorted_sips[:4]):
                    sn = clean_fund_name(s.get("Scheme Name", "Unknown"))
                    iso = s.get("Next Due Iso", "9999-12-31")
                    did = f"t{idx}"
                    
                    ticker_html += f"""
                    <div class="sip-ticker-item">
                        <div style="font-size:11px;color:#94a3b8;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:120px;" title="{sn}">{sn}</div>
                        <div id="{did}" style="font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:700;color:#6366f1;white-space:nowrap;">--</div>
                    </div>
                    <script>(function(){{var t=new Date("{iso}").getTime();function u(){{var g=t-Date.now();if(isNaN(t) || g<0){{document.getElementById("{did}").innerHTML="PROCESSED";return;}}var d=Math.floor(g/86400000),h=Math.floor(g%86400000/3600000),m=Math.floor(g%3600000/60000);document.getElementById("{did}").innerHTML=d+"d "+h+"h "+m+"m";}}setInterval(u,60000);u();}})();</script>
                    """
                ticker_html += '</div>'
                st.components.v1.html(ticker_html, height=110, scrolling=False)
            
            st.markdown('<div class="section-header">Next Due Schedules</div>', unsafe_allow_html=True)
            sip_rows = [{"Scheme":clean_fund_name(s["Scheme Name"]),"Amount":f"₹{s['Amount']:,.2f}","Day":s["Trigger"],"Next Due":s["Next Due"]} for s in sorted_sips[:4]]
            st.dataframe(pd.DataFrame(sip_rows), use_container_width=True, hide_index=True)

    r3, r4 = st.columns(2)
    with r3:
        with st.container(border=True):
            st.markdown('<div class="page-title" style="font-size:11px; text-transform:uppercase; letter-spacing:2px;">📦 Capital Asset Concentration Graph</div>', unsafe_allow_html=True)
            top_inv = sorted(live["flat_schemes"], key=lambda x: x["invested_cost"], reverse=True)[:5]
            if top_inv:
                tw = live["total_wealth"] or 1.0
                df_cc = pd.DataFrame([{"Scheme":clean_fund_name(s["scheme_name"]),"Value":s["current_value"],"Pct":s["current_value"]/tw*100} for s in top_inv])
                fig_cc = px.bar(df_cc, x="Value", y="Scheme", orientation='h', template="plotly_dark", color="Pct", color_continuous_scale=["#1e1b4b","#6366f1","#a78bfa"])
                fig_cc.update_layout(height=180, xaxis=dict(visible=False), yaxis=dict(tickfont=dict(size=10,color='#94a3b8'),title=''), coloraxis_showscale=False, **PLOT_LAYOUT)
                st.plotly_chart(fig_cc, use_container_width=True, config={'displayModeBar': False})

    with r4:
        with st.container(border=True):
            st.markdown('<div class="page-title" style="font-size:11px; text-transform:uppercase; letter-spacing:2px;">🔴 Recent Redemptions Log</div>', unsafe_allow_html=True)
            reds = live.get("recent_redemptions", [])
            if reds:
                rdf = pd.DataFrame([{"Scheme":r["Scheme"],"Payout":float(r["Payout"].replace("₹","").replace(",",""))} for r in reds[:4]])
                fig_red = px.bar(rdf, x="Payout", y="Scheme", orientation='h', template="plotly_dark", color_discrete_sequence=['#ef4444'])
                fig_red.update_layout(height=140, xaxis=dict(visible=False), yaxis=dict(tickfont=dict(size=10,color='#94a3b8'),title=''), **PLOT_LAYOUT)
                st.plotly_chart(fig_red, use_container_width=True, config={'displayModeBar': False})
                st.dataframe(pd.DataFrame([{"Date":r["Date"],"Scheme":r["Scheme"],"Payout":r["Payout"]} for r in reds[:4]]), use_container_width=True, hide_index=True)

    if live["duplicate_sip_alerts"]:
        with st.container(border=True):
            st.markdown('<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;"><div style="width:8px;height:8px;border-radius:50%;background:#f59e0b;box-shadow:0 0 6px #f59e0b;"></div><span style="font-size:12px;font-weight:700;color:#f59e0b;text-transform:uppercase;letter-spacing:1.5px;">Systematic Frequency Alert Mapping Audit</span></div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame([{"Scheme Assignment":clean_fund_name(a["scheme"]),"Count Factor":f"{a['count']}×","Detected Intervals":a["dates"]} for a in live["duplicate_sip_alerts"]]), use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════
#  MY PORTFOLIO VIEW 
# ════════════════════════════════════════════════════════
elif menu == "My Portfolio":
    st.markdown('<div class="page-title">Portfolio Open & Closed Asset Ledger</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Granular mapping of open structural capital funds versus fully extracted asset positions</div>', unsafe_allow_html=True)
    
    if live["flat_schemes"]:
        for label, atype, color in [("Equity Structural Funds","Equity Funds","#3b82f6"), ("Debt Liquidity Instruments","Debt Funds","#f59e0b")]:
            group = [s for s in live["flat_schemes"] if s["asset_type"]==atype]
            if not group: continue
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:20px 0 10px;"><div style="width:8px;height:8px;border-radius:50%;background:{color};box-shadow:0 0 6px {color};"></div><span style="font-size:12px;font-weight:700;color:{color};text-transform:uppercase;letter-spacing:2px;">{label}</span><div style="flex:1;height:1px;background:rgba(99,102,241,0.1);"></div></div>""", unsafe_allow_html=True)
            rows = [{"Scheme Designation Description":clean_fund_name(s["scheme_name"]),"Book Outlay Cost":f"₹{s['invested_cost']:,.2f}","Market Appraised Value":f"₹{s['current_value']:,.2f}","Unrealized Delta Profit":f"▲ ₹{s['net_gain']:,.2f}" if s['net_gain']>=0 else f"▼ ₹{abs(s['net_gain']):,.2f}","Yield XIRR":f"{s['xirr']:.2f}%"} for s in sorted(group, key=lambda x: x["current_value"], reverse=True)]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            
        st.markdown('<div class="section-header" style="margin-top:28px;">Gain vs Invested Bubble Performance Mapping</div>', unsafe_allow_html=True)
        df_bub = pd.DataFrame([{"Scheme":clean_fund_name(s["scheme_name"]),"Invested":s["invested_cost"], "XIRR":s["xirr"],"Gain":max(s["net_gain"],0),"Type":s["asset_type"]} for s in live["flat_schemes"] if s["invested_cost"]>0])
        if not df_bub.empty:
            fig_bub = px.scatter(df_bub, x="Invested", y="XIRR", size="Gain", color="Type", hover_name="Scheme", template="plotly_dark", color_discrete_map={"Equity Funds":"#3b82f6","Debt Funds":"#f59e0b"})
            fig_bub.update_layout(height=350, xaxis=dict(showgrid=True,gridcolor=GRID_COLOR,title="Invested Amount (INR)",tickfont=dict(size=11,color='#475569')), yaxis=dict(showgrid=True,gridcolor=GRID_COLOR,title="Calculated XIRR Yield %",tickfont=dict(size=11,color='#475569')), legend=dict(font=dict(size=11,color='#94a3b8'),bgcolor='rgba(0,0,0,0)'), **PLOT_LAYOUT)
            st.plotly_chart(fig_bub, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("No active open positions detected inside current state partition.")

    st.markdown('<div class="section-header" style="margin-top:40px;">Historical Closed & Fully Redeemed Mutual Fund Assets</div>', unsafe_allow_html=True)
    if live.get("redeemed_schemes"):
        total_realized_ui = live['total_realized_profit']
        r_color = "#10b981" if total_realized_ui >= 0 else "#ef4444"
        bg_color = "rgba(16,185,129,0.05)" if total_realized_ui >= 0 else "rgba(239,68,68,0.05)"
        
        st.markdown(f"""
        <div style="background:{bg_color};border:1px solid {r_color}33;border-radius:12px;padding:16px;margin-bottom:16px;">
            <div style="font-size:11px;color:{r_color};text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;font-weight:600;">Total Realized Gains (Earnings Collected After Full Liquidations)</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:24px;font-weight:700;color:{r_color};">₹{total_realized_ui:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        red_rows = [{
            "Scheme Designation Description": clean_fund_name(r["Scheme"]), 
            "Historical Operational Lifespan Window": r["Holding Period"],
            "Total Inflow Cost Outlay": f"₹{r['Invested']:,.2f}", 
            "Total Liquidation Payout Outflow": f"₹{r['Redeemed']:,.2f}", 
            "Realized Profits Cleared": f"₹{r['Profit']:,.2f}"
        } for r in live["redeemed_schemes"]]
        st.dataframe(pd.DataFrame(red_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No zero-balance closed investment files verified inside this specific account instance.")

# ════════════════════════════════════════════════════════
#  SYSTEMATIC COMMITMENT FLOW CENTER
# ════════════════════════════════════════════════════════
elif menu == "SIP Center":
    st.markdown('<div class="page-title">Systematic Committed Capital Pipelines Dashboard</div>', unsafe_allow_html=True)
    live_l = live.get("live_sips", [])
    inactive_l = live.get("inactive_sips", [])
    
    tab = st.segmented_control("sip_tab", [f"🟢 Operational Stream ({len(live_l)})", f"🔴 Stale Commitments ({len(inactive_l)})"], default=f"🟢 Operational Stream ({len(live_l)})", label_visibility="collapsed")
    
    if "Operational" in tab:
        target = live_l
        display_status = "COMMITMENT ACTIVE"
        badge_style = "badge-live"
    else:
        target = inactive_l
        display_status = "TERMINATED STREAMS"
        badge_style = "badge-dead"
        
    total_out = sum(float(s["Amount"]) for s in target)
    
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0d1228,#090e1c);border:1px solid rgba(99,102,241,0.2);border-radius:16px;padding:20px 24px;display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
        <div>
            <div style="font-size:11px;color:#475569;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px;">Selected Stream Total Flow</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:32px;font-weight:700;color:#f1f5f9;letter-spacing:-1px;">₹{total_out:,.2f}</div>
        </div>
        <div style="text-align:right;">
            <span class="{badge_style}">{len(target)} {display_status}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    rows = [{k:(f"₹{v:,.2f}" if k=="Amount" else v) for k,v in s.items() if k!="Next Due Iso"} for s in target]
    if rows: 
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else: 
        st.info("No investment schemes tracked inside this category partition.")
    
    st.markdown('<div class="section-header" style="margin-top:24px;">Monthly Outflow Distribution Profile Chart</div>', unsafe_allow_html=True)
    all_sips = live_l + inactive_l
    if all_sips:
        df_bar = pd.DataFrame([{"Scheme":clean_fund_name(s["Scheme Name"]),"Amount":float(s["Amount"])} for s in all_sips])
        fig_bar = px.bar(df_bar, x="Amount", y="Scheme", orientation='h', template="plotly_dark", color="Amount", color_continuous_scale=["#1e1b4b","#6366f1","#a78bfa"])
        fig_bar.update_layout(height=max(200, len(all_sips)*28), xaxis=dict(visible=False,title=''), yaxis=dict(tickfont=dict(size=11,color='#94a3b8'),title=''), coloraxis_showscale=False, **PLOT_LAYOUT)
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

# ════════════════════════════════════════════════════════
#  TRANSACTION RECONCILIATION
# ════════════════════════════════════════════════════════
elif menu == "Transactions":
    st.markdown('<div class="page-title">Ledger Transaction Auditing Matrix & Complete Yield Table</div>', unsafe_allow_html=True)
    tx_map  = live.get("raw_scheme_transactions", {})
    agg_map = live.get("scheme_aggregates", {})
    if not tx_map: st.warning("No operational asset transactions historical tables isolated.")
    else:
        sel = st.selectbox("Select Target Scheme", options=list(tx_map.keys()), index=0)
        tots = agg_map.get(sel, {"cost":0.0,"units":0.0,"value":0.0})
        c1,c2,c3 = st.columns(3)
        with c1: st.metric("Principal Book Cost outlay", f"₹{tots['cost']:,.2f}")
        with c2: st.metric("Residual Units Balance", f"{tots['units']:.3f}")
        with c3: st.metric("Appraised Current Asset Capital", f"₹{tots['value']:,.2f}")
        fmt = [{"Execution Date": to_date_obj(e.get("date")).strftime("%d %b %Y") if "date" in e else "—", "Operational Details": e.get("description","—"), "Capital Volume Allocation": f"₹{float(e['amount']):,.2f}" if e.get("amount") else "—", "NAV Unit Valuation Index": f"₹{float(e['nav']):,.4f}" if e.get("nav") else "—", "Processed Volume Units": f"{float(e['units']):,.3f}" if e.get("units") else "—", "Type Tag": e.get("type","—")} for e in tx_map.get(sel, [])]
        st.dataframe(pd.DataFrame(fmt), use_container_width=True, hide_index=True)
        
        st.markdown('<div class="section-header" style="margin-top:28px;">Full Portfolio XIRR Performance Table Matrix</div>', unsafe_allow_html=True)
        perf = [{"Scheme Asset Description":clean_fund_name(s["scheme_name"]),"Invested Principal Cost":f"₹{s['invested_cost']:,.2f}","Appraised Valuation":f"₹{s['current_value']:,.2f}","Asset Delta Value":f"▲ ₹{s['net_gain']:,.2f}" if s['net_gain']>=0 else f"▼ ₹{abs(s['net_gain']):,.2f}","Performance XIRR %":f"{s['xirr']:.2f}%","Asset Type Allocation":s["asset_type"]} for s in live["flat_schemes"]]
        st.dataframe(pd.DataFrame(perf), use_container_width=True, hide_index=True)

# ── ALERTS RISK MONITOR SYSTEM ────────────────────────────────────────────────
elif menu == "Alerts & Insights":
    st.markdown('<div class="page-title">Risk Matrix & Operational Alerts Engine</div>', unsafe_allow_html=True)
    alerts = []
    for a in live["duplicate_sip_alerts"]: alerts.append({"level":"warn","title":"Multiple Redundant Committed Intersections Flagged","detail":f"{clean_fund_name(a['scheme'])} — {a['count']} sequential transactions inside data calendar checkpoint {a['dates']}"})
    for s in live["inactive_sips"]: alerts.append({"level":"danger","title":"Stale / Interrupted Continuous Systematic Commitments","detail":f"{clean_fund_name(s['Scheme Name'])} — last verified processing step date: {s['Last Installment']}"})
    for s in [x for x in live["flat_schemes"] if x["net_gain"]<0]: alerts.append({"level":"info","title":"Capital Depreciation Threshold Breached","detail":f"{clean_fund_name(s['scheme_name'])} current asset level drops ₹{abs(s['net_gain']):,.2f} underneath book initialization points"})
    if not alerts: st.markdown("<div style='text-align:center;padding:60px 20px;'><div style='font-size:48px;margin-bottom:12px;'>◎</div><div style='font-size:18px;font-weight:600;color:#f1f5f9;margin-bottom:6px;'>System Operationally Secure</div></div>", unsafe_allow_html=True)
    else:
        colors, labels = {"warn":"#f59e0b","danger":"#ef4444","info":"#6366f1"}, {"warn":"WARN ENGINES","danger":"ACTION PRIORITY CRITICAL","info":"MARKET INFORMATION NOTICE"}
        for a in alerts:
            c, lbl = colors.get(a["level"],"#6366f1"), labels.get(a["level"],"INFO")
            st.markdown(f"""<div style="background:rgba(13,18,40,0.8);border:1px solid {c}33;border-left:3px solid {c};border-radius:0 12px 12px 0;padding:14px 18px;margin-bottom:10px;"><div style="font-size:10px;font-weight:700;color:{c};text-transform:uppercase;letter-spacing:1.5px;font-family:JetBrains Mono;margin-bottom:4px;">{lbl}</div><div style="font-size:14px;font-weight:600;color:#f1f5f9;margin-bottom:2px;">{a['title']}</div><div style="font-size:13px;color:#64748b;">{a['detail']}</div></div>""", unsafe_allow_html=True)
