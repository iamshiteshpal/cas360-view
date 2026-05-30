import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import io
import tempfile
import datetime
import requests
from datetime import date
from collections import Counter
from pyxirr import xirr
import casparser

PLOT_BASE = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Instrument Sans', color='#718096'),
    margin=dict(l=0, r=0, t=10, b=10),
)
GRID = 'rgba(255,255,255,0.04)'
C_GAIN = '#48bb78'
C_LOSS = '#fc8181'
C_ACCENT = '#63b3ed'
C_ACCENT2 = '#9f7aea'


def apply_page_config():
    st.set_page_config(
        page_title="CAS 360 View — Portfolio Intelligence",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_global_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&family=Instrument+Sans:wght@400;500;600&display=swap');
        :root {
          --bg:        #07090f;
          --bg2:       #0c0f1a;
          --bg3:       #111627;
          --border:    rgba(255,255,255,0.06);
          --border-hi: rgba(99,179,237,0.35);
          --accent:    #63b3ed;
          --accent2:   #9f7aea;
          --gain:      #48bb78;
          --loss:      #fc8181;
          --warn:      #f6ad55;
          --text:      #e2e8f0;
          --muted:     #718096;
          --faint:     #2d3748;
        }
        *, *::before, *::after { box-sizing: border-box; }
        html, body, .stApp {
          background: var(--bg) !important;
          color: var(--text) !important;
          font-family: 'Instrument Sans', sans-serif !important;
        }
        .stApp::after {
          content: '';
          position: fixed;
          inset: 0;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.025'/%3E%3C/svg%3E");
          pointer-events: none;
          z-index: 9999;
        }
        [data-testid="stSidebar"] {
          background: var(--bg2) !important;
          border-right: 1px solid var(--border) !important;
        }
        [data-testid="stSidebar"] * { font-family: 'Instrument Sans', sans-serif !important; }
        div[data-testid="stMetric"] {
          background: var(--bg2) !important;
          border: 1px solid var(--border) !important;
          border-radius: 12px !important;
          padding: 18px 20px !important;
          transition: border-color .25s, transform .2s;
        }
        div[data-testid="stMetric"]:hover {
          border-color: var(--border-hi) !important;
          transform: translateY(-2px);
        }
        div[data-testid="stMetricValue"] > div {
          font-family: 'IBM Plex Mono', monospace !important;
          font-size: 18px !important;
          font-weight: 600 !important;
          color: #f7fafc !important;
        }
        div[data-testid="stMetricLabel"] > div {
          font-size: 10px !important;
          color: var(--muted) !important;
          text-transform: uppercase;
          letter-spacing: 1.4px;
          font-weight: 500 !important;
        }
        div[data-testid="stMetricDelta"] > div { font-size: 11px !important; }
        [data-testid="stVerticalBlockBorderWrapper"] > div > div {
          background: var(--bg2) !important;
          border: 1px solid var(--border) !important;
          border-radius: 14px !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] > div > div:hover {
          border-color: rgba(99,179,237,0.2) !important;
        }
        [data-testid="stDataFrame"] {
          border-radius: 10px !important;
          overflow: hidden;
          border: 1px solid var(--border) !important;
        }
        [data-testid="stSelectbox"] > div > div,
        [data-testid="stTextInput"] input {
          background: var(--bg3) !important;
          border: 1px solid var(--border) !important;
          border-radius: 8px !important;
          color: var(--text) !important;
        }
        [data-testid="stTextInput"] input { font-family: 'IBM Plex Mono', monospace !important; }
        [data-testid="stFileUploader"] {
          background: rgba(99,179,237,0.03) !important;
          border: 2px dashed rgba(99,179,237,0.2) !important;
          border-radius: 14px !important;
        }
        [data-testid="stSegmentedControl"] > div {
          background: var(--bg3) !important;
          border: 1px solid var(--border) !important;
          border-radius: 8px !important;
        }
        [data-testid="stSegmentedControl"] button[aria-checked="true"] {
          background: linear-gradient(135deg,#2b6cb0,#553c9a) !important;
          color: #fff !important;
          border-radius: 6px !important;
        }
        hr { border-color: var(--border) !important; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: var(--bg); }
        ::-webkit-scrollbar-thumb { background: var(--faint); border-radius: 4px; }
        .card { background: var(--bg2); border: 1px solid var(--border); border-radius: 14px; padding: 22px 24px; margin-bottom: 16px; position: relative; }
        .card-title { font-family: 'Syne', sans-serif; font-size: 11px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: 2px; margin-bottom: 14px; }
        .pill-gain { display: inline-flex; align-items: center; gap: 4px; background: rgba(72,187,120,0.1); border: 1px solid rgba(72,187,120,0.25); color: var(--gain); font-family: 'IBM Plex Mono',monospace; font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 20px; }
        .pill-loss { display: inline-flex; align-items: center; gap: 4px; background: rgba(252,129,129,0.1); border: 1px solid rgba(252,129,129,0.25); color: var(--loss); font-family: 'IBM Plex Mono',monospace; font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 20px; }
        .notice { background: rgba(99,179,237,0.05); border: 1px solid rgba(99,179,237,0.15); border-left: 3px solid var(--accent); border-radius: 0 10px 10px 0; padding: 12px 16px; font-size: 13px; color: var(--muted); margin-bottom: 22px; display: flex; align-items: flex-start; gap: 10px; }
        .section-sep { font-size: 10px; font-weight: 700; color: var(--faint); text-transform: uppercase; letter-spacing: 2px; margin: 24px 0 12px; display: flex; align-items: center; gap: 10px; }
        .section-sep::after { content:''; flex:1; height:1px; background: var(--border); }
        .page-title { font-family: 'Syne', sans-serif; font-size: 26px; font-weight: 800; color: #f7fafc; letter-spacing: -0.5px; margin-bottom: 4px; }
        .page-sub { font-size: 13px; color: var(--muted); margin-bottom: 22px; }
        .sip-card { background: var(--bg3); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        .alloc-row { display: flex; align-items: center; justify-content: space-between; padding: 9px 0; border-bottom: 1px solid var(--border); }
        .alloc-dot { width:7px;height:7px;border-radius:50%;display:inline-block;margin-right:8px; }
        .alert-card { border-left: 3px solid; border-radius: 0 10px 10px 0; padding: 12px 16px; margin-bottom: 10px; background: var(--bg2); }
        div[data-testid="stAppViewBlockContainer"] { padding-top: 2.5rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def to_date(d):
    if not d:
        return date.today()
    if isinstance(d, str):
        try:
            return datetime.datetime.strptime(d.split("T")[0], "%Y-%m-%d").date()
        except Exception:
            return date.today()
    if hasattr(d, "date"):
        return d.date()
    return d


def to_dict(obj):
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_dict(i) for i in obj]
    if hasattr(obj, "model_dump"):
        return to_dict(obj.model_dump())
    if hasattr(obj, "dict"):
        return to_dict(obj.dict())
    return obj


def clean_name(name):
    if not name:
        return "Unknown Scheme"
    for sfx in [
        "- Direct Plan - Growth Option", "- Direct Plan - Growth",
        "- Direct Growth Plan", "- Direct Plan Growth",
        "Direct Plan Growth", "Direct Growth", "Direct Plan",
        "Regular Plan", "Growth",
    ]:
        name = name.replace(sfx, "")
    return name.strip()


def ordinal(n):
    suffix = "th" if 11 <= n <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def next_due_date(dom: int) -> date:
    today = date.today()
    try:
        candidate = today.replace(day=dom)
    except ValueError:
        candidate = today.replace(day=28)
    if candidate <= today:
        m, y = today.month + 1, today.year
        if m > 12:
            m, y = 1, y + 1
        try:
            candidate = candidate.replace(year=y, month=m)
        except ValueError:
            candidate = candidate.replace(year=y, month=m, day=28)
    return candidate


def calc_xirr(transactions, current_value, valuation_date_str):
    dates, amounts = [], []
    for tx in transactions:
        try:
            dt = to_date(tx.get("date"))
            amt = float(tx.get("amount", 0.0))
            if amt > 0:
                dates.append(dt)
                amounts.append(-amt)
        except Exception:
            continue
    if current_value > 0:
        try:
            dates.append(to_date(valuation_date_str))
            amounts.append(current_value)
        except Exception:
            pass
    if len(amounts) >= 2 and sum(amounts) != 0:
        try:
            rate = xirr(dates, amounts)
            return rate * 100 if rate is not None else 0.0
        except Exception:
            return 0.0
    return 0.0


def fmt_inr(v):
    """Full precision INR — used in tables, exports, HTML reports."""
    return f"₹{abs(v):,.2f}"


def fmt_inr_short(v):
    """
    Compact INR formatter for dashboard KPI tiles so values never truncate.
    ≥ 1 Cr  → ₹X.XX Cr
    ≥ 1 L   → ₹X.XX L
    < 1 L   → ₹X,XXX
    Negative values prefix with −.
    """
    sign = "−" if v < 0 else ""
    av = abs(v)
    if av >= 1_00_00_000:          # 1 crore and above
        return f"{sign}₹{av / 1_00_00_000:.2f} Cr"
    if av >= 1_00_000:             # 1 lakh and above
        return f"{sign}₹{av / 1_00_000:.2f} L"
    return f"{sign}₹{av:,.0f}"    # below 1 lakh — plain number


def gain_arrow(v):
    return "▲" if v >= 0 else "▼"


def gain_color(v):
    return C_GAIN if v >= 0 else C_LOSS


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


# ─────────────────────────────────────────────
# PDF PARSING
# ─────────────────────────────────────────────

def parse_pdf(pdf_bytes, password):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_bytes)
        path = f.name
    try:
        raw = casparser.read_cas_pdf(path, password=password)
        return to_dict(raw), None
    except Exception as exc:
        err = str(exc).lower()
        if any(k in err for k in ["password", "decrypt", "incorrect"]):
            return None, "wrong_password"
        return None, str(exc)
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


# ─────────────────────────────────────────────
# LIVE NAV FETCH
# ─────────────────────────────────────────────

def fetch_live_navs(holdings):
    live_dict = {}
    latest_date = None
    for holding in holdings:
        amfi = holding.get("amfi")
        if not amfi:
            continue
        try:
            response = requests.get(f"https://api.mfapi.in/mf/{amfi}", timeout=5)
            if response.status_code != 200:
                continue
            data = response.json().get("data", [])
            if not data:
                continue
            nav = float(data[0]["nav"])
            date_str = data[0]["date"]
            live_dict[holding["scheme"]] = {
                "nav": nav,
                "date": date_str,
                "live_value": nav * holding["units"],
            }
            latest_date = date_str
        except Exception:
            continue
    return live_dict, latest_date


# ─────────────────────────────────────────────
# EXPORT: EXCEL
# ─────────────────────────────────────────────

def generate_excel(d, live_data=None):
    out = io.BytesIO()
    live_data = live_data or {}
    display_wealth = d["total_value"]
    has_live = False

    if live_data:
        new_wealth = 0
        for h in d["holdings"]:
            sname = h["scheme"]
            if sname in live_data:
                new_wealth += live_data[sname]["live_value"]
                has_live = True
            else:
                new_wealth += h["value"]
        display_wealth = new_wealth if has_live else d["total_value"]

    display_pnl = display_wealth - d["total_invested"]

    try:
        with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
            pd.DataFrame([
                {"Field": "Name", "Value": d["investor_name"]},
                {"Field": "Email", "Value": d["investor_email"]},
                {"Field": "PAN", "Value": d.get("investor_pan", "—")},
                {"Field": "Statement Date", "Value": d["statement_date"]},
                {"Field": "Total Value", "Value": display_wealth},
                {"Field": "Total Invested", "Value": d["total_invested"]},
                {"Field": "Unrealized P&L", "Value": display_pnl},
                {"Field": "Realized P&L", "Value": d.get("realized_pnl", 0.0)},
            ]).to_excel(writer, sheet_name="Summary", index=False)

            if d["holdings"]:
                rows = []
                for s in d["holdings"]:
                    sname = s["scheme"]
                    cas_val = s["value"]
                    l_val = cas_val
                    nav = s.get("cas_nav", 0.0)
                    dt = s.get("cas_date", "—")
                    if live_data and sname in live_data:
                        l_val = live_data[sname]["live_value"]
                        nav = live_data[sname]["nav"]
                        dt = live_data[sname]["date"]
                        sname = sname + " (LIVE)"
                    rows.append({
                        "Scheme": clean_name(sname),
                        "Category": s["category"],
                        "SIP Invested": s.get("sip_invested", 0.0),
                        "Lump Sum Invested": s.get("lumpsum_invested", 0.0),
                        "Total Invested": s["invested"],
                        "CAS Value": cas_val,
                        "Live Value": l_val if live_data else "—",
                        "NAV": nav,
                        "NAV Date": dt,
                        "Current P&L": l_val - s["invested"],
                        "XIRR %": s["xirr"],
                    })
                pd.DataFrame(rows).to_excel(writer, sheet_name="Holdings", index=False)

            if d.get("redeemed"):
                pd.DataFrame(d["redeemed"]).to_excel(writer, sheet_name="Redeemed", index=False)

            all_sips = d.get("live_sips", []) + d.get("dead_sips", [])
            if all_sips:
                pd.DataFrame([
                    {
                        "Scheme": clean_name(s["scheme"]),
                        "Amount": s["amount"],
                        "Day": s["day_label"],
                        "Last Date": s["last_date"],
                        "Status": s["status"],
                    }
                    for s in all_sips
                ]).to_excel(writer, sheet_name="SIPs", index=False)

        return out.getvalue()
    except Exception:
        return None


# ─────────────────────────────────────────────
# EXPORT: HTML REPORT
# ─────────────────────────────────────────────

def generate_html(d, live_data=None):
    live_data = live_data or {}
    display_wealth = d["total_value"]

    if live_data:
        new_wealth = 0
        for h in d["holdings"]:
            sname = h["scheme"]
            if sname in live_data:
                new_wealth += live_data[sname]["live_value"]
            else:
                new_wealth += h["value"]
        display_wealth = new_wealth

    display_pnl = display_wealth - d["total_invested"]
    realized = d.get("realized_pnl", 0.0)

    rows_holdings = ""
    for s in d.get("holdings", []):
        sname = s["scheme"]
        cas_val = s["value"]
        l_val = cas_val
        nav = s.get("cas_nav", 0.0)
        dt = s.get("cas_date", "—")
        badge = ""
        if live_data and sname in live_data:
            l_val = live_data[sname]["live_value"]
            nav = live_data[sname]["nav"]
            dt = live_data[sname]["date"]
            badge = " 🟢"
        curr_pnl = l_val - s["invested"]
        rows_holdings += f"""<tr>
          <td>{clean_name(sname)}{badge}</td>
          <td>{fmt_inr(s['invested'])}</td>
          <td>{fmt_inr(cas_val)}</td>
          <td style=\"font-weight:700;\">{fmt_inr(l_val) if badge else '—'}</td>
          <td>₹{nav:,.4f}</td>
          <td>{dt}</td>
          <td style=\"color:{'#48bb78' if curr_pnl>=0 else '#fc8181'};font-weight:600;\">{fmt_inr(curr_pnl)}</td>
          <td style=\"color:{'#48bb78' if s['xirr']>=0 else '#fc8181'};font-family:monospace;\">{s['xirr']:.2f}%</td>
        </tr>"""

    rows_redeemed = ""
    for r in d.get("redeemed", []):
        p = r["profit"]
        rows_redeemed += f"""<tr>
          <td>{clean_name(r['scheme'])}</td><td>{fmt_inr(r['invested'])}</td>
          <td>{fmt_inr(r['redeemed'])}</td>
          <td style=\"color:{'#48bb78' if p>=0 else '#fc8181'};font-weight:600;\">{fmt_inr(p)}</td>
        </tr>"""
    if not rows_redeemed:
        rows_redeemed = "<tr><td colspan='4' style='text-align:center;color:#718096;padding:20px;'>No fully redeemed schemes.</td></tr>"

    rows_sip = ""
    for s in d.get("live_sips", []) + d.get("dead_sips", []):
        color = "#48bb78" if s["status"] == "Live" else "#fc8181"
        rows_sip += f"""<tr>
          <td>{clean_name(s['scheme'])}</td>
          <td style=\"font-family:'IBM Plex Mono',monospace;\">{fmt_inr(s['amount'])}</td>
          <td>{s['day_label']}</td><td>{s['last_date']}</td>
          <td style=\"color:{color};font-weight:700;\">{s['status'].upper()}</td>
        </tr>"""

    live_header = " — 🟢 LIVE DATA ACTIVE" if live_data else ""

    return f"""<!DOCTYPE html>
<html><head><meta charset=\"utf-8\">
<title>CAS 360 View — {d['investor_name']}</title>
<style>
  @media print {{body{{background:#07090f!important;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}}}
  body{{background:#07090f;color:#e2e8f0;font-family:'Helvetica Neue',Helvetica,sans-serif;padding:32px;line-height:1.5;}}
  h1{{font-size:24px;font-weight:800;color:#fff;margin:0 0 4px;letter-spacing:-0.5px;}}
  .sub{{font-size:12px;color:#63b3ed;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:20px;}}
  .card{{background:#0c0f1a;border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:22px;margin-bottom:20px;}}
  .grid-4{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:16px 0;}}
  .kpi{{background:#111627;border:1px solid rgba(255,255,255,0.05);border-radius:8px;padding:14px;}}
  .kpi-label{{font-size:9px;color:#718096;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:4px;}}
  .kpi-value{{font-size:18px;font-weight:700;font-family:monospace;color:#fff;}}
  table{{width:100%;border-collapse:collapse;border-radius:10px;overflow:hidden;border:1px solid rgba(255,255,255,0.07);margin:10px 0;}}
  th{{background:#111627;color:#9f7aea;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;padding:12px 14px;text-align:left;}}
  td{{background:#0c0f1a;color:#e2e8f0;font-size:12px;padding:12px 14px;border-bottom:1px solid rgba(255,255,255,0.04);}}
  tr:nth-child(even) td{{background:#111627;}}
  .sec{{font-size:10px;font-weight:700;color:#2d3748;text-transform:uppercase;letter-spacing:2px;margin:30px 0 12px;border-left:3px solid #63b3ed;padding-left:10px;}}
  .footer{{text-align:center;font-size:10px;color:#2d3748;border-top:1px solid rgba(255,255,255,0.05);padding-top:14px;margin-top:40px;}}
</style></head><body>
<div class=\"card\">
  <h1>CAS 360 VIEW</h1>
  <div class=\"sub\">Portfolio Intelligence Dashboard{live_header}</div>
  <table style=\"border:none;background:transparent;\"><tbody>
    <tr><td style=\"background:transparent;color:#718096;font-size:11px;width:120px;\">Name</td><td style=\"background:transparent;color:#f7fafc;font-weight:600;\">{d['investor_name'].title()}</td>
        <td style=\"background:transparent;color:#718096;font-size:11px;width:120px;\">Email</td><td style=\"background:transparent;color:#f7fafc;\">{d['investor_email'] or '—'}</td></tr>
    <tr><td style=\"background:transparent;color:#718096;font-size:11px;\">PAN</td><td style=\"background:transparent;color:#9f7aea;font-family:monospace;font-weight:700;\">{d.get('investor_pan','—')}</td>
        <td style=\"background:transparent;color:#718096;font-size:11px;\">Statement Date</td><td style=\"background:transparent;color:#f7fafc;\">{d['statement_date']}</td></tr>
  </tbody></table>
  <div class=\"grid-4\">
    <div class=\"kpi\"><div class=\"kpi-label\">Total Wealth</div><div class=\"kpi-value\">{fmt_inr(display_wealth)}</div></div>
    <div class=\"kpi\"><div class=\"kpi-label\">Invested</div><div class=\"kpi-value\" style=\"color:#63b3ed;\">{fmt_inr(d['total_invested'])}</div></div>
    <div class=\"kpi\"><div class=\"kpi-label\">Unrealized P&L</div><div class=\"kpi-value\" style=\"color:{'#48bb78' if display_pnl>=0 else '#fc8181'};\">{fmt_inr(display_pnl)}</div></div>
    <div class=\"kpi\"><div class=\"kpi-label\">Realized P&L</div><div class=\"kpi-value\" style=\"color:{'#48bb78' if realized>=0 else '#fc8181'};\">{fmt_inr(realized)}</div></div>
  </div>
</div>
<div class=\"sec\">Active Holdings</div>
<table><thead><tr><th>Scheme</th><th>Invested</th><th>CAS Value</th><th>Live Value</th><th>NAV</th><th>NAV Date</th><th>P&L</th><th>XIRR %</th></tr></thead>
<tbody>{rows_holdings}</tbody></table>
<div class=\"sec\">SIP Registry</div>
<table><thead><tr><th>Scheme</th><th>Amount</th><th>Day</th><th>Last Date</th><th>Status</th></tr></thead>
<tbody>{rows_sip}</tbody></table>
<div class=\"sec\">Fully Redeemed Positions</div>
<table><thead><tr><th>Scheme</th><th>Invested</th><th>Redeemed</th><th>Realized P&L</th></tr></thead>
<tbody>{rows_redeemed}</tbody></table>
<div class=\"footer\">Generated by CAS 360 View · Confidential</div>
</body></html>"""


# ─────────────────────────────────────────────
# DATA PROCESSING
# ─────────────────────────────────────────────

def process(raw):
    raw = to_dict(raw)
    info = raw.get("investor_info", {})

    result = {
        "investor_name": info.get("name", "Investor"),
        "investor_email": info.get("email", ""),
        "investor_pan": info.get("pan", "—"),
        "statement_date": str(date.today()),
        "total_value": 0.0,
        "total_invested": 0.0,
        "total_sip_invested": 0.0,
        "total_lumpsum_invested": 0.0,
        "unrealized_pnl": 0.0,
        "realized_pnl": 0.0,
        "alloc_values": {},
        "alloc_pct": {},
        "holdings": [],
        "live_sips": [],
        "dead_sips": [],
        "redeemed": [],
        "recent_redemptions": [],
        "tx_map": {},
        "agg_map": {},
        "duplicate_alerts": [],
        "special_transactions": [],
    }

    total_val = 0.0
    total_inv = 0.0
    type_map = {}

    for folio in raw.get("folios", []):
        for scheme in folio.get("schemes", []):
            valuation = scheme.get("valuation", {})
            scheme_name = scheme.get("scheme", "Unknown")
            valuation_date = str(valuation.get("date", result["statement_date"]))
            result["statement_date"] = valuation_date

            cost = float(valuation.get("cost", 0.0))
            value = float(valuation.get("value", 0.0))
            units = float(scheme.get("close", 0.0))
            scheme_type = str(scheme.get("type", "EQUITY")).upper()
            category = "Equity Funds" if scheme_type == "EQUITY" else "Debt Funds"

            transactions = scheme.get("transactions", [])
            result["tx_map"][scheme_name] = transactions

            invested = 0.0
            sip_invested = 0.0
            lumpsum_invested = 0.0
            redeemed_amount = 0.0

            SIP_TX_KEYS = ["SIP", "SYSTEMATIC", "RECURRING", "AUTO DEBIT", "E-DEBIT", "ECS", "MANDATE"]

            for tx in transactions:
                raw_amount = float(tx.get("amount") or 0.0)
                raw_units  = float(tx.get("units")  or 0.0)
                amount     = abs(raw_amount)
                txn_type   = str(tx.get("type",        "")).upper()
                description= str(tx.get("description", "")).upper()
                tx_date    = to_date(tx.get("date"))
                combined   = txn_type + " " + description

                # ── CLASSIFY ──────────────────────────────────────────────
                # GOLDEN RULE (user-defined):
                #
                #   OUTFLOW types  (Redemption, STP Out, Switch Out, SWP):
                #       negative units  = real transaction happened ✓
                #       positive units  = it was reversed / rejected ✗
                #
                #   INFLOW types   (SIP, Lumpsum Purchase, STP In, Switch In):
                #       positive units  = real transaction happened ✓
                #       negative units  = it was reversed / rejected ✗
                #
                #   Explicit reversal keywords ALSO force reversal regardless.

                is_reversal_kw = any(k in combined for k in [
                    "REVERSAL", "REVERSED", "REJECTION", "REJECTED",
                    "BOUNCE", "BOUNCED", "INSUFFICIENT", "FAILED",
                    "RETURN", "CANCELLED", "CANCEL",
                ])

                # ── STEP 1: identify BASE transaction type from description ──
                is_stp_out    = "STP" in combined and ("OUT" in combined or "TRANSFER OUT" in combined)
                is_stp_in     = "STP" in combined and ("IN"  in combined or "TRANSFER IN"  in combined) and not is_stp_out
                is_switch_out = "SWITCH" in combined and "OUT" in combined
                is_switch_in  = "SWITCH" in combined and "IN"  in combined and not is_switch_out
                is_swp        = "SWP" in combined or "SYSTEMATIC WITHDRAWAL" in combined
                is_sip_kw     = any(k in combined for k in SIP_TX_KEYS)
                is_redemption = any(k in combined for k in ["REDEMPTION", "PAYOUT", "WITHDRAWAL"]) and not is_swp
                is_purchase   = any(k in combined for k in ["PURCHASE", "LUMPSUM", "NFO", "NEW FUND", "REINVEST", "DIVIDEND REINVEST"])

                # Priority order matters — most specific first
                if is_stp_out:
                    base = "STP Out"
                elif is_stp_in:
                    base = "STP In"
                elif is_switch_out:
                    base = "Switch Out"
                elif is_switch_in:
                    base = "Switch In"
                elif is_swp:
                    base = "SWP"
                elif is_redemption:
                    base = "Redemption"
                elif is_sip_kw:
                    base = "SIP"          # SIP wins over purchase if SIP keyword present
                elif is_purchase:
                    base = "Lumpsum Purchase"
                else:
                    base = "Other"

                # ── STEP 2: apply golden rule to decide if this is a reversal ─
                OUTFLOW_BASES = {"Redemption", "STP Out", "Switch Out", "SWP"}
                INFLOW_BASES  = {"SIP", "Lumpsum Purchase", "STP In", "Switch In"}

                if base in OUTFLOW_BASES:
                    # Outflow: units normally go NEGATIVE when it actually happens.
                    # So POSITIVE units on an outflow = reversed / rejected.
                    is_reversal = (raw_units > 0) or is_reversal_kw
                elif base in INFLOW_BASES:
                    # Inflow: units normally go POSITIVE when it actually happens.
                    # So NEGATIVE units on an inflow = reversed / rejected.
                    is_reversal = (raw_units < 0) or is_reversal_kw
                else:
                    # "Other" — rely only on explicit keywords
                    is_reversal = is_reversal_kw

                # ── STEP 3: assign final tx_class ─────────────────────────────
                if is_reversal and base != "Other":
                    tx_class = base + " Reversal"
                elif is_reversal and base == "Other":
                    tx_class = "Reversal / Rejection"
                else:
                    tx_class = base

                # ── INFLOW OUTFLOW ACCOUNTING ──────────────────────────────
                # Reversals of buy-type transactions → subtract from invested
                # Reversals of sell-type transactions → subtract from redeemed
                BUY_CLASSES  = {"SIP", "Lumpsum Purchase", "STP In",  "Switch In"}
                SELL_CLASSES = {"Redemption", "SWP", "STP Out", "Switch Out"}
                REV_BUY_CLASSES  = {"SIP Reversal", "STP In Reversal",  "Switch In Reversal"}
                REV_SELL_CLASSES = {"Redemption Reversal", "SWP Reversal", "STP Out Reversal", "Switch Out Reversal"}

                if tx_class in BUY_CLASSES:
                    invested += amount
                    if tx_class == "SIP":
                        sip_invested += amount
                    else:
                        lumpsum_invested += amount
                elif tx_class in REV_BUY_CLASSES:
                    # Reverse a prior inflow
                    invested     = max(0.0, invested     - amount)
                    if tx_class == "SIP Reversal":
                        sip_invested = max(0.0, sip_invested - amount)
                    else:
                        lumpsum_invested = max(0.0, lumpsum_invested - amount)
                elif tx_class in SELL_CLASSES:
                    redeemed_amount += amount
                    if tx_class == "Redemption":
                        try:
                            result["recent_redemptions"].append({
                                "date_obj": tx_date,
                                "Date": tx_date.strftime("%d %b %Y"),
                                "Scheme": clean_name(scheme_name),
                                "Payout": amount,
                            })
                        except Exception:
                            pass
                elif tx_class in REV_SELL_CLASSES:
                    # Reverse a prior outflow
                    redeemed_amount = max(0.0, redeemed_amount - amount)

                # ── STORE ENRICHED TX FOR SPECIAL ACTIVITY LOG ─────────────
                result["special_transactions"].append({
                    "date_obj": tx_date,
                    "Date":     tx_date.strftime("%d %b %Y"),
                    "Scheme":   clean_name(scheme_name),
                    "Type":     tx_class,
                    "Amount":   amount,
                    "Raw Amount": raw_amount,
                    "Units":    raw_units,
                    "Description": tx.get("description", ""),
                    "Category": category,
                })

            if units < 0.001 and invested > 0 and redeemed_amount > 0:
                profit = redeemed_amount - invested
                result["redeemed"].append({
                    "scheme": scheme_name,
                    "invested": invested,
                    "sip_invested": sip_invested,
                    "lumpsum_invested": lumpsum_invested,
                    "redeemed": redeemed_amount,
                    "profit": profit,
                })
                result["realized_pnl"] += profit
                result["agg_map"][scheme_name] = {"cost": cost, "units": units, "value": value}
                continue

            total_val += value
            total_inv += cost
            type_map[category] = type_map.get(category, 0.0) + value
            result["agg_map"][scheme_name] = {"cost": cost, "units": units, "value": value}

            pnl = value - cost
            xirr_value = calc_xirr(transactions, value, valuation_date)
            cas_nav = float(valuation.get("nav", 0.0))
            if cas_nav == 0.0 and units > 0:
                cas_nav = value / units

            result["holdings"].append({
                "scheme": scheme_name,
                "amfi": scheme.get("amfi"),
                "units": units,
                "invested": cost,
                "sip_invested": sip_invested,
                "lumpsum_invested": lumpsum_invested,
                "value": value,
                "pnl": pnl,
                "xirr": xirr_value,
                "category": category,
                "cas_nav": cas_nav,
                "cas_date": valuation_date,
                "special_tx": [t for t in result["special_transactions"] if t["Scheme"] == clean_name(scheme_name)],
            })

            sip_keywords = ["SIP", "SYSTEMATIC", "RECURRING", "AUTO", "DEBIT", "E-DEBIT", "ECS", "MANDATE"]
            sip_transactions = [
                t for t in transactions
                if any(k in str(t.get("description", "")).upper() or k in str(t.get("type", "")).upper() for k in sip_keywords)
            ]

            if sip_transactions:
                days = [to_date(t.get("date")).day for t in sip_transactions]
                dom = Counter(days).most_common(1)[0][0] if days else 1

                sorted_sip = sorted(sip_transactions, key=lambda x: to_date(x.get("date")))
                latest_tx = sorted_sip[-1]
                amount_sip = float(latest_tx.get("amount", 0.0))

                if amount_sip > 0:
                    last_date = to_date(latest_tx.get("date"))
                    statement_date_obj = to_date(valuation_date)
                    cutoff = statement_date_obj - datetime.timedelta(days=90)
                    next_due = next_due_date(dom)
                    next_due_label = next_due.strftime("%d %b %Y")
                    next_due_iso = next_due.isoformat()

                    sip_record = {
                        "scheme": scheme_name,
                        "amount": amount_sip,
                        "day_label": ordinal(dom),
                        "last_date": last_date.strftime("%d %b %Y"),
                        "next_date": next_due_label,
                        "next_iso": next_due_iso,
                        "status": "Live" if last_date >= cutoff and units > 0.01 else "Inactive",
                    }

                    if sip_record["status"] == "Live":
                        result["live_sips"].append(sip_record)
                    else:
                        result["dead_sips"].append(sip_record)

    result["total_value"] = total_val
    result["total_invested"] = total_inv
    result["total_sip_invested"] = sum(h["sip_invested"] for h in result["holdings"])
    result["total_lumpsum_invested"] = sum(h["lumpsum_invested"] for h in result["holdings"])
    result["unrealized_pnl"] = total_val - total_inv
    result["alloc_values"] = type_map
    result["alloc_pct"] = {k: (v / total_val) * 100 for k, v in type_map.items()} if total_val else {}

    result["recent_redemptions"] = sorted(
        result["recent_redemptions"], key=lambda x: x["date_obj"], reverse=True
    )
    result["special_transactions"] = sorted(
        result["special_transactions"], key=lambda x: x["date_obj"], reverse=True
    )

    return result


# ─────────────────────────────────────────────
# SPECIAL TRANSACTION HELPERS
# ─────────────────────────────────────────────

TX_META = {
    "SIP":                   {"icon": "🔄", "color": "#63b3ed",  "group": "inflow"},
    "Lumpsum Purchase":      {"icon": "💰", "color": "#9f7aea",  "group": "inflow"},
    "STP In":                {"icon": "➡️", "color": "#68d391",  "group": "inflow"},
    "Switch In":             {"icon": "🔀", "color": "#4fd1c5",  "group": "inflow"},
    "STP Out":               {"icon": "⬅️", "color": "#f6ad55",  "group": "outflow"},
    "Switch Out":            {"icon": "🔁", "color": "#ed8936",  "group": "outflow"},
    "SWP":                   {"icon": "💸", "color": "#fc8181",  "group": "outflow"},
    "Redemption":            {"icon": "🏦", "color": "#fc8181",  "group": "outflow"},
    "SIP Reversal":          {"icon": "↩️", "color": "#fbb6ce",  "group": "reversal"},
    "STP In Reversal":       {"icon": "↩️", "color": "#fbb6ce",  "group": "reversal"},
    "STP Out Reversal":      {"icon": "↩️", "color": "#fbb6ce",  "group": "reversal"},
    "Switch In Reversal":    {"icon": "↩️", "color": "#fbb6ce",  "group": "reversal"},
    "Switch Out Reversal":   {"icon": "↩️", "color": "#fbb6ce",  "group": "reversal"},
    "SWP Reversal":          {"icon": "↩️", "color": "#fbb6ce",  "group": "reversal"},
    "Redemption Reversal":   {"icon": "↩️", "color": "#fbb6ce",  "group": "reversal"},
    "Reversal / Rejection":  {"icon": "⛔", "color": "#fc8181",  "group": "reversal"},
    "Other":                 {"icon": "◌",  "color": "#718096",  "group": "other"},
}

SPECIAL_TX_TYPES = [t for t in TX_META if t not in ("SIP", "Lumpsum Purchase", "Other")]


def tx_badge_html(tx_type):
    meta = TX_META.get(tx_type, TX_META["Other"])
    return (
        f'<span style="display:inline-flex;align-items:center;gap:4px;'
        f'background:{meta["color"]}18;border:1px solid {meta["color"]}44;'
        f'color:{meta["color"]};font-family:\'IBM Plex Mono\',monospace;'
        f'font-size:10px;font-weight:600;padding:2px 8px;border-radius:20px;">'
        f'{meta["icon"]} {tx_type}</span>'
    )


def build_special_tx_df(tx_list, types_filter=None):
    """Convert special_transactions list → display DataFrame."""
    rows = []
    for t in tx_list:
        if types_filter and t["Type"] not in types_filter:
            continue
        rows.append({
            "Date":        t["Date"],
            "Scheme":      t["Scheme"],
            "Type":        t["Type"],
            "Amount":      fmt_inr(t["Amount"]),
            "Units":       f'{t["Units"]:+.3f}',
            "Description": t.get("Description", ""),
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["Date", "Scheme", "Type", "Amount", "Units", "Description"]
    )


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

def initialize_session_state():
    defaults = {
        "profiles": {},
        "active": None,
        "show_email": True,
        "pin_ok": False,
        "switch_target": None,
        "live_data": {},
        "live_last_updated": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def active_data():
    active = st.session_state.active
    return st.session_state.profiles.get(active) if active else None


# ─────────────────────────────────────────────
# UPLOAD SCREEN
# ─────────────────────────────────────────────

def show_upload():
    st.markdown(
        """
        <div style="display:flex;justify-content:center;padding-top:48px;">
          <div style="max-width:520px;width:100%;text-align:center;">
            <div style="width:64px;height:64px;background:rgba(99,179,237,0.08);border:1px solid rgba(99,179,237,0.2);
                        border-radius:18px;display:flex;align-items:center;justify-content:center;
    margin:0 auto 22px;font-size:28px;">📂</div>
            <div style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;color:#f7fafc;
    letter-spacing:-0.5px;margin-bottom:8px;">Upload your CAS PDF</div>
            <div style="font-size:14px;color:#718096;margin-bottom:32px;line-height:1.7;">
              Consolidated Account Statement from CAMS or KFintech.<br>
              Your data never leaves your device.
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col = st.columns([1, 2, 1])[1]
    with col:
        uploaded = st.file_uploader("CAS PDF", type=["pdf"], label_visibility="collapsed")
        password = st.text_input("PDF Password", type="password", placeholder="PAN / Date of Birth")

        if uploaded and password:
            if st.button("Analyse Portfolio →", use_container_width=True, type="primary"):
                with st.spinner("Parsing…"):
                    data, error = parse_pdf(uploaded.read(), password)
                if error == "wrong_password":
                    st.error("Wrong password. Try your PAN number or date of birth (DDMMYYYY).")
                elif error:
                    st.error(f"Parse error: {error}")
                else:
                    portfolio = process(data)
                    investor_name = portfolio["investor_name"].title()
                    st.session_state.profiles[investor_name] = portfolio
                    st.session_state.active = investor_name
                    st.session_state.pin_ok = True
                    st.success(f"Portfolio loaded — {investor_name}")
                    st.rerun()


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

def build_sidebar(data):
    with st.sidebar:
        st.markdown(
            """
            <div style="padding:6px 0 20px;">
              <div style="font-family:'Syne',sans-serif;font-size:21px;font-weight:800;
    color:#f7fafc;letter-spacing:-0.5px;">CAS 360 <span style="color:#63b3ed;">View</span></div>
              <div style="font-size:10px;color:#2d3748;text-transform:uppercase;letter-spacing:2px;
    font-weight:600;margin-top:2px;">Portfolio Intelligence</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if data:
            menu = st.radio(
                "nav",
                ["Dashboard", "My Portfolio", "SIP Center", "Transactions", "Alerts"],
                label_visibility="collapsed",
            )
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            email_display = data["investor_email"] if st.session_state.show_email else "••••••••••"
            st.markdown(
                f"""
                <div style="background:rgba(99,179,237,0.04);border:1px solid rgba(99,179,237,0.12);
                            border-radius:10px;padding:12px 14px;margin-bottom:10px;">
                  <div style="font-size:13px;font-weight:600;color:#f7fafc;margin-bottom:2px;">
                    {data['investor_name'].title()}</div>
                """,
                unsafe_allow_html=True,
            )

            ec1, ec2 = st.columns([5, 1])
            with ec1:
                st.markdown(f"<div style='font-size:11px;color:#4a5568;'>{email_display}</div>", unsafe_allow_html=True)
            with ec2:
                if st.button("👁" if st.session_state.show_email else "🙈", key="eye"):
                    st.session_state.show_email = not st.session_state.show_email
                    st.rerun()

            try:
                statement_date = to_date(data["statement_date"]).strftime("%d %b %Y")
            except Exception:
                statement_date = "—"
            st.markdown(
                f"""
                <div style="font-size:10px;color:#2d3748;margin-top:6px;">STATEMENT · {statement_date}</div>
                </div>""",
                unsafe_allow_html=True,
            )

            if len(st.session_state.profiles) > 1:
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                keys = list(st.session_state.profiles.keys())
                index = keys.index(st.session_state.active) if st.session_state.active in keys else 0
                selected = st.selectbox("Switch Profile", keys, index=index, label_visibility="collapsed")
                if selected != st.session_state.active:
                    st.session_state.switch_target = selected
                    st.session_state.pin_ok = False
                if not st.session_state.pin_ok and st.session_state.switch_target:
                    pin = st.text_input("PIN", type="password", max_chars=4, placeholder="••••")
                    if pin == "2002":
                        st.session_state.active = st.session_state.switch_target
                        st.session_state.switch_target = None
                        st.session_state.pin_ok = True
                        st.rerun()
                    elif len(pin) == 4:
                        st.error("Wrong PIN")

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("＋ Add Another CAS", use_container_width=True):
                st.session_state.active = None
                st.session_state.pin_ok = False
                st.rerun()

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("🚪 Logout & Clear Data", use_container_width=True):
                st.session_state.clear()
                st.rerun()

            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown(
                "<div style='font-size:10px;color:#2d3748;text-transform:uppercase;letter-spacing:1.5px;font-weight:600;margin-bottom:8px;'>Export</div>",
                unsafe_allow_html=True,
            )

            live_data = st.session_state.get("live_data", {})
            xls = generate_excel(data, live_data)
            if xls:
                st.download_button(
                    "📊 Excel",
                    data=xls,
                    file_name=f"CAS360_{data['investor_name']}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

            st.download_button(
                "📄 HTML Report (Print as PDF)",
                data=generate_html(data, live_data),
                file_name=f"CAS360_{data['investor_name']}.html",
                mime="text/html",
                use_container_width=True,
            )
        else:
            menu = "upload"
            if st.session_state.profiles:
                keys = list(st.session_state.profiles.keys())
                selected = st.selectbox("Return to", ["— select —"] + keys, label_visibility="collapsed")
                if selected != "— select —":
                    st.session_state.active = selected
                    st.session_state.pin_ok = True
                    st.rerun()
    return menu


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────

def _dash_section(title):
    st.markdown(
        f'<div class="section-sep" style="margin:28px 0 14px;">{title}</div>',
        unsafe_allow_html=True,
    )


def _kpi_card(label, value, sub="", color="#f7fafc", bg_color="rgba(99,179,237,0.06)", border_color="rgba(99,179,237,0.15)"):
    return f"""
    <div style="background:{bg_color};border:1px solid {border_color};border-radius:12px;
                padding:16px 18px;height:100%;">
      <div style="font-size:10px;color:#718096;text-transform:uppercase;letter-spacing:1.2px;
                  margin-bottom:6px;font-weight:600;">{label}</div>
      <div style="font-family:'IBM Plex Mono',monospace;font-size:18px;font-weight:700;color:{color};">
        {value}</div>
      {f'<div style="font-size:11px;color:#4a5568;margin-top:3px;">{sub}</div>' if sub else ''}
    </div>"""


def render_dashboard(data):
    from collections import Counter as _Counter

    first_name = data["investor_name"].split()[0].title()
    try:
        statement_date = to_date(data["statement_date"]).strftime("%d %b %Y")
    except Exception:
        statement_date = "—"

    # ── Header ────────────────────────────────────────────────────────────────
    hc1, hc2 = st.columns([3, 1])
    with hc1:
        st.markdown(
            f"""
            <div style="margin-bottom:6px;">
              <div class="page-title">Welcome back, {first_name} 👋</div>
              <div class="page-sub">CAS Statement · {statement_date} &nbsp;·&nbsp; Base figures from your uploaded PDF</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with hc2:
        if st.button("🔄 Refresh Latest NAV", use_container_width=True):
            with st.spinner("Fetching latest NAVs from AMFI..."):
                live_data, live_date = fetch_live_navs(data["holdings"])
                st.session_state.live_data = live_data
                st.session_state.live_last_updated = live_date
            st.rerun()

    # ── Live NAV banner ───────────────────────────────────────────────────────
    display_wealth = data["total_value"]
    if st.session_state.live_data:
        st.markdown(
            f"""<div style="background:rgba(72,187,120,0.08);border:1px solid rgba(72,187,120,0.2);
                border-radius:8px;padding:7px 14px;margin-bottom:12px;display:inline-flex;
                align-items:center;gap:8px;color:#48bb78;font-size:11px;font-weight:700;">
                <span style="width:7px;height:7px;background:#48bb78;border-radius:50%;
                box-shadow:0 0 6px #48bb78;display:inline-block;"></span>
                LIVE DATA ACTIVE · NAVs as of {st.session_state.live_last_updated}</div>""",
            unsafe_allow_html=True,
        )
        new_wealth = sum(
            st.session_state.live_data[h["scheme"]]["live_value"]
            if h["scheme"] in st.session_state.live_data else h["value"]
            for h in data["holdings"]
        )
        display_wealth = new_wealth

    # ── MODE FILTER (the main selector) ──────────────────────────────────────
    VIEW_MODES = ["📊 Overall", "🔄 SIP", "💰 Lumpsum", "↔️ STP / Switch", "💸 SWP / Redemption"]
    view_mode = st.segmented_control(
        "view_mode", VIEW_MODES,
        default="📊 Overall",
        label_visibility="collapsed",
        key="dash_view_mode",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # ── OVERALL VIEW ─────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    if view_mode == "📊 Overall":

        display_pnl = display_wealth - data["total_invested"]
        pnl_pct     = (display_pnl / data["total_invested"] * 100) if data["total_invested"] else 0.0
        sip_monthly = sum(s["amount"] for s in data["live_sips"])

        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("Total Wealth",    fmt_inr(display_wealth))
        with m2: st.metric("Invested",        fmt_inr(data["total_invested"]))
        with m3: st.metric("Unrealized P&L",  fmt_inr(display_pnl),
                            delta=f"{gain_arrow(display_pnl)} {abs(pnl_pct):.2f}% all-time")
        with m4: st.metric("Monthly SIP",     fmt_inr(sip_monthly),
                            delta=f"{len(data['live_sips'])} active")

        # SIP vs Lump bar
        total_sip  = data.get("total_sip_invested", 0.0)
        total_lump = data.get("total_lumpsum_invested", 0.0)
        total_for_pct = (total_sip + total_lump) or 1.0
        sip_pct  = total_sip  / total_for_pct * 100
        lump_pct = total_lump / total_for_pct * 100

        st.markdown(
            f"""<div style="background:var(--bg2);border:1px solid var(--border);border-radius:14px;
                    padding:18px 22px;margin:14px 0 10px;">
              <div style="font-family:'Syne',sans-serif;font-size:11px;font-weight:700;color:var(--accent);
                          text-transform:uppercase;letter-spacing:2px;margin-bottom:14px;">
                Investment Mode Split — SIP vs Lump Sum</div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:14px;">
                <div style="background:#111627;border:1px solid rgba(99,179,237,0.15);border-radius:10px;padding:14px 18px;">
                  <div style="font-size:10px;color:#718096;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:6px;">🔄 SIP Invested</div>
                  <div style="font-family:'IBM Plex Mono',monospace;font-size:20px;font-weight:700;color:#63b3ed;">{fmt_inr(total_sip)}</div>
                  <div style="font-size:11px;color:#4a5568;margin-top:3px;">{sip_pct:.1f}% of total invested</div>
                </div>
                <div style="background:#111627;border:1px solid rgba(159,122,234,0.15);border-radius:10px;padding:14px 18px;">
                  <div style="font-size:10px;color:#718096;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:6px;">💰 Lump Sum Invested</div>
                  <div style="font-family:'IBM Plex Mono',monospace;font-size:20px;font-weight:700;color:#9f7aea;">{fmt_inr(total_lump)}</div>
                  <div style="font-size:11px;color:#4a5568;margin-top:3px;">{lump_pct:.1f}% of total invested</div>
                </div>
              </div>
              <div style="background:#0c0f1a;border-radius:8px;height:10px;overflow:hidden;position:relative;">
                <div style="position:absolute;left:0;top:0;height:100%;width:{sip_pct:.1f}%;
                            background:linear-gradient(90deg,#2b6cb0,#63b3ed);border-radius:8px 0 0 8px;"></div>
                <div style="position:absolute;right:0;top:0;height:100%;width:{lump_pct:.1f}%;
                            background:linear-gradient(90deg,#553c9a,#9f7aea);border-radius:0 8px 8px 0;"></div>
              </div>
              <div style="display:flex;justify-content:space-between;margin-top:6px;">
                <div style="font-size:10px;color:#63b3ed;font-family:'IBM Plex Mono',monospace;">● SIP {sip_pct:.1f}%</div>
                <div style="font-size:10px;color:#9f7aea;font-family:'IBM Plex Mono',monospace;">Lump Sum {lump_pct:.1f}% ●</div>
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

        ch, al = st.columns([3, 2])
        with ch:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Wealth Journey</div>', unsafe_allow_html=True)
            st.markdown(
                f"""<div style="font-family:'IBM Plex Mono',monospace;font-size:26px;font-weight:700;
                    color:#f7fafc;letter-spacing:-1px;margin-bottom:8px;">{fmt_inr(display_wealth)}</div>
                    <span class="{'pill-gain' if display_pnl>=0 else 'pill-loss'}">{gain_arrow(display_pnl)} {fmt_inr(display_pnl)}</span>""",
                unsafe_allow_html=True,
            )
            tf = st.segmented_control("tf_overall", ["1M","6M","1Y","3Y","ALL"], default="1Y", label_visibility="collapsed")
            bv, iv = display_wealth, data["total_invested"]
            slices = {
                "1M":  (["May 5","May 10","May 15","May 20","May 27"], [bv*.97,bv*.985,bv*.975,bv*.99,bv]),
                "6M":  (["Dec","Jan","Feb","Mar","Apr","May"], [iv*.87,iv*.92,iv*.95,iv*.97,bv*.99,bv]),
                "1Y":  (["Jun '25","Sep '25","Dec '25","Mar '26","May '26"], [iv*.91,iv*.95,iv*.97,bv*.99,bv]),
                "3Y":  (["May '23","Nov '23","May '24","Nov '24","May '25","Nov '25","May '26"], [iv*.35,iv*.55,iv*.70,iv*.83,iv*.93,bv*.98,bv]),
                "ALL": (["Jan '24","Jul '24","Jan '25","Jul '25","Jan '26","May '26"], [iv*.20,iv*.48,iv*.68,iv*.83,iv*.93,bv]),
            }
            xs, ys = slices.get(tf, slices["1Y"])
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers",
                line=dict(color=C_ACCENT, width=2.5, shape="spline"),
                fill="tozeroy", fillcolor="rgba(99,179,237,0.06)",
                hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>"))
            fig.update_layout(height=220,
                xaxis=dict(showgrid=False, tickfont=dict(size=11, color="#4a5568")),
                yaxis=dict(showgrid=True, gridcolor=GRID, tickfont=dict(size=11, color="#4a5568")),
                hovermode="x unified", **PLOT_BASE)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

        with al:
            st.markdown('<div class="card" style="height:100%;">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Asset Allocation</div>', unsafe_allow_html=True)
            if data["alloc_pct"]:
                df_pie = pd.DataFrame({"Class": list(data["alloc_pct"].keys()), "Pct": list(data["alloc_pct"].values())})
                fig_pie = px.pie(df_pie, names="Class", values="Pct", hole=0.7,
                    color_discrete_sequence=[C_ACCENT,"#f6ad55",C_GAIN,C_ACCENT2])
                fig_pie.update_traces(textinfo="none", hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>")
                fig_pie.update_layout(height=170, showlegend=False, **PLOT_BASE)
                st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
            colors = {"Equity Funds": C_ACCENT, "Debt Funds": "#f6ad55", "Gold Funds": C_GAIN, "International": C_ACCENT2}
            for ac, pct in data["alloc_pct"].items():
                val = data["alloc_values"].get(ac, 0.0)
                c = colors.get(ac, C_ACCENT2)
                st.markdown(
                    f"""<div class="alloc-row">
                      <div style="display:flex;align-items:center;flex:1;">
                        <span class="alloc-dot" style="background:{c};box-shadow:0 0 5px {c}55;"></span>
                        <span style="font-size:13px;font-weight:500;color:#e2e8f0;">{ac}</span>
                      </div>
                      <div style="text-align:right;min-width:110px;">
                        <div style="font-family:'IBM Plex Mono',monospace;font-size:12px;font-weight:600;color:#f7fafc;">₹{val:,.0f}</div>
                        <div style="font-size:11px;color:#4a5568;">{pct:.1f}%</div>
                      </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        r1, r2 = st.columns(2)
        with r1:
            st.markdown('<div class="card-title">Performance Breakdown</div>', unsafe_allow_html=True)
            profitable = sum(1 for h in data["holdings"] if h["pnl"] >= 0)
            losing = sum(1 for h in data["holdings"] if h["pnl"] < 0)
            fig_perf = go.Figure(go.Pie(
                labels=["Profitable","In Loss"], values=[profitable, losing],
                hole=0.65, marker_colors=[C_GAIN, C_LOSS], textinfo="none"))
            fig_perf.update_layout(height=120, showlegend=True,
                legend=dict(font=dict(size=11,color="#718096"), bgcolor="rgba(0,0,0,0)",
                            orientation="h", x=0.5, xanchor="center", y=-0.2), **PLOT_BASE)
            st.plotly_chart(fig_perf, use_container_width=True, config={"displayModeBar": False})
            _dash_section("Top Gainers")
            top_gainers = sorted([h for h in data["holdings"] if h["pnl"] > 0], key=lambda x: x["pnl"], reverse=True)[:3]
            if top_gainers:
                st.dataframe(pd.DataFrame([
                    {"Scheme": clean_name(h["scheme"]), "P&L": fmt_inr(h["pnl"]), "XIRR": f"{h['xirr']:.1f}%"}
                    for h in top_gainers
                ]), use_container_width=True, hide_index=True)

        with r2:
            st.markdown('<div class="card-title">⏱ SIP Countdown</div>', unsafe_allow_html=True)
            sorted_sips = sorted(data["live_sips"], key=lambda x: x["next_iso"])
            if sorted_sips:
                ticker_html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px;">'
                for idx, sip in enumerate(sorted_sips[:4]):
                    sn = clean_name(sip["scheme"]); ti = sip["next_iso"]; did = f"sip_{idx}"
                    ticker_html += f"""<div style="background:#111627;border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:10px 12px;">
                      <div style="font-size:11px;color:#718096;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-bottom:4px;" title="{sn}">{sn[:26]}…</div>
                      <div id="{did}" style="font-family:'IBM Plex Mono',monospace;font-size:12px;font-weight:700;color:#63b3ed;">—</div></div>
                    <script>(function(){{var t=new Date("{ti}T00:00:00").getTime();function tick(){{var diff=t-Date.now();var el=document.getElementById("{did}");if(!el)return;if(isNaN(t)||diff<=0){{el.textContent="DUE TODAY";return;}}var d=Math.floor(diff/86400000);var h=Math.floor(diff%86400000/3600000);var m=Math.floor(diff%3600000/60000);el.textContent=d+"d "+h+"h "+m+"m";}}setInterval(tick,30000);tick();}})();</script>"""
                ticker_html += "</div>"
                components.html(ticker_html, height=130, scrolling=False)
                st.dataframe(pd.DataFrame([
                    {"Scheme": clean_name(s["scheme"]), "Amount": fmt_inr(s["amount"]), "Day": s["day_label"], "Next": s["next_date"]}
                    for s in sorted_sips[:4]
                ]), use_container_width=True, hide_index=True)
            else:
                st.info("No live SIPs detected.")

        r3, r4 = st.columns(2)
        with r3:
            st.markdown('<div class="card-title">Capital Concentration</div>', unsafe_allow_html=True)
            top5 = sorted(data["holdings"], key=lambda x: x["value"], reverse=True)[:5]
            if top5:
                df_c = pd.DataFrame([{"Scheme": clean_name(h["scheme"]), "Value": h["value"],
                    "Pct": h["value"]/(display_wealth or 1)*100} for h in top5])
                fig_c = px.bar(df_c, x="Value", y="Scheme", orientation="h", color="Pct",
                    color_continuous_scale=["#1a365d", C_ACCENT, "#bee3f8"])
                fig_c.update_layout(height=180, xaxis=dict(visible=False),
                    yaxis=dict(tickfont=dict(size=10,color="#718096"),title=""),
                    coloraxis_showscale=False, **PLOT_BASE)
                st.plotly_chart(fig_c, use_container_width=True, config={"displayModeBar": False})

        with r4:
            st.markdown('<div class="card-title">⚡ Special Activity</div>', unsafe_allow_html=True)
            activity = [t for t in data.get("special_transactions",[]) if t["Type"] in SPECIAL_TX_TYPES]
            if activity:
                tc = _Counter(t["Type"] for t in activity)
                pills = '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px;">'
                for tx_type, cnt in sorted(tc.items(), key=lambda x: -x[1]):
                    meta = TX_META.get(tx_type, TX_META["Other"])
                    pills += (f'<span style="background:{meta["color"]}18;border:1px solid {meta["color"]}44;'
                        f'color:{meta["color"]};font-size:10px;font-family:\'IBM Plex Mono\',monospace;'
                        f'font-weight:600;padding:2px 9px;border-radius:20px;">{meta["icon"]} {tx_type} ×{cnt}</span>')
                pills += '</div>'
                st.markdown(pills, unsafe_allow_html=True)
                for t in activity[:5]:
                    meta = TX_META.get(t["Type"], TX_META["Other"])
                    units_str = f'{t["Units"]:+.3f} units' if t["Units"] != 0 else ""
                    st.markdown(
                        f"""<div style="background:#0c0f1a;border:1px solid rgba(255,255,255,0.05);
                            border-left:3px solid {meta['color']};border-radius:0 8px 8px 0;padding:8px 12px;margin-bottom:6px;">
                          <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div>
                              <span style="font-size:10px;font-weight:700;color:{meta['color']};font-family:'IBM Plex Mono',monospace;">{meta['icon']} {t['Type']}</span>
                              <div style="font-size:12px;color:#e2e8f0;font-weight:500;margin-top:2px;">{t['Scheme']}</div>
                              <div style="font-size:10px;color:#4a5568;margin-top:1px;">{t['Date']} &nbsp;·&nbsp; {units_str}</div>
                            </div>
                            <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:700;color:{meta['color']};text-align:right;">{fmt_inr(t['Amount'])}</div>
                          </div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                if len(activity) > 5:
                    st.markdown(f'<div style="font-size:11px;color:#4a5568;text-align:center;padding:4px 0;">+ {len(activity)-5} more — see My Portfolio</div>', unsafe_allow_html=True)
            else:
                st.info("No special transactions detected.")

    # ─────────────────────────────────────────────────────────────────────────
    # ── SIP VIEW ─────────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    elif view_mode == "🔄 SIP":
        all_tx = data.get("special_transactions", [])
        sip_txs    = [t for t in all_tx if t["Type"] == "SIP"]
        sip_rev    = [t for t in all_tx if t["Type"] == "SIP Reversal"]

        # Per-scheme SIP invested
        sip_by_scheme = {}
        for t in sip_txs:
            sip_by_scheme[t["Scheme"]] = sip_by_scheme.get(t["Scheme"], 0.0) + t["Amount"]

        total_sip_invested = sum(sip_by_scheme.values())
        total_sip_reversed = sum(t["Amount"] for t in sip_rev)
        live_sips  = data.get("live_sips", [])
        dead_sips  = data.get("dead_sips", [])
        sip_monthly = sum(s["amount"] for s in live_sips)

        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(_kpi_card("Total SIP Invested", fmt_inr(total_sip_invested),
                f"{len(sip_by_scheme)} schemes", "#63b3ed"), unsafe_allow_html=True)
        with k2:
            st.markdown(_kpi_card("Monthly SIP Amount", fmt_inr(sip_monthly),
                f"{len(live_sips)} live SIPs", "#48bb78", "rgba(72,187,120,0.06)", "rgba(72,187,120,0.15)"), unsafe_allow_html=True)
        with k3:
            st.markdown(_kpi_card("Inactive SIPs", str(len(dead_sips)),
                "Need attention", "#f6ad55", "rgba(246,173,85,0.06)", "rgba(246,173,85,0.15)"), unsafe_allow_html=True)
        with k4:
            st.markdown(_kpi_card("SIP Reversals / Bounces", fmt_inr(total_sip_reversed),
                f"{len(sip_rev)} events", "#fc8181", "rgba(252,129,129,0.06)", "rgba(252,129,129,0.15)"), unsafe_allow_html=True)

        _dash_section("🏆 Top Schemes by SIP Invested")
        if sip_by_scheme:
            df_sip = pd.DataFrame([
                {"Scheme": k, "SIP Invested": v}
                for k, v in sorted(sip_by_scheme.items(), key=lambda x: -x[1])
            ])
            fig_sip = px.bar(df_sip, x="SIP Invested", y="Scheme", orientation="h",
                color="SIP Invested", color_continuous_scale=["#1a365d","#2b6cb0","#63b3ed","#bee3f8"])
            fig_sip.update_layout(height=max(200, len(df_sip)*36),
                xaxis=dict(visible=False),
                yaxis=dict(tickfont=dict(size=11, color="#718096"), title=""),
                coloraxis_showscale=False, **PLOT_BASE)
            st.plotly_chart(fig_sip, use_container_width=True, config={"displayModeBar": False})

        sc1, sc2 = st.columns(2)
        with sc1:
            _dash_section("✅ Live SIPs")
            if live_sips:
                st.dataframe(pd.DataFrame([
                    {"Scheme": clean_name(s["scheme"]), "Amount": fmt_inr(s["amount"]),
                     "Day": s["day_label"], "Last": s["last_date"], "Next Due": s["next_date"]}
                    for s in sorted(live_sips, key=lambda x: x["amount"], reverse=True)
                ]), use_container_width=True, hide_index=True)
            else:
                st.info("No live SIPs.")

        with sc2:
            _dash_section("🔴 Inactive / Stopped SIPs")
            if dead_sips:
                st.dataframe(pd.DataFrame([
                    {"Scheme": clean_name(s["scheme"]), "Amount": fmt_inr(s["amount"]),
                     "Last Date": s["last_date"]}
                    for s in dead_sips
                ]), use_container_width=True, hide_index=True)
            else:
                st.info("No inactive SIPs found.")

        if sip_rev:
            _dash_section("↩️ SIP Reversals / Bounces")
            st.dataframe(pd.DataFrame([
                {"Date": t["Date"], "Scheme": t["Scheme"],
                 "Amount": fmt_inr(t["Amount"]), "Description": t.get("Description","")}
                for t in sip_rev
            ]), use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────────────────────────────────
    # ── LUMPSUM VIEW ─────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    elif view_mode == "💰 Lumpsum":
        all_tx = data.get("special_transactions", [])
        ls_txs  = [t for t in all_tx if t["Type"] == "Lumpsum Purchase"]
        ls_rev  = [t for t in all_tx if t["Type"] in ("Redemption", "Redemption Reversal")]

        ls_by_scheme = {}
        for t in ls_txs:
            ls_by_scheme[t["Scheme"]] = ls_by_scheme.get(t["Scheme"], 0.0) + t["Amount"]

        redemptions = [t for t in all_tx if t["Type"] == "Redemption"]
        red_by_scheme = {}
        for t in redemptions:
            red_by_scheme[t["Scheme"]] = red_by_scheme.get(t["Scheme"], 0.0) + t["Amount"]

        total_ls       = sum(ls_by_scheme.values())
        total_redeemed = sum(red_by_scheme.values())
        total_ls_schemes = len(ls_by_scheme)

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(_kpi_card("Total Lumpsum Invested", fmt_inr(total_ls),
                f"{total_ls_schemes} schemes", "#9f7aea", "rgba(159,122,234,0.06)", "rgba(159,122,234,0.15)"), unsafe_allow_html=True)
        with k2:
            st.markdown(_kpi_card("Total Redeemed", fmt_inr(total_redeemed),
                f"{len(red_by_scheme)} schemes redeemed from", "#fc8181", "rgba(252,129,129,0.06)", "rgba(252,129,129,0.15)"), unsafe_allow_html=True)
        with k3:
            net = total_ls - total_redeemed
            color = "#48bb78" if net >= 0 else "#fc8181"
            st.markdown(_kpi_card("Net Deployed", fmt_inr(net),
                "Invested minus redeemed", color, f"rgba({'72,187,120' if net>=0 else '252,129,129'},0.06)",
                f"rgba({'72,187,120' if net>=0 else '252,129,129'},0.15)"), unsafe_allow_html=True)
        with k4:
            red_rev = [t for t in all_tx if t["Type"] == "Redemption Reversal"]
            st.markdown(_kpi_card("Redemption Reversals", fmt_inr(sum(t["Amount"] for t in red_rev)),
                f"{len(red_rev)} events", "#f6ad55", "rgba(246,173,85,0.06)", "rgba(246,173,85,0.15)"), unsafe_allow_html=True)

        lc1, lc2 = st.columns(2)
        with lc1:
            _dash_section("🏆 Top Schemes by Lumpsum Invested")
            if ls_by_scheme:
                df_ls = pd.DataFrame([
                    {"Scheme": k, "Invested": v}
                    for k, v in sorted(ls_by_scheme.items(), key=lambda x: -x[1])
                ])
                fig_ls = px.bar(df_ls, x="Invested", y="Scheme", orientation="h",
                    color="Invested", color_continuous_scale=["#2d1b69","#553c9a","#9f7aea","#e9d8fd"])
                fig_ls.update_layout(height=max(200, len(df_ls)*36),
                    xaxis=dict(visible=False),
                    yaxis=dict(tickfont=dict(size=11, color="#718096"), title=""),
                    coloraxis_showscale=False, **PLOT_BASE)
                st.plotly_chart(fig_ls, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No lumpsum purchases found.")

        with lc2:
            _dash_section("🏦 Most Redeemed Schemes")
            if red_by_scheme:
                df_red = pd.DataFrame([
                    {"Scheme": k, "Redeemed": v}
                    for k, v in sorted(red_by_scheme.items(), key=lambda x: -x[1])
                ])
                fig_red = px.bar(df_red, x="Redeemed", y="Scheme", orientation="h",
                    color="Redeemed", color_continuous_scale=["#1a0a0a","#742a2a","#fc8181","#fed7d7"])
                fig_red.update_layout(height=max(200, len(df_red)*36),
                    xaxis=dict(visible=False),
                    yaxis=dict(tickfont=dict(size=11, color="#718096"), title=""),
                    coloraxis_showscale=False, **PLOT_BASE)
                st.plotly_chart(fig_red, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No redemptions found.")

        _dash_section("📋 All Lumpsum Purchases")
        if ls_txs:
            st.dataframe(pd.DataFrame([
                {"Date": t["Date"], "Scheme": t["Scheme"], "Amount": fmt_inr(t["Amount"]),
                 "Units": f'{t["Units"]:+.3f}', "Description": t.get("Description","")}
                for t in sorted(ls_txs, key=lambda x: x["date_obj"], reverse=True)
            ]), use_container_width=True, hide_index=True)

        _dash_section("🏦 All Redemptions")
        if redemptions:
            st.dataframe(pd.DataFrame([
                {"Date": t["Date"], "Scheme": t["Scheme"], "Amount": fmt_inr(t["Amount"]),
                 "Units": f'{t["Units"]:+.3f}', "Description": t.get("Description","")}
                for t in sorted(redemptions, key=lambda x: x["date_obj"], reverse=True)
            ]), use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────────────────────────────────
    # ── STP / SWITCH VIEW ────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    elif view_mode == "↔️ STP / Switch":
        all_tx = data.get("special_transactions", [])

        stp_out_txs    = [t for t in all_tx if t["Type"] == "STP Out"]
        stp_in_txs     = [t for t in all_tx if t["Type"] == "STP In"]
        switch_out_txs = [t for t in all_tx if t["Type"] == "Switch Out"]
        switch_in_txs  = [t for t in all_tx if t["Type"] == "Switch In"]

        total_stp_out    = sum(t["Amount"] for t in stp_out_txs)
        total_stp_in     = sum(t["Amount"] for t in stp_in_txs)
        total_switch_out = sum(t["Amount"] for t in switch_out_txs)
        total_switch_in  = sum(t["Amount"] for t in switch_in_txs)

        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(_kpi_card("STP Out (transferred)", fmt_inr(total_stp_out),
                f"{len(stp_out_txs)} events", "#f6ad55", "rgba(246,173,85,0.06)", "rgba(246,173,85,0.15)"), unsafe_allow_html=True)
        with k2:
            st.markdown(_kpi_card("STP In (received)", fmt_inr(total_stp_in),
                f"{len(stp_in_txs)} events", "#68d391", "rgba(104,211,145,0.06)", "rgba(104,211,145,0.15)"), unsafe_allow_html=True)
        with k3:
            st.markdown(_kpi_card("Switch Out", fmt_inr(total_switch_out),
                f"{len(switch_out_txs)} events", "#ed8936", "rgba(237,137,54,0.06)", "rgba(237,137,54,0.15)"), unsafe_allow_html=True)
        with k4:
            st.markdown(_kpi_card("Switch In", fmt_inr(total_switch_in),
                f"{len(switch_in_txs)} events", "#4fd1c5", "rgba(79,209,197,0.06)", "rgba(79,209,197,0.15)"), unsafe_allow_html=True)

        # STP flow chart
        if stp_out_txs or stp_in_txs:
            _dash_section("↔️ STP Flow — Where money moved")
            stp_out_by = {}
            for t in stp_out_txs:
                stp_out_by[t["Scheme"]] = stp_out_by.get(t["Scheme"], 0.0) + t["Amount"]
            stp_in_by = {}
            for t in stp_in_txs:
                stp_in_by[t["Scheme"]] = stp_in_by.get(t["Scheme"], 0.0) + t["Amount"]

            tc1, tc2 = st.columns(2)
            with tc1:
                st.markdown('<div style="font-size:12px;font-weight:600;color:#f6ad55;margin-bottom:8px;">⬅️ Money Left These Schemes (STP Out)</div>', unsafe_allow_html=True)
                if stp_out_by:
                    df_so = pd.DataFrame([{"Scheme": k, "Amount": v} for k,v in sorted(stp_out_by.items(), key=lambda x:-x[1])])
                    fig_so = px.bar(df_so, x="Amount", y="Scheme", orientation="h",
                        color="Amount", color_continuous_scale=["#7b341e","#dd6b20","#f6ad55","#fefcbf"])
                    fig_so.update_layout(height=max(160, len(df_so)*36),
                        xaxis=dict(visible=False), yaxis=dict(tickfont=dict(size=10,color="#718096"),title=""),
                        coloraxis_showscale=False, **PLOT_BASE)
                    st.plotly_chart(fig_so, use_container_width=True, config={"displayModeBar": False})

            with tc2:
                st.markdown('<div style="font-size:12px;font-weight:600;color:#68d391;margin-bottom:8px;">➡️ Money Entered These Schemes (STP In)</div>', unsafe_allow_html=True)
                if stp_in_by:
                    df_si = pd.DataFrame([{"Scheme": k, "Amount": v} for k,v in sorted(stp_in_by.items(), key=lambda x:-x[1])])
                    fig_si = px.bar(df_si, x="Amount", y="Scheme", orientation="h",
                        color="Amount", color_continuous_scale=["#1a4731","#276749","#68d391","#c6f6d5"])
                    fig_si.update_layout(height=max(160, len(df_si)*36),
                        xaxis=dict(visible=False), yaxis=dict(tickfont=dict(size=10,color="#718096"),title=""),
                        coloraxis_showscale=False, **PLOT_BASE)
                    st.plotly_chart(fig_si, use_container_width=True, config={"displayModeBar": False})

        # Switch flow chart
        if switch_out_txs or switch_in_txs:
            _dash_section("🔀 Switch Flow — Where money moved")
            sw_out_by = {}
            for t in switch_out_txs:
                sw_out_by[t["Scheme"]] = sw_out_by.get(t["Scheme"], 0.0) + t["Amount"]
            sw_in_by = {}
            for t in switch_in_txs:
                sw_in_by[t["Scheme"]] = sw_in_by.get(t["Scheme"], 0.0) + t["Amount"]

            sc1, sc2 = st.columns(2)
            with sc1:
                st.markdown('<div style="font-size:12px;font-weight:600;color:#ed8936;margin-bottom:8px;">⬅️ Switched Out From</div>', unsafe_allow_html=True)
                if sw_out_by:
                    df_swo = pd.DataFrame([{"Scheme": k, "Amount": v} for k,v in sorted(sw_out_by.items(), key=lambda x:-x[1])])
                    fig_swo = px.bar(df_swo, x="Amount", y="Scheme", orientation="h",
                        color="Amount", color_continuous_scale=["#7b341e","#c05621","#ed8936","#fbd38d"])
                    fig_swo.update_layout(height=max(160, len(df_swo)*36),
                        xaxis=dict(visible=False), yaxis=dict(tickfont=dict(size=10,color="#718096"),title=""),
                        coloraxis_showscale=False, **PLOT_BASE)
                    st.plotly_chart(fig_swo, use_container_width=True, config={"displayModeBar": False})
            with sc2:
                st.markdown('<div style="font-size:12px;font-weight:600;color:#4fd1c5;margin-bottom:8px;">➡️ Switched Into</div>', unsafe_allow_html=True)
                if sw_in_by:
                    df_swi = pd.DataFrame([{"Scheme": k, "Amount": v} for k,v in sorted(sw_in_by.items(), key=lambda x:-x[1])])
                    fig_swi = px.bar(df_swi, x="Amount", y="Scheme", orientation="h",
                        color="Amount", color_continuous_scale=["#1d4044","#2c7a7b","#4fd1c5","#b2f5ea"])
                    fig_swi.update_layout(height=max(160, len(df_swi)*36),
                        xaxis=dict(visible=False), yaxis=dict(tickfont=dict(size=10,color="#718096"),title=""),
                        coloraxis_showscale=False, **PLOT_BASE)
                    st.plotly_chart(fig_swi, use_container_width=True, config={"displayModeBar": False})

        # Reversal detail tables
        rev_types = ["STP In Reversal","STP Out Reversal","Switch In Reversal","Switch Out Reversal"]
        reversals = [t for t in all_tx if t["Type"] in rev_types]
        if reversals:
            _dash_section("↩️ STP / Switch Reversals")
            st.dataframe(pd.DataFrame([
                {"Date": t["Date"], "Scheme": t["Scheme"], "Type": t["Type"],
                 "Amount": fmt_inr(t["Amount"]), "Description": t.get("Description","")}
                for t in sorted(reversals, key=lambda x: x["date_obj"], reverse=True)
            ]), use_container_width=True, hide_index=True)

        if not (stp_out_txs or stp_in_txs or switch_out_txs or switch_in_txs):
            st.info("No STP or Switch transactions found in your portfolio.")

    # ─────────────────────────────────────────────────────────────────────────
    # ── SWP / REDEMPTION VIEW ────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    elif view_mode == "💸 SWP / Redemption":
        all_tx = data.get("special_transactions", [])

        swp_txs  = [t for t in all_tx if t["Type"] == "SWP"]
        red_txs  = [t for t in all_tx if t["Type"] == "Redemption"]
        swp_rev  = [t for t in all_tx if t["Type"] == "SWP Reversal"]
        red_rev  = [t for t in all_tx if t["Type"] == "Redemption Reversal"]

        total_swp = sum(t["Amount"] for t in swp_txs)
        total_red = sum(t["Amount"] for t in red_txs)
        total_out = total_swp + total_red

        # Returns on redeemed schemes
        redeemed_positions = data.get("redeemed", [])
        total_realized_pnl = data.get("realized_pnl", 0.0)

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(_kpi_card("Total Withdrawn (SWP)", fmt_inr(total_swp),
                f"{len(swp_txs)} SWP events", "#fc8181", "rgba(252,129,129,0.06)", "rgba(252,129,129,0.15)"), unsafe_allow_html=True)
        with k2:
            st.markdown(_kpi_card("Total Redeemed", fmt_inr(total_red),
                f"{len(red_txs)} redemption events", "#fc8181", "rgba(252,129,129,0.06)", "rgba(252,129,129,0.15)"), unsafe_allow_html=True)
        with k3:
            st.markdown(_kpi_card("Total Cash Out", fmt_inr(total_out),
                "SWP + Redemptions", "#f6ad55", "rgba(246,173,85,0.06)", "rgba(246,173,85,0.15)"), unsafe_allow_html=True)
        with k4:
            color = "#48bb78" if total_realized_pnl >= 0 else "#fc8181"
            st.markdown(_kpi_card("Realized P&L", fmt_inr(total_realized_pnl),
                "Fully exited positions", color, f"rgba({'72,187,120' if total_realized_pnl>=0 else '252,129,129'},0.06)",
                f"rgba({'72,187,120' if total_realized_pnl>=0 else '252,129,129'},0.15)"), unsafe_allow_html=True)

        # Top redeemed schemes chart
        red_by_scheme = {}
        for t in red_txs:
            red_by_scheme[t["Scheme"]] = red_by_scheme.get(t["Scheme"], 0.0) + t["Amount"]

        swp_by_scheme = {}
        for t in swp_txs:
            swp_by_scheme[t["Scheme"]] = swp_by_scheme.get(t["Scheme"], 0.0) + t["Amount"]

        oc1, oc2 = st.columns(2)
        with oc1:
            _dash_section("🏦 Most Redeemed Schemes")
            if red_by_scheme:
                df_r = pd.DataFrame([{"Scheme": k, "Redeemed": v} for k,v in sorted(red_by_scheme.items(), key=lambda x:-x[1])])
                fig_r = px.bar(df_r, x="Redeemed", y="Scheme", orientation="h",
                    color="Redeemed", color_continuous_scale=["#1a0a0a","#742a2a","#fc8181","#fed7d7"])
                fig_r.update_layout(height=max(200, len(df_r)*36),
                    xaxis=dict(visible=False), yaxis=dict(tickfont=dict(size=11,color="#718096"),title=""),
                    coloraxis_showscale=False, **PLOT_BASE)
                st.plotly_chart(fig_r, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No redemptions found.")

        with oc2:
            _dash_section("💸 SWP by Scheme")
            if swp_by_scheme:
                df_swp = pd.DataFrame([{"Scheme": k, "SWP Amount": v} for k,v in sorted(swp_by_scheme.items(), key=lambda x:-x[1])])
                fig_swp = px.bar(df_swp, x="SWP Amount", y="Scheme", orientation="h",
                    color="SWP Amount", color_continuous_scale=["#1a0a0a","#742a2a","#fc8181","#fbb6ce"])
                fig_swp.update_layout(height=max(200, len(df_swp)*36),
                    xaxis=dict(visible=False), yaxis=dict(tickfont=dict(size=11,color="#718096"),title=""),
                    coloraxis_showscale=False, **PLOT_BASE)
                st.plotly_chart(fig_swp, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No SWP transactions found.")

        # Fully exited positions with returns
        if redeemed_positions:
            _dash_section("📊 Fully Exited Positions — Returns Generated")
            exit_rows = []
            for r in redeemed_positions:
                profit = r["profit"]
                pnl_pct = (profit / r["invested"] * 100) if r["invested"] else 0.0
                exit_rows.append({
                    "Scheme": clean_name(r["scheme"]),
                    "Invested": fmt_inr(r["invested"]),
                    "Redeemed": fmt_inr(r["redeemed"]),
                    "P&L": (f"▲ {fmt_inr(profit)}" if profit >= 0 else f"▼ {fmt_inr(profit)}"),
                    "Return %": f"{'▲' if pnl_pct>=0 else '▼'} {abs(pnl_pct):.1f}%",
                })
            st.dataframe(pd.DataFrame(exit_rows), use_container_width=True, hide_index=True)

        # Detail tables
        if red_txs:
            _dash_section("📋 All Redemption Transactions")
            st.dataframe(pd.DataFrame([
                {"Date": t["Date"], "Scheme": t["Scheme"], "Amount": fmt_inr(t["Amount"]),
                 "Units": f'{t["Units"]:+.3f}', "Description": t.get("Description","")}
                for t in sorted(red_txs, key=lambda x: x["date_obj"], reverse=True)
            ]), use_container_width=True, hide_index=True)

        if swp_txs:
            _dash_section("📋 All SWP Transactions")
            st.dataframe(pd.DataFrame([
                {"Date": t["Date"], "Scheme": t["Scheme"], "Amount": fmt_inr(t["Amount"]),
                 "Units": f'{t["Units"]:+.3f}', "Description": t.get("Description","")}
                for t in sorted(swp_txs, key=lambda x: x["date_obj"], reverse=True)
            ]), use_container_width=True, hide_index=True)

        if swp_rev or red_rev:
            _dash_section("↩️ Reversals")
            st.dataframe(pd.DataFrame([
                {"Date": t["Date"], "Scheme": t["Scheme"], "Type": t["Type"],
                 "Amount": fmt_inr(t["Amount"]), "Description": t.get("Description","")}
                for t in sorted(swp_rev + red_rev, key=lambda x: x["date_obj"], reverse=True)
            ]), use_container_width=True, hide_index=True)

        if not (swp_txs or red_txs):
            st.info("No SWP or Redemption transactions found in your portfolio.")


# ─────────────────────────────────────────────
# MY PORTFOLIO
# ─────────────────────────────────────────────

def render_my_portfolio(data):
    st.markdown('<div class="page-title">Portfolio Ledger</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Open holdings and fully redeemed positions</div>', unsafe_allow_html=True)

    for label, category, color in [
        ("Equity Funds", "Equity Funds", C_ACCENT),
        ("Debt Funds", "Debt Funds", "#f6ad55"),
    ]:
        group = [item for item in data["holdings"] if item["category"] == category]
        if not group:
            continue
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:8px;margin:22px 0 10px;">
              <div style="width:7px;height:7px;border-radius:50%;background:{color};box-shadow:0 0 5px {color};"></div>
              <span style="font-size:11px;font-weight:700;color:{color};text-transform:uppercase;letter-spacing:2px;">{label}</span>
              <div style="flex:1;height:1px;background:rgba(255,255,255,0.05);"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        rows = []
        for item in sorted(group, key=lambda x: x["value"], reverse=True):
            scheme_name = item["scheme"]
            cas_value = item["value"]
            live_value = cas_value
            badge = ""
            show_nav = item.get("cas_nav", 0.0)
            show_date = item.get("cas_date", "—")
            try:
                show_date = to_date(show_date).strftime("%d %b %Y")
            except Exception:
                show_date = "—"
            if st.session_state.live_data and scheme_name in st.session_state.live_data:
                live_value = st.session_state.live_data[scheme_name]["live_value"]
                show_nav = st.session_state.live_data[scheme_name]["nav"]
                show_date = st.session_state.live_data[scheme_name]["date"]
                badge = " 🟢"

            current_pnl = live_value - item["invested"]
            rows.append({
                "Scheme": clean_name(scheme_name) + badge,
                "SIP Invested": fmt_inr(item.get("sip_invested", 0.0)),
                "Lump Sum": fmt_inr(item.get("lumpsum_invested", 0.0)),
                "Total Invested": fmt_inr(item["invested"]),
                "CAS Value": fmt_inr(cas_value),
                "Live Value": fmt_inr(live_value) if badge else "—",
                "NAV": f"₹{show_nav:,.4f}" if show_nav else "—",
                "NAV Date": show_date,
                "Current P&L": (f"▲ {fmt_inr(current_pnl)}" if current_pnl >= 0 else f"▼ {fmt_inr(current_pnl)}"),
                "XIRR %": f"{item['xirr']:.2f}%",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown('<div class="section-sep">Bubble Map — Invested vs XIRR</div>', unsafe_allow_html=True)
    df_bubble = pd.DataFrame([
        {
            "Scheme": clean_name(item["scheme"]),
            "Invested": item["invested"],
            "XIRR": item["xirr"],
            "Gain": max(item["pnl"], 0),
            "Type": item["category"],
        }
        for item in data["holdings"] if item["invested"] > 0
    ])
    if not df_bubble.empty:
        fig_bubble = px.scatter(
            df_bubble,
            x="Invested",
            y="XIRR",
            size="Gain",
            color="Type",
            hover_name="Scheme",
            color_discrete_map={"Equity Funds": C_ACCENT, "Debt Funds": "#f6ad55"},
        )
        fig_bubble.update_layout(
            height=340,
            xaxis=dict(showgrid=True, gridcolor=GRID, title="Invested (₹)", tickfont=dict(size=11, color="#718096")),
            yaxis=dict(showgrid=True, gridcolor=GRID, title="XIRR %", tickfont=dict(size=11, color="#718096")),
            legend=dict(font=dict(size=11, color="#718096"), bgcolor="rgba(0,0,0,0)"),
            **PLOT_BASE,
        )
        st.plotly_chart(fig_bubble, use_container_width=True, config={"displayModeBar": False})

    st.markdown('<div class="section-sep" style="margin-top:36px;">Fully Redeemed Positions</div>', unsafe_allow_html=True)
    if data.get("redeemed"):
        realized = data["realized_pnl"]
        color = gain_color(realized)
        st.markdown(
            f"""
            <div style="background:rgba({'72,187,120' if realized>=0 else '252,129,129'},0.05);border:1px solid rgba({'72,187,120' if realized>=0 else '252,129,129'},0.2);
                                border-radius:10px;padding:14px 18px;margin-bottom:14px;">
              <div style="font-size:10px;color:{color};text-transform:uppercase;letter-spacing:1px;font-weight:600;margin-bottom:4px;">Total Realized P&L</div>
              <div style="font-family:'IBM Plex Mono',monospace;font-size:22px;font-weight:700;color:{color};">
                {gain_arrow(realized)} {fmt_inr(realized)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        redeemed_rows = [
            {
                "Scheme": clean_name(item["scheme"]),
                "Invested": fmt_inr(item["invested"]),
                "Redeemed": fmt_inr(item["redeemed"]),
                "P&L": (f"▲ {fmt_inr(item['profit'])}" if item["profit"] >= 0 else f"▼ {fmt_inr(item['profit'])}"),
            }
            for item in data["redeemed"]
        ]
        st.dataframe(pd.DataFrame(redeemed_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No fully redeemed positions found.")

    # ─── SPECIAL TRANSACTIONS DETAIL ────────────────────────────────────
    st.markdown(
        '<div class="section-sep" style="margin-top:36px;">⚡ Special Transactions — Full History</div>',
        unsafe_allow_html=True,
    )
    special_txs = data.get("special_transactions", [])
    activity_all = [t for t in special_txs if t["Type"] in SPECIAL_TX_TYPES]

    if not activity_all:
        st.info("No special transactions (STP, SWP, Switch, Reversals, Rejections) found.")
    else:
        # ── Filter controls ───────────────────────────────────────────────
        fc1, fc2, fc3 = st.columns([2, 2, 1])
        with fc1:
            type_options = ["All Types"] + sorted(set(t["Type"] for t in activity_all))
            selected_type = st.selectbox("Filter by Type", type_options, key="sptx_type")
        with fc2:
            scheme_options = ["All Schemes"] + sorted(set(t["Scheme"] for t in activity_all))
            selected_scheme = st.selectbox("Filter by Scheme", scheme_options, key="sptx_scheme")
        with fc3:
            group_options = ["All", "inflow", "outflow", "reversal"]
            selected_group = st.selectbox("Group", group_options, key="sptx_group")

        # ── Apply filters ─────────────────────────────────────────────────
        filtered = activity_all
        if selected_type != "All Types":
            filtered = [t for t in filtered if t["Type"] == selected_type]
        if selected_scheme != "All Schemes":
            filtered = [t for t in filtered if t["Scheme"] == selected_scheme]
        if selected_group != "All":
            filtered = [t for t in filtered if TX_META.get(t["Type"], {}).get("group") == selected_group]

        # ── Summary stats ─────────────────────────────────────────────────
        total_inflow  = sum(t["Amount"] for t in filtered if TX_META.get(t["Type"], {}).get("group") == "inflow")
        total_outflow = sum(t["Amount"] for t in filtered if TX_META.get(t["Type"], {}).get("group") == "outflow")
        total_rev     = sum(t["Amount"] for t in filtered if TX_META.get(t["Type"], {}).get("group") == "reversal")

        sm1, sm2, sm3, sm4 = st.columns(4)
        sm1.metric("Filtered Records", len(filtered))
        sm2.metric("Total Inflow",  fmt_inr(total_inflow))
        sm3.metric("Total Outflow", fmt_inr(total_outflow))
        sm4.metric("Reversed / Rejected", fmt_inr(total_rev))

        # ── Type pill summary ─────────────────────────────────────────────
        from collections import Counter as _Counter
        tc = _Counter(t["Type"] for t in filtered)
        pills = '<div style="display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 14px;">'
        for tx_type, cnt in sorted(tc.items(), key=lambda x: -x[1]):
            meta = TX_META.get(tx_type, TX_META["Other"])
            pills += (
                f'<span style="background:{meta["color"]}18;border:1px solid {meta["color"]}44;'
                f'color:{meta["color"]};font-size:10px;font-family:\'IBM Plex Mono\',monospace;'
                f'font-weight:600;padding:2px 9px;border-radius:20px;">'
                f'{meta["icon"]} {tx_type} <span style="opacity:.6;">×{cnt}</span></span>'
            )
        pills += '</div>'
        st.markdown(pills, unsafe_allow_html=True)

        # ── Full table ────────────────────────────────────────────────────
        if filtered:
            df_special = build_special_tx_df(filtered)
            st.dataframe(df_special, use_container_width=True, hide_index=True)

        # ── Per-scheme breakdown for holdings ─────────────────────────────
        st.markdown(
            '<div class="section-sep" style="margin-top:24px;">Per-Scheme Special Transaction Summary</div>',
            unsafe_allow_html=True,
        )
        scheme_groups = {}
        for t in activity_all:
            scheme_groups.setdefault(t["Scheme"], []).append(t)

        for s_name, s_txs in sorted(scheme_groups.items()):
            inflow_amt  = sum(t["Amount"] for t in s_txs if TX_META.get(t["Type"], {}).get("group") == "inflow")
            outflow_amt = sum(t["Amount"] for t in s_txs if TX_META.get(t["Type"], {}).get("group") == "outflow")
            rev_amt     = sum(t["Amount"] for t in s_txs if TX_META.get(t["Type"], {}).get("group") == "reversal")
            type_pills  = " ".join(
                f'{TX_META.get(tt, TX_META["Other"])["icon"]} {tt} ×{cnt}'
                for tt, cnt in _Counter(t["Type"] for t in s_txs).most_common()
            )
            with st.expander(f"{s_name}  —  {len(s_txs)} events  ·  {type_pills}"):
                sc1, sc2, sc3 = st.columns(3)
                sc1.metric("Inflow",   fmt_inr(inflow_amt))
                sc2.metric("Outflow",  fmt_inr(outflow_amt))
                sc3.metric("Reversed", fmt_inr(rev_amt))
                st.dataframe(
                    build_special_tx_df(sorted(s_txs, key=lambda x: x["date_obj"], reverse=True)),
                    use_container_width=True,
                    hide_index=True,
                )


# ─────────────────────────────────────────────
# SIP CENTER
# ─────────────────────────────────────────────

def render_sip_center(data):
    st.markdown('<div class="page-title">SIP Center</div>', unsafe_allow_html=True)
    live_sips = data.get("live_sips", [])
    dead_sips = data.get("dead_sips", [])

    tab = st.segmented_control(
        "sip_tab",
        [f"🟢 Live ({len(live_sips)})", f"🔴 Inactive ({len(dead_sips)})"],
        default=f"🟢 Live ({len(live_sips)})",
        label_visibility="collapsed",
    )
    target_list = live_sips if "Live" in tab else dead_sips
    total_outflow = sum(item["amount"] for item in target_list)
    status_label = "LIVE" if "Live" in tab else "INACTIVE"

    st.markdown(
        f"""
        <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;
    padding:20px 24px;display:flex;justify-content:space-between;
                    align-items:center;margin-bottom:16px;">
          <div>
            <div style="font-size:10px;color:var(--muted);text-transform:uppercase;
    letter-spacing:1.5px;margin-bottom:4px;">Total Monthly Outflow</div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:30px;font-weight:700;
    color:#f7fafc;letter-spacing:-1px;">{fmt_inr(total_outflow)}</div>
          </div>
          <div style="font-size:12px;font-weight:700;color:{'#48bb78' if 'Live' in tab else '#fc8181'};">
            {len(target_list)} {status_label}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if target_list:
        rows = [
            {
                "Scheme": clean_name(item["scheme"]),
                "Amount": fmt_inr(item["amount"]),
                "Day": item["day_label"],
                "Last Date": item["last_date"],
                "Next Due": item["next_date"],
                "Status": item["status"],
            }
            for item in target_list
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No SIPs in this category.")

    all_sips = live_sips + dead_sips
    if all_sips:
        st.markdown('<div class="section-sep">Monthly Outflow by Scheme</div>', unsafe_allow_html=True)
        df_bar = pd.DataFrame([
            {"Scheme": clean_name(item["scheme"]), "Amount": item["amount"]}
            for item in all_sips
        ])
        fig_bar = px.bar(
            df_bar,
            x="Amount",
            y="Scheme",
            orientation="h",
            color="Amount",
            color_continuous_scale=["#1a365d", C_ACCENT, "#bee3f8"],
        )
        fig_bar.update_layout(
            height=max(200, len(all_sips) * 30),
            xaxis=dict(visible=False),
            yaxis=dict(tickfont=dict(size=11, color="#718096"), title=""),
            coloraxis_showscale=False,
            **PLOT_BASE,
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────
# TRANSACTIONS
# ─────────────────────────────────────────────

def render_transactions(data):
    st.markdown('<div class="page-title">Transaction Ledger</div>', unsafe_allow_html=True)
    tx_map = data.get("tx_map", {})
    agg_map = data.get("agg_map", {})

    if not tx_map:
        st.warning("No transaction data found.")
        return

    selected_scheme = st.selectbox("Select Scheme", list(tx_map.keys()), label_visibility="visible")
    totals = agg_map.get(selected_scheme, {"cost": 0.0, "units": 0.0, "value": 0.0})
    c1, c2, c3 = st.columns(3)
    c1.metric("Book Cost", fmt_inr(totals["cost"]))
    c2.metric("Units", f"{totals['units']:.3f}")
    c3.metric("Current Value", fmt_inr(totals["value"]))

    rows = []
    for transaction in tx_map.get(selected_scheme, []):
        rows.append({
            "Date": to_date(transaction.get("date")).strftime("%d %b %Y") if transaction.get("date") else "—",
            "Description": transaction.get("description", "—"),
            "Amount": fmt_inr(float(transaction["amount"])) if transaction.get("amount") else "—",
            "NAV": f"₹{float(transaction['nav']):,.4f}" if transaction.get("nav") else "—",
            "Units": f"{float(transaction['units']):,.3f}" if transaction.get("units") else "—",
            "Type": transaction.get("type", "—"),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown('<div class="section-sep" style="margin-top:28px;">All Holdings — XIRR Table</div>', unsafe_allow_html=True)
    performance = [
        {
            "Scheme": clean_name(item["scheme"]),
            "SIP Invested": fmt_inr(item.get("sip_invested", 0.0)),
            "Lump Sum": fmt_inr(item.get("lumpsum_invested", 0.0)),
            "Total Invested": fmt_inr(item["invested"]),
            "Value": fmt_inr(item["value"]),
            "P&L": (f"▲ {fmt_inr(item['pnl'])}" if item["pnl"] >= 0 else f"▼ {fmt_inr(item['pnl'])}"),
            "XIRR %": f"{item['xirr']:.2f}%",
            "Category": item["category"],
        }
        for item in data["holdings"]
    ]
    st.dataframe(pd.DataFrame(performance), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# ALERTS
# ─────────────────────────────────────────────

def render_alerts(data):
    st.markdown('<div class="page-title">Alerts & Insights</div>', unsafe_allow_html=True)

    alerts = []
    for duplicate in data.get("duplicate_alerts", []):
        alerts.append(("warn", "Duplicate SIP Detected", f"{clean_name(duplicate['scheme'])} — {duplicate['count']}× entries on {duplicate['dates']}"))
    for sip in data.get("dead_sips", []):
        alerts.append(("danger", "Inactive SIP", f"{clean_name(sip['scheme'])} — last processed {sip['last_date']}"))
    for holding in [item for item in data["holdings"] if item["pnl"] < 0]:
        alerts.append(("info", "Unrealized Loss", f"{clean_name(holding['scheme'])} — down {fmt_inr(holding['pnl'])} from cost"))

    if not alerts:
        st.markdown(
            """
            <div style="text-align:center;padding:60px 20px;">
              <div style="font-size:48px;margin-bottom:12px;">◎</div>
              <div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:700;color:#f7fafc;margin-bottom:6px;">All Clear</div>
              <div style="font-size:13px;color:#718096;">No alerts detected in your portfolio.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    colors = {"warn": "#f6ad55", "danger": "#fc8181", "info": "#63b3ed"}
    labels = {"warn": "WARNING", "danger": "ACTION REQUIRED", "info": "INFO"}
    for level, title, detail in alerts:
        color = colors.get(level, C_ACCENT)
        label = labels.get(level, "INFO")
        st.markdown(
            f"""
            <div class="alert-card" style="border-color:{color};">
              <div style="font-size:9px;font-weight:700;color:{color};text-transform:uppercase;
                          letter-spacing:1.5px;font-family:'IBM Plex Mono',monospace;margin-bottom:4px;">{label}</div>
              <div style="font-size:14px;font-weight:600;color:#f7fafc;margin-bottom:3px;">{title}</div>
              <div style="font-size:13px;color:#718096;">{detail}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def run_app():
    apply_page_config()
    inject_global_styles()
    initialize_session_state()
    active = active_data()
    menu = build_sidebar(active)
    if not active:
        show_upload()
        st.stop()
    if menu == "Dashboard":
        render_dashboard(active)
    elif menu == "My Portfolio":
        render_my_portfolio(active)
    elif menu == "SIP Center":
        render_sip_center(active)
    elif menu == "Transactions":
        render_transactions(active)
    elif menu == "Alerts":
        render_alerts(active)


run_app()