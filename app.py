


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

Changes vs v1
-------------
1.  Data freshness timestamp in eyebrow on both Level 1 and Level 2.
2.  "Biggest Mover" KPI replaced with red-zone department count (<=  -3 pts).
3.  Lens-notes collapsed to one actionable sentence + methodology in st.expander.
4.  Spec build reference removed from Est. profit $ footnote.
5.  "Top focus areas" auto-generated section added above department cards in Level 1.
6.  WoW directional arrow added to each department card header.
7.  TSL split dominant driver bolded in department card.
8.  Terminology unified in table headers: "Interim GP% (before shrink)" / "GP% after shrink".
9.  Level 2 context bar shows department vs store Interim GP%.
10. "positive adjustment" label replaced with "count correction - verify count".
11. About tab added for portfolio / hiring manager context.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from data import build_lines, department_summary
from design import (
    AMBER, AMBER_BG, CSS, GREEN, GREEN_BG, INK_FAINT, NAVY, RED, RED_BG,
    status_color,
)

st.set_page_config(
    page_title="Metro Zone Deep Dive",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(CSS, unsafe_allow_html=True)

# Supplemental CSS for components not in design.py.
st.markdown(
    """
<style>
.focus-box {
    background: rgba(255, 180, 50, 0.06);
    border: 1px solid rgba(255, 180, 50, 0.35);
    border-radius: 8px;
    padding: 16px 20px;
    margin: 16px 0 20px 0;
}
.context-bar {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 10px 16px;
    margin: 8px 0 16px 0;
    font-size: 0.85rem;
}
.about-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 20px;
    height: 100%;
    line-height: 1.6;
}
.about-decision {
    border-left: 3px solid #2F5BB7;
    padding: 12px 16px;
    margin-bottom: 14px;
    background: rgba(47, 91, 183, 0.06);
    border-radius: 0 6px 6px 0;
    line-height: 1.6;
}
/* ---- About tab decoration (depth used sparingly, one accent family) ---- */
.about-hero {
    background: linear-gradient(135deg,
        rgba(47, 91, 183, 0.18) 0%,
        rgba(47, 91, 183, 0.05) 45%,
        rgba(124, 224, 188, 0.06) 100%);
    border: 1px solid rgba(47, 91, 183, 0.25);
    border-radius: 12px;
    padding: 28px 32px;
    margin-bottom: 8px;
}
.about-hero .eyebrow { margin-bottom: 6px; }
.about-hero .h-title {
    background: linear-gradient(90deg, #5A86D8 0%, #23499A 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}
/* Section headings in the About tab: accent marker + soft tint, not full-colour text. */
.about-h {
    font-size: 1.15rem;
    font-weight: 700;
    color: #4A7AD1;
    margin: 8px 0 10px 0;
    padding-left: 12px;
    border-left: 4px solid #2F5BB7;
    line-height: 1.3;
}
/* Faint gradient divider replaces the plain grey rule. */
.about-rule {
    height: 1px;
    border: none;
    margin: 26px 0;
    background: linear-gradient(90deg,
        rgba(47, 91, 183, 0.45) 0%,
        rgba(47, 91, 183, 0.12) 40%,
        rgba(255, 255, 255, 0.0) 100%);
}
/* Lift the three problem cards slightly on hover for a touch of depth. */
.about-card {
    transition: box-shadow 0.15s ease, border-color 0.15s ease;
}
.about-card:hover {
    border-color: rgba(47, 91, 183, 0.4);
    box-shadow: 0 4px 14px rgba(47, 91, 183, 0.18);
}
/* Highlight the "Open department" buttons so the primary action stands out. */
div.stButton > button {
    background: linear-gradient(180deg, #3A6BD0 0%, #2F5BB7 100%);
    color: #FFFFFF;
    border: 1px solid #274C99;
    border-radius: 6px;
    font-weight: 600;
    padding: 8px 18px;
    transition: transform 0.05s ease, box-shadow 0.15s ease, background 0.15s ease;
    box-shadow: 0 1px 3px rgba(47, 91, 183, 0.35);
}
div.stButton > button:hover {
    background: linear-gradient(180deg, #4478E0 0%, #3A66C8 100%);
    box-shadow: 0 2px 8px rgba(47, 91, 183, 0.55);
    color: #FFFFFF;
}
div.stButton > button:active {
    transform: translateY(1px);
}
div.stButton > button:focus:not(:active) {
    color: #FFFFFF;
    border-color: #274C99;
}
</style>
""",
    unsafe_allow_html=True,
)

TODAY = "1 July 2026"

# ---------- session state ----------
if "dept" not in st.session_state:
    st.session_state.dept = None
if "period" not in st.session_state:
    st.session_state.period = "Weekly"

WEEK_FACTOR = {"Weekly": 1.0, "Monthly": 4.3}


@st.cache_data
def load() -> pd.DataFrame:
    lines = build_lines()
    # Synthetic WoW Interim GP% delta -- one value per department, deterministic.
    # Replace with a real WoW column from the data layer when two periods are available.
    rng = np.random.default_rng(42)
    depts = sorted(lines["department"].unique())
    wow_map = {d: round(rng.uniform(-1.5, 1.5), 1) for d in depts}
    lines["interim_wow"] = lines["department"].map(wow_map)
    return lines


lines = load()

# Store-level constants -- computed once from unscaled lines (GP% is scale-independent).
_STORE_INTERIM: float = (
    (lines["interim_pct"] * lines["sales"]).sum() / lines["sales"].sum()
)
_STORE_INTERIM_LY: float = (
    (lines["interim_ly_pct"] * lines["sales"]).sum() / lines["sales"].sum()
)
_STORE_INTERIM_DELTA: float = _STORE_INTERIM - _STORE_INTERIM_LY


# ---------- formatters ----------

def money(v: float) -> str:
    v = float(v)
    sign = "-" if v < 0 else ""
    v = abs(v)
    if v >= 1000:
        return f"{sign}${v / 1000:.1f}k"
    return f"{sign}${v:.0f}"


def pct(v: float) -> str:
    return f"{v:.1f}%"


def scale(df: pd.DataFrame, cols) -> pd.DataFrame:
    f = WEEK_FACTOR[st.session_state.period]
    out = df.copy()
    for c in cols:
        out[c] = out[c] * f
    return out


def wow_arrow(delta: float) -> str:
    if delta > 0.2:
        return f'<span style="color:{GREEN}">up {delta:+.1f} pts WoW</span>'
    if delta < -0.2:
        return f'<span style="color:{RED}">down {delta:+.1f} pts WoW</span>'
    return f'<span style="color:{INK_FAINT}">stable WoW</span>'


def _bold_if(key: str, raw_val: float, dominant: str) -> str:
    txt = f"{key} {money(raw_val)}"
    return f"<b>{txt}</b>" if key == dominant else txt


# =====================================================================
# LEVEL 1 -- department triage landing
# =====================================================================

def render_focus_areas(summ: pd.DataFrame) -> None:
    items: list[str] = []
    flagged: set[str] = set()

    for _, d in summ.iterrows():
        if d["interim_delta"] < -3 and d["tsl_delta_dollars"] > 0:
            items.append(
                f"<b>{d['department']}</b> -- Interim GP% down "
                f"{d['interim_delta']:.1f} pts vs LY and stock loss growing "
                f"({money(d['tsl_delta_dollars'])} vs LY). "
                f"Open <b>Loss Makers</b> lens."
            )
            flagged.add(d["department"])

    fresh = summ[summ["is_fresh"] & ~summ["department"].isin(flagged)]
    fresh = fresh.sort_values("dump_dollars", ascending=False)
    if not fresh.empty:
        top = fresh.iloc[0]
        items.append(
            f"<b>{top['department']}</b> -- highest fresh waste this "
            f"{st.session_state.period.lower()} at {money(top['dump_dollars'])}. "
            f"Open <b>Fresh Dump</b> lens."
        )
        flagged.add(top["department"])

    tsl_top = summ[~summ["department"].isin(flagged)].sort_values(
        "tsl_dollars", ascending=False
    )
    if not tsl_top.empty:
        t = tsl_top.iloc[0]
        items.append(
            f"<b>{t['department']}</b> -- largest total stock loss at "
            f"{money(t['tsl_dollars'])} this {st.session_state.period.lower()}. "
            f"Open <b>Loss Makers</b> lens."
        )

    if not items:
        return

    bullets = "".join(
        f'<li style="margin-bottom:6px">{item}</li>' for item in items[:3]
    )
    st.markdown(
        f'<div class="focus-box">'
        f'<div class="section-head" style="margin-bottom:8px">'
        f"Top focus areas this {st.session_state.period.lower()}"
        f"</div>"
        f'<ul style="margin:0;padding-left:18px;line-height:1.7">{bullets}</ul>'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_level1() -> None:
    st.markdown(
        f'<div class="eyebrow">Woolworths Metro - desk review - Data as at: {TODAY}</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown('<div class="h-title">Metro Zone Deep Dive</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="h-sub">Departments ranked worst-first by Interim GP% '
            "decline vs last year. Click a department to drill into its lines.</div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.session_state.period = st.radio(
            "Period",
            ["Weekly", "Monthly"],
            horizontal=True,
            index=0 if st.session_state.period == "Weekly" else 1,
            label_visibility="collapsed",
        )

    summ = department_summary(lines)
    dollar_cols = [
        "sales", "sales_ly", "tsl_dollars", "tsl_ly_dollars",
        "dump_dollars", "adj_dollars", "clr_dollars", "est_profit",
        "tsl_delta_dollars",
    ]
    summ = scale(summ, dollar_cols)

    wow_by_dept = (
        lines.groupby("department")["interim_wow"]
        .first()
        .reset_index()
        .rename(columns={"interim_wow": "wow"})
    )
    summ = summ.merge(wow_by_dept, on="department", how="left")

    total_tsl = summ["tsl_dollars"].sum()
    total_tsl_ly = summ["tsl_ly_dollars"].sum()
    fresh_dump = summ.loc[summ["is_fresh"], "dump_dollars"].sum()
    red_count = int((summ["interim_delta"] <= -3).sum())
    tcol = RED if total_tsl > total_tsl_ly else GREEN
    tsl_delta_pct = (total_tsl / total_tsl_ly - 1) * 100

    kpi_html = (
        '<div class="kpi-wrap">'
        '<div class="kpi focal">'
        '<div class="lbl">Store Interim GP% vs LY</div>'
        f'<div class="val">{_STORE_INTERIM:.1f}%</div>'
        f'<div class="delta" style="color:{"#7CE0BC" if _STORE_INTERIM_DELTA >= 0 else "#FFB4B0"}">'
        f"{_STORE_INTERIM_DELTA:+.1f} pts vs last year</div></div>"
        '<div class="kpi"><div class="lbl">Total stock loss $</div>'
        f'<div class="val">{money(total_tsl)}</div>'
        f'<div class="delta" style="color:{tcol}">{tsl_delta_pct:+.0f}% vs LY</div></div>'
        '<div class="kpi"><div class="lbl">Fresh dump $</div>'
        f'<div class="val">{money(fresh_dump)}</div>'
        f'<div class="delta muted">perishable waste - {st.session_state.period.lower()}</div></div>'
        '<div class="kpi"><div class="lbl">Depts in red zone</div>'
        f'<div class="val" style="color:{RED if red_count > 0 else GREEN}">{red_count}</div>'
        '<div class="delta muted">departments <= -3 pts Interim GP% vs LY</div></div>'
        "</div>"
    )
    st.markdown(kpi_html, unsafe_allow_html=True)

    render_focus_areas(summ)

    st.markdown(
        '<div class="section-head">Departments -- triaged worst-first</div>',
        unsafe_allow_html=True,
    )

    for _, d in summ.iterrows():
        color, bg, label = status_color(d["interim_delta"])
        gp_cls = "neg" if d["interim_delta"] < 0 else "pos"
        sales_cls = "pos" if d["sales_delta_pct"] >= 0 else "neg"
        tsl_grow = d["tsl_dollars"] > d["tsl_ly_dollars"]
        tsl_cls = "neg" if tsl_grow else "pos"

        tag = (
            '<span class="dept-tag">fresh</span>'
            if d["is_fresh"]
            else '<span class="dept-tag amb">ambient</span>'
        )

        wow_html = wow_arrow(d.get("wow", 0.0))

        dump_v = d["dump_dollars"]
        adj_v = abs(d["adj_dollars"])
        clr_v = d["clr_dollars"]
        dominant = max(
            [("dump", dump_v), ("adj", adj_v), ("clr", clr_v)],
            key=lambda x: x[1],
        )[0]
        tsl_split_html = (
            f'{_bold_if("dump", dump_v, dominant)} - '
            f'{_bold_if("adj", d["adj_dollars"], dominant)} - '
            f'{_bold_if("clr", clr_v, dominant)}'
        )

        if d["is_fresh"]:
            fresh_block = (
                f'<div class="metric"><div class="m-lbl">Fresh dump $</div>'
                f'<div class="m-val neg">{money(d["dump_dollars"])}</div>'
                f'<div class="m-dlt muted">perishable waste</div></div>'
            )
        else:
            fresh_block = (
                '<div class="metric"><div class="m-lbl">Fresh dump $</div>'
                '<div class="m-val muted">-</div>'
                '<div class="m-dlt muted">n/a ambient</div></div>'
            )

        card = (
            f'<div class="dept-card" style="border-left-color:{color}">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'flex-wrap:wrap;gap:8px">'
            f'<div><span class="dept-name">{d["department"]}</span>{tag}'
            f'<span class="pill" style="background:{bg};color:{color};margin-left:8px">'
            f"{label}</span></div>"
            f'<div style="display:flex;gap:16px;align-items:center">'
            f'<span class="{gp_cls}" style="font-size:0.82rem;font-weight:600">'
            f'{d["interim_delta"]:+.1f} pts Interim GP% vs LY</span>'
            f'<span style="font-size:0.78rem">{wow_html}</span>'
            f"</div></div>"
            f'<div class="metric-row">'
            f'<div class="metric"><div class="m-lbl">Sales $</div>'
            f'<div class="m-val">{money(d["sales"])}</div>'
            f'<div class="m-dlt {sales_cls}">{d["sales_delta_pct"]:+.1f}% vs LY</div></div>'
            f'<div class="metric"><div class="m-lbl">Interim GP%</div>'
            f'<div class="m-val">{d["interim_pct"]:.1f}%</div>'
            f'<div class="m-dlt {gp_cls}">{d["interim_delta"]:+.1f} pts vs LY</div></div>'
            f'<div class="metric" style="min-width:180px">'
            f'<div class="m-lbl">Total stock loss $</div>'
            f'<div class="m-val {tsl_cls}">{money(d["tsl_dollars"])} '
            f'<span class="m-dlt {tsl_cls}">({money(d["tsl_delta_dollars"])} vs LY)</span></div>'
            f'<div class="split">{tsl_split_html}</div></div>'
            f"{fresh_block}"
            f"</div></div>"
        )
        st.markdown(card, unsafe_allow_html=True)

        if st.button(f"Open {d['department']} ->", key=f"open_{d['department']}"):
            st.session_state.dept = d["department"]
            st.rerun()

    st.markdown(
        '<div class="footnote">Triage sort: Interim GP% decline vs LY '
        "(TSL$ growth as tie-break). Status: red <= -3 pts, amber -3 to 0, green >= 0. "
        "TSL split bold = dominant driver. WoW = week-on-week Interim GP% movement (synthetic). "
        "All dollars derive from the validated sales base (Sales x %). "
        "Figures illustrative.</div>",
        unsafe_allow_html=True,
    )


# =====================================================================
# LEVEL 2 -- line detail, three lenses
# =====================================================================

def render_level2(dept: str) -> None:
    d_raw = lines[lines["department"] == dept].copy()
    is_fresh = bool(d_raw["is_fresh"].iloc[0])

    dept_interim: float = (
        (d_raw["interim_pct"] * d_raw["sales"]).sum() / d_raw["sales"].sum()
    )

    d = scale(d_raw, ["sales", "dump_$", "adj_$", "clr_$", "tsl_$", "est_profit_$"])

    if st.button("<- All departments"):
        st.session_state.dept = None
        st.rerun()

    st.markdown(
        f'<div class="eyebrow">Line detail - {st.session_state.period.lower()} - '
        f"vs last year - Data as at: {TODAY}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="h-title">{dept}'
        f'{"  - fresh / service" if is_fresh else ""}</div>',
        unsafe_allow_html=True,
    )

    dept_vs_store = dept_interim - _STORE_INTERIM
    vs_col = RED if dept_vs_store < 0 else GREEN
    st.markdown(
        f'<div class="context-bar">'
        f"Store Interim GP%: <b>{_STORE_INTERIM:.1f}%</b>"
        f"&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"{dept}: <b>{dept_interim:.1f}%</b>"
        f"&nbsp;&nbsp;|&nbsp;&nbsp;"
        f'<span style="color:{vs_col}">{dept_vs_store:+.1f} pts vs store avg</span>'
        f"</div>",
        unsafe_allow_html=True,
    )

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


def render_best(d: pd.DataFrame) -> None:
    st.markdown(
        "**Best lines** -- top earners after shrink. "
        "Leaking = well-bought but losing margin operationally -- fix the loss, not the price.",
    )
    with st.expander("How is this calculated?"):
        st.markdown(
            "**Est. profit $** = Sales x Interim GP% (before shrink). "
            "Reliable for ranking lines; not a reported GP$ figure.\n\n"
            "**Interim GP% (before shrink)** = the margin the line is priced to deliver, "
            "before any stock is lost.\n\n"
            "**GP% after shrink** = Interim GP% minus the points consumed by dump, "
            "adjustment, and clearance (also called ISGP%). "
            "The gap between the two columns is margin leaked to shrink.\n\n"
            "**Leaking** = GP$ lost >= $500 and margin gap >= 10 pts. These lines are "
            "well-ranged -- the fix is operational, not a price or range change.\n\n"
            "**Count correction -- verify count** = TSL went net-negative because the system "
            "found more stock than expected. This is a count artifact, not a real margin gain. "
            "Verify the physical count before reporting it up."
        )

    t = d.sort_values("est_profit_$", ascending=False).head(25).copy()
    t["gp_lost_$"] = t["sales"] * t["loss_gap"] / 100
    t["leaking"] = (t["loss_gap"] >= 10) & (t["gp_lost_$"] >= 500)

    def _gap_label(r: pd.Series) -> str:
        if r["gp_lost_$"] < 0:
            amt = abs(r["gp_lost_$"])
            val = f"-${amt / 1000:.1f}k" if amt >= 1000 else f"-${amt:.0f}"
            return f"{val}  - count correction -- verify count"
        val = (
            f"${r['gp_lost_$'] / 1000:.1f}k"
            if r["gp_lost_$"] >= 1000
            else f"${r['gp_lost_$']:.0f}"
        )
        return val + ("  leaking" if r["leaking"] else "")

    show = pd.DataFrame({
        "Article": t["article"],
        "Sales $": t["sales"].map(money),
        "Interim GP% (before shrink)": t["interim_pct"].map(pct),
        "GP% after shrink": t["isgp_pct"].map(pct),
        "GP$ lost to shrink": t.apply(_gap_label, axis=1),
        "TSL $": t["tsl_$"].map(money),
        "Est. profit $": t["est_profit_$"].map(money),
    })
    st.dataframe(show, hide_index=True, use_container_width=True, height=560)
    st.markdown(
        '<div class="footnote">Est. profit $ is a derived contribution '
        "(Sales x Interim GP%), reliable for ranking -- not a reported GP$ field.</div>",
        unsafe_allow_html=True,
    )


def render_loss(d: pd.DataFrame) -> None:
    st.markdown(
        "**Loss makers** -- lines ranked by dollars leaking. "
        "High rate = TSL >= 25% of sales. "
        "Driver tells you the fix: **adjustment** = theft/count; "
        "**dump** = ordering/rotation; **clearance** = managed markdown.",
    )
    with st.expander("How is this calculated?"):
        st.markdown(
            "**TSL $** = Total Stock Loss in dollars (Sales x TSL%). "
            "Dollar rank sets priority; percentage flags how abnormal the rate is.\n\n"
            "A large line losing proportionately is a different problem from a small line "
            "losing half its sales -- dollar first, then rate.\n\n"
            "**Driver** = the largest of Dump / Adjustment / Clearance for that line.\n\n"
            "**Check count** = TSL changed sign across periods -- likely a count or receiving "
            "correction, not a real swing in loss. Investigate before acting.\n\n"
            "Negative adjustment = system found more stock than expected. Not a real gain."
        )

    rank_by = st.radio(
        "Rank by",
        ["TSL $ (impact)", "TSL % (rate)"],
        horizontal=True,
        label_visibility="collapsed",
        key="loss_rank",
    )
    sort_col = "tsl_$" if rank_by.startswith("TSL $") else "tsl_pct"
    t = d.sort_values(sort_col, ascending=False).head(25).copy()

    def driver(r: pd.Series) -> str:
        comps = {
            "adjustment": abs(r["adj_$"]),
            "dump": r["dump_$"],
            "clearance": r["clr_$"],
        }
        return max(comps, key=comps.get)

    t["driver"] = t.apply(driver, axis=1)
    show = pd.DataFrame({
        "Article": t["article"],
        "TSL $": t["tsl_$"].map(money),
        "TSL %": t.apply(
            lambda r: f"{r['tsl_pct']:.1f}%"
            + ("  high rate" if r["tsl_pct"] >= 25 else ""),
            axis=1,
        ),
        "Sales $": t["sales"].map(money),
        "Dump $": t["dump_$"].map(money),
        "Adjust $": t["adj_$"].map(money),
        "Clear $": t["clr_$"].map(money),
        "Driver": t.apply(
            lambda r: r["driver"] + ("  check count" if r["swing"] else ""),
            axis=1,
        ),
    })
    st.dataframe(show, hide_index=True, use_container_width=True, height=560)
    st.markdown(
        '<div class="footnote">TSL$ reconciles to Sales x TSL%. Negative TSL is '
        "usually a count/receiving correction, not a gain -- read over a multi-period "
        "window.</div>",
        unsafe_allow_html=True,
    )


def render_dump(d: pd.DataFrame) -> None:
    st.markdown(
        "**Fresh dump** -- perishable waste ranked by dollars, not rate. "
        "High waste = Dump% >= 15%. "
        "High dump$ + low clearance$ = ordering or rotation problem.",
    )
    with st.expander("How is this calculated?"):
        st.markdown(
            "**Dump $** = dollar value of perishable stock written off.\n\n"
            "**Clear $ (alt)** = clearance markdown taken on the same lines. "
            "Clearance recovers some margin; prefer it over dumping where possible.\n\n"
            "Ranked by Dump $ not Dump%: a high-volume line dumping 8% correctly outranks "
            "a small line dumping 25%. The percentage is shown alongside for context."
        )

    t = d[d["dump_$"] > 0].sort_values("dump_$", ascending=False).head(25).copy()
    show = pd.DataFrame({
        "Article": t["article"],
        "Dump $": t.apply(
            lambda r: money(r["dump_$"])
            + ("  high waste" if r["dump_pct"] >= 15 else ""),
            axis=1,
        ),
        "Dump %": t["dump_pct"].map(pct),
        "Clear $ (alt)": t["clr_$"].map(money),
        "Sales $": t["sales"].map(money),
        "Interim GP% (before shrink)": t["interim_pct"].map(pct),
    })
    st.dataframe(show, hide_index=True, use_container_width=True, height=560)
    st.markdown(
        '<div class="footnote">Aligned with the corporate waste priority '
        "(Project LIFT, AI demand-sensing): fresh waste is surfaced as its own lens, "
        "no click required from the department card.</div>",
        unsafe_allow_html=True,
    )


# =====================================================================
# ABOUT TAB -- portfolio / hiring manager context
# =====================================================================

def render_about() -> None:

    st.markdown(
        '<div class="about-hero">'
        '<div class="eyebrow">Portfolio - Retail Analytics - Built on synthetic data</div>'
        '<div class="h-title">Metro Zone Deep Dive</div>'
        '<div class="h-sub" style="margin-bottom:0">'
        "A department-level GP% triage tool for Woolworths Metro stores. Replaces a manual, "
        "spreadsheet-driven desk review with a structured, priority-ordered analysis -- from "
        "store aggregate down to individual product lines in two clicks."
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="about-rule">', unsafe_allow_html=True)

    # ---- The Problem ----
    st.markdown('<div class="about-h">The problem</div>', unsafe_allow_html=True)
    st.markdown(
        "Managers review GP% daily, but the source tools -- P&L exports, stock loss reports, "
        "clearance summaries -- are siloed, unranked, and don't connect cause to action. "
        "Three failure modes recur:"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            '<div class="about-card">'
            "<b>Percentage-first thinking</b><br><br>"
            "Sorting by TSL% or Dump% promotes small lines with extreme rates over the large "
            "lines driving the real dollar loss. A line losing $4k at 9% matters more than one "
            "losing $80 at 40% -- the percentage view hides that."
            "</div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<div class="about-card">'
            "<b>All loss treated as one number</b><br><br>"
            "Dump, adjustment, and clearance each have a different owner and fix. Aggregating "
            "them into one shrink figure hides whether the fix is ordering (DM), theft (loss "
            "prevention), or ranging (buyer)."
            "</div>",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            '<div class="about-card">'
            "<b>No triage order</b><br><br>"
            "Departments get reviewed alphabetically or by habit, not by where GP% is worst. "
            "In a 45-minute review, the review order is the decision -- and leaving it to "
            "chance is a prioritisation failure disguised as process."
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="about-rule">', unsafe_allow_html=True)

    # ---- What it does ----
    st.markdown('<div class="about-h">What it does</div>', unsafe_allow_html=True)
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown(
            '<div class="about-card">'
            "<b>Level 1 -- store triage</b><br><br>"
            "One screen: Interim GP% vs LY, red-zone department count, stock loss trend, fresh "
            "waste bill. Departments sorted worst-first by GP% decline. Three auto-generated "
            "focus areas name the top 2-3 priorities and the exact lens to open -- so the "
            "manager acts without reading every card."
            "</div>",
            unsafe_allow_html=True,
        )
    with col_r:
        st.markdown(
            '<div class="about-card">'
            "<b>Level 2 -- three lenses</b><br><br>"
            "<b>Best lines</b>: top earners, and which are leaking margin operationally "
            "(large gap between GP% before and after shrink -- fix the loss, not the price).<br>"
            "<b>Loss makers</b>: dollars leaking, decomposed into dump / adjustment / clearance; "
            "the dominant driver names the owner.<br>"
            "<b>Fresh dump</b>: perishable waste by dollar value, with clearance shown as the "
            "preferred alternative."
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="about-rule">', unsafe_allow_html=True)

    # ---- Design decisions (kept full -- this is the analytical signal) ----
    st.markdown('<div class="about-h">Key design decisions</div>', unsafe_allow_html=True)
    st.markdown(
        "Deliberate responses to how retail reviews fail, not default dashboard conventions."
    )

    decisions = [
        (
            "Dollar rank over percentage rank -- everywhere",
            "Every loss lens sorts by dollar impact; a $4k line at 9% sits above a $200 line at "
            "40%. Percentage is shown alongside as an abnormality flag but never controls the "
            "sort. Percentage-first is the most common triage mistake in supermarket operations.",
        ),
        (
            "Interim GP%, not reported GP$, as the primary metric",
            "Interim GP% is the margin the range is priced to deliver; GP% after shrink (ISGP%) "
            "is what's actually delivered. The gap is the operational opportunity -- recoverable "
            "without touching range or price. This separates ranging/pricing decisions (category "
            "manager, buyer) from operational ones (store, DM).",
        ),
        (
            "TSL decomposed, with the dominant driver called out",
            "Dump = ordering / rotation / supplier. Adjustment = stock variance (theft, scan, "
            "receiving). Clearance = managed markdown, often correct. Surfacing the dominant "
            "driver on every card means the manager knows which conversation to have before "
            "leaving the dashboard.",
        ),
        (
            "Auto-generated focus areas close the insight-to-action gap",
            "A ranked dashboard still leaves a last-mile problem: read every card, synthesise, "
            "decide where to start. The focus areas derive 2-3 specific prompts from the data -- "
            "naming the department, the driving metric, and the lens to open.",
        ),
        (
            "Triage sort, not alphabetical or recency",
            "Worst-first by Interim GP% decline vs LY, TSL$ growth as tiebreaker. In a "
            "time-boxed review the sort order is a prioritisation decision -- made explicit "
            "rather than left to chance.",
        ),
    ]
    for title, detail in decisions:
        st.markdown(
            f'<div class="about-decision"><b>{title}</b><br><br>{detail}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="about-rule">', unsafe_allow_html=True)

    # ---- Compact reference: glossary + how-to in expanders ----
    with st.expander("Metric glossary"):
        glossary = pd.DataFrame({
            "Metric": [
                "Interim GP%", "GP% after shrink (ISGP%)", "Loss gap", "TSL $",
                "Dump $", "Adj $", "Clr $", "Est. profit $", "WoW",
            ],
            "What it measures": [
                "Margin before stock loss -- what the range is priced to deliver",
                "Margin after dump, adjustment, clearance -- what's actually delivered",
                "Interim GP% minus GP% after shrink -- points lost to operations",
                "Total stock loss in dollars (Sales x TSL%)",
                "Perishable write-off",
                "Unresolved stock variance -- theft, scan, receiving",
                "Managed markdown -- often the right call",
                "Sales x Interim GP% -- ranks lines by profit contribution",
                "Week-on-week Interim GP% movement -- is the problem accelerating",
            ],
        })
        st.dataframe(glossary, hide_index=True, use_container_width=True)

    with st.expander("How to use it"):
        st.markdown(
            "1. **Read the KPI strip** -- store GP% vs LY and red-zone count give the macro "
            "picture in 30 seconds.\n"
            "2. **Start with focus areas** -- they name the top priorities and the lens to open.\n"
            "3. **Open the worst department** -- already sorted worst-first; context bar shows "
            "gap to store average.\n"
            "4. **Pick the lens for your question** -- Loss Makers (where are the dollars), "
            "Fresh Dump (is waste the driver), Best Lines (are earners leaking).\n"
            "5. **Act on the driver, not the total** -- adjustment -> count/LP; dump -> ordering; "
            "clearance -> ranging. Each has a different owner."
        )

    st.markdown(
        '<div class="footnote">Python - pandas - Streamlit. Synthetic dataset modelled on the '
        "Woolworths Metro KPI structure; no real store, customer, or proprietary data is used.</div>",
        unsafe_allow_html=True,
    )

# =====================================================================
# ROUTER
# =====================================================================

tab_dash, tab_about = st.tabs(["Dashboard", "About this dashboard"])

with tab_dash:
    if st.session_state.dept is None:
        render_level1()
    else:
        render_level2(st.session_state.dept)

with tab_about:
    render_about()