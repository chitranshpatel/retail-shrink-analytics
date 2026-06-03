# Metro Zone Deep Dive — Dashboard Redesign

A Streamlit implementation of the **Metro Zone Deep Dive** build specification: a
decision tool for Woolworths Metro store and department managers that converts a
dense, uniform data table into a triaged, drill-down dashboard.

> Portfolio project. All figures are **synthetic but internally consistent** — every
> sort, colour, flag and dollar figure behaves exactly as it would on real data.

---

## What it does

**Level 1 — Department triage landing**
- Departments ranked **worst-first by Interim GP% decline vs last year**, with **TSL$
  growth as the tie-break** (the spec's triage sort).
- A focal KPI strip: store Interim GP% vs LY (focal tile), total TSL$, fresh dump$,
  biggest mover.
- One card per department, **all components visible** (no hidden score): Sales$,
  Interim GP%, TSL$ with the **Dump / Adjustment / Clearance split shown beneath**.
- **Two card variants**: fresh / service departments carry a dedicated Dump$ figure;
  ambient departments show "—".
- **Status colour** on the left rail: red ≤ −3 pts, amber −3 to 0, green ≥ 0
  (Interim GP% vs LY).
- **Weekly / Monthly** period toggle, applied everywhere. Baseline = same period last year.

**Level 2 — Line detail (three lenses)**
- **Best lines** — ranked by est. profit contribution (Sales × Interim GP%), with ISGP%
  beside Interim GP% to expose the **loss gap**; lines with a gap ≥ 10 pts flagged
  *leaking* (well-bought but losing it operationally).
- **Loss makers** — ranked by TSL$, split into Dump / Adjustment / Clearance dollars,
  with a **driver** label and a *check count* flag for sign-swinging TSL.
- **Fresh dump** (fresh departments only) — ranked by **Dump$** (not %, not TSL), with
  Clearance$ beside it as the managed alternative; Dump% ≥ 15 flagged *high waste*.

All line views are **sortable dollar tables** — a scatter/quadrant was rejected because
it is unreadable beyond ~30 items, and departments have hundreds of lines.

---

## The validated dollar base

The whole design rests on one finding: **every percentage is a % of sales.** Because
`Interim GP% = ISGP% − TSL%` only subtracts validly if all three share the sales
denominator (and `Sales × Interim GP%` reconciles), all loss percentages convert to
reliable dollars:

```
Dump$        = Sales$ × Dump%
Adjustment$  = Sales$ × Adj%
Clearance$   = Sales$ × Clr%
TSL$         = Sales$ × TSL%
Est. profit$ = Sales$ × Interim GP%   (derived contribution — ranking-only, footnoted)
```

Negative TSL (a count finding *more* stock than expected) is treated as a likely
data/process artifact, not a gain — see the spec for the multi-period handling.

---

## Design notes (web-design-principles)

- **Design system first**: spacing tokens on a 4-based scale, REM type scale, a
  restrained palette (one ink, one canvas, navy + teal accents, functional R/A/G) —
  all in `design.py`, so components pick values rather than invent them.
- **Hierarchy**: the focal navy KPI tile and the triaged card order establish one clear
  focal point; secondary info (sub-splits, captions) is de-emphasised in weight/colour
  rather than the primary being shouted.
- **Depth, sparingly**: shadow + gradient reserved for the focal KPI and card hover; the
  status rail replaces a heavier border. Everything else stays flat.
- **Gestalt**: each card groups a department's metrics by proximity; the three lenses
  are visually identical tables so the eye learns the pattern once.

---

## From prototype to production: what it would take to ship this

This dashboard is built in Streamlit so the idea could be proven quickly. In real
life it probably wouldn't ship that way. Based on what's publicly known, Woolworths
uses Tableau for reporting and runs on Google Cloud. So for this section, let's
assume the dashboard gets rebuilt in **Tableau on top of a cloud data warehouse** —
a realistic home for it — and ask: what would make rolling it out to every store
hard?

The design itself travels fine. The triage logic, the three lenses, the dollar
maths, the driver labels — none of that depends on Streamlit. The hard parts are
everything around it. (To be clear, the points below are reasoned from the
screenshots and public information, not from any inside access to Woolworths'
systems.)

### Getting the data right

The prototype makes up its own numbers. A production version would pull live data
from the company's data warehouse, and that's where the real work sits.

The biggest one comes straight from the screenshots: the dashboard seems to work
almost entirely in percentages — ISGP%, Interim GP%, TSL% — rather than gross profit
in dollars per line. If that's right, then the "estimated profit" figure has to be
worked out as Sales × Interim GP%. That's fine for ranking lines against each other,
but it's a derived number, not a reported one. Before something like this went live,
someone would need to confirm that calculation holds up, or get a proper
gross-profit-in-dollars figure added to the data. That's a pipeline job, not a
dashboard one.

Then there's freshness. A store manager will assume the numbers are from this
morning. But stock loss data tends to lag — adjustments only land after a stock
count, deliveries after the paperwork clears. So the dashboard would need to be
honest about how old the numbers are, or people end up making calls on stale figures.

### Making sure each store only sees its own numbers

This is the most sensitive part. A manager in one store should see their store and
nobody else's. Across a large chain that isn't hundreds of separate dashboards — it's
one dashboard with strict rules about who sees which rows, tied to each person's
login and location. Get it wrong and you've shown one store's performance, and
possibly its theft data, to another. Tableau can handle this, but it has to be set up
carefully and tested hard.

It would also need to use the login people already have. No manager is going to
accept a separate password for one more tool.

### The loss data is touchy

The adjustment number is essentially a theft-and-error signal. Showing it widely has
people implications, not just technical ones — this kind of data feeds into how staff
get managed. So who's allowed to see adjustment-driven loss, and in how much detail,
would be a decision for the business to make before launch, rather than something
left switched on by default.

### Where people actually use it

This was designed for someone sitting at a desk. But a store manager spends most of
the day on the floor, often with a tablet or handheld rather than a big monitor. If
that's where they'd actually look at it, a wide table full of dollar columns is the
wrong shape, and the layout would need rethinking for a small screen. Worth checking
early, because it can change the whole design.

### Rolling it out without breaking trust

A lot of managers would use this, with very different comfort levels around data. The
sensible approach is to roll it out in stages rather than everywhere at once — pilot
it in a few stores, fix what's confusing, then go wide.

The fastest way to lose people is a number that doesn't match what they already see
in their current reports. If this dashboard says one thing and their existing report
says another — even because of a slightly different calculation or refresh time —
they'll stop trusting all of it. So the numbers would need to be reconciled against
whatever the existing source of truth is before launch.

And someone has to own it. When a figure looks wrong at 6am, the manager needs to
know who to tell, and trust it'll get fixed.

### The short version

The thinking behind this dashboard is the part that lasts — the validated dollar
base, the triage, the three decisions it's built around. Moving it into production
would be less about the design and more about four things: getting clean, current
data out of the warehouse; making sure every store sees only its own rows; handling
the sensitive loss data carefully; and rolling it out slowly enough that managers
trust it. The two I'd raise first are the apparent lack of a gross-profit-in-dollars
figure per line, and the per-store security setup.

---

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (default http://localhost:8501).

## Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit app — two-level routing, KPI strip, triage cards, three lenses |
| `data.py` | Synthetic data on the validated sales base + department triage aggregation |
| `design.py` | Design tokens and CSS (the design system) |
| `requirements.txt` | Dependencies |

## Known demo artifacts

- A handful of synthetic lines show **negative TSL** with an unusually high Interim GP%.
  This is the §3 "count correction" case by design; in production the multi-period swing
  flag would catch and contextualise it. Harmless in the demo.
- The one figure that remains a true estimate is **Est. profit $** (no GP-dollars-per-line
  exists in source). It is reliable for ranking and is footnoted in the UI accordingly.
