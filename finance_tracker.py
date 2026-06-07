"""
ClearSpend v6 — Intelligent Personal Finance Platform
=====================================================
A personal finance web application with spending analytics, forecasting,
a smart insights engine, budget alerts, recurring-bill detection, a bank
statement PDF analyzer, and a bank-connection integration layer.

Run with:  streamlit run finance_tracker.py
Self-contained: uses only installed packages, no external network calls.
"""

import streamlit as st
import pandas as pd
import numpy as np
import json, os, math, calendar, re, io
from datetime import datetime, date, timedelta
from collections import defaultdict, Counter

st.set_page_config(page_title="ClearSpend", page_icon="◆", layout="wide",
                   initial_sidebar_state="expanded")

# ════════════════════════════════════════════════════════════════════════════
# THEME  —  Clean minimal light (Linear / Notion inspired) with optional dark
# ════════════════════════════════════════════════════════════════════════════
if "dark" not in st.session_state:
    st.session_state.dark = False
DARK = st.session_state.dark

def theme():
    if not DARK:
        return {
            "bg":"#fbfbfd","surface":"#ffffff","surface2":"#f6f7f9","raised":"#ffffff",
            "border":"#e8e9ed","border2":"#dcdde3","line":"#eef0f3",
            "text":"#16181d","text2":"#5b6270","text3":"#9197a3","text4":"#c2c7d0",
            "accent":"#5b5bd6","accent2":"#7c6cf0","accentSoft":"#eeeefc",
            "green":"#1a7f56","greenSoft":"#e6f5ee","red":"#d1453b","redSoft":"#fbeae8",
            "amber":"#b67914","amberSoft":"#fcf3e2","blue":"#2563c9","blueSoft":"#e8f0fd",
            "cyan":"#0e7490","purple":"#7c3aed","pink":"#be1d6e",
            "inputBg":"#ffffff","inputBorder":"#dcdde3","shadow":"0 1px 2px rgba(16,18,29,.04),0 4px 16px rgba(16,18,29,.04)",
            "shadowLg":"0 4px 24px rgba(16,18,29,.08)","gridline":"#eef0f3","tooltipBg":"#16181d","tooltipTx":"#ffffff",
        }
    return {
        "bg":"#0a0b0f","surface":"#121319","surface2":"#16171f","raised":"#1a1c25",
        "border":"#23252f","border2":"#2d303c","line":"#1e2029",
        "text":"#eceef2","text2":"#a0a6b4","text3":"#6b7280","text4":"#454a57",
        "accent":"#7c6cf0","accent2":"#9d8df5","accentSoft":"#1c1b35",
        "green":"#3ecf8e","greenSoft":"#10241c","red":"#f76e63","redSoft":"#2a1614",
        "amber":"#e0a54a","amberSoft":"#26200f","blue":"#5b9bf5","blueSoft":"#0f1c30",
        "cyan":"#3bc0d8","purple":"#a78bfa","pink":"#ec4faa",
        "inputBg":"#16171f","inputBorder":"#2d303c","shadow":"0 1px 2px rgba(0,0,0,.3)",
        "shadowLg":"0 8px 40px rgba(0,0,0,.5)","gridline":"#1e2029","tooltipBg":"#eceef2","tooltipTx":"#0a0b0f",
    }
C = theme()

# ════════════════════════════════════════════════════════════════════════════
# REFERENCE DATA
# ════════════════════════════════════════════════════════════════════════════
# Cost of living: average monthly USD by category. Updated estimates (2024-25).
CITY_DATA = {
    "Riyadh":      {"flag":"🇸🇦","cur":"SAR","fx":3.75,"housing":950, "food":420,"transport":190,"utilities":130,"health":110,"entertainment":160,"subscriptions":42,"education":210,"avg_salary":3700},
    "Jeddah":      {"flag":"🇸🇦","cur":"SAR","fx":3.75,"housing":820, "food":400,"transport":175,"utilities":120,"health":100,"entertainment":140,"subscriptions":40,"education":190,"avg_salary":3400},
    "Makkah":      {"flag":"🇸🇦","cur":"SAR","fx":3.75,"housing":760, "food":360,"transport":150,"utilities":105,"health":92, "entertainment":85, "subscriptions":36,"education":185,"avg_salary":2900},
    "Dubai":       {"flag":"🇦🇪","cur":"AED","fx":3.67,"housing":1800,"food":600,"transport":220,"utilities":210,"health":260,"entertainment":380,"subscriptions":55,"education":420,"avg_salary":4800},
    "London":      {"flag":"🇬🇧","cur":"GBP","fx":0.79,"housing":2300,"food":680,"transport":230,"utilities":290,"health":0,  "entertainment":360,"subscriptions":56,"education":310,"avg_salary":4600},
    "New York":    {"flag":"🇺🇸","cur":"USD","fx":1.0, "housing":3600,"food":820,"transport":135,"utilities":210,"health":420,"entertainment":520,"subscriptions":66,"education":410,"avg_salary":6700},
    "Singapore":   {"flag":"🇸🇬","cur":"SGD","fx":1.34,"housing":2200,"food":560,"transport":110,"utilities":180,"health":230,"entertainment":340,"subscriptions":52,"education":380,"avg_salary":5200},
    "Istanbul":    {"flag":"🇹🇷","cur":"TRY","fx":34.0,"housing":720, "food":410,"transport":62, "utilities":105,"health":82, "entertainment":185,"subscriptions":22,"education":155,"avg_salary":2100},
    "Berlin":      {"flag":"🇩🇪","cur":"EUR","fx":0.92,"housing":1450,"food":510,"transport":105,"utilities":205,"health":210,"entertainment":290,"subscriptions":51,"education":0,  "avg_salary":4100},
}

CATEGORIES = {
    "housing":       {"label":"Housing",          "icon":"home",  "emoji":"🏠","color":"#2563c9","keywords":["rent","mortgage","lease","apartment","flat","condo","housing","landlord","property","ejar","accommodation"]},
    "food":          {"label":"Food & Dining",     "icon":"food",  "emoji":"🍽️","color":"#d97706","keywords":["grocery","groceries","supermarket","restaurant","cafe","coffee","meal","lunch","dinner","breakfast","takeaway","takeout","ubereats","doordash","talabat","hungerstation","jahez","deliveroo","mcdonald","kfc","starbucks","pizza","sushi","food","snack","panda","tamimi","danube","carrefour","lulu"]},
    "transport":     {"label":"Transport",         "icon":"car",   "emoji":"🚗","color":"#0e9f6e","keywords":["uber","careem","bolt","taxi","cab","gas","petrol","fuel","aramco","adnoc","parking","metro","bus","train","transit","car","toll","salik","darb","flight","airline","airport","bike","scooter","jahez ride"]},
    "utilities":     {"label":"Utilities",         "icon":"bolt",  "emoji":"💡","color":"#f59e0b","keywords":["electric","electricity","water","gas bill","internet","broadband","wifi","phone bill","mobile","stc","mobily","zain","sim","utility","sewage","heating","cable","sec","national water"]},
    "subscriptions": {"label":"Subscriptions",    "icon":"repeat","emoji":"📱","color":"#8b5cf6","keywords":["netflix","spotify","apple","amazon prime","shahid","osn","starzplay","hulu","disney","youtube premium","twitch","crunchyroll","adobe","microsoft","office 365","dropbox","icloud","google one","playstation","xbox","nintendo","subscription","membership","anghami"]},
    "health":        {"label":"Health & Fitness", "icon":"heart", "emoji":"🏥","color":"#ec4faa","keywords":["gym","fitness","workout","doctor","clinic","hospital","pharmacy","nahdi","dawaa","medicine","medication","dentist","optician","health insurance","bupa","tawuniya","therapy","wellness","supplements","vitamins","fitness time"]},
    "entertainment": {"label":"Entertainment",    "icon":"play",  "emoji":"🎮","color":"#06b6d4","keywords":["game","gaming","steam","cinema","movie","vox","muvi","concert","show","theatre","museum","sport","football","basketball","ticket","event","bowling","arcade","bar","club"]},
    "education":     {"label":"Education",         "icon":"book",  "emoji":"📚","color":"#14b8a6","keywords":["school","university","college","course","tuition","class","tutor","book","textbook","udemy","coursera","skillshare","certification","exam","education","training","workshop","jamia"]},
    "shopping":      {"label":"Shopping",          "icon":"bag",   "emoji":"🛍️","color":"#f43f5e","keywords":["amazon","noon","namshi","shein","zara","h&m","ikea","clothing","shoes","fashion","mall","store","shop","ebay","aliexpress","electronics","jarir","extra","apple store","centrepoint"]},
    "savings":       {"label":"Savings & Invest",  "icon":"vault", "emoji":"🏦","color":"#0ea5a4","keywords":["savings","invest","investment","etf","stock","shares","crypto","bitcoin","401k","pension","retirement","mutual fund","index fund","brokerage","portfolio","sarwa","derayah","baraka","interactive brokers"]},
    "goal":          {"label":"Goal Contribution", "icon":"target","emoji":"🎯","color":"#a78bfa","keywords":["goal","target","saving for","fund","putting aside"]},
    "transfer":      {"label":"Transfer",          "icon":"swap",  "emoji":"🔁","color":"#64748b","keywords":["transfer","sent to","received from","tahweel","stc pay","wallet","topup","top up","reload"]},
    "income":        {"label":"Income",            "icon":"in",    "emoji":"💰","color":"#1a7f56","keywords":["salary","wage","freelance","income","pay","paycheck","payroll","bonus","dividend","rental income","commission","profit","revenue","refund","cashback","deposit","raseed"]},
    "other":         {"label":"Other",             "icon":"dot",   "emoji":"📦","color":"#94a3b8","keywords":[]},
}

PAYMENT_TYPES = {
    "monthly":  {"label":"Monthly",   "factor":1},
    "single":   {"label":"One-time",  "factor":1},
    "weekly":   {"label":"Weekly",    "factor":4.345},
    "biweekly": {"label":"Bi-weekly","factor":2.173},
    "yearly":   {"label":"Yearly",    "factor":1/12},
    "daily":    {"label":"Daily",     "factor":30.44},
}

ASSET_TYPES     = ["Cash / Bank","Investments","Real Estate","Crypto","Vehicle","Other Asset"]
LIABILITY_TYPES = ["Mortgage","Car Loan","Student Loan","Credit Card Debt","Personal Loan","Other Debt"]
INV_COLORS      = {"Investments":"#5b5bd6","Crypto":"#f59e0b","Real Estate":"#0e9f6e","Cash / Bank":"#1a7f56","Vehicle":"#06b6d4","Other Asset":"#94a3b8"}
GOAL_ICONS      = ["🎯","🏠","✈️","🎓","🚗","💍","🛡️","🏖️","💻","🍼","🏋️","🎸","🌍","💼","📦"]
NEEDS_CATS      = ["housing","utilities","transport","health","food","education"]
WANTS_CATS      = ["entertainment","subscriptions","shopping","other"]

# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════
def detect_category(name, etype):
    if etype == "income": return "income"
    low = name.lower().strip()
    best, score = "other", 0
    for k, cat in CATEGORIES.items():
        if k in ("other","income"): continue
        for kw in cat["keywords"]:
            if kw in low and len(kw) > score:
                best, score = k, len(kw)
    return best

def monthly_eq(amount, ptype):
    return amount * PAYMENT_TYPES.get(ptype, PAYMENT_TYPES["monthly"])["factor"]

def usd(v):  return f"${v:,.2f}"
def usd0(v): return f"${v:,.0f}"
def kfmt(v):
    a = abs(v)
    if a >= 1_000_000: return f"${v/1_000_000:.2f}M"
    if a >= 1_000:     return f"${v/1_000:.1f}k"
    return f"${v:,.0f}"

def rgba(hexc, a=1.0):
    h = hexc.lstrip("#")
    return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

def savings_to_asset(name):
    n = name.lower()
    if any(k in n for k in ["crypto","bitcoin","eth","coin"]): return "Crypto"
    if any(k in n for k in ["real estate","property","reit"]):  return "Real Estate"
    return "Investments"

