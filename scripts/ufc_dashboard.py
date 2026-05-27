import pandas as pd
import numpy as np
import os
import warnings

from bokeh.plotting import figure, output_file, save
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.transform import linear_cmap
from bokeh.palettes import Viridis256, Plasma256, Category10, Category20

import seaborn as sns
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")


# Set paths
DATA_DIR = "../data"
OUTPUT_DIR = "../output"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# Load data
print("Loading data...")

events_df = pd.read_csv(f"{DATA_DIR}/Cleaned_Events.csv")
fighter_stats_df = pd.read_csv(f"{DATA_DIR}/Cleaned_Fighter_Stats.csv")
fights_df = pd.read_csv(f"{DATA_DIR}/Cleaned_Fights.csv")
fighters_df = pd.read_csv(f"{DATA_DIR}/Fixed_Cleaned_Fighters.csv")

print(f"Events: {len(events_df)}")
print(f"Fighter Stats: {len(fighter_stats_df)}")
print(f"Fights: {len(fights_df)}")
print(f"Fighters: {len(fighters_df)}")


# Data preprocessing
print("\nPreprocessing data...")

# Convert date
events_df["Date"] = pd.to_datetime(events_df["Date"])

# Merge fighter physical attributes with stats
fighter_stats_df = fighter_stats_df.merge(
    fighters_df[["Fighter_Id", "height_cm", "weight_kg", "reach_cm"]],
    on="Fighter_Id",
    how="left"
)

# Clean weight class names
fights_df["Weight_Class"] = fights_df["Weight_Class"].str.upper().str.strip()
fighter_stats_df["Weight_Class"] = fighter_stats_df["Weight_Class"].str.upper().str.strip()

# Standardize weight class names
weight_class_mapping = {
    "BANTAMWEIGHT": "Bantamweight",
    "FEATHERWEIGHT": "Featherweight",
    "FLYWEIGHT": "Flyweight",
    "HEAVYWEIGHT": "Heavyweight",
    "LIGHT HEAVYWEIGHT": "Light Heavyweight",
    "LIGHTWEIGHT": "Lightweight",
    "MIDDLEWEIGHT": "Middleweight",
    "WELTERWEIGHT": "Welterweight",
    "WOMEN'S BANTAMWEIGHT": "Women's Bantamweight",
    "WOMEN'S FEATHERWEIGHT": "Women's Featherweight",
    "WOMEN'S FLYWEIGHT": "Women's Flyweight",
    "WOMEN'S STRAWWEIGHT": "Women's Strawweight",
}

fights_df["Weight_Class_Standard"] = fights_df["Weight_Class"].map(weight_class_mapping)
fighter_stats_df["Weight_Class_Standard"] = fighter_stats_df["Weight_Class"].map(weight_class_mapping)

# Merge events with fights to get dates
fights_df = fights_df.merge(events_df[["Event_Id", "Date"]], on="Event_Id", how="left")
fights_df["Year"] = fights_df["Date"].dt.year

print("Data preprocessing complete.")


# ============================================
# HELPER FUNCTIONS
# ============================================

def style_plot(p):
    p.background_fill_color = "#ffffff"
    p.border_fill_color = "#ffffff"
    p.outline_line_color = "#cccccc"

    p.title.text_font_size = "14pt"
    p.title.text_font_style = "bold"

    p.xaxis.axis_label_text_font_size = "10pt"
    p.yaxis.axis_label_text_font_size = "10pt"

    p.xaxis.major_label_text_font_size = "8pt"
    p.yaxis.major_label_text_font_size = "8pt"

    p.grid.grid_line_alpha = 0.3

    # Make pan tool active by default
    p.toolbar.active_drag = "auto"

    # Legend styling
    if p.legend:
        p.legend.location = "top_left"
        p.legend.click_policy = "hide"
        p.legend.background_fill_alpha = 0.85
        p.legend.border_line_color = "#cccccc"
        p.legend.label_text_font_size = "8pt"

    return p


