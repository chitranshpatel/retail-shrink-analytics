"""
Synthetic data for the Metro Zone Deep Dive dashboard.

Everything is built on the validated finding from the spec: every percentage is a
% of sales, so all dollar fields derive cleanly as Sales$ x %.

    Dump$        = Sales$ x Dump%
    Adjustment$  = Sales$ x Adj%
    Clearance$   = Sales$ x Clr%
    TSL$         = Sales$ x TSL%   (TSL% = Dump% + Adj% + Clr%)
    Est. profit$ = Sales$ x Interim GP%
    Interim GP%  = ISGP% - TSL%

Figures are illustrative (portfolio demo), but internally consistent so every
sort, colour and flag in the UI behaves exactly as it would on real data.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

# (name, is_fresh)
DEPARTMENTS = [
    ("Fruit & Veg", True),
    ("Bakery", True),
    ("Deli", True),
    ("Meat & Seafood", True),
    ("Dairy & Chilled", False),
    ("Grocery", False),
    ("Frozen", False),
    ("Health & Beauty", False),
]

# subcategory pools per department -> realistic article names
ARTICLES = {
    "Fruit & Veg": [
        ("Strawberries 250g", "Berries"), ("Bananas Cavendish kg", "Tropical"),
        ("Bagged Salad Mix 200g", "Pre-pack"), ("Avocado Loose ea", "Fruit"),
        ("Mushroom Cup 200g", "Pre-pack"), ("Blueberries 125g", "Berries"),
        ("Baby Spinach 120g", "Pre-pack"), ("Tomatoes Truss kg", "Salad"),
        ("Seedless Grapes kg", "Tropical"), ("Cucumber Lebanese ea", "Salad"),
        ("Raspberries 125g", "Berries"), ("Rockmelon Half ea", "Melons"),
    ],
    "Bakery": [
        ("Sourdough Loaf", "In-store Bread"), ("Mud Cake Whole", "Cakes"),
        ("Dinner Rolls 6pk", "Bread Rolls"), ("Croissant 4pk", "Pastry"),
        ("Banana Bread", "Cakes"), ("Vienna Loaf", "In-store Bread"),
        ("Custard Tart 4pk", "Pastry"), ("Choc Chip Muffin 4pk", "Cakes"),
        ("Garlic Bread 2pk", "Bread Rolls"), ("Lamington 2pk", "Cakes"),
    ],
    "Deli": [
        ("Roast Chicken Hot ea", "Hot Food"), ("Cheese Tasty Block 500g", "Deli Cheese"),
        ("Sliced Ham 200g", "Smallgoods"), ("Shaved Turkey 150g", "Smallgoods"),
        ("Fresh Dip Trio", "Antipasto"), ("Olives Mixed 200g", "Antipasto"),
        ("Prosciutto 100g", "Smallgoods"), ("Antipasto Mix Tub", "Antipasto"),
        ("Bacon Rashers 250g", "Smallgoods"), ("Fetta Marinated 180g", "Deli Cheese"),
    ],
    "Meat & Seafood": [
        ("Beef Mince Premium 500g", "Beef"), ("Chicken Breast 1kg", "Poultry"),
        ("Salmon Portions 300g", "Seafood"), ("Pork Sausages 500g", "Pork"),
        ("Lamb Chops 600g", "Lamb"), ("Chicken Thigh 1kg", "Poultry"),
        ("Beef Scotch Fillet kg", "Beef"), ("Prawns Cooked 500g", "Seafood"),
        ("Pork Belly kg", "Pork"), ("Beef Sausages 500g", "Beef"),
    ],
    "Dairy & Chilled": [
        ("Full Cream Milk 2L", "White Milk"), ("Greek Yoghurt 1kg", "Yoghurt"),
        ("Block Butter 250g", "Butter"), ("Free Range Eggs 12pk", "Eggs"),
        ("Tasty Cheese Slices 250g", "Cheese"), ("Thickened Cream 300ml", "Cream"),
        ("Flavoured Milk 600ml", "Flavoured"), ("Cottage Cheese 250g", "Cheese"),
    ],
    "Grocery": [
        ("Infant Formula 900g", "Baby"), ("Pasta Dry 500g", "Pantry"),
        ("Energy Drink 4pk", "Drinks"), ("Coffee Beans 1kg", "Hot Drinks"),
        ("Breakfast Cereal 750g", "Pantry"), ("Olive Oil 1L", "Pantry"),
        ("Chocolate Block 180g", "Confectionery"), ("Sparkling Water 10pk", "Drinks"),
        ("Tinned Tomatoes 400g", "Pantry"), ("Laundry Liquid 2L", "Cleaning"),
    ],
    "Frozen": [
        ("Ice Cream 2L Tub", "Ice Cream"), ("Frozen Peas 1kg", "Vegetables"),
        ("Pizza Frozen 2pk", "Meals"), ("Fish Fingers 425g", "Seafood"),
        ("Frozen Berries 500g", "Fruit"), ("Garlic Bread Frozen", "Bakery"),
        ("Potato Chips 1kg", "Vegetables"), ("Gelato 1L", "Ice Cream"),
    ],
    "Health & Beauty": [
        ("Shampoo 400ml", "Hair Care"), ("Toothpaste 110g", "Oral"),
        ("Vitamin C 60pk", "Vitamins"), ("Hand Wash 250ml", "Body"),
        ("Paracetamol 100pk", "Pharmacy"), ("Razor Blades 4pk", "Shaving"),
        ("Sunscreen SPF50 200ml", "Body"), ("Deodorant 150ml", "Body"),
    ],
}


def _line_row(dept: str, is_fresh: bool, name: str, sub: str) -> dict:
    # base weekly sales — fresh staples skew higher
    sales = float(RNG.uniform(1500, 18000))

    # ISGP% — commercial margin before loss
    isgp = float(RNG.uniform(16, 48))

    # loss components as % of sales. fresh carries real dump; ambient barely any.
    if is_fresh:
        dump = float(max(0, RNG.normal(6, 6)))      # some lines spike high
        clr = float(max(0, RNG.normal(1.5, 1.2)))
    else:
        dump = float(max(0, RNG.normal(0.2, 0.4)))
        clr = float(max(0, RNG.normal(0.5, 0.6)))

    # adjustment can be negative (net positive count = "found" stock)
    adj = float(RNG.normal(1.0, 1.5))

    # occasional swing line: large sign-changing adjustment -> data integrity flag
    swing = RNG.random() < 0.08
    if swing:
        adj = float(RNG.choice([-1, 1]) * RNG.uniform(12, 22))

    tsl_pct = dump + adj + clr
    interim = isgp - tsl_pct

    return {
        "department": dept,
        "is_fresh": is_fresh,
        "article": name,
        "subcategory": sub,
        "sales": round(sales, 2),
        "asp": round(RNG.uniform(0.5, 28), 2),
        "isgp_pct": round(isgp, 1),
        "dump_pct": round(dump, 1),
        "adj_pct": round(adj, 1),
        "clr_pct": round(clr, 1),
        "tsl_pct": round(tsl_pct, 1),
        "interim_pct": round(interim, 1),
        "swing": swing,
    }


def build_lines() -> pd.DataFrame:
    rows = []
    for dept, is_fresh in DEPARTMENTS:
        pool = ARTICLES[dept]
        # repeat the pool a few times with variation so each dept has dozens of lines
        for rep in range(6):
            for name, sub in pool:
                label = name if rep == 0 else f"{name} (v{rep})"
                rows.append(_line_row(dept, is_fresh, label, sub))
    df = pd.DataFrame(rows)

    # derive dollar fields — all on the validated sales base
    df["dump_$"] = df["sales"] * df["dump_pct"] / 100
    df["adj_$"] = df["sales"] * df["adj_pct"] / 100
    df["clr_$"] = df["sales"] * df["clr_pct"] / 100
    df["tsl_$"] = df["sales"] * df["tsl_pct"] / 100
    df["est_profit_$"] = df["sales"] * df["interim_pct"] / 100
    df["loss_gap"] = (df["isgp_pct"] - df["interim_pct"]).round(1)

    # LY comparison: synthesise a last-year interim% so we can show variance.
    # bias some departments to be clearly worse YoY so triage has signal.
    dept_drift = {
        "Deli": -4.1, "Bakery": -3.4, "Fruit & Veg": -2.3, "Meat & Seafood": -1.5,
        "Dairy & Chilled": -0.9, "Grocery": -0.3, "Frozen": 0.4, "Health & Beauty": 0.8,
    }
    df["interim_ly_pct"] = df.apply(
        lambda r: round(r["interim_pct"] - dept_drift[r["department"]]
                        + RNG.normal(0, 1.2), 1), axis=1)
    df["sales_ly"] = (df["sales"] * RNG.uniform(0.9, 1.1, len(df))).round(2)
    df["tsl_ly_$"] = (df["tsl_$"] * RNG.uniform(0.7, 1.05, len(df))).round(2)

    return df


def department_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to department level for the Level 1 triage landing."""
    g = df.groupby(["department", "is_fresh"], as_index=False).agg(
        sales=("sales", "sum"),
        sales_ly=("sales_ly", "sum"),
        tsl_dollars=("tsl_$", "sum"),
        tsl_ly_dollars=("tsl_ly_$", "sum"),
        dump_dollars=("dump_$", "sum"),
        adj_dollars=("adj_$", "sum"),
        clr_dollars=("clr_$", "sum"),
        est_profit=("est_profit_$", "sum"),
    )
    # sales-weighted interim GP% this year and LY
    def wavg(sub, col):
        return np.average(df.loc[sub.index, col], weights=df.loc[sub.index, "sales"])

    interim_now, interim_ly = [], []
    for dept in g["department"]:
        sub = df[df["department"] == dept]
        interim_now.append(np.average(sub["interim_pct"], weights=sub["sales"]))
        interim_ly.append(np.average(sub["interim_ly_pct"], weights=sub["sales"]))
    g["interim_pct"] = np.round(interim_now, 1)
    g["interim_ly_pct"] = np.round(interim_ly, 1)
    g["interim_delta"] = (g["interim_pct"] - g["interim_ly_pct"]).round(1)
    g["sales_delta_pct"] = ((g["sales"] / g["sales_ly"] - 1) * 100).round(1)
    g["tsl_delta_dollars"] = (g["tsl_dollars"] - g["tsl_ly_dollars"]).round(0)

    # TRIAGE SORT: worst Interim GP% decline vs LY first; TSL$ growth as tie-break
    g = g.sort_values(
        ["interim_delta", "tsl_delta_dollars"],
        ascending=[True, False]
    ).reset_index(drop=True)
    return g


if __name__ == "__main__":
    d = build_lines()
    print(d.shape)
    print(department_summary(d)[["department", "interim_delta", "tsl_delta_dollars"]])