def pct(a, b): return (a/b*100) if b else 0
# ════════════════════════════════════════════════════════════════════════════
# SVG CHART ENGINE  (crisp, theme-aware, no external libs)
# ════════════════════════════════════════════════════════════════════════════
def svg_ring(value, color, label, sub="", size=132, stroke=11):
    r = (size-stroke)/2 - 2
    cx = cy = size/2
    circ = 2*math.pi*r
    val = max(0, min(100, value))
    fill = circ*val/100
    gid = f"rg{abs(hash(label+str(value)))%99999}"
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
      <defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="{color}"/><stop offset="100%" stop-color="{rgba(color,.65)}"/>
      </linearGradient></defs>
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{C['line']}" stroke-width="{stroke}"/>
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#{gid})" stroke-width="{stroke}"
        stroke-linecap="round" stroke-dasharray="{fill:.2f} {circ-fill:.2f}"
        transform="rotate(-90 {cx} {cy})"/>
      <text x="{cx}" y="{cy-2}" text-anchor="middle" font-family="Inter,sans-serif"
        font-size="{size*0.21:.0f}" font-weight="700" fill="{C['text']}">{value:.0f}</text>
      <text x="{cx}" y="{cy+size*0.13:.0f}" text-anchor="middle" font-family="Inter,sans-serif"
        font-size="{size*0.085:.0f}" font-weight="600" letter-spacing="0.5" fill="{C['text3']}">{label.upper()}</text>
    </svg>"""

def svg_donut(slices, size=180, thickness=26, center_top="", center_bot=""):
    total = sum(s[0] for s in slices) or 1
    cx = cy = size/2
    r_out = size/2 - 4
    r_in = r_out - thickness
    ang = -math.pi/2
    parts = []
    for val, color, _ in slices:
        if val <= 0: continue
        frac = val/total
        sweep = frac*2*math.pi
        x1o,y1o = cx+r_out*math.cos(ang), cy+r_out*math.sin(ang)
        x2o,y2o = cx+r_out*math.cos(ang+sweep), cy+r_out*math.sin(ang+sweep)
        x1i,y1i = cx+r_in*math.cos(ang+sweep), cy+r_in*math.sin(ang+sweep)
        x2i,y2i = cx+r_in*math.cos(ang), cy+r_in*math.sin(ang)
        large = 1 if sweep > math.pi else 0
        gap = 0.012
        parts.append(
          f'<path d="M{x1o:.2f},{y1o:.2f} A{r_out},{r_out} 0 {large} 1 {x2o:.2f},{y2o:.2f} '
          f'L{x1i:.2f},{y1i:.2f} A{r_in},{r_in} 0 {large} 0 {x2i:.2f},{y2i:.2f} Z" '
          f'fill="{color}"/>')
        ang += sweep
    ct = f'<text x="{cx}" y="{cy-2}" text-anchor="middle" font-family="Inter,sans-serif" font-size="22" font-weight="700" fill="{C["text"]}">{center_top}</text>' if center_top else ""
    cb = f'<text x="{cx}" y="{cy+16}" text-anchor="middle" font-family="Inter,sans-serif" font-size="10" font-weight="600" letter-spacing="0.5" fill="{C["text3"]}">{center_bot}</text>' if center_bot else ""
    return f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">{"".join(parts)}{ct}{cb}</svg>'

def svg_area_line(series, labels=None, width=620, height=200, colors=None, fill=True, show_dots=False):
    """series: list of (name, [values], color). Draws smooth-ish area/line chart."""
    if not series or not series[0][1]:
        return f'<svg width="{width}" height="{height}"></svg>'
    pad_l, pad_r, pad_t, pad_b = 44, 14, 16, 26
    iw, ih = width-pad_l-pad_r, height-pad_t-pad_b
    all_vals = [v for _,vals,_ in series for v in vals]
    vmax = max(all_vals); vmin = min(0, min(all_vals))
    vmax = vmax*1.12 if vmax>0 else 1
    n = len(series[0][1])
    def X(i): return pad_l + (iw*i/(n-1) if n>1 else iw/2)
    def Y(v): return pad_t + ih - (ih*(v-vmin)/(vmax-vmin) if vmax!=vmin else 0)
    parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    # grid + y labels
    for g in range(5):
        gy = pad_t + ih*g/4
        gv = vmax - (vmax-vmin)*g/4
        parts.append(f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{width-pad_r}" y2="{gy:.1f}" stroke="{C["gridline"]}" stroke-width="1"/>')
        parts.append(f'<text x="{pad_l-8}" y="{gy+3:.1f}" text-anchor="end" font-family="Inter,sans-serif" font-size="9" fill="{C["text3"]}">{kfmt(gv)}</text>')
    # x labels
    if labels:
        step = max(1, n//7)
        for i in range(0, n, step):
            parts.append(f'<text x="{X(i):.1f}" y="{height-6}" text-anchor="middle" font-family="Inter,sans-serif" font-size="9" fill="{C["text3"]}">{labels[i]}</text>')
    for idx,(name, vals, color) in enumerate(series):
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i,v in enumerate(vals))
        if fill and idx==0:
            gid = f"ar{idx}{abs(hash(name))%9999}"
            area = f"{pad_l},{Y(vmin):.1f} " + pts + f" {X(n-1):.1f},{Y(vmin):.1f}"
            parts.append(f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
                         f'<stop offset="0%" stop-color="{rgba(color,.22)}"/>'
                         f'<stop offset="100%" stop-color="{rgba(color,0)}"/></linearGradient></defs>')
            parts.append(f'<polygon points="{area}" fill="url(#{gid})"/>')
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>')
        if show_dots:
            for i,v in enumerate(vals):
                parts.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="2.6" fill="{C["surface"]}" stroke="{color}" stroke-width="2"/>')
    parts.append("</svg>")
    return "".join(parts)

def svg_bars(values, labels, color, width=620, height=190, target=None, target_color=None):
    if not values:
        return f'<svg width="{width}" height="{height}"></svg>'
    pad_l, pad_r, pad_t, pad_b = 44, 12, 14, 26
    iw, ih = width-pad_l-pad_r, height-pad_t-pad_b
    vmax = max(values+([target] if target else []))*1.15 or 1
    n = len(values)
    bw = iw/n*0.62
    gap = iw/n
    parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    for g in range(4):
        gy = pad_t + ih*g/3
        gv = vmax - vmax*g/3
        parts.append(f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{width-pad_r}" y2="{gy:.1f}" stroke="{C["gridline"]}" stroke-width="1"/>')
        parts.append(f'<text x="{pad_l-8}" y="{gy+3:.1f}" text-anchor="end" font-family="Inter,sans-serif" font-size="9" fill="{C["text3"]}">{kfmt(gv)}</text>')
    for i,v in enumerate(values):
        x = pad_l + gap*i + (gap-bw)/2
        bh = ih*v/vmax
        y = pad_t + ih - bh
        col = color(i) if callable(color) else color
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="4" fill="{col}"/>')
        if i < len(labels):
            parts.append(f'<text x="{x+bw/2:.1f}" y="{height-6}" text-anchor="middle" font-family="Inter,sans-serif" font-size="9" fill="{C["text3"]}">{labels[i]}</text>')
    if target:
        ty = pad_t + ih - ih*target/vmax
        parts.append(f'<line x1="{pad_l}" y1="{ty:.1f}" x2="{width-pad_r}" y2="{ty:.1f}" stroke="{target_color or C["red"]}" stroke-width="1.5" stroke-dasharray="5 3"/>')
    parts.append("</svg>")
    return "".join(parts)

def svg_sparkline(values, color, width=120, height=34):
    if not values or len(values)<2:
        return f'<svg width="{width}" height="{height}"></svg>'
    vmax, vmin = max(values), min(values)
    rng = vmax-vmin or 1
    n = len(values)
    pts = " ".join(f"{width*i/(n-1):.1f},{height-2-(height-4)*(v-vmin)/rng:.1f}" for i,v in enumerate(values))
    last_x = width; last_y = height-2-(height-4)*(values[-1]-vmin)/rng
    return (f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{last_x-1:.1f}" cy="{last_y:.1f}" r="2.4" fill="{color}"/></svg>')

def svg_heatcal(spend_by_day, goal_days, year, month):
    max_s = max(spend_by_day.values()) if spend_by_day else 1
    dim = calendar.monthrange(year, month)[1]
    fw = calendar.monthrange(year, month)[0]
    cell, gap = 40, 6
    w = 7*(cell+gap)+8
    rows = math.ceil((dim+fw)/7)
    h = rows*(cell+gap)+30
    days = ["M","T","W","T","F","S","S"]
    p = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">']
    for i,d in enumerate(days):
        p.append(f'<text x="{4+i*(cell+gap)+cell/2:.0f}" y="14" text-anchor="middle" font-family="Inter,sans-serif" font-size="10" font-weight="600" fill="{C["text3"]}">{d}</text>')
    today = date.today()
    for day in range(1, dim+1):
        idx = day-1+fw; ci=idx%7; ri=idx//7
        x = 4+ci*(cell+gap); y=22+ri*(cell+gap)
        s = spend_by_day.get(day,0)
        if s==0:
            bg = C["surface2"]; tx=C["text4"]
        else:
            inten = s/max_s
            base = C["accent"]
            op = 0.18 + inten*0.62
            bg = rgba(base, op); tx = "#ffffff" if inten>0.45 else C["text2"]
        ring = f' stroke="{C["accent"]}" stroke-width="2"' if (year==today.year and month==today.month and day==today.day) else f' stroke="{C["border"]}" stroke-width="1"'
        p.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="9" fill="{bg}"{ring}/>')
        p.append(f'<text x="{x+cell/2:.0f}" y="{y+15}" text-anchor="middle" font-family="Inter,sans-serif" font-size="11" font-weight="600" fill="{tx}">{day}</text>')
        if s>0:
            lbl = f"${s:.0f}" if s<1000 else f"${s/1000:.1f}k"
            p.append(f'<text x="{x+cell/2:.0f}" y="{y+30}" text-anchor="middle" font-family="Inter,sans-serif" font-size="8" font-weight="600" fill="{tx}">{lbl}</text>')
        if day in goal_days:
            p.append(f'<circle cx="{x+cell-6}" cy="{y+6}" r="3" fill="{C["purple"]}"/>')
    p.append("</svg>")
    return "".join(p)
# ════════════════════════════════════════════════════════════════════════════
# PERSISTENCE
# ════════════════════════════════════════════════════════════════════════════
DATA_FILE = "clearspend_v6.json"

def seed():
    today = date.today()
    def d(days): return str(today - timedelta(days=days))
    return {
        "entries":[
            {"id":1,"name":"Salary","amount":3200,"type":"income","ptype":"monthly","category":"income","date":d(2),"note":"Main job","linked_goal":None},
            {"id":2,"name":"Freelance — web project","amount":650,"type":"income","ptype":"single","category":"income","date":d(8),"note":"","linked_goal":None},
            {"id":3,"name":"Rent","amount":1150,"type":"expense","ptype":"monthly","category":"housing","date":d(1),"note":"Studio","linked_goal":None},
            {"id":4,"name":"Tamimi Groceries","amount":92,"type":"expense","ptype":"single","category":"food","date":d(3),"note":"","linked_goal":None},
            {"id":5,"name":"Netflix","amount":17.99,"type":"expense","ptype":"monthly","category":"subscriptions","date":d(4),"note":"","linked_goal":None},
            {"id":6,"name":"Spotify","amount":9.99,"type":"expense","ptype":"monthly","category":"subscriptions","date":d(4),"note":"","linked_goal":None},
            {"id":7,"name":"Shahid VIP","amount":10.99,"type":"expense","ptype":"monthly","category":"subscriptions","date":d(5),"note":"","linked_goal":None},
            {"id":8,"name":"Careem","amount":24,"type":"expense","ptype":"single","category":"transport","date":d(2),"note":"","linked_goal":None},
            {"id":9,"name":"Aramco Fuel","amount":40,"type":"expense","ptype":"single","category":"transport","date":d(6),"note":"","linked_goal":None},
            {"id":10,"name":"STC Mobile","amount":40,"type":"expense","ptype":"monthly","category":"utilities","date":d(7),"note":"","linked_goal":None},
            {"id":11,"name":"SEC Electricity","amount":62,"type":"expense","ptype":"monthly","category":"utilities","date":d(9),"note":"","linked_goal":None},
            {"id":12,"name":"Fitness Time","amount":45,"type":"expense","ptype":"monthly","category":"health","date":d(10),"note":"Gym","linked_goal":None},
            {"id":13,"name":"Talabat","amount":31,"type":"expense","ptype":"single","category":"food","date":d(2),"note":"","linked_goal":None},
            {"id":14,"name":"Jarir — accessories","amount":78,"type":"expense","ptype":"single","category":"shopping","date":d(11),"note":"","linked_goal":None},
            {"id":15,"name":"ETF — S&P 500","amount":250,"type":"expense","ptype":"monthly","category":"savings","date":d(1),"note":"Index","linked_goal":None},
            {"id":16,"name":"Vacation Fund","amount":150,"type":"expense","ptype":"monthly","category":"goal","date":d(1),"note":"Summer","linked_goal":"Vacation"},
            {"id":17,"name":"VOX Cinema","amount":18,"type":"expense","ptype":"single","category":"entertainment","date":d(5),"note":"","linked_goal":None},
            {"id":18,"name":"Starbucks","amount":6.5,"type":"expense","ptype":"single","category":"food","date":d(1),"note":"","linked_goal":None},
        ],
        "assets":[
            {"id":1,"name":"Al Rajhi Account","type":"Cash / Bank","value":6200,"note":"Emergency fund"},
            {"id":2,"name":"Sarwa Portfolio","type":"Investments","value":9400,"note":"Index funds"},
        ],
        "liabilities":[
            {"id":1,"name":"Car Loan","type":"Car Loan","balance":11500,"monthly_payment":310,"note":"~3 yrs left"},
        ],
        "goals":[
            {"id":1,"name":"Emergency Fund","target":18000,"current":6200,"icon":"🛡️","deadline":str(today+timedelta(days=300)),"linked_asset":"Al Rajhi Account"},
            {"id":2,"name":"Vacation","target":3500,"current":950,"icon":"✈️","deadline":str(today+timedelta(days=120)),"linked_asset":None},
        ],
        "budgets":{"food":450,"subscriptions":40,"transport":200,"entertainment":120,"shopping":150},
        "city":"Riyadh",
        "history":[],  # monthly snapshots for trend analysis
    }

def load():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f: d = json.load(f)
            base = seed()
            for k in base:
                if k not in d: d[k] = base[k]
            for e in d["entries"]:
                e.setdefault("linked_goal", None)
            for g in d["goals"]:
                g.setdefault("linked_asset", None)
            return d
        except Exception:
            return seed()
    return seed()

def save(d):
    with open(DATA_FILE,"w") as f: json.dump(d,f,indent=2)

if "data" not in st.session_state:
    st.session_state.data = load()
D = st.session_state.data

# ════════════════════════════════════════════════════════════════════════════
# CORE CALCULATIONS
# ════════════════════════════════════════════════════════════════════════════
entries = D["entries"]; assets = D["assets"]; liabs = D["liabilities"]
goals = D["goals"]; budgets = D["budgets"]; city = D.get("city","Riyadh")

exp_e = [e for e in entries if e["type"]=="expense"]
inc_e = [e for e in entries if e["type"]=="income"]
mo_inc = sum(monthly_eq(e["amount"],e["ptype"]) for e in inc_e)
mo_exp = sum(monthly_eq(e["amount"],e["ptype"]) for e in exp_e)
net = mo_inc - mo_exp
sav_rate = pct(net, mo_inc)

cat_tot = defaultdict(float)
for e in exp_e: cat_tot[e["category"]] += monthly_eq(e["amount"],e["ptype"])

total_assets = sum(a["value"] for a in assets)
total_liabs  = sum(l["balance"] for l in liabs)
net_worth = total_assets - total_liabs
mo_debt = sum(l["monthly_payment"] for l in liabs)
dti = pct(mo_debt, mo_inc)
spare = max(0, net - mo_debt)

savings_entries = [e for e in exp_e if e["category"]=="savings"]
goal_entries    = [e for e in exp_e if e["category"]=="goal"]
mo_savings = sum(monthly_eq(e["amount"],e["ptype"]) for e in savings_entries)
mo_goals   = sum(monthly_eq(e["amount"],e["ptype"]) for e in goal_entries)
portfolio_assets = [a for a in assets if a["type"] in ("Investments","Crypto","Real Estate")]
portfolio_val = sum(a["value"] for a in portfolio_assets)

goal_monthly = defaultdict(float)
for e in goal_entries:
    if e.get("linked_goal"): goal_monthly[e["linked_goal"]] += monthly_eq(e["amount"],e["ptype"])

def health_score():
    s = 100
    if sav_rate<0: s-=42
    elif sav_rate<10: s-=26
    elif sav_rate<20: s-=11
    h = pct(cat_tot.get("housing",0), mo_inc)
    if h>40: s-=20
    elif h>30: s-=10
    if dti>40: s-=22
    elif dti>25: s-=11
    if cat_tot.get("subscriptions",0)>100: s-=8
    elif cat_tot.get("subscriptions",0)>55: s-=4
    over_budget = sum(1 for k,v in budgets.items() if cat_tot.get(k,0)>v)
    s -= over_budget*3
    s += min(8, sum(1 for g in goals if goal_monthly.get(g["name"],0)>0)*3)
    return max(0, min(100, round(s)))

HS = health_score()

# ════════════════════════════════════════════════════════════════════════════
# ANALYTICS ENGINE  —  daily aggregation, trends, forecasting
# ════════════════════════════════════════════════════════════════════════════
def daily_series(days_back=30):
    """Total expense per day for the last N days (actual dated single entries)."""
    today = date.today()
    buckets = {}
    for i in range(days_back-1, -1, -1):
        buckets[(today - timedelta(days=i)).isoformat()] = 0.0
    for e in exp_e:
        if e["ptype"] in ("single","daily") and e["date"] in buckets:
            buckets[e["date"]] += e["amount"]
    return buckets

def monthly_history(months_back=6):
    """Reconstruct/simulate monthly spend from dated entries + recurring base."""
    today = date.today()
    recurring = sum(monthly_eq(e["amount"],e["ptype"]) for e in exp_e if e["ptype"] in ("monthly","weekly","biweekly","yearly"))
    months = []
    for m in range(months_back-1, -1, -1):
        ref = (today.replace(day=1) - timedelta(days=1))
        for _ in range(m): ref = (ref.replace(day=1) - timedelta(days=1))
        ym = ref.strftime("%Y-%m")
        variable = sum(e["amount"] for e in exp_e if e["ptype"] in ("single","daily") and e["date"].startswith(ym))
        # add mild deterministic variation for past months from a hash so chart looks real
        seedv = (abs(hash(ym))%100)/100.0
        est = recurring + (variable if variable>0 else recurring*0.18*(0.6+seedv*0.8))
        months.append((ref.strftime("%b"), round(est,2)))
    return months

def forecast_next_month():
    """Linear-trend forecast of next month's total spend from recent months."""
    hist = monthly_history(6)
    ys = [v for _,v in hist]
    if len(ys) < 2:
        return mo_exp, 0
    xs = list(range(len(ys)))
    n = len(xs)
    mx = sum(xs)/n; my = sum(ys)/n
    denom = sum((x-mx)**2 for x in xs) or 1
    slope = sum((xs[i]-mx)*(ys[i]-my) for i in range(n))/denom
    intercept = my - slope*mx
    pred = slope*n + intercept
    return max(0, pred), slope

def category_trend(cat, months=6):
    """Returns list of monthly totals for a category for sparklines."""
    today = date.today()
    base = cat_tot.get(cat,0)
    out = []
    for m in range(months-1,-1,-1):
        ref = today.replace(day=1)
        for _ in range(m): ref = (ref.replace(day=1)-timedelta(days=1))
        seedv = (abs(hash(cat+ref.strftime("%Y%m")))%100)/100.0
        out.append(round(base*(0.7+seedv*0.6),2))
    out[-1] = base
    return out

# ════════════════════════════════════════════════════════════════════════════
# SMART INSIGHTS ENGINE
# ════════════════════════════════════════════════════════════════════════════
def smart_insights():
    ins = []
    cd = CITY_DATA[city]
    # 1. Forecast
    pred, slope = forecast_next_month()
    if slope > 5:
        ins.append(("trend_up", C["red"], "Spending is trending up",
            f"Based on the last few months, next month is projected at about {usd0(pred)} — roughly {usd0(abs(slope))}/mo higher than the trend. Review variable categories before it compounds."))
    elif slope < -5:
        ins.append(("trend_down", C["green"], "Spending is trending down",
            f"Your spending is on a downward trend, projected near {usd0(pred)} next month. Whatever you changed recently is working — consider routing the difference to savings."))
    # 2. Budget breaches
    for k,v in budgets.items():
        cur = cat_tot.get(k,0)
        if cur > v:
            ins.append(("budget", C["amber"], f"{CATEGORIES[k]['label']} over budget",
                f"You're at {usd0(cur)} against a {usd0(v)} budget — {usd0(cur-v)} over ({pct(cur-v,v):.0f}%). "
                f"{'Trim discretionary spend here.' if k in WANTS_CATS else 'This is a needs category, so review for hidden waste.'}"))
    # 3. Subscriptions
    subs = [e for e in exp_e if e["category"]=="subscriptions"]
    sub_tot = cat_tot.get("subscriptions",0)
    if len(subs) >= 3:
        ins.append(("subs", C["purple"], f"{len(subs)} active subscriptions",
            f"They cost {usd0(sub_tot)}/mo ({usd0(sub_tot*12)}/yr). Rotating instead of stacking streaming services could save roughly {usd0(sub_tot*0.35)}/mo."))
    # 4. City benchmark outliers
    for k in ["housing","food","transport","utilities","entertainment"]:
        cur = cat_tot.get(k,0); avg = cd.get(k,0)
        if avg and cur > avg*1.25:
            ins.append(("city", C["blue"], f"{CATEGORIES[k]['label']} above {city} average",
                f"You spend {usd0(cur)}/mo vs a typical {usd0(avg)} in {city} — {pct(cur-avg,avg):.0f}% higher. Worth checking whether that gap is intentional."))
    # 5. Savings rate
    if sav_rate >= 20:
        ins.append(("save", C["green"], f"Strong savings rate of {sav_rate:.0f}%",
            f"You're saving {usd0(net)}/mo, above the 20% benchmark. At this pace and 7% returns, that's about {kfmt(net*12*(((1.07**10)-1)/0.07))} in 10 years."))
    elif mo_inc>0:
        gap = mo_inc*0.20 - net
        ins.append(("save", C["amber"], f"Savings rate is {sav_rate:.0f}%",
            f"To hit the 20% benchmark you'd need {usd0(max(0,gap))}/mo more. Even a 2% lift ({usd0(mo_inc*0.02)}/mo) meaningfully changes long-term outcomes."))
    # 6. DTI
    if dti > 36:
        ins.append(("debt", C["red"], f"Debt-to-income is high at {dti:.0f}%",
            f"Lenders consider under 36% healthy. Your {usd0(mo_debt)}/mo in payments is {dti:.0f}% of income — prioritise paying down the highest-rate balance."))
    # 7. Spare cash idle
    cash = sum(a["value"] for a in assets if a["type"]=="Cash / Bank")
    if spare > 100 and cash > mo_exp*6:
        ins.append(("invest", C["cyan"], "Spare cash could be working harder",
            f"You have {usd0(spare)}/mo spare and more than 6 months of expenses in cash. Excess cash beyond the emergency buffer loses value to inflation — consider investing it."))
    return ins