def bokeh_scatter(data, x_col, y_col, title, x_label, y_label, color_col, palette):
    clean = data[[x_col, y_col, color_col, "Full Name"]].dropna().copy()

    source = ColumnDataSource(clean)

    mapper = linear_cmap(
        field_name=color_col,
        palette=palette,
        low=float(clean[color_col].min()),
        high=float(clean[color_col].max())
    )

    p = figure(
        title=title,
        x_axis_label=x_label,
        y_axis_label=y_label,
        width=430,
        height=340,
        tools="pan,wheel_zoom,box_zoom,reset,save",
        active_drag="pan"
    )

    p.circle(
        x=x_col,
        y=y_col,
        size=6,
        source=source,
        color=mapper,
        alpha=0.75,
        legend_label=title
    )

    p.add_tools(HoverTool(tooltips=[
        ("Fighter", "@{Full Name}"),
        (x_label, f"@{{{x_col}}}"),
        (y_label, f"@{{{y_col}}}"),
    ]))

    return style_plot(p)


def bokeh_bar(data, x_col, y_col, title, x_label, y_label, color="#d20a0a", width=430, height=340):
    clean = data[[x_col, y_col]].dropna().copy()
    clean[x_col] = clean[x_col].astype(str)

    source = ColumnDataSource(clean)
    factors = clean[x_col].tolist()

    p = figure(
        title=title,
        x_range=factors,
        x_axis_label=x_label,
        y_axis_label=y_label,
        width=width,
        height=height,
        tools="pan,wheel_zoom,box_zoom,reset,save",
        active_drag="pan"
    )

    p.vbar(
        x=x_col,
        top=y_col,
        width=0.75,
        source=source,
        color=color,
        alpha=0.85,
        legend_label=title
    )

    p.add_tools(HoverTool(tooltips=[
        (x_label, f"@{{{x_col}}}"),
        (y_label, f"@{{{y_col}}}{{0.00}}"),
    ]))

    p.xaxis.major_label_orientation = 0.9

    return style_plot(p)


def bokeh_line(data, x_col, y_col, title, x_label, y_label, color="#d20a0a", width=430, height=340):
    clean = data[[x_col, y_col]].dropna().copy()

    source = ColumnDataSource(clean)

    p = figure(
        title=title,
        x_axis_label=x_label,
        y_axis_label=y_label,
        width=width,
        height=height,
        tools="pan,wheel_zoom,box_zoom,reset,save",
        active_drag="pan"
    )

    p.line(
        x=x_col,
        y=y_col,
        source=source,
        line_width=3,
        color=color,
        legend_label=title
    )

    p.circle(
        x=x_col,
        y=y_col,
        source=source,
        size=7,
        color=color,
        alpha=0.85,
        legend_label=title
    )

    p.add_tools(HoverTool(tooltips=[
        (x_label, f"@{{{x_col}}}"),
        (y_label, f"@{{{y_col}}}{{0.00}}"),
    ]))

    return style_plot(p)


def save_seaborn_heatmap(corr_data, filename_png, filename_html, title):
    plt.figure(figsize=(11, 9))

    sns.heatmap(
        corr_data,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={"label": "Correlation"}
    )

    plt.title(title, fontsize=16, fontweight="bold", pad=20)
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()

    png_path = f"{OUTPUT_DIR}/{filename_png}"
    html_path = f"{OUTPUT_DIR}/{filename_html}"

    plt.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close()

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: #ffffff;
            font-family: Arial, sans-serif;
            text-align: center;
        }}

        img {{
            max-width: 100%;
            height: auto;
        }}
    </style>
</head>
<body>
    <img src="{filename_png}" alt="{title}">
</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)


def categorize_method(method):
    if pd.isna(method):
        return "Unknown"

    method = str(method).upper()

    if "KO" in method or "TKO" in method:
        return "KO/TKO"
    elif "SUB" in method or "CHOKE" in method or "ARM" in method:
        return "Submission"
    elif "DEC" in method:
        return "Decision"
    else:
        return "Other"


# ============================================
# ANALYSIS 1: Physical Attributes vs Performance Metrics
# ============================================

