#!/usr/bin/env python3
"""Fix top15 endpoint by directly editing app.py."""

import os

APP = os.path.join(os.path.dirname(__file__), "app.py")

with open(APP, encoding="utf-8") as f:
    content = f.read()


# ── 1. Replace DIVISION_ORDER with men's divisions only ─────────────────────
OLD_DIVISION_BLOCK = '''DIVISION_ORDER = [
    "Heavyweight",
    "Light Heavyweight",
    "Middleweight",
    "Welterweight",
    "Lightweight",
    "Featherweight",
    "Bantamweight",
    "Flyweight",
    "Women's Featherweight",
    "Women's Bantamweight",
    "Women's Flyweight",
    "Women's Strawweight"
]'''

NEW_DIVISION_BLOCK = '''DIVISION_ORDER = [
    "Flyweight",
    "Bantamweight",
    "Featherweight",
    "Lightweight",
    "Welterweight",
    "Middleweight",
    "Light Heavyweight",
    "Heavyweight"
]'''

if OLD_DIVISION_BLOCK in content:
    content = content.replace(OLD_DIVISION_BLOCK, NEW_DIVISION_BLOCK)
    print("Fixed DIVISION_ORDER: removed women's divisions.")
else:
    print("DIVISION_ORDER block not found or already updated.")


# ── 2. Fix top15_all division column check ──────────────────────────────────
OLD_TOP15_ALL_LINE = '''divs = [d for d in DIVISION_ORDER if d in fighter_stats_df["Weight_Class"].values]'''

NEW_TOP15_ALL_CODE = '''wc_col = "Weight_Class_Std" if "Weight_Class_Std" in fighter_stats_df.columns else "Weight_Class"
    available = fighter_stats_df[wc_col].dropna().unique().tolist()
    divs = [d for d in DIVISION_ORDER if d in available]'''

if OLD_TOP15_ALL_LINE in content:
    content = content.replace(OLD_TOP15_ALL_LINE, NEW_TOP15_ALL_CODE)
    print("Fixed top15_all: now uses Weight_Class_Std if available.")
else:
    print("top15_all line not found or already fixed.")


# ── 3. Fix top15_division filter line ───────────────────────────────────────
OLD_DIVISION_FILTER_LINE = '''df = fighter_stats_df[fighter_stats_df["Weight_Class"] == division].copy()'''

NEW_DIVISION_FILTER_CODE = '''wc_col = "Weight_Class_Std" if "Weight_Class_Std" in fighter_stats_df.columns else "Weight_Class"
    df = fighter_stats_df[fighter_stats_df[wc_col] == division].copy()'''

if OLD_DIVISION_FILTER_LINE in content:
    content = content.replace(OLD_DIVISION_FILTER_LINE, NEW_DIVISION_FILTER_CODE)
    print("Fixed top15_division: now filters using Weight_Class_Std if available.")
else:
    print("top15_division filter line not found or already fixed.")


# ── 4. Save updated app.py ──────────────────────────────────────────────────
with open(APP, "w", encoding="utf-8") as f:
    f.write(content)

print("Done. app.py top15 endpoint fixed.")