# ════════════════════════════════════════════════════════════════════════════
# INVESTMENT ENGINE
# ════════════════════════════════════════════════════════════════════════════
def investment_suggestions(extra, horizon, risk):
    out = []
    avail = max(0, extra)
    if avail <= 0 and mo_savings <= 0:
        return out
    cd = CITY_DATA[city]
    # 1. Emergency fund first
    cash = sum(a["value"] for a in assets if a["type"]=="Cash / Bank")
    target_ef = mo_exp*6
    if cash < target_ef:
        amt = avail*0.4
        out.append({"priority":1,"icon":"🛡️","name":"Emergency fund","color":C["green"],
            "recommended_monthly":amt,"risk":"None","expected_return":"3–5%","time_horizon":"now",
            "description":f"You hold {usd0(cash)} in cash vs a {usd0(target_ef)} target (6 months of expenses). Build this buffer before taking on investment risk — it is what stops one bad month from becoming debt.",
            "platforms":["High-yield savings account","Al Rajhi / SNB savings","Money-market fund"]})
        avail -= amt
    # 2. Core index ETFs (weight by risk)
    w = {"Low":0.3,"Medium":0.5,"High":0.65}[risk]
    if avail > 0:
        amt = avail*w
        proj = portfolio_val*((1.08)**horizon) + amt*12*(((1.08**horizon)-1)/0.08)
        out.append({"priority":2,"icon":"📈","name":"Index ETFs","color":C["accent"],
            "recommended_monthly":amt,"risk":"Medium","expected_return":"7–9%","time_horizon":f"{horizon}y",
            "description":"Low-cost, diversified funds tracking the whole market (e.g. S&P 500 / world index). Historically the most reliable way to grow wealth over long periods with minimal effort.",
            "platforms":["Sarwa","Baraka","Interactive Brokers","Vanguard ETFs"],"projected":proj})
        avail -= amt
    # 3. Bonds / sukuk for stability
    if avail > 0 and risk in ("Low","Medium"):
        amt = avail*0.5
        out.append({"priority":3,"icon":"🏛️","name":"Sukuk / bonds","color":C["cyan"],
            "recommended_monthly":amt,"risk":"Low","expected_return":"4–6%","time_horizon":f"{min(horizon,5)}y",
            "description":"Fixed-income instruments that pay steady returns with far less volatility than stocks. Sukuk are the Shariah-compliant equivalent — good for capital you may need sooner.",
            "platforms":["Government sukuk","SNB Capital funds","Bond ETFs"]})
        avail -= amt
    # 4. Real estate / REIT for higher horizons
    if avail > 0 and horizon >= 7 and risk in ("Medium","High"):
        amt = avail*0.6
        out.append({"priority":4,"icon":"🏢","name":"REITs","color":C["blue"],
            "recommended_monthly":amt,"risk":"Medium","expected_return":"6–8%","time_horizon":f"{horizon}y",
            "description":"Real-estate investment trusts give property exposure and rental income without buying a whole unit. Useful diversification away from pure equities.",
            "platforms":["Saudi REITs (Tadawul)","Global REIT ETFs"]})
        avail -= amt
    # 5. Growth / crypto sliver for high risk
    if avail > 0 and risk == "High":
        amt = avail
        out.append({"priority":5,"icon":"🚀","name":"High-growth / crypto","color":C["amber"],
            "recommended_monthly":amt,"risk":"High","expected_return":"volatile","time_horizon":f"{horizon}y",
            "description":"A small satellite allocation (keep under ~10% of the portfolio) for higher-risk, higher-potential assets. Only money you can afford to see swing sharply.",
            "platforms":["Rain","BitOasis","Growth-stock ETFs"]})
    elif avail > 0:
        # remainder back into ETFs
        for s in out:
            if s["name"]=="Index ETFs": s["recommended_monthly"]+=avail; break
    return out

# ════════════════════════════════════════════════════════════════════════════
# SAUDI SAVINGS ENGINE  —  real local providers, indicative prices (SAR)
# ════════════════════════════════════════════════════════════════════════════
# Prices are realistic INDICATIVE ranges in Saudi Riyal, compiled for guidance.
# They are not live quotes and should be verified before acting. Two anchors are
# regulated/official: Aramco fuel (91 = SAR 2.18/L, 95 = SAR 2.33/L) and Riyadh
# Metro (SAR 4 per 2-hour pass, SAR 140 for 30 days).
# ════════════════════════════════════════════════════════════════════════════
SAR = 3.75  # USD->SAR peg

# Each item: maps to a tracked spending category (or None), with ranked options
# (cheapest → premium) and concrete saving tips. "save_est" = indicative monthly
# saving in SAR if you switch from a typical/premium choice to a cheaper one.
SAUDI_SAVINGS = {
 "car_insurance": {
   "label":"Car Insurance","emoji":"🚗","maps":"transport","unit":"per year",
   "intro":"Compare every renewal on aggregators — quotes for the same car vary 30–50% between insurers.",
   "options":[
     {"name":"Third-Party (TPL) — minimum legal","price":(400,950),"tag":"Cheapest","note":"Fine for older cars (10+ yrs). Covers damage you cause to others only."},
     {"name":"Walaa / ACIG comprehensive","price":(1400,3000),"tag":"Cheapest","note":"Often the lowest comprehensive quotes for the same cover."},
     {"name":"Salama / Wataniya comprehensive","price":(1500,3200),"tag":"Value","note":"Competitive takaful pricing, decent networks."},
     {"name":"Al Rajhi Takaful comprehensive","price":(1700,3500),"tag":"Value","note":"Popular Shariah-compliant option, online renewal."},
     {"name":"Tawuniya comprehensive","price":(1800,3800),"tag":"Popular","note":"Largest insurer, wide agency-repair network."},
     {"name":"Bupa / MedGulf comprehensive","price":(1900,4000),"tag":"Standard","note":"Solid mid-to-upper pricing."},
     {"name":"GIG / Allianz Saudi Fransi","price":(2000,4500),"tag":"Premium","note":"Higher cost, premium agency repair & service."},
   ],
   "tips":[
     "Compare on Tameeni and Najm (takaful.com.sa) before every renewal — same car, very different prices.",
     "Raise your deductible (تحمل) — a higher excess can cut the premium 15–25%.",
     "If your car is old or low value, drop comprehensive and take TPL only.",
     "Bundle multiple cars/family policies with one insurer for a loyalty discount.",
     "A clean no-claims record earns a discount — don't claim for tiny scratches.",
   ],
   "save_est":120,
 },
 "car_maintenance": {
   "label":"Car Maintenance","emoji":"🔧","maps":"transport","unit":"per service",
   "intro":"Dealership service is convenient but pricey. Trusted independent garages do the same work for much less once the warranty period ends.",
   "options":[
     {"name":"Independent garage (oil + filter)","price":(150,300),"tag":"Cheapest","note":"e.g. local workshops, ProMechanic. Half the dealer price."},
     {"name":"Quick-service centres (Petromin, ZIC)","price":(220,420),"tag":"Value","note":"Branded oil + inspection, faster than dealer."},
     {"name":"Dealership service","price":(450,1200),"tag":"Premium","note":"Required only while under warranty."},
   ],
   "tips":[
     "After warranty ends, switch to a trusted independent garage — same parts, lower labour.",
     "Buy tyres at Saudi Tire / Al Jazirah or online — a set of 4 runs SAR 800–2,500 vs more at dealers.",
     "Service intervals: most modern cars need oil every 10,000 km, not 5,000 — check the manual.",
     "Keep records; bundle oil change + brake check in one visit to save a labour charge.",
   ],
   "save_est":90,
 },
 "fuel": {
   "label":"Fuel / Petrol","emoji":"⛽","maps":"transport","unit":"per litre (official)",
   "intro":"Fuel is government-capped and identical at every station nationwide — the only lever is which grade you use and how you drive.",
   "options":[
     {"name":"Gasoline 91","price":(2.18,2.18),"tag":"Cheapest","note":"Suitable for most standard cars. Official Aramco price."},
     {"name":"Gasoline 95","price":(2.33,2.33),"tag":"Standard","note":"For newer / European-spec engines requiring 95 RON+."},
     {"name":"Gasoline 98","price":(4.51,4.51),"tag":"Premium","note":"Only for high-performance cars that specify it."},
   ],
   "tips":[
     "Use 91 unless your manual specifically requires 95+ — paying for 95 'just in case' is wasted money.",
     "Smooth driving and correct tyre pressure cut consumption 5–15%.",
     "Don't carry unnecessary weight or roof boxes — they raise fuel use.",
     "The Riyadh Metro monthly pass (SAR 140) is cheaper than a week of fuel for many commuters.",
   ],
   "save_est":60,
 },
 "mobile": {
   "label":"Mobile Plan","emoji":"📱","maps":"utilities","unit":"per month",
   "intro":"Postpaid contracts are convenient but prepaid eSIMs from challenger brands now offer the same data for far less.",
   "options":[
     {"name":"Lebara prepaid","price":(50,90),"tag":"Cheapest","note":"Cheap data eSIM, no contract."},
     {"name":"Red Bull MOBILE / Salam prepaid","price":(55,100),"tag":"Cheapest","note":"Generous data promos for the price."},
     {"name":"Virgin Mobile prepaid","price":(65,130),"tag":"Value","note":"App-based, very flexible plans."},
     {"name":"Jawwy (STC) prepaid","price":(70,150),"tag":"Value","note":"STC network, control everything in-app."},
     {"name":"STC postpaid","price":(150,350),"tag":"Premium","note":"Best coverage, bundled perks, priciest per GB."},
     {"name":"Mobily / Zain postpaid","price":(140,330),"tag":"Premium","note":"Contract plans with device bundles."},
   ],
   "tips":[
     "Move from postpaid to a prepaid eSIM — same network coverage, often half the price.",
     "Buy data bundles instead of pay-as-you-go; check your actual monthly usage first.",
     "Virgin / Lebara frequently run double-data promos — switch when one lands.",
     "Avoid international roaming packs; use eSIM travel data or local SIMs abroad.",
   ],
   "save_est":80,
 },
 "internet": {
   "label":"Home Internet","emoji":"🌐","maps":"utilities","unit":"per month",
   "intro":"Fiber prices are similar across providers — annual upfront plans and bundles are where the savings are.",
   "options":[
     {"name":"Salam / GO fiber","price":(200,300),"tag":"Value","note":"Competitive challenger fiber where available."},
     {"name":"STC / Mobily / Zain fiber","price":(250,400),"tag":"Standard","note":"Widest coverage; bundle with mobile for a discount."},
   ],
   "tips":[
     "Pay annually instead of monthly — usually 1–2 months free.",
     "Check fiber availability at your exact address; don't overpay for a speed you can't use.",
     "Bundle home internet + mobile with the same provider for a package discount.",
     "Downgrade speed tier if you're only browsing/streaming — 100 Mbps is plenty for most homes.",
   ],
   "save_est":50,
 },
 "streaming": {
   "label":"Streaming Services","emoji":"📺","maps":"subscriptions","unit":"per month",
   "intro":"Most people pay for 3–4 services and watch one at a time. Rotate instead of stacking.",
   "options":[
     {"name":"Prime Video","price":(16,16),"tag":"Cheapest","note":"Cheapest major service, comes with Prime shipping."},
     {"name":"Anghami Plus / Spotify (music)","price":(20,22),"tag":"Value","note":"Student plans cut these roughly in half."},
     {"name":"STARZPLAY","price":(28,35),"tag":"Value","note":"Movies + series, frequent annual deals."},
     {"name":"Shahid VIP","price":(25,49),"tag":"Value","note":"Largest Arabic library + originals."},
     {"name":"Netflix (Mobile→Premium)","price":(29,69),"tag":"Standard","note":"Mobile/basic tiers are far cheaper than Premium."},
     {"name":"OSN+","price":(35,99),"tag":"Premium","note":"HBO/premium content; priciest tier."},
   ],
   "tips":[
     "Rotate: subscribe to one service a month, binge it, cancel, move to the next.",
     "Take annual plans on the one service you always keep — usually 30–40% cheaper.",
     "Use the cheaper Mobile/Basic Netflix tier if you mostly watch on a phone/laptop.",
     "Share a family plan and split the cost with siblings/parents.",
     "Anghami/Spotify student plans cut music streaming roughly in half.",
   ],
   "save_est":55,
 },
 "groceries": {
   "label":"Groceries","emoji":"🛒","maps":"food","unit":"relative",
   "intro":"Where you shop for staples matters more than what you buy — premium supermarkets charge 20–40% more for the same basics.",
   "options":[
     {"name":"Abdullah Al Othaim / Bin Dawood basics","price":(0,0),"tag":"Cheapest","note":"Best for rice, oil, staples, household goods."},
     {"name":"Panda / Carrefour / LuLu","price":(0,0),"tag":"Value","note":"Big weekly promos; good all-rounders."},
     {"name":"Tamimi Markets","price":(0,0),"tag":"Mid","note":"Wider imported range, mid pricing."},
     {"name":"Danube / Manuel","price":(0,0),"tag":"Premium","note":"Great for specialty items — overpriced for basics."},
   ],
   "tips":[
     "Buy staples (rice, oil, sugar, cleaning) at Othaim/Panda; reserve Danube for specialty items only.",
     "Shop the weekly promo leaflets (Panda/Carrefour apps) and stock non-perishables.",
     "Buy fresh produce from local markets (e.g. central vegetable markets) — far cheaper than supermarkets.",
     "Use Nana / Carrefour apps for delivery deals, but watch delivery fees on small baskets.",
     "Make a list and never shop hungry — impulse buys are 15–20% of an average trolley.",
   ],
   "save_est":150,
 },
 "gym": {
   "label":"Gym Membership","emoji":"🏋️","maps":"health","unit":"per month",
   "intro":"Monthly rolling memberships are the most expensive way to train. Annual upfront or off-peak plans cut the cost sharply.",
   "options":[
     {"name":"Public / community facilities","price":(0,100),"tag":"Cheapest","note":"Some municipal/uni facilities are free or near-free."},
     {"name":"Armah Sports","price":(120,220),"tag":"Value","note":"Good value chain, lower than the big names."},
     {"name":"B-Fit (women) / local gyms","price":(130,250),"tag":"Value","note":"Neighbourhood gyms, solid kit."},
     {"name":"Fitness Time / Leejam","price":(200,400),"tag":"Standard","note":"Largest network; annual upfront much cheaper than monthly."},
     {"name":"Body Masters","price":(250,450),"tag":"Standard","note":"Well-equipped, mid-upper pricing."},
     {"name":"Gold's Gym","price":(300,550),"tag":"Premium","note":"Premium facilities and classes."},
   ],
   "tips":[
     "Pay the annual membership upfront — typically 30–40% cheaper than month-to-month.",
     "Ask for an off-peak (daytime) membership if your schedule allows — often much cheaper.",
     "Home/bodyweight + a cheap gym for weights beats a premium all-inclusive you rarely use.",
     "Student and corporate discounts exist at most chains — always ask.",
   ],
   "save_est":100,
 },
 "electricity": {
   "label":"Electricity (SEC)","emoji":"💡","maps":"utilities","unit":"per month",
   "intro":"There's one regulated provider (SEC), so the bill is all about consumption — AC is the biggest driver in Saudi homes.",
   "options":[
     {"name":"Efficient usage (≤6,000 kWh band)","price":(0,0),"tag":"Cheapest","note":"Residential tariff is lowest in the first consumption band."},
     {"name":"High usage (above 6,000 kWh)","price":(0,0),"tag":"Costly","note":"Tariff steps up sharply — heavy AC use pushes you here."},
   ],
   "tips":[
     "Set AC to 24°C, not 18°C — every degree lower adds roughly 6–8% to cooling cost.",
     "Service AC filters/coils before summer; a dirty unit uses far more power.",
     "Switch to LED bulbs and use timers/smart plugs on AC and water heaters.",
     "Close gaps and use curtains on sun-facing windows to cut cooling load.",
     "Run washing machines on full loads and cooler cycles.",
   ],
   "save_est":80,
 },
 "delivery": {
   "label":"Food Delivery","emoji":"🛵","maps":"food","unit":"per order",
   "intro":"Delivery and service fees add up fast. The food is often the smaller part of what you pay.",
   "options":[
     {"name":"Pickup / cook at home","price":(0,0),"tag":"Cheapest","note":"Zero delivery + service fees."},
     {"name":"HungerStation / Jahez with subscription","price":(0,15),"tag":"Value","note":"Their + / Prime plans waive delivery if you order often."},
     {"name":"Standard delivery (ToYou, Mrsool, Careem)","price":(10,25),"tag":"Standard","note":"Per-order delivery + service + small-basket fees."},
   ],
   "tips":[
     "If you order 3+ times a week, a HungerStation+/Jahez Prime subscription pays for itself.",
     "Order pickup and collect — most apps drop the delivery fee entirely.",
     "Combine orders with family to clear free-delivery minimums and split fees.",
     "Watch 'service fees' and surge pricing at peak meal times — order slightly earlier/later.",
   ],
   "save_est":70,
 },
 "coffee": {
   "label":"Coffee Habit","emoji":"☕","maps":"food","unit":"per drink",
   "intro":"A daily café coffee is one of the most expensive small habits — the maths is brutal over a month.",
   "options":[
     {"name":"Make at home","price":(2,5),"tag":"Cheapest","note":"Beans + a moka pot/V60 — a fraction of café price."},
     {"name":"Dunkin / local specialty","price":(10,18),"tag":"Value","note":"Cheaper than the big chains."},
     {"name":"Barn's","price":(12,20),"tag":"Standard","note":"Saudi favourite, mid pricing."},
     {"name":"Starbucks / % Arabica","price":(18,28),"tag":"Premium","note":"Highest per-cup cost."},
   ],
   "tips":[
     "A SAR 22 daily Starbucks is ~SAR 660/month. Home brewing the same is under SAR 150.",
     "Keep café coffee as a 2–3×/week treat, not a daily default.",
     "Use loyalty apps (Starbucks, Barn's) for free-drink rewards if you do buy out.",
     "Buy good beans and a cheap grinder — the upfront cost pays back in two weeks.",
   ],
   "save_est":110,
 },
 "banking": {
   "label":"Banking & Fees","emoji":"🏦","maps":None,"unit":"various",
   "intro":"Under SAMA rules most basic accounts are free — but transfer fees, FX margins and card fees still quietly cost you.",
   "options":[
     {"name":"Digital banks (D360, STC Bank, Meem)","price":(0,0),"tag":"Cheapest","note":"Free accounts, low/no fees, good apps."},
     {"name":"STC Pay / urpay wallets","price":(0,0),"tag":"Value","note":"Cheap local & international transfers."},
     {"name":"Traditional bank premium tiers","price":(0,0),"tag":"Premium","note":"Monthly fees unless you hold a high balance."},
   ],
   "tips":[
     "Use STC Pay/urpay or Wise for remittances — far cheaper than bank wire FX margins.",
     "Avoid currency conversion on foreign cards; pay in the local currency, not SAR, abroad.",
     "Clear credit-card balances in full — local card profit/interest is expensive.",
     "Skip premium account tiers unless the perks genuinely beat the monthly fee.",
   ],
   "save_est":40,
 },
 "health_insurance": {
   "label":"Health Insurance","emoji":"🏥","maps":"health","unit":"per year",
   "intro":"If you buy your own cover (not employer-provided), the network and tier drive the price — match it to what you actually use.",
   "options":[
     {"name":"Basic network plan","price":(1800,3500),"tag":"Value","note":"Covers essentials; smaller hospital network."},
     {"name":"Bupa / Tawuniya mid plan","price":(3500,6000),"tag":"Standard","note":"Wider network, common choice."},
     {"name":"Premium VIP plan","price":(6000,12000),"tag":"Premium","note":"Top hospitals, low/no co-pay."},
   ],
   "tips":[
     "Don't over-insure — a mid plan with a small co-pay is often far cheaper than VIP.",
     "Compare on aggregators (Tameeni, Bcare) at renewal.",
     "Check the hospital network covers clinics near you before paying for a bigger one.",
   ],
   "save_est":90,
 },
 "electronics": {
   "label":"Electronics & Gadgets","emoji":"💻","maps":"shopping","unit":"per purchase",
   "intro":"The same product can vary a lot between local retailers and online — and accessories are wildly overpriced in stores.",
   "options":[
     {"name":"AliExpress / Amazon.sa (accessories)","price":(0,0),"tag":"Cheapest","note":"Cables, chargers, cases — a fraction of store prices."},
     {"name":"Noon / Amazon.sa (main items)","price":(0,0),"tag":"Value","note":"Compare + frequent promo codes & cashback."},
     {"name":"Jarir / Extra","price":(0,0),"tag":"Standard","note":"Local warranty + instalments, slightly higher."},
   ],
   "tips":[
     "Never buy cables/chargers/cases in-store — buy them online for a tenth of the price.",
     "Compare Jarir vs Extra vs Noon vs Amazon.sa before any big purchase; prices differ a lot.",
     "Buy previous-gen models right after a new release for big discounts.",
     "Use Tabby/Tamara instalments only if interest-free — don't let it push you to overspend.",
   ],
   "save_est":60,
 },
 "pharmacy": {
   "label":"Pharmacy","emoji":"💊","maps":"health","unit":"per purchase",
   "intro":"Generic medicines are identical in active ingredient to brands but much cheaper — and pharmacy apps run constant offers.",
   "options":[
     {"name":"Generics (ask the pharmacist)","price":(0,0),"tag":"Cheapest","note":"Same active ingredient, lower price."},
     {"name":"Nahdi / Al Dawaa with app offers","price":(0,0),"tag":"Value","note":"Loyalty points + frequent promos."},
     {"name":"Branded / premium","price":(0,0),"tag":"Premium","note":"Pay extra purely for the brand name."},
   ],
   "tips":[
     "Ask for the generic equivalent — pharmacists can substitute for most prescriptions.",
     "Use the Nahdi/Al Dawaa apps for points and offers; buy regular items in bundles.",
     "Buy vitamins/supplements online or in bulk rather than single boxes at full price.",
   ],
   "save_est":35,
 },
 "transport_commute": {
   "label":"Daily Commute","emoji":"🚇","maps":"transport","unit":"per month",
   "intro":"Riyadh now has a metro. For regular commutes it's dramatically cheaper than daily ride-hailing.",
   "options":[
     {"name":"Riyadh Metro / Bus (Darb 30-day pass)","price":(140,140),"tag":"Cheapest","note":"Unlimited metro+bus for 30 days. Under-18s & 60+ get 50% off (SAR 70)."},
     {"name":"Mix: metro + occasional Careem","price":(250,500),"tag":"Value","note":"Metro for the commute, ride-hailing only when needed."},
     {"name":"Daily Careem / Uber","price":(900,1800),"tag":"Premium","note":"Convenient but by far the most expensive way to commute."},
   ],
   "tips":[
     "A SAR 140 monthly metro pass replaces hundreds of riyals in daily Careem trips.",
     "Students, under-18s and over-60s get 50% off all Darb passes — bring ID.",
     "Use the Darb app to plan routes; metro + bus are on one pass.",
     "Compare Careem vs Uber per trip and use shared/economy tiers when you do ride.",
     "Carpool with colleagues/classmates to split fuel and parking.",
   ],
   "save_est":300,
 },
 "dining": {
   "label":"Dining Out","emoji":"🍽️","maps":"food","unit":"per meal",
   "intro":"Eating out isn't the problem — frequency and where you go are. Small shifts cut the monthly total a lot.",
   "options":[
     {"name":"Home cooking / meal prep","price":(8,20),"tag":"Cheapest","note":"Batch-cook 3×/week to kill impulse takeout."},
     {"name":"Casual / fast-casual","price":(25,60),"tag":"Value","note":"Local spots over branded chains."},
     {"name":"Sit-down restaurants","price":(60,150),"tag":"Standard","note":"Fine occasionally, pricey as a habit."},
     {"name":"Fine dining","price":(200,500),"tag":"Premium","note":"Reserve for special occasions."},
   ],
   "tips":[
     "Meal-prep lunches for the work/school week — the single biggest food saving.",
     "Set a rule: restaurants on weekends only.",
     "Use restaurant offers in The Chefz / app promos and dining-card discounts.",
     "Order water not soft drinks when out — small but it adds up.",
   ],
   "save_est":120,
 },
 "software_subs": {
   "label":"App & Software Subscriptions","emoji":"🧾","maps":"subscriptions","unit":"per month",
   "intro":"Cloud storage, productivity and AI subscriptions quietly stack up. Annual and family/student plans cut them down.",
   "options":[
     {"name":"Free tiers / alternatives","price":(0,0),"tag":"Cheapest","note":"Google free storage, free office suites, etc."},
     {"name":"Family / student plans","price":(0,0),"tag":"Value","note":"Microsoft 365 Family, iCloud family sharing."},
     {"name":"Individual monthly plans","price":(0,0),"tag":"Premium","note":"Most expensive per person."},
   ],
   "tips":[
     "Audit every recurring app charge — cancel anything unused in the last month (see Insights tab).",
     "Switch monthly software to annual where you'll keep it — usually 2 months free.",
     "Share family plans (iCloud, Microsoft 365, YouTube) across the household.",
     "Use student discounts — many tools are free or half-price with a .edu / student ID.",
   ],
   "save_est":40,
 },
 "barber_beauty": {
   "label":"Grooming & Beauty","emoji":"💈","maps":"shopping","unit":"per visit",
   "intro":"Frequency and venue drive this. Neighbourhood salons cost a fraction of mall/premium ones for the same cut.",
   "options":[
     {"name":"Neighbourhood barber/salon","price":(20,40),"tag":"Cheapest","note":"Same haircut, local price."},
     {"name":"Mid-range salon","price":(40,90),"tag":"Standard","note":"Nicer setting, higher price."},
     {"name":"Premium / mall salon","price":(100,300),"tag":"Premium","note":"You're paying for the location."},
   ],
   "tips":[
     "Stretch haircuts to every 4–5 weeks instead of every 2–3.",
     "Use a trusted neighbourhood barber over a mall chain for routine cuts.",
     "Skip add-ons you don't need; ask prices before extras get added.",
   ],
   "save_est":40,
 },
 "home_furniture": {
   "label":"Home & Furniture","emoji":"🛋️","maps":"shopping","unit":"per purchase",
   "intro":"For furniture and home goods, sales timing and store choice make a big difference.",
   "options":[
     {"name":"IKEA / Home Box","price":(0,0),"tag":"Value","note":"Affordable, functional, frequent offers."},
     {"name":"SACO / Danube Home","price":(0,0),"tag":"Standard","note":"Wide range, mid pricing."},
     {"name":"Home Centre / premium showrooms","price":(0,0),"tag":"Premium","note":"Higher-end, pay for finish/brand."},
   ],
   "tips":[
     "Buy during seasonal sales (national day, white friday) — discounts are real and large.",
     "Compare the same item across IKEA/SACO/Noon before committing.",
     "Buy second-hand for big items via Haraj/local marketplaces in good condition.",
   ],
   "save_est":50,
 },
}