print("\nGenerating Physical Attributes vs Performance Metrics analysis...")

# Filter fighters with complete data
physical_data = fighter_stats_df[
    (fighter_stats_df["height_cm"].notna()) &
    (fighter_stats_df["weight_kg"].notna()) &
    (fighter_stats_df["reach_cm"].notna()) &
    (fighter_stats_df["Win_Rate"].notna())
].copy()

p1 = bokeh_scatter(
    physical_data,
    "height_cm",
    "Win_Rate",
    "Height vs Win Rate",
    "Height (cm)",
    "Win Rate",
    "Win_Rate",
    Viridis256
)

p2 = bokeh_scatter(
    physical_data,
    "weight_kg",
    "Win_Rate",
    "Weight vs Win Rate",
    "Weight (kg)",
    "Win Rate",
    "Win_Rate",
    Viridis256
)

p3 = bokeh_scatter(
    physical_data,
    "reach_cm",
    "Win_Rate",
    "Reach vs Win Rate",
    "Reach (cm)",
    "Win Rate",
    "Win_Rate",
    Viridis256
)

p4 = bokeh_scatter(
    physical_data,
    "height_cm",
    "Sig. Str. %",
    "Height vs Striking Accuracy",
    "Height (cm)",
    "Striking Accuracy %",
    "Sig. Str. %",
    Plasma256
)

p5 = bokeh_scatter(
    physical_data,
    "weight_kg",
    "Sig. Str. %",
    "Weight vs Striking Accuracy",
    "Weight (kg)",
    "Striking Accuracy %",
    "Sig. Str. %",
    Plasma256
)

p6 = bokeh_scatter(
    physical_data,
    "reach_cm",
    "Sig. Str. %",
    "Reach vs Striking Accuracy",
    "Reach (cm)",
    "Striking Accuracy %",
    "Sig. Str. %",
    Plasma256
)

fig1 = gridplot(
    [[p1, p2, p3], [p4, p5, p6]],
    sizing_mode="stretch_width"
)

output_file(
    f"{OUTPUT_DIR}/physical_attributes_vs_performance.html",
    title="Physical Attributes vs Performance Metrics"
)

save(fig1)

print("Saved: physical_attributes_vs_performance.html")


# Correlation heatmap for physical attributes and performance
corr_metrics = [
    "height_cm",
    "weight_kg",
    "reach_cm",
    "Win_Rate",
    "Sig. Str. %",
    "KO Rate",
    "SUB Rate",
    "TD",
    "SUB"
]

corr_data = physical_data[corr_metrics].corr()

save_seaborn_heatmap(
    corr_data,
    "correlation_heatmap.png",
    "correlation_heatmap.html",
    "Correlation Matrix: Physical Attributes vs Performance Metrics"
)

print("Saved: correlation_heatmap.html")


# ============================================
# ANALYSIS 2: Fight Outcomes Analysis
# ============================================

print("\nGenerating Fight Outcomes analysis...")

# Analyze fight outcomes by performance metrics
fight_outcomes = fights_df.copy()
fight_outcomes["Method_Category"] = fight_outcomes["Method"].str.upper()

# Add Win_Method to fights_df for use in later analysis
fights_df["Win_Method"] = fights_df["Method"].apply(categorize_method)
fight_outcomes["Win_Method"] = fight_outcomes["Method"].apply(categorize_method)

# Calculate average performance metrics by win method
performance_by_method = fight_outcomes.groupby("Win_Method").agg({
    "KD_1": "mean",
    "STR_1": "mean",
    "TD_1": "mean",
    "SUB_1": "mean",
    "Sig. Str. %_1": "mean",
    "Ctrl_1": "mean"
}).reset_index()

b1 = bokeh_bar(
    performance_by_method,
    "Win_Method",
    "KD_1",
    "Avg Knockdowns",
    "Win Method",
    "Avg Knockdowns",
    "#8ecae6"
)

b2 = bokeh_bar(
    performance_by_method,
    "Win_Method",
    "STR_1",
    "Avg Strikes",
    "Win Method",
    "Avg Strikes",
    "#90be6d"
)

