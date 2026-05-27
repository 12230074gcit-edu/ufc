#!/usr/bin/env python3
"""Fix top15 endpoint to use Weight_Class_Std instead of Weight_Class and keep men's divisions only."""

import os

APP = os.path.join(os.path.dirname(__file__), "app.py")

with open(APP, encoding="utf-8") as f:
    content = f.read()


# ── 1. Force men's divisions only ───────────────────────────────────────────
OLD_DIVISION_ORDER = '''DIVISION_ORDER = [
    "Heavyweight", "Light Heavyweight", "Middleweight", "Welterweight",
    "Lightweight", "Featherweight", "Bantamweight", "Flyweight",
    "Women's Featherweight", "Women's Bantamweight", "Women's Flyweight", "Women's Strawweight"
]'''

NEW_DIVISION_ORDER = '''DIVISION_ORDER = [
    "Flyweight",
    "Bantamweight",
    "Featherweight",
    "Lightweight",
    "Welterweight",
    "Middleweight",
    "Light Heavyweight",
    "Heavyweight"
]'''

if OLD_DIVISION_ORDER in content:
    content = content.replace(OLD_DIVISION_ORDER, NEW_DIVISION_ORDER)
    print("Fixed: removed women's divisions from DIVISION_ORDER")
else:
    print("DIVISION_ORDER old format not found. It may already be updated.")


# ── 2. Fix /api/top15 endpoint ──────────────────────────────────────────────
OLD = '''@app.route("/api/top15")
def top15_all():
    divs = [d for d in DIVISION_ORDER if d in fighter_stats_df["Weight_Class"].values]
    return jsonify({"divisions": divs})

@app.route("/api/top15/<division>")
def top15_division(division):
    df = fighter_stats_df[fighter_stats_df["Weight_Class"] == division].copy()'''

NEW = '''@app.route("/api/top15")
def top15_all():
    wc_col = "Weight_Class_Std" if "Weight_Class_Std" in fighter_stats_df.columns else "Weight_Class"
    available = fighter_stats_df[wc_col].dropna().unique().tolist()
    divs = [d for d in DIVISION_ORDER if d in available]
    return jsonify({"divisions": divs})

@app.route("/api/top15/<division>")
def top15_division(division):
    wc_col = "Weight_Class_Std" if "Weight_Class_Std" in fighter_stats_df.columns else "Weight_Class"
    df = fighter_stats_df[fighter_stats_df[wc_col] == division].copy()'''

if OLD in content:
    content = content.replace(OLD, NEW)
    print("Fixed: top15 now uses Weight_Class_Std")
else:
    print("Exact old top15 block not found. Trying line-by-line fallback...")

    old_line_1 = '    divs = [d for d in DIVISION_ORDER if d in fighter_stats_df["Weight_Class"].values]'
    new_line_1 = '''    wc_col = "Weight_Class_Std" if "Weight_Class_Std" in fighter_stats_df.columns else "Weight_Class"
    available = fighter_stats_df[wc_col].dropna().unique().tolist()
    divs = [d for d in DIVISION_ORDER if d in available]'''

    old_line_2 = '    df = fighter_stats_df[fighter_stats_df["Weight_Class"] == division].copy()'
    new_line_2 = '''    wc_col = "Weight_Class_Std" if "Weight_Class_Std" in fighter_stats_df.columns else "Weight_Class"
    df = fighter_stats_df[fighter_stats_df[wc_col] == division].copy()'''

    fixed_any = False

    if old_line_1 in content:
        content = content.replace(old_line_1, new_line_1)
        print("Fixed: top15_all division list line")
        fixed_any = True

    if old_line_2 in content:
        content = content.replace(old_line_2, new_line_2)
        print("Fixed: top15_division filter line")
        fixed_any = True

    if not fixed_any:
        if "/api/top15" in content:
            print("ERROR: top15 endpoint exists, but the expected lines were not found.")
            print("Open app.py and check if the endpoint was already modified.")
        else:
            print("ERROR: top15 endpoint not found at all.")


# ── 3. Save app.py ──────────────────────────────────────────────────────────
with open(APP, "w", encoding="utf-8") as f:
    f.write(content)

print("Done.")