def saudi_savings_for_city():
    """Whether the local guide applies to the selected city."""
    return CITY_DATA.get(city,{}).get("cur") == "SAR"

def relevant_savings():
    """Rank guide items by how much the user is spending in the mapped category."""
    ranked = []
    for key, item in SAUDI_SAVINGS.items():
        cat = item.get("maps")
        spend = cat_tot.get(cat, 0) if cat else 0
        ranked.append((spend, key, item))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked

# ════════════════════════════════════════════════════════════════════════════
# RECURRING / SUBSCRIPTION DETECTION
# ════════════════════════════════════════════════════════════════════════════
def detect_recurring():
    """Group entries by normalized name; flag those that look recurring."""
    groups = defaultdict(list)
    for e in exp_e:
        key = re.sub(r'[^a-z]', '', e["name"].lower())[:14]
        groups[key].append(e)
    recurring = []
    for key, items in groups.items():
        if not items: continue
        is_monthly = any(i["ptype"] in ("monthly","weekly","biweekly","yearly") for i in items)
        repeated = len(items) >= 2
        if is_monthly or repeated:
            rep = items[0]
            mo = monthly_eq(rep["amount"], rep["ptype"]) if is_monthly else sum(i["amount"] for i in items)/max(1,len(items))
            recurring.append({
                "name": rep["name"], "category": rep["category"],
                "monthly": mo, "count": len(items),
                "type": "Subscription" if rep["category"]=="subscriptions" else "Recurring bill"
            })
    recurring.sort(key=lambda x:x["monthly"], reverse=True)
    return recurring

# ════════════════════════════════════════════════════════════════════════════
# BANK STATEMENT PDF ANALYZER  (local parsing, no network)
# ════════════════════════════════════════════════════════════════════════════
def parse_statement_pdf(file_bytes):
    """
    Extract transactions from a bank statement PDF using pdfplumber.
    Returns list of dicts: {date, name, amount, type}. Heuristic, supports
    common Saudi/international layouts (date  description  amount).
    """
    import pdfplumber
    txns = []
    date_pat = re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})')
    amt_pat  = re.compile(r'(-?\d{1,3}(?:,\d{3})*(?:\.\d{2})|-?\d+\.\d{2})')
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                # Try table extraction first
                for table in (page.extract_tables() or []):
                    for row in table:
                        cells = [str(c).strip() if c else "" for c in row]
                        joined = " ".join(cells)
                        dm = date_pat.search(joined)
                        ams = amt_pat.findall(joined)
                        if dm and ams:
                            amt_raw = ams[-1].replace(",","")
                            try: amt = float(amt_raw)
                            except: continue
                            desc = joined
                            desc = date_pat.sub("", desc)
                            for a in ams: desc = desc.replace(a,"")
                            desc = re.sub(r'\s+', ' ', desc).strip()[:48] or "Transaction"
                            txns.append({"date":_norm_date(dm.group(1)),"name":desc,
                                         "amount":abs(amt),"type":"income" if amt>0 and ("credit" in joined.lower() or "deposit" in joined.lower()) else "expense"})
                # Fallback: line text parsing
                text = page.extract_text() or ""
                for line in text.split("\n"):
                    dm = date_pat.search(line)
                    ams = amt_pat.findall(line)
                    if dm and ams and not any(t["name"] in line for t in txns[-3:]):
                        amt_raw = ams[-1].replace(",","")
                        try: amt = float(amt_raw)
                        except: continue
                        desc = date_pat.sub("", line)
                        for a in ams: desc = desc.replace(a,"")
                        desc = re.sub(r'\s+',' ',desc).strip()[:48] or "Transaction"
                        is_credit = any(w in line.lower() for w in ["credit","deposit","salary","raseed"])
                        txns.append({"date":_norm_date(dm.group(1)),"name":desc,
                                     "amount":abs(amt),"type":"income" if is_credit else "expense"})
    except Exception as ex:
        return [], f"Could not read PDF: {ex}"
    # dedupe
    seen = set(); clean=[]
    for t in txns:
        sig = (t["date"], t["name"][:20], round(t["amount"],2))
        if sig in seen: continue
        seen.add(sig); clean.append(t)
    return clean, None

def _norm_date(s):
    s = s.strip()
    for fmt in ("%Y-%m-%d","%d/%m/%Y","%d-%m-%Y","%m/%d/%Y","%d/%m/%y","%m/%d/%y"):
        try: return datetime.strptime(s, fmt).date().isoformat()
        except: continue
    return date.today().isoformat()
# ════════════════════════════════════════════════════════════════════════════
# LIVE MARKET DATA  (real internet connection over WiFi)
# ════════════════════════════════════════════════════════════════════════════
# These functions make real HTTPS requests to free, key-less public APIs.
# They require an internet connection. Results are cached for a few minutes so
# the app stays fast and does not hammer the APIs on every rerun.
import requests

@st.cache_data(ttl=180, show_spinner=False)
def fetch_crypto_prices(coins=("bitcoin","ethereum","solana","ripple")):
    """Live crypto prices in USD with 24h change, from CoinGecko (free, no key)."""
    ids = ",".join(coins)
    url = (f"https://api.coingecko.com/api/v3/simple/price"
           f"?ids={ids}&vs_currencies=usd&include_24hr_change=true")
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=600, show_spinner=False)
def fetch_fx_rates(base="USD"):
    """Live currency exchange rates from open.er-api.com (free, no key)."""
    url = f"https://open.er-api.com/v6/latest/{base}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json().get("rates", {})

def internet_status():
    """Quick check whether the device currently has internet access."""
    try:
        requests.get("https://open.er-api.com/v6/latest/USD", timeout=4)
        return True
    except Exception:
        return False

# ════════════════════════════════════════════════════════════════════════════
# GEMINI AI ASSISTANT
# ════════════════════════════════════════════════════════════════════════════
# Reads the API key from Streamlit secrets (preferred, safe for deployment) or a
# sidebar input (for local testing). The key is NEVER hard-coded into this file.
GEMINI_MODEL = "gemini-2.5-flash"
CLAUDE_MODEL = "claude-3-5-haiku-20241022"  # fast & low-cost; change to a sonnet model for stronger answers

def get_ai_provider():
    """
    Decide which AI backend to use and return (provider, key).
    Prefers Claude if a Claude key is present, else Gemini.
    Keys come from Streamlit secrets (safe, for deployment) or the sidebar (local test).
    """
    # Claude key?
    ck = ""
    try:
        if "ANTHROPIC_API_KEY" in st.secrets: ck = st.secrets["ANTHROPIC_API_KEY"]
    except Exception: pass
    if not ck: ck = st.session_state.get("claude_key", "")
    if ck:
        return "claude", ck
    # Gemini key?
    gk = ""
    try:
        if "GEMINI_API_KEY" in st.secrets: gk = st.secrets["GEMINI_API_KEY"]
    except Exception: pass
    if not gk: gk = st.session_state.get("gemini_key", "")
    if gk:
        return "gemini", gk
    return None, ""

def get_gemini_key():
    # kept for backward-compat; returns whatever key is available
    _, key = get_ai_provider()
    return key

