"""
Metro Zone Deep Dive — dashboard redesign (portfolio build).

Implements the locked build spec:
  - Level 1: triaged department landing (worst Interim GP% decline vs LY first;
             TSL$ growth tie-break), components visible, fresh/ambient card variants,
             weekly/monthly toggle, LY baseline, status colour.
  - Level 2: three sortable dollar lenses — Best lines / Loss makers / Fresh dump.
  - All dollars derive from the validated sales base (Sales x %).

Design follows the web-design-principles skill: one type scale, 4-based spacing
tokens, restrained palette, depth reserved for the focal KPI and triage cards,
hierarchy via size/weight/colour with secondary info de-emphasised.
"""
from __future__ import annotations
import streamlit as st
import pandas as pd

from data import build_lines, department_summary
from design import (CSS, status_color, GREEN, AMBER, RED, NAVY, INK_FAINT,
                    GREEN_BG, AMBER_BG, RED_BG)

st.set_page_config(page_title="Metro Zone Deep Dive", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(CSS, unsafe_allow_html=True)

# ---------- state ----------
if "dept" not in st.session_state:
    st.session_state.dept = None
if "period" not in st.session_state:
    st.session_state.period = "Weekly"

WEEK_FACTOR = {"Weekly": 1.0, "Monthly": 4.3}


@st.cache_data
def load():
    lines = build_lines()
    return lines


lines = load()


def money(v: float) -> str:
    v = float(v)
    sign = "-" if v < 0 else ""
    v = abs(v)
    if v >= 1000:
        return f"{sign}${v/1000:.1f}k"
    return f"{sign}${v:.0f}"


def pct(v: float) -> str:
    return f"{v:.1f}%"


def scale(df: pd.DataFrame, cols) -> pd.DataFrame:
    f = WEEK_FACTOR[st.session_state.period]
    out = df.copy()
    for c in cols:
        out[c] = out[c] * f
    return out


# =====================================================================
# LEVEL 1 — department triage landing
# =====================================================================
def render_level1():
    st.markdown('<div class="eyebrow">Woolworths Metro · desk review</div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown('<div class="h-title">Metro Zone Deep Dive</div>', unsafe_allow_html=True)
        st.markdown('<div class="h-sub">Departments ranked worst-first by Interim GP% '
                    'decline vs last year. The dashboard does the triage — click a '
                    'department to see its lines.</div>', unsafe_allow_html=True)
    with c2:
        st.session_state.period = st.radio(
            "Period", ["Weekly", "Monthly"], horizontal=True,
            index=0 if st.session_state.period == "Weekly" else 1,
            label_visibility="collapsed")

    summ = department_summary(lines)
    dollar_cols = ["sales", "sales_ly", "tsl_dollars", "tsl_ly_dollars",
                   "dump_dollars", "adj_dollars", "clr_dollars", "est_profit",
                   "tsl_delta_dollars"]
    summ = scale(summ, dollar_cols)

    # ---- KPI strip (focal element = store Interim GP% vs LY) ----
    store_interim = (lines["interim_pct"] * lines["sales"]).sum() / lines["sales"].sum()
    store_interim_ly = (lines["interim_ly_pct"] * lines["sales"]).sum() / lines["sales"].sum()
    store_delta = store_interim - store_interim_ly
    total_tsl = summ["tsl_dollars"].sum()
    total_tsl_ly = summ["tsl_ly_dollars"].sum()
    fresh_dump = summ.loc[summ["is_fresh"], "dump_dollars"].sum()
    mover = summ.iloc[0]

    dcol = GREEN if store_delta >= 0 else RED
    tcol = RED if total_tsl > total_tsl_ly else GREEN
    tsl_delta_pct = (total_tsl / total_tsl_ly - 1) * 100

    kpi_html = (
        '<div class="kpi-wrap">'
        '<div class="kpi focal">'
        '<div class="lbl">Store Interim GP% vs LY</div>'
        f'<div class="val">{store_interim:.1f}%</div>'
        f'<div class="delta" style="color:{"#7CE0BC" if store_delta>=0 else "#FFB4B0"}">'
        f'{store_delta:+.1f} pts vs last year</div></div>'
        '<div class="kpi"><div class="lbl">Total stock loss $</div>'
        f'<div class="val">{money(total_tsl)}</div>'
        f'<div class="delta" style="color:{tcol}">{tsl_delta_pct:+.0f}% vs LY</div></div>'
        '<div class="kpi"><div class="lbl">Fresh dump $</div>'
        f'<div class="val">{money(fresh_dump)}</div>'
        f'<div class="delta muted">perishable waste · {st.session_state.period.lower()}</div></div>'
        '<div class="kpi"><div class="lbl">Biggest mover</div>'
        f'<div class="val" style="font-size:1.25rem">{mover["department"]}</div>'
        f'<div class="delta neg">{mover["interim_delta"]:+.1f} pts Interim GP%</div></div>'
        '</div>'
    )
    st.markdown(kpi_html, unsafe_allow_html=True)

    st.markdown('<div class="section-head">Departments — triaged worst-first</div>',
                unsafe_allow_html=True)

    # ---- department cards ----
    for _, d in summ.iterrows():
        color, bg, label = status_color(d["interim_delta"])
        gp_cls = "neg" if d["interim_delta"] < 0 else "pos"
        sales_cls = "pos" if d["sales_delta_pct"] >= 0 else "neg"
        tsl_grow = d["tsl_dollars"] > d["tsl_ly_dollars"]
        tsl_cls = "neg" if tsl_grow else "pos"

        tag = ('<span class="dept-tag">fresh</span>' if d["is_fresh"]
               else '<span class="dept-tag amb">ambient</span>')

        if d["is_fresh"]:
            fresh_block = (f'<div class="metric"><div class="m-lbl">Fresh dump $</div>'
                           f'<div class="m-val neg">{money(d["dump_dollars"])}</div>'
                           f'<div class="m-dlt muted">perishable waste</div></div>')
        else:
            fresh_block = ('<div class="metric"><div class="m-lbl">Fresh dump $</div>'
                           '<div class="m-val muted">—</div>'
                           '<div class="m-dlt muted">n/a ambient</div></div>')

        card = (
            f'<div class="dept-card" style="border-left-color:{color}">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">'
            f'<div><span class="dept-name">{d["department"]}</span>{tag}'
            f'<span class="pill" style="background:{bg};color:{color};margin-left:8px">{label}</span></div>'
            f'<div class="{gp_cls}" style="font-size:0.82rem;font-weight:600">'
            f'{d["interim_delta"]:+.1f} pts Interim GP% vs LY</div></div>'
            f'<div class="metric-row">'
            f'<div class="metric"><div class="m-lbl">Sales $</div>'
            f'<div class="m-val">{money(d["sales"])}</div>'
            f'<div class="m-dlt {sales_cls}">{d["sales_delta_pct"]:+.1f}% vs LY</div></div>'
            f'<div class="metric"><div class="m-lbl">Interim GP%</div>'
            f'<div class="m-val">{d["interim_pct"]:.1f}%</div>'
            f'<div class="m-dlt {gp_cls}">{d["interim_delta"]:+.1f} pts</div></div>'
            f'<div class="metric" style="min-width:180px">'
            f'<div class="m-lbl">Total stock loss $</div>'
            f'<div class="m-val {tsl_cls}">{money(d["tsl_dollars"])} '
            f'<span class="m-dlt {tsl_cls}">({money(d["tsl_delta_dollars"])} vs LY)</span></div>'
            f'<div class="split">dump {money(d["dump_dollars"])} · adj {money(d["adj_dollars"])} · clr {money(d["clr_dollars"])}</div></div>'
            f'{fresh_block}'
            f'</div></div>'
        )
        st.markdown(card, unsafe_allow_html=True)

        # click target (Streamlit button under each card)
        if st.button(f"Open {d['department']} →", key=f"open_{d['department']}"):
            st.session_state.dept = d["department"]
            st.rerun()

    st.markdown('<div class="footnote">Triage sort: Interim GP% decline vs LY '
                '(TSL$ growth as tie-break). Status colour: red ≤ −3 pts, amber −3 to 0, '
                'green ≥ 0. All dollars derive from the validated sales base (Sales × %). '
                'Figures illustrative.</div>', unsafe_allow_html=True)


# =====================================================================
# LEVEL 2 — line detail, three lenses
# =====================================================================
def render_level2(dept: str):
    d = lines[lines["department"] == dept].copy()
    is_fresh = bool(d["is_fresh"].iloc[0])
    d = scale(d, ["sales", "dump_$", "adj_$", "clr_$", "tsl_$", "est_profit_$"])

    if st.button("← All departments"):
        st.session_state.dept = None
        st.rerun()

    st.markdown(f'<div class="eyebrow">Line detail · {st.session_state.period.lower()} · vs last year</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="h-title">{dept}'
                f'{" · fresh / service" if is_fresh else ""}</div>', unsafe_allow_html=True)

    lens_options = ["Best lines", "Loss makers"]
    if is_fresh:
        lens_options.append("Fresh dump")
    lens = st.radio("Lens", lens_options, horizontal=True, label_visibility="collapsed")

    if lens == "Best lines":
        render_best(d)
    elif lens == "Loss makers":
        render_loss(d)
    else:
        render_dump(d)


def render_best(d: pd.DataFrame):
    st.markdown('<div class="lens-note"><b>Best lines</b> — ranked by estimated profit '
                'contribution (Sales × Interim GP%): the real profit each line delivers '
                '<i>after</i> stock loss. <b>GP$ lost to shrink</b> shows the dollar value '
                'of margin eaten by dump, adjustment, and clearance — compare it directly to '
                'Est. profit $ in the next column to see how much of each line\'s margin is '
                'leaking. A line flagged <b>leaking</b> (≥ $500 lost and ≥ 10 pts gap) is '
                'well-bought but losing it operationally: fix the loss, don\'t touch pricing. '
                'A negative value labelled <b>positive adjustment</b> means stock loss went '
                'net-negative — the §3 count artifact (a count finding more stock than the '
                'system expected), not a real margin gain.</div>', unsafe_allow_html=True)

    t = d.sort_values("est_profit_$", ascending=False).head(25).copy()
    t["gp_lost_$"] = t["sales"] * t["loss_gap"] / 100
    t["leaking"] = (t["loss_gap"] >= 10) & (t["gp_lost_$"] >= 500)

    def _gap_label(r):
        if r["gp_lost_$"] < 0:
            amt = abs(r["gp_lost_$"])
            val = f"−${amt/1000:.1f}k" if amt >= 1000 else f"−${amt:.0f}"
            return f"{val}  · positive adjustment"
        val = f"${r['gp_lost_$']/1000:.1f}k" if r["gp_lost_$"] >= 1000 else f"${r['gp_lost_$']:.0f}"
        return val + ("  ⚑ leaking" if r["leaking"] else "")

    show = pd.DataFrame({
        "Article": t["article"],
        "Sales $": t["sales"].map(money),
        "Interim GP%": t["interim_pct"].map(pct),
        "ISGP%": t["isgp_pct"].map(pct),
        "GP$ lost to shrink": t.apply(_gap_label, axis=1),
        "TSL $": t["tsl_$"].map(money),
        "Est. profit $": t["est_profit_$"].map(money),
    })
    st.dataframe(show, hide_index=True, use_container_width=True, height=560)
    st.markdown('<div class="footnote">Est. profit $ is a derived contribution '
                '(Sales × Interim GP%), reliable for ranking — not a reported GP$ field. '
                'It is the one figure to footnote in the live UI (see spec §7, item 1).</div>',
                unsafe_allow_html=True)


def render_loss(d: pd.DataFrame):
    st.markdown('<div class="lens-note"><b>Loss makers</b> — ranked by TSL $ (the dollars '
                'leaking, what to fix first), with TSL % beside it (loss as a share of sales '
                '— how abnormal the line is). A big line with proportionate loss is not the '
                'same as a small line losing half its sales: the dollar sets priority, the '
                'percentage flags abnormality (≥ 25% of sales = <b>high rate</b>). TSL $ is '
                'always split into Dump / Adjustment / Clearance because each needs a '
                'different fix — <b>adjustment</b> → theft / count / scan; <b>dump</b> → '
                'ordering / spoilage; <b>clearance</b> → managed markdown (often the right '
                'call). A sign-changing TSL across periods is flagged <b>check count</b> — a '
                'data-integrity issue, not real loss.</div>', unsafe_allow_html=True)

    rank_by = st.radio("Rank by", ["TSL $ (impact)", "TSL % (rate)"],
                       horizontal=True, label_visibility="collapsed",
                       key="loss_rank")
    sort_col = "tsl_$" if rank_by.startswith("TSL $") else "tsl_pct"
    t = d.sort_values(sort_col, ascending=False).head(25).copy()

    def driver(r):
        comps = {"adjustment": abs(r["adj_$"]), "dump": r["dump_$"], "clearance": r["clr_$"]}
        return max(comps, key=comps.get)

    t["driver"] = t.apply(driver, axis=1)
    show = pd.DataFrame({
        "Article": t["article"],
        "TSL $": t["tsl_$"].map(money),
        "TSL %": t.apply(lambda r: f"{r['tsl_pct']:.1f}%"
                         + ("  ⚑ high rate" if r["tsl_pct"] >= 25 else ""), axis=1),
        "Sales $": t["sales"].map(money),
        "Dump $": t["dump_$"].map(money),
        "Adjust $": t["adj_$"].map(money),
        "Clear $": t["clr_$"].map(money),
        "Driver": t.apply(lambda r: r["driver"]
                          + ("  ⚑ check count" if r["swing"] else ""), axis=1),
    })
    st.dataframe(show, hide_index=True, use_container_width=True, height=560)
    st.markdown('<div class="footnote">TSL$ reconciles to Sales × TSL%. Negative TSL is '
                'usually a count/receiving correction, not a gain — read over a multi-period '
                'window (see spec §3).</div>', unsafe_allow_html=True)


def render_dump(d: pd.DataFrame):
    st.markdown('<div class="lens-note"><b>Fresh dump</b> — perishable waste ranked by '
                '<b>Dump $</b>, not Dump% and not total TSL. Ranking on dollars means a '
                'high-volume line dumping 8% correctly outranks a tiny line dumping 25% — '
                'the trap percentage-sorting would cause. Clearance$ sits beside it as the '
                'preferred alternative: clearing stock before it perishes beats binning it. '
                'High dump$ + low clearance$ = an ordering / rotation problem. Dump% ≥ 15 '
                'flagged <b>high waste</b>.</div>', unsafe_allow_html=True)

    t = d[d["dump_$"] > 0].sort_values("dump_$", ascending=False).head(25).copy()
    show = pd.DataFrame({
        "Article": t["article"],
        "Dump $": t.apply(lambda r: money(r["dump_$"])
                         + ("  ⚑ high waste" if r["dump_pct"] >= 15 else ""), axis=1),
        "Dump %": t["dump_pct"].map(pct),
        "Clear $ (alt)": t["clr_$"].map(money),
        "Sales $": t["sales"].map(money),
        "Interim GP%": t["interim_pct"].map(pct),
    })
    st.dataframe(show, hide_index=True, use_container_width=True, height=560)
    st.markdown('<div class="footnote">Aligned with the corporate waste priority '
                '(Project LIFT, AI demand-sensing): fresh waste is surfaced as its own lens, '
                'no click required from the department card.</div>', unsafe_allow_html=True)


# ---------- router ----------
if st.session_state.dept is None:
    render_level1()
else:
    render_level2(st.session_state.dept)