b3 = bokeh_bar(
    performance_by_method,
    "Win_Method",
    "TD_1",
    "Avg Takedowns",
    "Win Method",
    "Avg Takedowns",
    "#f28482"
)

b4 = bokeh_bar(
    performance_by_method,
    "Win_Method",
    "SUB_1",
    "Avg Submissions",
    "Win Method",
    "Avg Submissions",
    "#f6d365"
)

b5 = bokeh_bar(
    performance_by_method,
    "Win_Method",
    "Sig. Str. %_1",
    "Striking Accuracy %",
    "Win Method",
    "Striking Accuracy %",
    "#ffafcc"
)

b6 = bokeh_bar(
    performance_by_method,
    "Win_Method",
    "Ctrl_1",
    "Control Time",
    "Win Method",
    "Control Time",
    "#cdb4db"
)

fig3 = gridplot(
    [[b1, b2, b3], [b4, b5, b6]],
    sizing_mode="stretch_width"
)

output_file(
    f"{OUTPUT_DIR}/fight_outcomes_analysis.html",
    title="Average Performance Metrics by Win Method"
)

save(fig3)

print("Saved: fight_outcomes_analysis.html")


# ============================================
# ANALYSIS 3: Weight Class Patterns
# ============================================

print("\nGenerating Weight Class Patterns analysis...")

# Analyze patterns across weight classes
weight_class_stats = fighter_stats_df.groupby("Weight_Class_Standard").agg({
    "height_cm": "mean",
    "weight_kg": "mean",
    "reach_cm": "mean",
    "Win_Rate": "mean",
    "Sig. Str. %": "mean",
    "KO Rate": "mean",
    "SUB Rate": "mean",
    "TD": "mean",
    "SUB": "mean"
}).reset_index()

weight_class_stats = weight_class_stats.sort_values("weight_kg")
weight_class_stats["Weight_Class_Standard"] = weight_class_stats["Weight_Class_Standard"].astype(str)

source_wc = ColumnDataSource(weight_class_stats)
weight_classes = weight_class_stats["Weight_Class_Standard"].tolist()

w1 = figure(
    title="Physical Attributes by Weight Class",
    x_range=weight_classes,
    x_axis_label="Weight Class",
    y_axis_label="Measurement",
    width=650,
    height=400,
    tools="pan,wheel_zoom,box_zoom,reset,save",
    active_drag="pan"
)

w1.line(
    x="Weight_Class_Standard",
    y="height_cm",
    source=source_wc,
    line_width=3,
    color="#1f77b4",
    legend_label="Height (cm)"
)

w1.circle(
    x="Weight_Class_Standard",
    y="height_cm",
    source=source_wc,
    size=7,
    color="#1f77b4",
    legend_label="Height (cm)"
)

w1.line(
    x="Weight_Class_Standard",
    y="weight_kg",
    source=source_wc,
    line_width=3,
    color="#d62728",
    legend_label="Weight (kg)"
)

w1.circle(
    x="Weight_Class_Standard",
    y="weight_kg",
    source=source_wc,
    size=7,
    color="#d62728",
    legend_label="Weight (kg)"
)

w1.line(
    x="Weight_Class_Standard",
    y="reach_cm",
    source=source_wc,
    line_width=3,
    color="#2ca02c",
    legend_label="Reach (cm)"
)

w1.circle(
    x="Weight_Class_Standard",
    y="reach_cm",
    source=source_wc,
    size=7,
    color="#2ca02c",
    legend_label="Reach (cm)"
)

w1.add_tools(HoverTool(tooltips=[
    ("Weight Class", "@Weight_Class_Standard"),
    ("Height", "@height_cm{0.00}"),
    ("Weight", "@weight_kg{0.00}"),
    ("Reach", "@reach_cm{0.00}"),
]))

w1.xaxis.major_label_orientation = 0.9

style_plot(w1)