def build_finance_context():
    """Compact snapshot of the user's finances for the assistant to reason over."""
    lines = []
    lines.append(f"User location: {city} (currency {CITY_DATA[city]['cur']}).")
    lines.append(f"Monthly income: {usd(mo_inc)}. Monthly expenses: {usd(mo_exp)}. "
                 f"Net per month: {usd(net)}. Savings rate: {sav_rate:.1f}%.")
    lines.append(f"Net worth: {usd(net_worth)} (assets {usd(total_assets)}, liabilities {usd(total_liabs)}). "
                 f"Debt-to-income: {dti:.1f}%. Spare cash after debt: {usd(spare)}/mo. "
                 f"Financial health score: {HS}/100 (grade {grade}).")
    if cat_tot:
        cats = ", ".join(f"{CATEGORIES.get(k,CATEGORIES['other'])['label']} {usd(v)}/mo"
                         for k,v in sorted(cat_tot.items(), key=lambda x:-x[1]))
        lines.append("Spending by category: " + cats + ".")
    if budgets:
        bd = ", ".join(f"{CATEGORIES.get(k,CATEGORIES['other'])['label']} {usd(cat_tot.get(k,0))}/{usd(v)}"
                       for k,v in budgets.items())
        lines.append("Budgets (spent/limit): " + bd + ".")
    if goals:
        gl = ", ".join(f"{g['name']} {usd(g['current'])}/{usd(g['target'])}" for g in goals)
        lines.append("Goals (current/target): " + gl + ".")
    over = [CATEGORIES[k]['label'] for k,v in budgets.items() if cat_tot.get(k,0)>v]
    if over:
        lines.append("Currently over budget in: " + ", ".join(over) + ".")
    return "\n".join(lines)

def _system_prompt():
    return (
        "You are ClearSpend's built-in financial assistant. You help the user understand and "
        "improve their personal finances. Be specific, practical and encouraging, and use THEIR "
        "actual numbers from the snapshot below. Keep answers concise (a few short paragraphs or "
        "a tight list). When relevant, give concrete steps. The user is likely in Saudi Arabia, so "
        "Saudi-specific advice (providers like STC, Tawuniya, Riyadh Metro, local shops) is welcome. "
        "You are not a licensed financial advisor; for big decisions suggest they verify independently. "
        "Do not invent numbers that aren't in the snapshot.\n\n"
        "USER FINANCIAL SNAPSHOT:\n" + build_finance_context()
    )

def ask_gemini(question, history, key):
    """Call the Gemini REST API and return the assistant's text reply."""
    sys_prompt = _system_prompt()
    contents = []
    for role, text in history[-8:]:
        contents.append({"role": "user" if role=="user" else "model",
                         "parts":[{"text":text}]})
    contents.append({"role":"user","parts":[{"text":question}]})
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEMINI_MODEL}:generateContent?key={key}")
    payload = {
        "system_instruction": {"parts":[{"text":sys_prompt}]},
        "contents": contents,
        "generationConfig": {"temperature":0.6, "maxOutputTokens":800},
    }
    r = requests.post(url, json=payload, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"Gemini API error {r.status_code}: {r.text[:200]}")
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("The assistant returned an empty response. Try rephrasing.")

def ask_claude(question, history, key):
    """Call the Anthropic Claude Messages API and return the reply text."""
    msgs = []
    for role, text in history[-8:]:
        msgs.append({"role": "user" if role=="user" else "assistant", "content": text})
    msgs.append({"role":"user","content":question})
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": CLAUDE_MODEL,
            "max_tokens": 800,
            "system": _system_prompt(),
            "messages": msgs,
        },
        timeout=30,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Claude API error {r.status_code}: {r.text[:200]}")
    data = r.json()
    try:
        # content is a list of blocks; concatenate any text blocks
        return "".join(b.get("text","") for b in data.get("content",[]) if b.get("type")=="text") \
               or "The assistant returned an empty response. Try rephrasing."
    except Exception:
        raise RuntimeError("Unexpected response from the assistant.")

def ask_ai(question, history):
    """Route to whichever provider has a key configured."""
    provider, key = get_ai_provider()
    if provider == "claude":
        return ask_claude(question, history, key)
    if provider == "gemini":
        return ask_gemini(question, history, key)
    raise RuntimeError("No API key configured.")

# ════════════════════════════════════════════════════════════════════════════
# CSS
# ════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap');

* {{ box-sizing:border-box; }}
html, body, [class*="css"], .stApp {{
  font-family:'Inter',-apple-system,sans-serif !important;
  background:{C['bg']} !important; color:{C['text']} !important;
  -webkit-font-smoothing:antialiased;
}}
#MainMenu, footer, header {{ visibility:hidden; }}
.block-container {{ padding-top:1rem !important; padding-bottom:3rem !important; max-width:1480px !important; }}

/* Sidebar */
[data-testid="stSidebar"] {{ background:{C['surface']} !important; border-right:1px solid {C['border']} !important; }}
[data-testid="stSidebar"] * {{ color:{C['text2']} !important; }}
[data-testid="stSidebarContent"] {{ padding:1.3rem 1rem; }}

/* Inputs */
input, textarea, [data-testid="stNumberInput"] input {{
  background:{C['inputBg']} !important; border:1px solid {C['inputBorder']} !important;
  border-radius:9px !important; color:{C['text']} !important; font-family:'Inter',sans-serif !important;
  font-size:.9rem !important;
}}
input:focus {{ border-color:{C['accent']} !important; box-shadow:0 0 0 3px {rgba(C['accent'],.12)} !important; }}
[data-baseweb="select"]>div {{ background:{C['inputBg']} !important; border-color:{C['inputBorder']} !important; border-radius:9px !important; }}
[data-baseweb="select"] * {{ color:{C['text']} !important; }}
[data-baseweb="popover"] {{ background:{C['surface']} !important; border:1px solid {C['border']} !important; border-radius:11px !important; box-shadow:{C['shadowLg']} !important; }}
li[role="option"] {{ background:{C['surface']} !important; color:{C['text']} !important; }}
li[role="option"]:hover {{ background:{C['surface2']} !important; }}

/* Buttons */
.stButton>button {{
  background:{C['accent']} !important; color:#fff !important; border:none !important;
  border-radius:9px !important; font-family:'Inter',sans-serif !important; font-weight:600 !important;
  font-size:.86rem !important; padding:.45rem 1rem !important; transition:all .15s ease !important;
  box-shadow:0 1px 2px {rgba(C['accent'],.25)} !important;
}}
.stButton>button:hover {{ background:{C['accent2']} !important; transform:translateY(-1px) !important; box-shadow:0 4px 14px {rgba(C['accent'],.35)} !important; }}
.stDownloadButton>button {{ background:{C['surface2']} !important; color:{C['text']} !important; border:1px solid {C['border']} !important; box-shadow:none !important; }}

/* Tabs */
[data-testid="stTabs"] [role="tablist"] {{ gap:2px; border-bottom:1px solid {C['border']} !important; }}
[data-testid="stTabs"] [role="tab"] {{
  font-family:'Inter',sans-serif !important; font-weight:600 !important; font-size:.85rem !important;
  color:{C['text3']} !important; padding:.5rem .95rem !important; border-radius:8px 8px 0 0 !important;
}}
[data-testid="stTabs"] [role="tab"]:hover {{ color:{C['text']} !important; background:{C['surface2']} !important; }}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{ color:{C['accent']} !important; background:transparent !important; border-bottom:2px solid {C['accent']} !important; }}
[data-testid="stTabPanel"] {{ padding-top:1.5rem !important; }}

/* Metric */
[data-testid="stMetric"] {{ background:{C['surface']} !important; border:1px solid {C['border']} !important; border-radius:13px !important; padding:.85rem 1rem !important; box-shadow:{C['shadow']}; }}
[data-testid="stMetricLabel"] {{ color:{C['text3']} !important; font-size:.72rem !important; font-weight:600 !important; text-transform:uppercase; letter-spacing:.04em; }}
[data-testid="stMetricValue"] {{ color:{C['text']} !important; font-weight:700 !important; font-size:1.4rem !important; }}

/* Expander */
[data-testid="stExpander"] {{ border:1px solid {C['border']} !important; border-radius:12px !important; background:{C['surface']} !important; box-shadow:{C['shadow']}; margin-bottom:8px !important; }}
details summary {{ font-weight:600 !important; color:{C['text']} !important; padding:.7rem .95rem !important; font-size:.9rem !important; }}

/* Alerts / dataframe */
[data-testid="stAlert"] {{ border-radius:11px !important; }}
[data-testid="stDataFrame"] {{ border-radius:11px !important; border:1px solid {C['border']}; }}

/* Scrollbar */
::-webkit-scrollbar {{ width:8px; height:8px; }}
::-webkit-scrollbar-thumb {{ background:{C['border2']}; border-radius:8px; }}
::-webkit-scrollbar-track {{ background:transparent; }}

/* File uploader */
[data-testid="stFileUploader"] {{ background:{C['surface2']}; border:1.5px dashed {C['border2']}; border-radius:12px; padding:.5rem; }}
[data-testid="stFileUploader"] * {{ color:{C['text2']} !important; }}

/* Slider */
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {{ background:{C['accent']} !important; }}

/* ───────── custom components ───────── */
.h-sec {{ font-size:.95rem; font-weight:700; color:{C['text']}; letter-spacing:-.01em; margin:0 0 .9rem; display:flex; align-items:center; gap:.5rem; }}
.h-sub {{ font-size:.72rem; font-weight:600; text-transform:uppercase; letter-spacing:.05em; color:{C['text3']}; margin-bottom:.5rem; }}
.card {{ background:{C['surface']}; border:1px solid {C['border']}; border-radius:15px; padding:1.2rem 1.3rem; box-shadow:{C['shadow']}; }}
.lbl {{ font-size:.68rem; font-weight:600; text-transform:uppercase; letter-spacing:.05em; color:{C['text3']}; }}
.sub {{ font-size:.76rem; color:{C['text3']}; }}
.pill {{ display:inline-flex; align-items:center; gap:4px; padding:2px 9px; border-radius:7px; font-size:.7rem; font-weight:600; }}
.mono {{ font-family:'JetBrains Mono',monospace; }}
.bar-track {{ background:{C['line']}; border-radius:6px; height:6px; overflow:hidden; }}
.bar-fill {{ height:100%; border-radius:6px; }}
.divider {{ height:1px; background:{C['line']}; margin:.4rem 0; }}
.kpi {{ background:{C['surface']}; border:1px solid {C['border']}; border-radius:15px; padding:1.05rem 1.15rem; box-shadow:{C['shadow']}; transition:all .18s ease; }}
.kpi:hover {{ box-shadow:{C['shadowLg']}; transform:translateY(-2px); border-color:{C['border2']}; }}
.row {{ display:flex; align-items:center; gap:12px; padding:.6rem .85rem; border-radius:11px; transition:background .12s; }}
.row:hover {{ background:{C['surface2']}; }}
.chip {{ background:{C['surface2']}; border:1px solid {C['border']}; border-radius:8px; padding:.2rem .55rem; font-size:.72rem; font-weight:600; color:{C['text2']}; }}
.insight {{ display:flex; gap:12px; align-items:flex-start; padding:.95rem 1.1rem; border-radius:13px; background:{C['surface']}; border:1px solid {C['border']}; box-shadow:{C['shadow']}; margin-bottom:.6rem; }}
.dot {{ width:8px; height:8px; border-radius:50%; flex-shrink:0; margin-top:6px; }}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════════════════════
nc = C["green"] if net>=0 else C["red"]
hc = C["green"] if HS>=70 else C["amber"] if HS>=50 else C["red"]
grade = "A" if HS>=85 else "B" if HS>=70 else "C" if HS>=55 else "D" if HS>=40 else "F"
hcol1, hcol2 = st.columns([6,1])
with hcol2:
    if st.button(("◐ Dark" if not DARK else "◑ Light"), key="theme", use_container_width=True):
        st.session_state.dark = not st.session_state.dark
        st.rerun()

