"""
Design system for the Metro Zone dashboard.

Built per the web-design-principles skill:
- Spacing scale divisible by 4, exposed as tokens (rule 4).
- Restrained palette: one dark, one light, two accents + functional R/A/G (rule 4).
- One type scale (rule 4). Smaller text gets greater line-height.
- Depth (shadow, subtle gradient, accent rail) reserved for the few elements that
  earn emphasis — the triage cards and the focal KPI (rule 6).
- Hierarchy via size/weight/colour; secondary info de-emphasised, not just target boosted (rule 5).
"""

# ---- colour tokens ----
INK = "#1A2230"          # near-black text
INK_SOFT = "#5A6473"     # secondary text (de-emphasised)
INK_FAINT = "#9AA3B0"    # tertiary / captions
PAPER = "#FFFFFF"
CANVAS = "#F4F6F9"       # app background
LINE = "#E2E7EF"         # hairlines

NAVY = "#1F3A5F"         # primary brand accent
TEAL = "#2BA98A"         # secondary accent (sparingly)

GREEN = "#1D9E75"        # status: on/above LY
AMBER = "#E0931F"        # status: slipping
RED = "#D2453F"          # status: problem

GREEN_BG = "#E7F5EF"
AMBER_BG = "#FBF1DF"
RED_BG = "#FAE8E7"
NAVY_BG = "#EAF0F7"

# status thresholds (Interim GP% pts vs LY) — from spec §4.2
def status_color(delta_pts: float):
    if delta_pts <= -3:
        return RED, RED_BG, "Problem"
    if delta_pts < 0:
        return AMBER, AMBER_BG, "Slipping"
    return GREEN, GREEN_BG, "On track"


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {{
  --s1: 0.25rem;  /* 4px  */
  --s2: 0.5rem;   /* 8px  */
  --s3: 0.75rem;  /* 12px */
  --s4: 1rem;     /* 16px */
  --s5: 1.5rem;   /* 24px */
  --s6: 2rem;     /* 32px */
  --s7: 2.5rem;   /* 40px */
  --radius: 14px;
  --radius-sm: 9px;
}}

html, body, [class*="css"], .stApp {{
  font-family: 'Inter', -apple-system, sans-serif;
  color: {INK};
}}
.stApp {{ background: {CANVAS}; }}

/* tighten Streamlit's default chrome */
.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1180px; }}
#MainMenu, footer, header {{ visibility: hidden; }}

/* ---------- type scale ---------- */
.eyebrow {{
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.09em;
  text-transform: uppercase; color: {INK_FAINT}; margin-bottom: var(--s1);
}}
.h-title {{ font-size: 1.9rem; font-weight: 700; letter-spacing: -0.02em; color: {INK}; line-height: 1.15; }}
.h-sub {{ font-size: 0.95rem; color: {INK_SOFT}; line-height: 1.5; margin-top: var(--s1); }}
.section-head {{ font-size: 1.15rem; font-weight: 600; color: {INK}; margin: var(--s5) 0 var(--s3); }}

/* ---------- KPI strip ---------- */
.kpi-wrap {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--s3); margin: var(--s5) 0 var(--s6); }}
.kpi {{
  background: {PAPER}; border: 1px solid {LINE}; border-radius: var(--radius);
  padding: var(--s4) var(--s5);
}}
.kpi.focal {{
  background: linear-gradient(135deg, {NAVY} 0%, #2C5183 100%);
  border: none; box-shadow: 0 10px 24px -12px rgba(31,58,95,0.55);
}}
.kpi .lbl {{ font-size: 0.74rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: {INK_FAINT}; }}
.kpi.focal .lbl {{ color: rgba(255,255,255,0.72); }}
.kpi .val {{ font-size: 1.7rem; font-weight: 700; letter-spacing: -0.02em; margin-top: var(--s1); line-height: 1; }}
.kpi.focal .val {{ color: #fff; }}
.kpi .delta {{ font-size: 0.8rem; font-weight: 500; margin-top: var(--s2); }}

/* ---------- department triage card ---------- */
.dept-card {{
  background: {PAPER}; border: 1px solid {LINE}; border-radius: var(--radius);
  padding: var(--s4) var(--s5); margin-bottom: var(--s3);
  border-left: 4px solid {LINE};
  box-shadow: 0 1px 2px rgba(26,34,48,0.04);
  transition: box-shadow .15s ease;
}}
.dept-card:hover {{ box-shadow: 0 8px 20px -12px rgba(26,34,48,0.25); }}
.dept-name {{ font-size: 1.12rem; font-weight: 600; color: {INK}; }}
.dept-tag {{ font-size: 0.7rem; font-weight: 600; color: {TEAL};
  background: #E6F5F0; padding: 2px 8px; border-radius: 20px; margin-left: var(--s2); }}
.dept-tag.amb {{ color: {INK_FAINT}; background: #EEF1F5; }}

.metric-row {{ display: flex; gap: var(--s6); flex-wrap: wrap; align-items: flex-start; margin-top: var(--s2); }}
.metric {{ display: flex; flex-direction: column; gap: 1px; min-width: 90px; }}
.metric .m-lbl {{ font-size: 0.68rem; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; color: {INK_FAINT}; }}
.metric .m-val {{ font-size: 1.05rem; font-weight: 600; color: {INK}; }}
.metric .m-dlt {{ font-size: 0.74rem; font-weight: 500; }}
.split {{ font-size: 0.72rem; color: {INK_FAINT}; margin-top: 2px; }}

.pos {{ color: {GREEN}; }}
.neg {{ color: {RED}; }}
.warn {{ color: {AMBER}; }}
.muted {{ color: {INK_FAINT}; }}

.pill {{ font-size: 0.68rem; font-weight: 600; padding: 3px 9px; border-radius: 20px; }}

/* lens explainer */
.lens-note {{
  font-size: 0.8rem; color: {INK_SOFT}; line-height: 1.55;
  background: {NAVY_BG}; border-radius: var(--radius-sm);
  padding: var(--s3) var(--s4); margin: var(--s2) 0 var(--s4);
  border-left: 3px solid {NAVY};
}}
.flag {{ font-size: 0.66rem; font-weight: 700; padding: 2px 7px; border-radius: 6px; }}
.flag-leak {{ background: {RED_BG}; color: {RED}; }}
.flag-waste {{ background: {AMBER_BG}; color: {AMBER}; }}
.flag-swing {{ background: #ECE7F7; color: #6B4FBB; }}

/* buttons */
.stButton > button {{
  border-radius: var(--radius-sm); border: 1px solid {LINE};
  font-weight: 500; font-size: 0.85rem; color: {INK};
  background: {PAPER}; transition: all .12s ease;
}}
.stButton > button:hover {{ border-color: {NAVY}; color: {NAVY}; }}

.footnote {{ font-size: 0.72rem; color: {INK_FAINT}; line-height: 1.5; margin-top: var(--s4); font-style: italic; }}
</style>
"""