w2 = bokeh_bar(
    weight_class_stats,
    "Weight_Class_Standard",
    "Win_Rate",
    "Win Rates by Weight Class",
    "Weight Class",
    "Win Rate",
    "#9467bd",
    width=650,
    height=400
)

w3 = bokeh_bar(
    weight_class_stats,
    "Weight_Class_Standard",
    "KO Rate",
    "KO/TKO Rates by Weight Class",
    "Weight Class",
    "KO Rate",
    "#ff7f0e",
    width=650,
    height=400
)

w4 = bokeh_bar(
    weight_class_stats,
    "Weight_Class_Standard",
    "SUB Rate",
    "Submission Rates by Weight Class",
    "Weight Class",
    "Submission Rate",
    "#17becf",
    width=650,
    height=400
)

fig4 = gridplot(
    [[w1, w2], [w3, w4]],
    sizing_mode="stretch_width"
)

output_file(
    f"{OUTPUT_DIR}/weight_class_patterns.html",
    title="Weight Class Patterns Analysis"
)

save(fig4)

print("Saved: weight_class_patterns.html")


# ============================================
# ANALYSIS 4: Win Methods Correlation with Physical Attributes
# ============================================

print("\nGenerating Win Methods Correlation analysis...")

# Merge fight data with fighter physical attributes
fights_with_physical = fights_df.merge(
    fighters_df[["Fighter_Id", "height_cm", "weight_kg", "reach_cm"]],
    left_on="Fighter_Id_1",
    right_on="Fighter_Id",
    how="left"
)

fights_with_physical["Win_Method"] = fights_with_physical["Method"].apply(categorize_method)

# Calculate average physical attributes by win method
physical_by_method = fights_with_physical.groupby("Win_Method").agg({
    "height_cm": "mean",
    "weight_kg": "mean",
    "reach_cm": "mean"
}).reset_index()

m1 = bokeh_bar(
    physical_by_method,
    "Win_Method",
    "height_cm",
    "Avg Height by Win Method",
    "Win Method",
    "Height (cm)",
    "#8ecae6"
)

m2 = bokeh_bar(
    physical_by_method,
    "Win_Method",
    "weight_kg",
    "Avg Weight by Win Method",
    "Win Method",
    "Weight (kg)",
    "#f28482"
)

m3 = bokeh_bar(
    physical_by_method,
    "Win_Method",
    "reach_cm",
    "Avg Reach by Win Method",
    "Win Method",
    "Reach (cm)",
    "#90be6d"
)

fig5 = gridplot(
    [[m1, m2, m3]],
    sizing_mode="stretch_width"
)

output_file(
    f"{OUTPUT_DIR}/win_methods_correlation.html",
    title="Physical Attributes by Win Method"
)

save(fig5)

print("Saved: win_methods_correlation.html")


# ============================================
# ANALYSIS 5: Performance Trends Over Time
# ============================================

print("\nGenerating Performance Trends Over Time analysis...")

# Calculate yearly averages
yearly_stats = fights_df.groupby("Year").agg({
    "KD_1": "mean",
    "STR_1": "mean",
    "TD_1": "mean",
    "SUB_1": "mean",
    "Sig. Str. %_1": "mean",
    "Ctrl_1": "mean"
}).reset_index()

yearly_stats = yearly_stats.sort_values("Year")

t1 = bokeh_line(
    yearly_stats,
    "Year",
    "KD_1",
    "Avg Knockdowns Over Time",
    "Year",
    "Avg Knockdowns",
    "#1f77b4"
)

t2 = bokeh_line(
    yearly_stats,
    "Year",
    "STR_1",
    "Avg Strikes Over Time",
    "Year",
    "Avg Strikes",
    "#d62728"
)

t3 = bokeh_line(
    yearly_stats,
    "Year",
    "TD_1",
    "Avg Takedowns Over Time",
    "Year",
    "Avg Takedowns",
    "#2ca02c"
)

t4 = bokeh_line(
    yearly_stats,
    "Year",
    "SUB_1",
    "Avg Submissions Over Time",
    "Year",
    "Avg Submissions",
    "#9467bd"
)