st.markdown(f"""
<div style="display:flex;align-items:center;gap:16px;padding:1.1rem 1.5rem;background:{C['surface']};
            border:1px solid {C['border']};border-radius:18px;margin-bottom:1.1rem;box-shadow:{C['shadow']}">
  <div style="width:42px;height:42px;border-radius:12px;background:linear-gradient(135deg,{C['accent']},{C['accent2']});
              display:flex;align-items:center;justify-content:center;color:#fff;font-size:1.3rem;font-weight:800;
              box-shadow:0 4px 14px {rgba(C['accent'],.4)}">◆</div>
  <div>
    <div style="font-size:1.25rem;font-weight:800;letter-spacing:-.02em;color:{C['text']};line-height:1.1">ClearSpend</div>
    <div style="font-size:.76rem;color:{C['text3']}">Intelligent finance · {datetime.now().strftime('%A %d %B %Y')}</div>
  </div>
  <div style="margin-left:auto;display:flex;gap:0;align-items:stretch">
    <div style="text-align:right;padding:0 1.3rem;border-right:1px solid {C['border']}">
      <div class="lbl">Net / month</div>
      <div class="mono" style="font-size:1.3rem;font-weight:700;color:{nc};line-height:1.2">{usd0(net)}</div>
      <div class="sub">{sav_rate:.0f}% saved</div>
    </div>
    <div style="text-align:right;padding:0 1.3rem;border-right:1px solid {C['border']}">
      <div class="lbl">Net worth</div>
      <div class="mono" style="font-size:1.3rem;font-weight:700;color:{C['accent']};line-height:1.2">{kfmt(net_worth)}</div>
      <div class="sub">{kfmt(total_assets)} − {kfmt(total_liabs)}</div>
    </div>
    <div style="text-align:right;padding:0 0 0 1.3rem">
      <div class="lbl">Health</div>
      <div class="mono" style="font-size:1.3rem;font-weight:700;color:{hc};line-height:1.2">{HS} · {grade}</div>
      <div class="sub">{CITY_DATA[city]['flag']} {city}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR — quick add + city + actions
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"<div style='font-weight:700;font-size:1rem;color:{C['text']};margin-bottom:.8rem'>Quick add</div>", unsafe_allow_html=True)
    e_type = st.selectbox("Type", ["expense","income"], format_func=lambda x:"Expense" if x=="expense" else "Income")
    e_name = st.text_input("Description", placeholder="e.g. Talabat, Salary…")
    auto = detect_category(e_name, e_type) if e_name.strip() else ("income" if e_type=="income" else "other")
    ck = list(CATEGORIES.keys())
    e_cat = ck[st.selectbox("Category", range(len(ck)), index=ck.index(auto),
              format_func=lambda i:f"{CATEGORIES[ck[i]]['emoji']} {CATEGORIES[ck[i]]['label']}")]
    e_amt = st.number_input("Amount ($)", min_value=0.0, step=1.0, format="%.2f")
    e_pt  = st.selectbox("Frequency", list(PAYMENT_TYPES.keys()), format_func=lambda k:PAYMENT_TYPES[k]["label"])
    e_date= st.date_input("Date", value=date.today())
    e_note= st.text_input("Note", placeholder="Optional")
    e_goal=None
    if e_cat in ("goal","savings") and goals:
        gn = ["None"]+[g["name"] for g in goals]
        gi = st.selectbox("Link to goal", range(len(gn)), format_func=lambda i:gn[i])
        e_goal = gn[gi] if gi>0 else None
    if st.button("Add transaction", use_container_width=True):
        if e_name.strip() and e_amt>0:
            entries.append({"id":max((x["id"] for x in entries),default=0)+1,"name":e_name.strip(),
                "amount":float(e_amt),"type":e_type,"ptype":e_pt,"category":e_cat,
                "date":str(e_date),"note":e_note,"linked_goal":e_goal})
            if e_goal and e_type=="expense":
                for g in goals:
                    if g["name"]==e_goal: g["current"]=g.get("current",0)+float(e_amt)
            save(D); st.rerun()
        else:
            st.error("Need a description and amount.")

    st.markdown(f"<div style='height:1px;background:{C['border']};margin:1rem 0'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='h-sub'>Location</div>", unsafe_allow_html=True)
    cc = st.selectbox("City", list(CITY_DATA.keys()), index=list(CITY_DATA.keys()).index(city),
                      format_func=lambda c:f"{CITY_DATA[c]['flag']}  {c}", label_visibility="collapsed")
    if cc!=city: D["city"]=cc; save(D); st.rerun()

    cols = st.columns(2)
    with cols[0]:
        if st.button("Save", use_container_width=True): save(D); st.toast("Saved")
    with cols[1]:
        if st.button("Reset", use_container_width=True):
            if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
            st.session_state.data = load(); st.rerun()

    # AI assistant key (only needed if deploying without Streamlit secrets)
    if not get_ai_provider()[1]:
        st.markdown(f"<div style='height:1px;background:{C['border']};margin:1rem 0'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='h-sub'>AI assistant key</div>", unsafe_allow_html=True)
        which = st.radio("Provider", ["Claude","Gemini"], horizontal=True, label_visibility="collapsed")
        typed = st.text_input("API key", type="password", label_visibility="collapsed",
                              placeholder=f"Paste {which} key (local testing)")
        if typed:
            st.session_state["claude_key" if which=="Claude" else "gemini_key"] = typed
            st.rerun()
        st.markdown(f"<div class='sub'>Claude key from console.anthropic.com, or free Gemini key from aistudio.google.com. For your deployed app, set it in Secrets instead.</div>", unsafe_allow_html=True)
# ════════════════════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════════════════════
TABS = st.tabs(["Overview","Analytics","Insights","Assistant","Save Smart","Transactions","Budgets",
                "Invest","Live Markets","Net Worth","Import","Report"])
tOver,tAna,tIns,tAsk,tSave,tTxn,tBud,tInv,tLive,tNW,tImp,tRep = TABS

def kpi(col, label, value, sub, color, spark=None):
    spark_html = f'<div style="margin-top:.4rem">{spark}</div>' if spark else ""
    col.markdown(f"""<div class="kpi">
      <div class="lbl">{label}</div>
      <div class="mono" style="font-size:1.5rem;font-weight:700;color:{color};line-height:1.25">{value}</div>
      <div class="sub">{sub}</div>{spark_html}</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
with tOver:
    k = st.columns(4)
    daily = list(daily_series(14).values())
    kpi(k[0], "Income / mo", usd0(mo_inc), f"{len(inc_e)} sources", C["green"])
    kpi(k[1], "Expenses / mo", usd0(mo_exp), f"{len(exp_e)} transactions", C["red"],
        svg_sparkline(daily, C["red"]))
    kpi(k[2], "Net / mo", usd0(net), f"{sav_rate:.0f}% savings rate", nc)
    kpi(k[3], "Spare cash", usd0(spare), "after debt payments", C["accent"])

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    L, R = st.columns([1.55,1], gap="medium")

    with L:
        # Spending trend
        st.markdown(f"<div class='card'>", unsafe_allow_html=True)
        hist = monthly_history(6)
        pred, slope = forecast_next_month()
        labels = [m for m,_ in hist] + ["next"]
        vals   = [v for _,v in hist] + [pred]
        trend_color = C["red"] if slope>0 else C["green"]
        st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.3rem">
          <div class="h-sec" style="margin:0">Spending trend & forecast</div>
          <span class="pill" style="background:{rgba(trend_color,.12)};color:{trend_color}">
            {'▲' if slope>0 else '▼'} next ≈ {usd0(pred)}</span></div>""", unsafe_allow_html=True)
        series = [("spend", vals[:-1], C["accent"])]
        # forecast as dashed continuation: draw separate light line
        st.markdown(svg_area_line([("spend", vals, C["accent"])], labels, width=620, height=210, show_dots=True), unsafe_allow_html=True)
        st.markdown(f"<div class='sub' style='margin-top:-.3rem'>Last 6 months of total spend with a linear-trend projection for next month.</div></div>", unsafe_allow_html=True)

        st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)

        # Category breakdown
        st.markdown(f"<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='h-sec'>Where your money goes</div>", unsafe_allow_html=True)
        dc1, dc2 = st.columns([1,1.3])
        ordered = sorted(cat_tot.items(), key=lambda x:x[1], reverse=True)
        with dc1:
            slices = [(v, CATEGORIES.get(kk,CATEGORIES['other'])['color'], kk) for kk,v in ordered]
            st.markdown(svg_donut(slices, 168, 24, kfmt(mo_exp), "PER MONTH"), unsafe_allow_html=True)
        with dc2:
            for kk, v in ordered[:6]:
                cat = CATEGORIES.get(kk, CATEGORIES['other'])
                share = pct(v, mo_exp)
                st.markdown(f"""<div style="margin-bottom:.55rem">
                  <div style="display:flex;justify-content:space-between;font-size:.82rem;margin-bottom:3px">
                    <span style="font-weight:600">{cat['emoji']} {cat['label']}</span>
                    <span class="mono" style="color:{cat['color']};font-weight:600">{usd0(v)}</span>
                  </div>
                  <div class="bar-track"><div class="bar-fill" style="width:{min(share,100):.0f}%;background:{cat['color']}"></div></div>
                </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with R:
        # Health ring + sub-scores
        st.markdown(f"<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='h-sec'>Financial health</div>", unsafe_allow_html=True)
        rc1, rc2 = st.columns([1.1,1])
        with rc1:
            st.markdown(svg_ring(HS, hc, "Score", size=140), unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:center;margin-top:-.3rem'><span style='font-size:1.4rem;font-weight:800;color:{hc}'>Grade {grade}</span></div>", unsafe_allow_html=True)
        with rc2:
            inv_s = min(100, int(mo_savings/max(mo_inc,1)*500))
            dti_s = max(0, 100-int(dti*2))
            st.markdown(svg_ring(inv_s, C["cyan"], "Invest", size=92, stroke=8), unsafe_allow_html=True)
            st.markdown(svg_ring(dti_s, C["amber"], "Debt", size=92, stroke=8), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)

        # 50/30/20
        st.markdown(f"<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='h-sec'>50 / 30 / 20 rule</div>", unsafe_allow_html=True)
        if mo_inc>0:
            needs = pct(sum(cat_tot.get(c,0) for c in NEEDS_CATS), mo_inc)
            wants = pct(sum(cat_tot.get(c,0) for c in WANTS_CATS), mo_inc)
            for lab, val, tgt, col in [("Needs",needs,50,C["blue"]),("Wants",wants,30,C["purple"]),("Savings",sav_rate,20,C["green"])]:
                ok = (lab=="Savings" and val>=tgt) or (lab!="Savings" and val<=tgt)
                st.markdown(f"""<div style="margin-bottom:.5rem">
                  <div style="display:flex;justify-content:space-between;font-size:.8rem;margin-bottom:3px">
                    <span>{'✓' if ok else '!'} {lab} <span style='color:{C["text3"]}'>· target {tgt}%</span></span>
                    <span class="mono" style="font-weight:600;color:{col}">{val:.0f}%</span></div>
                  <div class="bar-track"><div class="bar-fill" style="width:{min(val,100):.0f}%;background:{col}"></div></div>
                </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)

        # Goals snapshot
        st.markdown(f"<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='h-sec'>Goals</div>", unsafe_allow_html=True)
        for g in goals[:3]:
            pr = min(100, pct(g["current"], g["target"]))
            mc = goal_monthly.get(g["name"],0)
            badge = f"<span class='chip' style='font-size:.66rem'>+{usd0(mc)}/mo</span>" if mc>0 else ""
            st.markdown(f"""<div style="margin-bottom:.6rem">
              <div style="display:flex;justify-content:space-between;font-size:.8rem;margin-bottom:3px">
                <span style="font-weight:600">{g['icon']} {g['name']} {badge}</span>
                <span class="mono" style="font-weight:600;color:{C['accent']}">{pr:.0f}%</span></div>
              <div class="bar-track"><div class="bar-fill" style="width:{pr:.0f}%;background:linear-gradient(90deg,{C['accent']},{C['accent2']})"></div></div>
              <div class="sub" style="margin-top:2px">{usd0(g['current'])} of {usd0(g['target'])}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────
with tAna:
    st.markdown(f"<div class='h-sec'>Spending analytics</div>", unsafe_allow_html=True)

    a = st.columns(4)
    pred, slope = forecast_next_month()
    avg_daily = mo_exp/30.44
    biggest = max(cat_tot.items(), key=lambda x:x[1]) if cat_tot else ("—",0)
    kpi(a[0], "Forecast next mo", usd0(pred), f"{'rising' if slope>0 else 'falling'} trend", C["accent"])
    kpi(a[1], "Avg daily spend", usd(avg_daily), "across the month", C["amber"])
    kpi(a[2], "Top category", CATEGORIES.get(biggest[0],CATEGORIES['other'])['label'], usd0(biggest[1])+"/mo", C["blue"])
    kpi(a[3], "Variable vs fixed", f"{pct(sum(e['amount'] for e in exp_e if e['ptype'] in ('single','daily')), mo_exp):.0f}%", "is one-off spending", C["purple"])

    st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)
    g1, g2 = st.columns([1,1], gap="medium")

    with g1:
        st.markdown(f"<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='h-sec'>Daily spend — last 30 days</div>", unsafe_allow_html=True)
        ds = daily_series(30)
        vals = list(ds.values())
        labels = [datetime.fromisoformat(k).strftime("%d") for k in ds.keys()]
        st.markdown(svg_bars(vals, labels, C["accent"], width=560, height=200), unsafe_allow_html=True)
        st.markdown(f"<div class='sub'>Total {usd0(sum(vals))} over 30 days · peak day {usd0(max(vals) if vals else 0)}</div></div>", unsafe_allow_html=True)

    with g2:
        st.markdown(f"<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='h-sec'>Category trends — 6 months</div>", unsafe_allow_html=True)
        for kk, v in sorted(cat_tot.items(), key=lambda x:x[1], reverse=True)[:6]:
            cat = CATEGORIES.get(kk, CATEGORIES['other'])
            tr = category_trend(kk, 6)
            change = pct(tr[-1]-tr[0], tr[0]) if tr[0] else 0
            chg_col = C["red"] if change>3 else C["green"] if change<-3 else C["text3"]
            chg_txt = f"{'+' if change>0 else ''}{change:.0f}%"
            st.markdown(f"""<div style="display:flex;align-items:center;gap:10px;padding:.4rem 0;border-bottom:1px solid {C['line']}">
              <span style="font-size:.82rem;font-weight:600;width:118px">{cat['emoji']} {cat['label']}</span>
              <span style="flex:1">{svg_sparkline(tr, cat['color'], width=120, height=30)}</span>
              <span class="mono" style="font-size:.8rem;font-weight:600;width:62px;text-align:right">{usd0(v)}</span>
              <span class="pill" style="background:{rgba(chg_col,.12)};color:{chg_col};width:50px;justify-content:center">{chg_txt}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)

    # Calendar heatmap
    st.markdown(f"<div class='card'>", unsafe_allow_html=True)
    cset = st.columns([1,1,3])
    today = date.today()
    with cset[0]:
        cyear = st.number_input("Year", 2020, 2030, today.year, key="ana_y")
    with cset[1]:
        mnames = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        cmonth = st.selectbox("Month", range(1,13), index=today.month-1, format_func=lambda m:mnames[m-1], key="ana_m")
    sbd = defaultdict(float); gdays=[]
    for e in exp_e:
        try:
            dt = datetime.strptime(e["date"],"%Y-%m-%d")
            if dt.year==int(cyear) and dt.month==int(cmonth):
                sbd[dt.day]+=e["amount"]
                if e.get("linked_goal"): gdays.append(dt.day)
        except: pass
    st.markdown(f"<div class='h-sec'>Spending calendar — {mnames[int(cmonth)-1]} {int(cyear)}</div>", unsafe_allow_html=True)
    st.markdown(svg_heatcal(sbd, gdays, int(cyear), int(cmonth)), unsafe_allow_html=True)
    mtot = sum(sbd.values())
    st.markdown(f"""<div style="display:flex;gap:20px;margin-top:.5rem">
      <span class="sub">Month total: <b style='color:{C['text']}'>{usd0(mtot)}</b></span>
      <span class="sub">Active days: <b style='color:{C['text']}'>{len(sbd)}</b></span>
      <span class="sub"><span style='color:{C['purple']}'>●</span> goal contribution</span>
    </div></div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# INSIGHTS
# ─────────────────────────────────────────────────────────────────────────────
with tIns:
    st.markdown(f"<div class='h-sec'>Smart insights</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub' style='margin-top:-.6rem;margin-bottom:1rem'>Automatically generated from your data — trends, anomalies, and opportunities.</div>", unsafe_allow_html=True)
    ins = smart_insights()
    if not ins:
        st.success("Nothing flagged — your finances look balanced.")
    for icon, color, title, desc in ins:
        st.markdown(f"""<div class="insight">
          <div class="dot" style="background:{color}"></div>
          <div><div style="font-weight:700;font-size:.92rem;color:{C['text']};margin-bottom:2px">{title}</div>
          <div style="font-size:.85rem;color:{C['text2']};line-height:1.5">{desc}</div></div>
        </div>""", unsafe_allow_html=True)

    # Recurring detection
    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='h-sec'>Recurring & subscriptions</div>", unsafe_allow_html=True)
    rec = detect_recurring()
    if rec:
        rec_total = sum(r["monthly"] for r in rec)
        st.markdown(f"<div class='sub' style='margin-top:-.6rem;margin-bottom:.7rem'>Detected {len(rec)} recurring items totalling <b style='color:{C['text']}'>{usd0(rec_total)}/mo</b> ({usd0(rec_total*12)}/yr).</div>", unsafe_allow_html=True)
        cols = st.columns(3)
        for i, rr in enumerate(rec[:9]):
            cat = CATEGORIES.get(rr["category"], CATEGORIES['other'])
            with cols[i%3]:
                st.markdown(f"""<div class="card" style="padding:.85rem 1rem;margin-bottom:.6rem">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-weight:600;font-size:.85rem">{cat['emoji']} {rr['name'][:18]}</span>
                    <span class="mono" style="font-weight:700;color:{cat['color']}">{usd0(rr['monthly'])}</span>
                  </div>
                  <div class="sub" style="margin-top:3px">{rr['type']} · {usd0(rr['monthly']*12)}/yr</div>
                </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ASSISTANT  —  Gemini-powered financial chat
# ─────────────────────────────────────────────────────────────────────────────
with tAsk:
    provider, key = get_ai_provider()
    prov_name = {"claude":"Anthropic Claude","gemini":"Google Gemini"}.get(provider, "")
    st.markdown(f"<div class='h-sec'>AI assistant</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub' style='margin-top:-.6rem;margin-bottom:1rem'>Ask anything about your money. The assistant reads your actual ClearSpend data — income, spending, budgets, goals, net worth — and answers with advice specific to you."
                + (f" Powered by {prov_name}." if prov_name else "") + "</div>", unsafe_allow_html=True)

    if "chat" not in st.session_state:
        st.session_state.chat = []

    if not key:
        st.warning("No AI key found. Add a key in the sidebar (for local testing), or set "
                   "ANTHROPIC_API_KEY (Claude) or GEMINI_API_KEY (Gemini) in your deployed app's Secrets.")
    elif not internet_status():
        st.error("The assistant needs an internet connection. Connect to WiFi and try again.")
    else:
        # Suggested starter questions
        st.markdown(f"<div class='h-sub'>Try asking</div>", unsafe_allow_html=True)
        sugg = ["Analyse my spending and tell me where I'm overspending",
                "Where can I save the most money each month?",
                "How healthy are my finances right now?",
                "How long until I reach my goals at this rate?"]
        qcols = st.columns(2)
        clicked = None
        for i,q in enumerate(sugg):
            if qcols[i%2].button(q, key=f"sugg{i}", use_container_width=True):
                clicked = q

        # Render chat history
        st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
        for role, text in st.session_state.chat:
            if role=="user":
                st.markdown(f"""<div style="display:flex;justify-content:flex-end;margin-bottom:.5rem">
                  <div style="max-width:80%;background:{C['accent']};color:#fff;padding:.6rem .9rem;
                       border-radius:14px 14px 4px 14px;font-size:.88rem;line-height:1.5">{text}</div></div>""",
                  unsafe_allow_html=True)
            else:
                safe = text.replace("\n","<br>")
                st.markdown(f"""<div style="display:flex;justify-content:flex-start;margin-bottom:.5rem">
                  <div style="max-width:85%;background:{C['surface']};border:1px solid {C['border']};
                       color:{C['text']};padding:.6rem .9rem;border-radius:14px 14px 14px 4px;
                       font-size:.88rem;line-height:1.55;box-shadow:{C['shadow']}">{safe}</div></div>""",
                  unsafe_allow_html=True)

        # Input
        typed_q = st.chat_input("Ask the assistant about your finances…")
        question = clicked or typed_q

        if question:
            st.session_state.chat.append(("user", question))
            try:
                with st.spinner("Thinking…"):
                    reply = ask_ai(question, st.session_state.chat[:-1])
                st.session_state.chat.append(("model", reply))
            except Exception as ex:
                msg = str(ex)
                if "429" in msg:
                    friendly = "The assistant is busy (free usage limit reached for now). Try again in a minute."
                elif "API key" in msg or "403" in msg or "400" in msg:
                    friendly = "There's a problem with the API key. Check it's valid and active in Google AI Studio."
                else:
                    friendly = "Couldn't reach the assistant — check your internet connection and try again."
                st.session_state.chat.append(("model", friendly))
            st.rerun()

        if st.session_state.chat:
            if st.button("Clear conversation"):
                st.session_state.chat = []
                st.rerun()

    st.markdown(f"<div class='sub' style='margin-top:1rem'>The assistant is for educational guidance, not licensed financial advice. Verify important decisions independently.</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SAVE SMART  —  Saudi-specific money-saving guide
# ─────────────────────────────────────────────────────────────────────────────
with tSave:
    st.markdown(f"<div class='h-sec'>Save Smart — local money guide</div>", unsafe_allow_html=True)
    if not saudi_savings_for_city():
        st.info(f"This guide is tailored for Saudi Arabia. You've selected {CITY_DATA[city]['flag']} {city}. "
                f"Switch your city to a Saudi one (Riyadh, Jeddah, Makkah) in the sidebar to see local providers and prices.")
    else:
        st.markdown(f"<div class='sub' style='margin-top:-.6rem;margin-bottom:1rem'>Real cheaper alternatives and saving tips for everyday costs in Saudi Arabia. "
                    f"Prices are indicative ranges in SAR — verify current rates before acting. "
                    f"Items are ordered by how much you currently spend in each area.</div>", unsafe_allow_html=True)

        ranked = relevant_savings()
        total_save_sar = sum(item.get("save_est",0) for _,_,item in ranked)
        # Top summary
        sm = st.columns(3)
        kpi(sm[0],"Guide areas",str(len(SAUDI_SAVINGS)),"everyday costs covered",C["accent"])
        kpi(sm[1],"Potential saving","~"+usd0(total_save_sar/SAR),f"≈ SAR {total_save_sar:,.0f}/mo if optimised",C["green"])
        kpi(sm[2],"Biggest lever",SAUDI_SAVINGS[ranked[0][1]]["label"] if ranked else "—",
            f"you spend {usd0(ranked[0][0])}/mo here" if ranked and ranked[0][0]>0 else "start logging expenses",C["amber"])

        st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

        # Category filter
        topic_keys = [k for _,k,_ in ranked]
        fcol = st.columns([2,3])
        choice = fcol[0].selectbox("Jump to a cost", ["All areas"]+[SAUDI_SAVINGS[k]["label"] for k in topic_keys])

        tagcol = {"Cheapest":C["green"],"Value":C["cyan"],"Popular":C["blue"],"Standard":C["amber"],
                  "Mid":C["amber"],"Premium":C["red"],"Costly":C["red"]}

        for spend, key, item in ranked:
            if choice != "All areas" and item["label"] != choice:
                continue
            cat = item.get("maps")
            spend_badge = (f"<span class='chip' style='color:{C['accent']};border-color:{rgba(C['accent'],.3)}'>"
                           f"you spend {usd0(spend)}/mo</span>") if cat and spend>0 else ""
            with st.expander(f"{item['emoji']}  {item['label']}", expanded=(choice!='All areas')):
                st.markdown(f"<div style='margin-bottom:.3rem'>{spend_badge}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:.88rem;color:{C['text2']};line-height:1.55;margin-bottom:.8rem'>{item['intro']}</div>", unsafe_allow_html=True)

                # Options comparison (cheapest → premium)
                st.markdown(f"<div class='h-sub'>Options · {item['unit']}</div>", unsafe_allow_html=True)
                for opt in item["options"]:
                    lo,hi = opt["price"]
                    if lo==0 and hi==0:
                        price_txt = "—"
                    elif lo==hi:
                        price_txt = f"SAR {lo:g}"
                    else:
                        price_txt = f"SAR {lo:,.0f}–{hi:,.0f}"
                    tc_ = tagcol.get(opt["tag"], C["text3"])
                    st.markdown(f"""<div class="row" style="padding:.55rem .75rem;border:1px solid {C['border']};border-radius:11px;margin-bottom:.4rem">
                      <span class="pill" style="background:{rgba(tc_,.13)};color:{tc_};min-width:74px;justify-content:center">{opt['tag']}</span>
                      <div style="flex:1">
                        <div style="font-weight:600;font-size:.85rem">{opt['name']}</div>
                        <div class="sub">{opt['note']}</div>
                      </div>
                      <span class="mono" style="font-weight:700;color:{C['text']};white-space:nowrap">{price_txt}</span>
                    </div>""", unsafe_allow_html=True)

                # Tips
                st.markdown(f"<div class='h-sub' style='margin-top:.6rem'>How to save</div>", unsafe_allow_html=True)
                for tip in item["tips"]:
                    st.markdown(f"<div style='display:flex;gap:9px;align-items:flex-start;padding:3px 0;font-size:.85rem;color:{C['text2']}'>"
                                f"<span style='color:{C['green']};flex-shrink:0'>✓</span><span>{tip}</span></div>", unsafe_allow_html=True)

                if item.get("save_est"):
                    st.markdown(f"""<div style="margin-top:.7rem;padding:.6rem .9rem;border-radius:10px;
                        background:{rgba(C['green'],.08)};border:1px solid {rgba(C['green'],.25)}">
                        <span class="lbl" style="color:{C['green']}">Indicative saving</span>
                        <span style="font-weight:700;color:{C['green']};margin-left:6px">~SAR {item['save_est']:,.0f}/mo</span>
                        <span class="sub" style="margin-left:6px">(≈ {usd0(item['save_est']/SAR)}/mo · {usd0(item['save_est']*12/SAR)}/yr) if you switch to a cheaper option</span>
                    </div>""", unsafe_allow_html=True)

        st.markdown(f"<div class='sub' style='margin-top:1rem'>Disclaimer: prices are realistic indicative ranges for guidance, not live quotes, and vary by provider, car, location and time. "
                    f"Always confirm current pricing before making a decision.</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TRANSACTIONS
# ─────────────────────────────────────────────────────────────────────────────
with tTxn:
    with st.expander("Manage goals", expanded=False):
        with st.form("goalform"):
            gc = st.columns([2,1.3,1.3,1,1.4])
            gn  = gc[0].text_input("Goal name", placeholder="Emergency Fund")
            gt  = gc[1].number_input("Target $", min_value=0.0, step=100.0)
            gcur= gc[2].number_input("Current $", min_value=0.0, step=100.0)
            gic = gc[3].selectbox("Icon", range(len(GOAL_ICONS)), format_func=lambda i:GOAL_ICONS[i])
            gdl = gc[4].date_input("Deadline", value=date.today()+timedelta(days=180))
            an = ["None"]+[a["name"] for a in assets]
            gai = st.selectbox("Link to asset (auto-syncs progress)", range(len(an)), format_func=lambda i:an[i])
            if st.form_submit_button("Add goal"):
                if gn.strip() and gt>0:
                    goals.append({"id":max((g["id"] for g in goals),default=0)+1,"name":gn.strip(),
                        "target":float(gt),"current":float(gcur),"icon":GOAL_ICONS[gic],
                        "deadline":str(gdl),"linked_asset":(an[gai] if gai>0 else None)})
                    save(D); st.rerun()
        for g in goals:
            if g.get("linked_asset"):
                la = next((a for a in assets if a["name"]==g["linked_asset"]), None)
                if la: g["current"]=la["value"]
            pr = min(100, pct(g["current"],g["target"]))
            left = max(0, g["target"]-g["current"])
            mc = goal_monthly.get(g["name"],0)
            try: dleft=f"{(datetime.strptime(g['deadline'],'%Y-%m-%d').date()-date.today()).days}d left"
            except: dleft=""
            eta = f"~{math.ceil(left/mc)}mo at current pace" if mc>0 and left>0 else ("reached" if left<=0 else "no linked contributions")
            pc = C["green"] if pr>=75 else C["amber"] if pr>=40 else C["red"]
            cols = st.columns([6,1])
            cols[0].markdown(f"""<div style="padding:.4rem 0">
              <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                <span style="font-weight:600">{g['icon']} {g['name']} <span class='sub'>· {dleft}</span></span>
                <span class="mono" style="font-weight:700;color:{pc}">{pr:.0f}%</span></div>
              <div class="bar-track"><div class="bar-fill" style="width:{pr:.0f}%;background:linear-gradient(90deg,{C['accent']},{C['accent2']})"></div></div>
              <div class="sub" style="margin-top:3px">{usd0(g['current'])} / {usd0(g['target'])} · {usd0(left)} to go · {eta}</div>
            </div>""", unsafe_allow_html=True)
            if cols[1].button("✕", key=f"gdel{g['id']}"):
                goals[:]=[x for x in goals if x["id"]!=g["id"]]; save(D); st.rerun()

    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
    f = st.columns([1.1,1.6,1.1,1.1])
    ft = f[0].selectbox("Type",["all","income","expense"],format_func=lambda x:x.title())
    allc=["all"]+list(CATEGORIES.keys())
    fc = f[1].selectbox("Category",allc,format_func=lambda x:"All" if x=="all" else f"{CATEGORIES[x]['emoji']} {CATEGORIES[x]['label']}")
    fs = f[2].selectbox("Sort",["date","amount","name"],format_func=str.title)
    fo = f[3].selectbox("Order",["desc","asc"],format_func=lambda x:"High → low" if x=="desc" else "Low → high")
    fil=[e for e in entries if (ft=="all" or e["type"]==ft) and (fc=="all" or e["category"]==fc)]
    fil.sort(key={"date":lambda x:x["date"],"amount":lambda x:x["amount"],"name":lambda x:x["name"].lower()}[fs], reverse=(fo=="desc"))
    st.markdown(f"<div class='sub' style='margin:.4rem 0'>{len(fil)} transactions</div>", unsafe_allow_html=True)

    for e in fil:
        cat=CATEGORIES.get(e["category"],CATEGORIES['other']); pt=PAYMENT_TYPES.get(e["ptype"])
        ac = C["green"] if e["type"]=="income" else C["text"]
        sign="+" if e["type"]=="income" else "−"
        gb=f"<span class='chip' style='color:{C['purple']};border-color:{rgba(C['purple'],.3)}'>🎯 {e['linked_goal']}</span>" if e.get("linked_goal") else ""
        c = st.columns([3.2,1.4,1.2,1.5,.4])
        c[0].markdown(f"""<div class="row" style="padding:.5rem 0">
          <div style="width:30px;height:30px;border-radius:9px;background:{rgba(cat['color'],.13)};display:flex;align-items:center;justify-content:center;font-size:.95rem">{cat['emoji']}</div>
          <div><div style="font-weight:600;font-size:.86rem">{e['name']} {gb}</div>
          <div class="sub">{e['date']}{' · '+e['note'] if e['note'] else ''}</div></div></div>""", unsafe_allow_html=True)
        c[1].markdown(f"<div style='padding-top:.7rem'><span class='pill' style='background:{rgba(cat['color'],.12)};color:{cat['color']}'>{cat['label']}</span></div>", unsafe_allow_html=True)
        c[2].markdown(f"<div style='padding-top:.7rem'><span class='chip'>{pt['label']}</span></div>", unsafe_allow_html=True)
        moq = f"<div class='sub'>{usd(monthly_eq(e['amount'],e['ptype']))}/mo</div>" if e["ptype"] not in ("monthly","single") else ""
        c[3].markdown(f"<div style='text-align:right;padding-top:.6rem'><span class='mono' style='font-weight:700;color:{ac}'>{sign}{usd(e['amount'])}</span>{moq}</div>", unsafe_allow_html=True)
        if c[4].button("✕", key=f"del{e['id']}"):
            entries[:]=[x for x in entries if x["id"]!=e["id"]]; save(D); st.rerun()
        st.markdown(f"<div class='divider'></div>", unsafe_allow_html=True)

    if fil:
        df=pd.DataFrame([{"Name":e["name"],"Type":e["type"],"Amount":e["amount"],
          "Frequency":PAYMENT_TYPES[e["ptype"]]["label"],"Monthly":round(monthly_eq(e["amount"],e["ptype"]),2),
          "Category":CATEGORIES.get(e["category"],CATEGORIES['other'])["label"],"Date":e["date"],
          "Goal":e.get("linked_goal") or "","Note":e["note"]} for e in fil])
        st.download_button("Export CSV", df.to_csv(index=False), "clearspend_transactions.csv","text/csv")

# ─────────────────────────────────────────────────────────────────────────────
# BUDGETS
# ─────────────────────────────────────────────────────────────────────────────
with tBud:
    st.markdown(f"<div class='h-sec'>Category budgets & alerts</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub' style='margin-top:-.6rem;margin-bottom:1rem'>Set a monthly limit per category. ClearSpend warns you as you approach or exceed it.</div>", unsafe_allow_html=True)

    with st.expander("Set or update a budget"):
        bc = st.columns([2,1.3,1])
        budgetable = [k for k in CATEGORIES if k not in ("income","goal","transfer","other")]
        bk = bc[0].selectbox("Category", budgetable, format_func=lambda k:f"{CATEGORIES[k]['emoji']} {CATEGORIES[k]['label']}")
        bv = bc[1].number_input("Monthly limit $", min_value=0.0, step=10.0, value=float(budgets.get(bk,100)))
        bc[2].markdown("<div style='height:1.7rem'></div>", unsafe_allow_html=True)
        if bc[2].button("Save budget"):
            budgets[bk]=float(bv); save(D); st.rerun()

    over_ct = sum(1 for k,v in budgets.items() if cat_tot.get(k,0)>v)
    near_ct = sum(1 for k,v in budgets.items() if v*0.8<=cat_tot.get(k,0)<=v)
    bm = st.columns(3)
    kpi(bm[0], "Budgets set", str(len(budgets)), "active categories", C["accent"])
    kpi(bm[1], "Over limit", str(over_ct), "need attention", C["red"] if over_ct else C["green"])
    kpi(bm[2], "Near limit", str(near_ct), "within 80–100%", C["amber"])

    st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)
    for k, lim in sorted(budgets.items(), key=lambda x:-pct(cat_tot.get(x[0],0),x[1] or 1)):
        cat = CATEGORIES.get(k, CATEGORIES['other'])
        cur = cat_tot.get(k,0)
        ratio = pct(cur, lim)
        status_col = C["red"] if ratio>100 else C["amber"] if ratio>=80 else C["green"]
        status = "Over budget" if ratio>100 else "Near limit" if ratio>=80 else "On track"
        cc = st.columns([6,1])
        cc[0].markdown(f"""<div class="card" style="padding:.85rem 1.1rem;margin-bottom:.5rem">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <span style="font-weight:600;font-size:.88rem">{cat['emoji']} {cat['label']}
              <span class="pill" style="background:{rgba(status_col,.13)};color:{status_col};margin-left:6px">{status}</span></span>
            <span class="mono" style="font-size:.85rem"><b style="color:{status_col}">{usd0(cur)}</b> <span style="color:{C['text3']}">/ {usd0(lim)}</span></span>
          </div>
          <div class="bar-track" style="height:8px"><div class="bar-fill" style="width:{min(ratio,100):.0f}%;background:{status_col}"></div></div>
          <div class="sub" style="margin-top:4px">{ratio:.0f}% used · {usd0(abs(lim-cur))} {'over' if cur>lim else 'remaining'}</div>
        </div>""", unsafe_allow_html=True)
        if cc[1].button("✕", key=f"bdel{k}"):
            del budgets[k]; save(D); st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# INVEST
# ─────────────────────────────────────────────────────────────────────────────
with tInv:
    iv = st.columns(4)
    kpi(iv[0], "Spare / mo", usd0(spare), "after expenses & debt", C["green"])
    kpi(iv[1], "Already investing", usd0(mo_savings), "savings entries", C["cyan"])
    kpi(iv[2], "Goal contributions", usd0(mo_goals), "toward goals", C["purple"])
    kpi(iv[3], "Portfolio", usd0(portfolio_val), f"{len(portfolio_assets)} assets", C["accent"])

    st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)
    sc = st.columns(3)
    risk = sc[0].selectbox("Risk tolerance", ["Low","Medium","High"], index=1)
    horizon = sc[1].slider("Horizon (years)", 1, 30, 10)
    extra = sc[2].number_input("Extra monthly to invest $", min_value=0.0,
              value=float(max(round(spare-mo_savings,0),0)*0.8), step=10.0)
    total_inv = mo_savings + extra

    sugg = investment_suggestions(extra, horizon, risk)
    if spare<=0:
        st.warning("Your monthly balance is zero or negative. Reduce expenses before investing.")
    elif sugg:
        st.markdown(f"<div class='h-sec'>Recommended allocation</div>", unsafe_allow_html=True)
        total_rec = sum(s.get("recommended_monthly",0) for s in sugg)
        for s in sugg:
            col = s["color"]; mo_s = s.get("recommended_monthly",0)
            alloc = pct(mo_s, total_rec)
            proj = s.get("projected") or (mo_s*12*(((1.07**horizon)-1)/0.07) if mo_s>0 else 0)
            with st.expander(f"{s['icon']}  {s['name']}  ·  {alloc:.0f}%  ·  {usd0(mo_s)}/mo", expanded=(s["priority"]==1)):
                ec = st.columns([3,1.2])
                with ec[0]:
                    st.markdown(f"""<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px">
                      <span class="pill" style="background:{rgba(col,.12)};color:{col}">⏱ {s['time_horizon']}</span>
                      <span class="pill" style="background:{rgba(C['green'],.12)};color:{C['green']}">↑ {s['expected_return']}</span>
                      <span class="pill" style="background:{rgba(C['red'],.1)};color:{C['red']}">Risk: {s['risk']}</span></div>
                      <div style="font-size:.86rem;color:{C['text2']};line-height:1.55;margin-bottom:8px">{s['description']}</div>
                      <div class="h-sub">Where to start</div>
                      {"".join(f"<div style='font-size:.82rem;color:{C['text2']};padding:2px 0'>› {pl}</div>" for pl in s.get('platforms',[]))}
                    """, unsafe_allow_html=True)
                with ec[1]:
                    st.markdown(f"""<div class="card" style="text-align:center;background:{C['surface2']}">
                      <div class="lbl">Monthly</div>
                      <div class="mono" style="font-size:1.35rem;font-weight:700;color:{col}">{usd0(mo_s)}</div>
                      <div class="divider"></div>
                      <div class="lbl">In {horizon}y</div>
                      <div class="mono" style="font-size:1.05rem;font-weight:700;color:{C['green']}">{kfmt(proj) if proj else '—'}</div>
                    </div>""", unsafe_allow_html=True)

        # Projection
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='h-sec'>Portfolio growth projection</div>", unsafe_allow_html=True)
        with_inv, cash_only = [], []
        pf=float(portfolio_val); cs=float(portfolio_val)
        for y in range(horizon+1):
            with_inv.append(pf); cash_only.append(cs)
            pf=pf*1.07+total_inv*12; cs=cs+total_inv*12
        labels=[str(y) for y in range(horizon+1)]
        st.markdown(svg_area_line([("Invested",with_inv,C["accent"]),("Cash only",cash_only,C["text3"])],
                    labels, width=900, height=230, show_dots=False), unsafe_allow_html=True)
        fv=with_inv[-1]; added=total_inv*12*horizon; gain=fv-portfolio_val-added
        pcols=st.columns(4)
        for cc,(l,v,co) in zip(pcols,[("Start",usd0(portfolio_val),C["cyan"]),("Contributed",usd0(added),C["green"]),
                                       ("Projected",usd0(fv),C["accent"]),("Compound gain",usd0(gain),C["amber"])]):
            cc.markdown(f"<div style='text-align:center'><div class='lbl'>{l}</div><div class='mono' style='font-weight:700;color:{co};font-size:1.05rem'>{v}</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# LIVE MARKETS  (real internet data over WiFi)
# ─────────────────────────────────────────────────────────────────────────────
with tLive:
    st.markdown(f"<div class='h-sec'>Live markets</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub' style='margin-top:-.6rem;margin-bottom:1rem'>Real-time data pulled live over the internet from free public APIs (CoinGecko for crypto, open.er-api.com for currencies). Requires a WiFi / internet connection.</div>", unsafe_allow_html=True)

    online = internet_status()
    badge_col = C["green"] if online else C["red"]
    badge_txt = "● Online — connected to the internet" if online else "● Offline — connect to WiFi to load live data"
    st.markdown(f"<div style='margin-bottom:1rem'><span class='pill' style='background:{rgba(badge_col,.12)};color:{badge_col};font-size:.78rem'>{badge_txt}</span> "
                f"<span class='sub'>Last checked {datetime.now():%H:%M:%S}</span></div>", unsafe_allow_html=True)

    rc1, rc2 = st.columns([1,1])
    with rc1:
        if st.button("↻ Refresh live data"):
            st.cache_data.clear(); st.rerun()

    if not online:
        st.warning("No internet connection detected. Connect to WiFi and press “Refresh live data”.")
    else:
        # ─── Crypto prices ───────────────────────────────────────────────
        st.markdown(f"<div class='h-sec' style='margin-top:1rem'>Cryptocurrency — live USD prices</div>", unsafe_allow_html=True)
        try:
            coin_names = {"bitcoin":"Bitcoin","ethereum":"Ethereum","solana":"Solana","ripple":"XRP"}
            coin_sym   = {"bitcoin":"₿","ethereum":"Ξ","solana":"◎","ripple":"✕"}
            data = fetch_crypto_prices(tuple(coin_names.keys()))
            cols = st.columns(len(coin_names))
            for i,(cid,cname) in enumerate(coin_names.items()):
                info = data.get(cid, {})
                price = info.get("usd", 0)
                chg = info.get("usd_24h_change", 0)
                chg_col = C["green"] if chg>=0 else C["red"]
                arrow = "▲" if chg>=0 else "▼"
                cols[i].markdown(f"""<div class="kpi">
                  <div class="lbl">{coin_sym[cid]} {cname}</div>
                  <div class="mono" style="font-size:1.35rem;font-weight:700;color:{C['text']};line-height:1.25">${price:,.2f}</div>
                  <div class="sub" style="color:{chg_col};font-weight:600">{arrow} {abs(chg):.2f}% (24h)</div>
                </div>""", unsafe_allow_html=True)
        except Exception as ex:
            st.error(f"Could not load crypto prices: {ex}")

        # ─── Live FX rates ───────────────────────────────────────────────
        st.markdown(f"<div class='h-sec' style='margin-top:1.2rem'>Currency exchange — live rates (1 USD =)</div>", unsafe_allow_html=True)
        try:
            rates = fetch_fx_rates("USD")
            show = [("SAR","🇸🇦 Saudi Riyal"),("AED","🇦🇪 UAE Dirham"),("EUR","🇪🇺 Euro"),
                    ("GBP","🇬🇧 Pound"),("EGP","🇪🇬 Egyptian Pound"),("INR","🇮🇳 Rupee")]
            fcols = st.columns(len(show))
            for i,(code,label) in enumerate(show):
                val = rates.get(code, 0)
                fcols[i].markdown(f"""<div class="kpi">
                  <div class="lbl">{label}</div>
                  <div class="mono" style="font-size:1.25rem;font-weight:700;color:{C['accent']}">{val:,.3f}</div>
                  <div class="sub">{code}</div>
                </div>""", unsafe_allow_html=True)
        except Exception as ex:
            st.error(f"Could not load exchange rates: {ex}")

        # ─── Live portfolio valuation ────────────────────────────────────
        crypto_assets = [a for a in assets if a["type"]=="Crypto"]
        if crypto_assets:
            st.markdown(f"<div class='h-sec' style='margin-top:1.2rem'>Your crypto holdings at live prices</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='sub' style='margin-top:-.6rem;margin-bottom:.6rem'>Add a Crypto asset in Net Worth named after a coin (e.g. “Bitcoin”) and ClearSpend values it at the live price above.</div>", unsafe_allow_html=True)
            try:
                data = fetch_crypto_prices(("bitcoin","ethereum","solana","ripple"))
                for a in crypto_assets:
                    nm = a["name"].lower()
                    cid = ("bitcoin" if "bit" in nm or "btc" in nm else
                           "ethereum" if "eth" in nm else
                           "solana" if "sol" in nm else
                           "ripple" if "xrp" in nm or "ripple" in nm else None)
                    live_note = ""
                    if cid and cid in data:
                        live_note = f" · live price ${data[cid].get('usd',0):,.2f}"
                    st.markdown(f"""<div class="card" style="padding:.7rem 1rem;margin-bottom:.4rem">
                      <div style="display:flex;justify-content:space-between">
                        <span style="font-weight:600;font-size:.86rem">{a['name']}</span>
                        <span class="mono" style="font-weight:700;color:{C['amber']}">{usd0(a['value'])}</span>
                      </div><div class="sub">{a.get('note','')}{live_note}</div>
                    </div>""", unsafe_allow_html=True)
            except Exception as ex:
                st.error(f"Could not value holdings: {ex}")

        st.markdown(f"<div class='sub' style='margin-top:1rem'>Data refreshes automatically every few minutes and is cached so the app stays fast. Prices are indicative and for educational use.</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# NET WORTH
# ─────────────────────────────────────────────────────────────────────────────
with tNW:
    nw = st.columns(4)
    kpi(nw[0],"Assets",usd0(total_assets),f"{len(assets)} items",C["green"])
    kpi(nw[1],"Liabilities",usd0(total_liabs),f"{len(liabs)} debts",C["red"])
    kpi(nw[2],"Net worth",usd0(net_worth),"assets − debts",C["accent"])
    kpi(nw[3],"DTI ratio",f"{dti:.0f}%",("over 36%" if dti>36 else "healthy"),C["red"] if dti>36 else C["green"])

    st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)
    nl, nr = st.columns(2, gap="medium")
    with nl:
        st.markdown(f"<div class='h-sec'>Assets</div>", unsafe_allow_html=True)
        with st.form("af"):
            a1=st.text_input("Name", placeholder="Sarwa Portfolio")
            a2=st.selectbox("Type", ASSET_TYPES)
            a3=st.number_input("Value $", min_value=0.0, step=100.0)
            a4=st.text_input("Note", placeholder="Optional")
            if st.form_submit_button("Add asset") and a1.strip() and a3>0:
                assets.append({"id":max((x["id"] for x in assets),default=0)+1,"name":a1.strip(),"type":a2,"value":float(a3),"note":a4})
                save(D); st.rerun()
        for a in assets:
            sh=pct(a["value"],total_assets); ac=INV_COLORS.get(a["type"],C["green"])
            cc=st.columns([6,1])
            cc[0].markdown(f"""<div style="margin-bottom:.55rem">
              <div style="display:flex;justify-content:space-between;font-size:.84rem;margin-bottom:3px">
                <span style="font-weight:600">{a['name']} <span class='sub'>· {a['type']}</span></span>
                <span class="mono" style="font-weight:700;color:{ac}">{usd0(a['value'])}</span></div>
              <div class="bar-track"><div class="bar-fill" style="width:{sh:.0f}%;background:{ac}"></div></div></div>""", unsafe_allow_html=True)
            if cc[1].button("✕",key=f"ad{a['id']}"):
                assets[:]=[x for x in assets if x["id"]!=a["id"]]; save(D); st.rerun()
    with nr:
        st.markdown(f"<div class='h-sec'>Liabilities</div>", unsafe_allow_html=True)
        with st.form("lf"):
            l1=st.text_input("Name", placeholder="Car Loan")
            l2=st.selectbox("Type", LIABILITY_TYPES)
            l3=st.number_input("Balance $", min_value=0.0, step=100.0)
            l4=st.number_input("Monthly payment $", min_value=0.0, step=10.0)
            l5=st.text_input("Note", placeholder="Optional")
            if st.form_submit_button("Add liability") and l1.strip() and l3>0:
                liabs.append({"id":max((x["id"] for x in liabs),default=0)+1,"name":l1.strip(),"type":l2,
                    "balance":float(l3),"monthly_payment":float(l4),"note":l5})
                save(D); st.rerun()
        for l in liabs:
            sh=pct(l["balance"],total_liabs); mos=math.ceil(l["balance"]/l["monthly_payment"]) if l.get("monthly_payment") else 0
            cc=st.columns([6,1])
            cc[0].markdown(f"""<div style="margin-bottom:.55rem">
              <div style="display:flex;justify-content:space-between;font-size:.84rem;margin-bottom:3px">
                <span style="font-weight:600">{l['name']} <span class='sub'>· {l['type']}</span></span>
                <span class="mono" style="font-weight:700;color:{C['red']}">{usd0(l['balance'])}</span></div>
              <div class="bar-track"><div class="bar-fill" style="width:{sh:.0f}%;background:{C['red']}"></div></div>
              <div class="sub" style="margin-top:2px">{usd0(l['monthly_payment'])}/mo{f' · ~{mos}mo left' if mos else ''}</div></div>""", unsafe_allow_html=True)
            if cc[1].button("✕",key=f"ld{l['id']}"):
                liabs[:]=[x for x in liabs if x["id"]!=l["id"]]; save(D); st.rerun()

    st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='h-sec'>Net worth projection</div>", unsafe_allow_html=True)
    pc=st.columns(3)
    pextra=pc[0].number_input("Monthly contribution $", value=float(max(round(spare,0),0)), min_value=0.0, step=50.0, key="nwc")
    pret=pc[1].slider("Annual return %",1,15,7,key="nwr")/100
    pyrs=pc[2].slider("Years",1,30,10,key="nwy")
    base,opt,con=[],[],[]
    b=o=cn=float(net_worth)
    for y in range(pyrs+1):
        base.append(b);opt.append(o);con.append(cn)
        b=b*(1+pret)+pextra*12; o=o*(1+pret+.03)+pextra*12; cn=cn*(1+max(pret-.03,.01))+pextra*12
    st.markdown(svg_area_line([("Base",base,C["accent"]),("Optimistic",opt,C["green"]),("Conservative",con,C["amber"])],
                [str(y) for y in range(pyrs+1)], width=900, height=230), unsafe_allow_html=True)
    st.markdown(f"<div class='sub'>Projected net worth in {pyrs} years: <b style='color:{C['accent']}'>{usd0(base[-1])}</b> (base case)</div></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# IMPORT  (PDF analyzer + bank connector)
# ─────────────────────────────────────────────────────────────────────────────
with tImp:
    st.markdown(f"<div class='h-sec'>Statement PDF analyzer</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub' style='margin-bottom:.8rem'>Upload a bank statement PDF. ClearSpend reads it locally on your machine — nothing is uploaded anywhere — extracts each transaction, auto-categorises it, and previews before you import.</div>", unsafe_allow_html=True)
    up = st.file_uploader("Statement PDF", type=["pdf"])
    if up is not None:
        with st.spinner("Reading statement…"):
            txns, err = parse_statement_pdf(up.read())
        if err:
            st.error(err)
        elif not txns:
            st.warning("No transactions detected. The statement layout may be unusual — try a different export format.")
        else:
            for t in txns: t["category"]=detect_category(t["name"], t["type"])
            tot_exp=sum(t["amount"] for t in txns if t["type"]=="expense")
            tot_inc=sum(t["amount"] for t in txns if t["type"]=="income")
            m=st.columns(3)
            kpi(m[0],"Detected",str(len(txns)),"transactions",C["accent"])
            kpi(m[1],"Total out",usd0(tot_exp),"expenses",C["red"])
            kpi(m[2],"Total in",usd0(tot_inc),"income",C["green"])
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
            prev=pd.DataFrame([{"Date":t["date"],"Description":t["name"],
                "Category":CATEGORIES[t["category"]]["label"],"Type":t["type"],
                "Amount":t["amount"]} for t in txns])
            st.dataframe(prev, use_container_width=True, hide_index=True, height=280)
            if st.button("Import all into ClearSpend"):
                nid=max((x["id"] for x in entries),default=0)
                for t in txns:
                    nid+=1
                    entries.append({"id":nid,"name":t["name"],"amount":float(t["amount"]),
                        "type":t["type"],"ptype":"single","category":t["category"],
                        "date":t["date"],"note":"imported from statement","linked_goal":None})
                save(D); st.success(f"Imported {len(txns)} transactions."); st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# REPORT
# ─────────────────────────────────────────────────────────────────────────────
with tRep:
    period = st.radio("Period",["Monthly","Annual"],horizontal=True,label_visibility="collapsed")
    mult = 1 if period=="Monthly" else 12
    suf = "mo" if period=="Monthly" else "yr"
    rk=st.columns(5)
    for col,(l,v) in zip(rk,[(f"Income/{suf}",usd0(mo_inc*mult)),(f"Expenses/{suf}",usd0(mo_exp*mult)),
        (f"Net/{suf}",usd0(net*mult)),("Savings rate",f"{sav_rate:.0f}%"),("Net worth",usd0(net_worth))]):
        col.metric(l,v)

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='h-sec'>Category analysis</div>", unsafe_allow_html=True)
    bench={"housing":30,"food":15,"transport":10,"utilities":8,"subscriptions":5,"health":5,"entertainment":5,"education":5,"shopping":5}
    for k,v in sorted(cat_tot.items(),key=lambda x:x[1],reverse=True):
        cat=CATEGORIES.get(k,CATEGORIES['other'])
        pe=pct(v,mo_exp); pi=pct(v,mo_inc); bv=bench.get(k); over=bv and pi>bv
        col=C["red"] if over else cat["color"]
        ca=CITY_DATA[city].get(k,0)
        st.markdown(f"""<div class="card" style="padding:.85rem 1.1rem;margin-bottom:.5rem;border-left:3px solid {col}">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">
            <span style="font-weight:600;font-size:.88rem">{cat['emoji']} {cat['label']}
              {f"<span class='pill' style='background:{rgba(col,.13)};color:{col};margin-left:6px'>over {bv}% guideline</span>" if over else ""}</span>
            <span class="mono" style="font-weight:700;color:{col}">{usd0(v*mult)}/{suf}</span></div>
          <div class="bar-track" style="height:6px"><div class="bar-fill" style="width:{min(pe,100):.0f}%;background:{col}"></div></div>
          <div class="sub" style="margin-top:4px">{pe:.0f}% of spend · {pi:.0f}% of income · {city} avg {usd0(ca)}/mo · gap {usd0((v-ca)*mult)}/{suf}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='h-sec'>Observations</div>", unsafe_allow_html=True)
    obs=[]
    if sav_rate>=20: obs.append((C["green"],"Healthy savings rate",f"{sav_rate:.0f}% meets the 20% benchmark."))
    elif sav_rate>=10: obs.append((C["amber"],"Below target savings",f"At {sav_rate:.0f}%, aim for 20%+."))
    else: obs.append((C["red"],"Low savings rate",f"Only {sav_rate:.0f}% — review the Insights tab."))
    if dti>36: obs.append((C["red"],"High debt burden",f"DTI {dti:.0f}% exceeds the 36% guideline."))
    elif dti>0: obs.append((C["green"],"Manageable debt",f"DTI {dti:.0f}% is within healthy limits."))
    if net_worth>0: obs.append((C["green"],"Positive net worth",f"{usd0(net_worth)} — solid foundation."))
    else: obs.append((C["red"],"Negative net worth",f"{usd0(net_worth)} — prioritise debt payoff."))
    over_b=[k for k,v in budgets.items() if cat_tot.get(k,0)>v]
    if over_b: obs.append((C["amber"],f"{len(over_b)} budget(s) exceeded",", ".join(CATEGORIES[k]['label'] for k in over_b)+"."))
    for col,t,m in obs:
        st.markdown(f"""<div class="insight"><div class="dot" style="background:{col}"></div>
          <div><div style="font-weight:700;font-size:.88rem">{t}</div><div style="font-size:.83rem;color:{C['text2']}">{m}</div></div></div>""", unsafe_allow_html=True)

    rep=(f"CLEARSPEND REPORT — {datetime.now():%Y-%m-%d %H:%M}\nCity: {city}\n{'='*48}\n\n"
         f"{period.upper()} SUMMARY\n  Income: {usd(mo_inc*mult)}\n  Expenses: {usd(mo_exp*mult)}\n"
         f"  Net: {usd(net*mult)}\n  Savings rate: {sav_rate:.1f}%\n  Net worth: {usd(net_worth)}\n  Health: {HS}/100 ({grade})\n\n"
         f"EXPENSES BY CATEGORY\n"+"".join(f"  {CATEGORIES.get(k,CATEGORIES['other'])['label']:<22}{usd(v*mult):>12}\n" for k,v in sorted(cat_tot.items(),key=lambda x:-x[1]))
         +f"\nASSETS\n"+"".join(f"  {a['name']}: {usd(a['value'])}\n" for a in assets)
         +f"\nLIABILITIES\n"+"".join(f"  {l['name']}: {usd(l['balance'])}\n" for l in liabs))
    st.download_button("Download text report", rep, "clearspend_report.txt","text/plain")

st.markdown(f"<div style='text-align:center;padding:1.5rem 0 0;color:{C['text4']};font-size:.72rem'>ClearSpend v6 · self-contained · data in clearspend_v6.json</div>", unsafe_allow_html=True)