t5 = bokeh_line(
    yearly_stats,
    "Year",
    "Sig. Str. %_1",
    "Striking Accuracy Over Time",
    "Year",
    "Striking Accuracy %",
    "#ff7f0e"
)

t6 = bokeh_line(
    yearly_stats,
    "Year",
    "Ctrl_1",
    "Control Time Over Time",
    "Year",
    "Control Time",
    "#8c564b"
)

fig6 = gridplot(
    [[t1, t2, t3], [t4, t5, t6]],
    sizing_mode="stretch_width"
)

output_file(
    f"{OUTPUT_DIR}/performance_trends_over_time.html",
    title="Performance Trends Over Time"
)

save(fig6)

print("Saved: performance_trends_over_time.html")


# Win method distribution over time
win_method_yearly = fights_df.groupby(["Year", "Win_Method"]).size().reset_index(name="Count")

win_method_pivot = win_method_yearly.pivot(
    index="Year",
    columns="Win_Method",
    values="Count"
).fillna(0)

win_method_pivot.index = win_method_pivot.index.astype(str)
win_method_pivot = win_method_pivot.reset_index()

methods = [col for col in win_method_pivot.columns if col != "Year"]

source_win = ColumnDataSource(win_method_pivot)

if len(methods) <= 10:
    colors = Category10[10]
else:
    colors = Category20[20]

fig7 = figure(
    title="Win Method Distribution Over Time",
    x_range=win_method_pivot["Year"].tolist(),
    x_axis_label="Year",
    y_axis_label="Number of Fights",
    width=1000,
    height=500,
    tools="pan,wheel_zoom,box_zoom,reset,save",
    active_drag="pan"
)

fig7.vbar_stack(
    methods,
    x="Year",
    width=0.8,
    color=colors[:len(methods)],
    source=source_win,
    legend_label=methods
)

fig7.add_tools(HoverTool(tooltips=[
    ("Year", "@Year"),
]))

fig7.xaxis.major_label_orientation = 0.9

style_plot(fig7)

output_file(
    f"{OUTPUT_DIR}/win_method_distribution_over_time.html",
    title="Win Method Distribution Over Time"
)

save(fig7)

print("Saved: win_method_distribution_over_time.html")


# ============================================
# COMPREHENSIVE DASHBOARD
# ============================================

print("\nCreating comprehensive interactive dashboard...")

dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>UFC Fighter Analysis Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;600;700&family=Roboto:wght@300;400;500&display=swap" rel="stylesheet">

    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Roboto', sans-serif;
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%);
            min-height: 100vh;
            color: #ffffff;
        }

        .header {
            text-align: center;
            background: linear-gradient(180deg, #d20a0a 0%, #8b0000 100%);
            padding: 40px 20px;
            border-bottom: 4px solid #c9a227;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            position: relative;
            overflow: hidden;
        }

        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="50" font-size="50" fill="rgba(255,255,255,0.05)">⚔</text></svg>');
            background-size: 100px;
            animation: float 20s linear infinite;
        }

        @keyframes float {
            0% {
                transform: translateY(0) rotate(0deg);
            }

            100% {
                transform: translateY(-100px) rotate(360deg);
            }
        }

        .header h1 {
            font-family: 'Oswald', sans-serif;
            font-size: 3.5em;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 3px;
            color: #ffffff;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            position: relative;
            z-index: 1;
        }

        .header p {
            font-size: 1.2em;
            color: #c9a227;
            font-weight: 500;
            margin-top: 10px;
            position: relative;
            z-index: 1;
        }

        .header-divider {
            height: 4px;
            background: linear-gradient(90deg, transparent, #c9a227, transparent);
            margin: 20px auto;
            width: 60%;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px 20px;
        }

        .tabs {
            display: flex;
            background: linear-gradient(180deg, #2d2d2d 0%, #1a1a1a 100%);
            border-radius: 10px 10px 0 0;
            overflow: hidden;
            border: 2px solid #c9a227;
            border-bottom: none;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }

        .tab {
            flex: 1;
            padding: 18px 15px;
            text-align: center;
            cursor: pointer;
            background: transparent;
            color: #ffffff;
            border: none;
            transition: all 0.3s ease;
            font-family: 'Oswald', sans-serif;
            font-size: 1.1em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
        }

        .tab:hover {
            background: rgba(201, 162, 39, 0.2);
            color: #c9a227;
        }

        .tab.active {
            background: linear-gradient(180deg, #d20a0a 0%, #8b0000 100%);
            color: #ffffff;
            font-weight: 700;
        }

        .tab.active::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 60%;
            height: 3px;
            background: #c9a227;
        }

        .content {
            background: linear-gradient(180deg, #2d2d2d 0%, #1a1a1a 100%);
            padding: 30px;
            border-radius: 0 0 10px 10px;
            display: none;
            border: 2px solid #c9a227;
            border-top: none;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }

        .content.active {
            display: block;
            animation: fadeIn 0.5s ease;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }

            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .chart-container {
            margin: 25px 0;
            background: rgba(0, 0, 0, 0.3);
            border: 2px solid #c9a227;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }

        .summary {
            background: linear-gradient(135deg, rgba(210, 10, 10, 0.1) 0%, rgba(139, 0, 0, 0.1) 100%);
            padding: 25px;
            border-radius: 8px;
            margin: 25px 0;
            border-left: 4px solid #d20a0a;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }

        .summary h3 {
            font-family: 'Oswald', sans-serif;
            color: #c9a227;
            font-size: 1.5em;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .summary p {
            color: #e0e0e0;
            line-height: 1.6;
            margin-bottom: 15px;
        }

        .summary ul {
            list-style: none;
            padding-left: 0;
        }

        .summary li {
            color: #e0e0e0;
            padding: 10px 0;
            padding-left: 25px;
            position: relative;
            line-height: 1.5;
        }

        .summary li::before {
            content: '⚔';
            position: absolute;
            left: 0;
            color: #d20a0a;
            font-size: 1.2em;
        }

        .summary strong {
            color: #c9a227;
            font-weight: 600;
        }

        h2 {
            font-family: 'Oswald', sans-serif;
            color: #ffffff;
            font-size: 2.2em;
            border-bottom: 3px solid #d20a0a;
            padding-bottom: 15px;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }

        iframe {
            border-radius: 5px;
            background: #ffffff;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 25px 0;
        }

        .stat-card {
            background: linear-gradient(135deg, rgba(210, 10, 10, 0.2) 0%, rgba(139, 0, 0, 0.2) 100%);
            padding: 20px;
            border-radius: 8px;
            border: 2px solid #c9a227;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-card h4 {
            font-family: 'Oswald', sans-serif;
            color: #c9a227;
            font-size: 1.3em;
            margin-bottom: 10px;
            text-transform: uppercase;
        }

        .stat-card .value {
            font-size: 2em;
            font-weight: 700;
            color: #ffffff;
        }
    </style>
</head>

<body>
    <div class="header">
        <h1>⚔ UFC Fighter Analysis Dashboard ⚔</h1>
        <div class="header-divider"></div>
        <p>Analyze Physical Attributes & Performance Metrics</p>
    </div>

    <div class="container">
        <div class="tabs">
            <button class="tab active" onclick="showTab('overview', event)">Overview</button>
            <button class="tab" onclick="showTab('physical', event)">Physical Attributes</button>
            <button class="tab" onclick="showTab('outcomes', event)">Fight Outcomes</button>
            <button class="tab" onclick="showTab('weight', event)">Weight Classes</button>
            <button class="tab" onclick="showTab('trends', event)">Trends Over Time</button>
        </div>

        <div id="overview" class="content active">
            <h2>📊 Dashboard Overview</h2>

            <div class="summary">
                <h3>🔍 Key Findings Summary</h3>
                <p>This dashboard provides comprehensive analysis of UFC fighters' physical attributes and their impact on performance metrics.</p>

                <ul>
                    <li><strong>Physical Attributes:</strong> Height, weight, and reach correlations with win rates and striking accuracy</li>
                    <li><strong>Fight Outcomes:</strong> Performance metrics such as knockdowns, strikes, takedowns, submissions, and control time by win method</li>
                    <li><strong>Weight Classes:</strong> Patterns and competitive advantages across different weight divisions</li>
                    <li><strong>Win Methods:</strong> Correlation between physical attributes and KO/TKO, submission, or decision wins</li>
                    <li><strong>Trends:</strong> Performance evolution over time using aggregated statistics</li>
                </ul>
            </div>

            <div class="chart-container">
                <iframe src="correlation_heatmap.html" width="100%" height="800" frameborder="0"></iframe>
            </div>
        </div>

        <div id="physical" class="content">
            <h2>📏 Physical Attributes vs Performance Metrics</h2>

            <div class="summary">
                <p>Analysis of how height, weight, and reach correlate with fighter performance metrics including win rates and striking accuracy.</p>
            </div>

            <div class="chart-container">
                <iframe src="physical_attributes_vs_performance.html" width="100%" height="800" frameborder="0"></iframe>
            </div>
        </div>

        <div id="outcomes" class="content">
            <h2>🥊 Fight Outcomes Analysis</h2>

            <div class="summary">
                <p>Examination of fight outcomes in relation to striking accuracy, takedown success, submission attempts, and control time across different win methods.</p>
            </div>

            <div class="chart-container">
                <iframe src="fight_outcomes_analysis.html" width="100%" height="700" frameborder="0"></iframe>
            </div>

            <div class="chart-container">
                <iframe src="win_methods_correlation.html" width="100%" height="400" frameborder="0"></iframe>
            </div>
        </div>

        <div id="weight" class="content">
            <h2>⚖️ Weight Class Patterns</h2>

            <div class="summary">
                <p>Study of patterns across different weight classes to identify competitive advantages and performance variations.</p>
            </div>

            <div class="chart-container">
                <iframe src="weight_class_patterns.html" width="100%" height="800" frameborder="0"></iframe>
            </div>
        </div>

        <div id="trends" class="content">
            <h2>📈 Performance Trends Over Time</h2>

            <div class="summary">
                <p>Exploration of trends in fighter performance over time using aggregated statistics from historical fight data.</p>
            </div>

            <div class="chart-container">
                <iframe src="performance_trends_over_time.html" width="100%" height="800" frameborder="0"></iframe>
            </div>

            <div class="chart-container">
                <iframe src="win_method_distribution_over_time.html" width="100%" height="500" frameborder="0"></iframe>
            </div>
        </div>
    </div>

    <script>
        function showTab(tabName, event) {
            var contents = document.getElementsByClassName('content');

            for (var i = 0; i < contents.length; i++) {
                contents[i].classList.remove('active');
            }

            var tabs = document.getElementsByClassName('tab');

            for (var i = 0; i < tabs.length; i++) {
                tabs[i].classList.remove('active');
            }

            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
"""

with open(f"{OUTPUT_DIR}/ufc_analysis_dashboard.html", "w", encoding="utf-8") as f:
    f.write(dashboard_html)

print("Saved: ufc_analysis_dashboard.html")


print("\n" + "=" * 50)
print("DASHBOARD GENERATION COMPLETE")
print("=" * 50)

print("\nGenerated files:")
print("1. physical_attributes_vs_performance.html - Scatter plots of physical attributes vs performance")
print("2. correlation_heatmap.html - Correlation matrix heatmap")
print("3. fight_outcomes_analysis.html - Performance metrics by win method")
print("4. weight_class_patterns.html - Weight class analysis")
print("5. win_methods_correlation.html - Physical attributes by win method")
print("6. performance_trends_over_time.html - Performance trends over years")
print("7. win_method_distribution_over_time.html - Win method distribution over time")
print("8. ufc_analysis_dashboard.html - COMPREHENSIVE INTERACTIVE DASHBOARD")

print("\nOpen 'ufc_analysis_dashboard.html' in your browser to view the complete dashboard!")