from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
import warnings
import base64
import re
import unicodedata

warnings.filterwarnings("ignore")

app = Flask(__name__, static_folder="static", static_url_path="/static")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


# ── Helper Functions ──────────────────────────────────────────────────────────
def safe_float(val, default=0.0):
    try:
        v = float(val)
        if np.isnan(v):
            return default
        return v
    except Exception:
        return default


def normalize_rate(val, default=0.0):
    """
    Converts rates to 0-1 format.
    Example:
    65 becomes 0.65
    0.65 stays 0.65
    """
    v = safe_float(val, default)
    return v / 100 if v > 1 else v


def display_rate(val, default=0.0):
    """
    Converts rates to percentage display format.
    Example:
    0.65 becomes 65
    65 stays 65
    """
    v = safe_float(val, default)
    return v if v > 1 else v * 100


def clean_plotly_json(obj):
    """
    Converts Plotly/Numpy/Pandas objects into normal JSON lists.
    This prevents Plotly from returning bdata/dtype binary objects,
    which the frontend may fail to render correctly.
    """
    if isinstance(obj, dict):
        if "bdata" in obj and "dtype" in obj:
            try:
                dtype = np.dtype(obj["dtype"])
                raw = base64.b64decode(obj["bdata"])
                arr = np.frombuffer(raw, dtype=dtype)

                if "shape" in obj:
                    shape = tuple(
                        int(x.strip())
                        for x in str(obj["shape"]).split(",")
                        if x.strip()
                    )
                    arr = arr.reshape(shape)

                return arr.tolist()
            except Exception:
                return obj

        return {k: clean_plotly_json(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [clean_plotly_json(v) for v in obj]

    if isinstance(obj, tuple):
        return [clean_plotly_json(v) for v in obj]

    if isinstance(obj, np.ndarray):
        return obj.tolist()

    if isinstance(obj, pd.Series):
        return obj.tolist()

    if isinstance(obj, pd.Index):
        return obj.tolist()

    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        return float(obj)

    if isinstance(obj, np.bool_):
        return bool(obj)

    return obj


def jfig(fig):
    return clean_plotly_json(fig.to_plotly_json())


def categorize_method(m):
    if pd.isna(m):
        return "Unknown"

    m = str(m).upper()

    if "KO" in m or "TKO" in m:
        return "KO/TKO"
    if "SUB" in m or "CHOKE" in m:
        return "Submission"
    if "DEC" in m:
        return "Decision"

    return "Other"


# ── Data Loading ──────────────────────────────────────────────────────────────
print("Loading UFC data...")

events_df = pd.read_csv(os.path.join(DATA_DIR, "Cleaned_Events.csv"))
fighter_stats_df = pd.read_csv(os.path.join(DATA_DIR, "Cleaned_Fighter_Stats.csv"))
fights_df = pd.read_csv(os.path.join(DATA_DIR, "Cleaned_Fights.csv"))
fighters_df = pd.read_csv(os.path.join(DATA_DIR, "Fixed_Cleaned_Fighters.csv"))

events_df["Date"] = pd.to_datetime(events_df["Date"], errors="coerce")

fights_df = fights_df.merge(
    events_df[["Event_Id", "Date"]],
    on="Event_Id",
    how="left"
)

fights_df["Year"] = fights_df["Date"].dt.year

fighter_stats_df = fighter_stats_df.merge(
    fighters_df[["Fighter_Id", "height_cm", "weight_kg", "reach_cm"]],
    on="Fighter_Id",
    how="left"
)

rename_cols = {
    "KO Rate": "KO_Rate",
    "SUB Rate": "Sub_Rate",
    "DEC Rate": "DEC_Rate",
    "Sig. Str. %": "Strike_Acc",
}

fighter_stats_df.rename(columns=rename_cols, inplace=True)
fighters_df.rename(columns=rename_cols, inplace=True)

numeric_cols = [
    "height_cm",
    "weight_kg",
    "reach_cm",
    "Win_Rate",
    "Strike_Acc",
    "KO_Rate",
    "Sub_Rate",
    "DEC_Rate",
    "Total_Fights",
    "Avg_Takedowns",
    "Avg_Sub_Attempts",
    "W",
    "L",
    "D"
]

for df in [fighters_df, fighter_stats_df]:
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

fight_numeric_cols = [
    "KD_1",
    "KD_2",
    "TD_1",
    "TD_2",
    "SUB_1",
    "SUB_2",
    "STR_1",
    "STR_2",
    "Sig. Str. %_1",
    "Sig. Str. %_2",
    "Ctrl_1",
    "Ctrl_2"
]

for col in fight_numeric_cols:
    if col in fights_df.columns:
        fights_df[col] = pd.to_numeric(fights_df[col], errors="coerce")


# ── Weight Class Mapping ──────────────────────────────────────────────────────
WC_MAP = {
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

WC_ORDER = [
    "Women's Strawweight",
    "Women's Flyweight",
    "Women's Bantamweight",
    "Women's Featherweight",
    "Flyweight",
    "Bantamweight",
    "Featherweight",
    "Lightweight",
    "Welterweight",
    "Middleweight",
    "Light Heavyweight",
    "Heavyweight"
]

for df in [fights_df, fighter_stats_df, fighters_df]:
    if "Weight_Class" in df.columns:
        df["Weight_Class"] = df["Weight_Class"].astype(str).str.upper().str.strip()
        df["Weight_Class_Std"] = df["Weight_Class"].map(WC_MAP)

if "Method" in fights_df.columns:
    fights_df["Win_Method"] = fights_df["Method"].apply(categorize_method)
else:
    fights_df["Win_Method"] = "Unknown"


# ── Percentile Star Ratings ───────────────────────────────────────────────────
PCTILES = {}

for col in ["Strike_Acc", "KO_Rate", "Sub_Rate", "Win_Rate", "Total_Fights", "Avg_Takedowns"]:
    if col in fighter_stats_df.columns:
        vals = fighter_stats_df[col].dropna()
        if not vals.empty:
            PCTILES[col] = [float(vals.quantile(q)) for q in [0.2, 0.4, 0.6, 0.8]]


def star_rating(value, col):
    if col not in PCTILES or pd.isna(value):
        return 3

    value = safe_float(value, 0)
    thresholds = PCTILES[col]

    for i, t in enumerate(thresholds):
        if value <= t:
            return i + 1

    return 5


print("Data ready.")


# ── Chart Theme ───────────────────────────────────────────────────────────────
PAL = [
    "#d20000",
    "#ef4444",
    "#f87171",
    "#fca5a5",
    "#6b7280",
    "#9ca3af",
    "#374151",
    "#4b5563"
]

GRID = "#e5e7eb"

FILL = {
    "#d20000": "rgba(210,0,0,0.10)",
    "#ef4444": "rgba(239,68,68,0.10)",
    "#f87171": "rgba(248,113,113,0.08)",
    "#fca5a5": "rgba(252,165,165,0.08)",
    "#6b7280": "rgba(107,114,128,0.08)",
    "#9ca3af": "rgba(156,163,175,0.08)",
    "#374151": "rgba(55,65,81,0.08)",
    "#4b5563": "rgba(75,85,99,0.08)",
}


def L(height=None, title=None, **kw):
    d = dict(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#374151", family="Inter, sans-serif", size=12),
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor="#d20000",
            font=dict(color="#111827", size=12)
        ),
        margin=dict(t=55, r=20, b=45, l=60),
        legend=dict(
            bgcolor="rgba(255,255,255,0.9)",
            font=dict(color="#374151"),
            bordercolor="#e5e7eb",
            borderwidth=1
        ),
    )

    if title:
        d["title"] = dict(
            text=title,
            font=dict(size=15, color="#111827", family="Inter, sans-serif"),
            x=0.01
        )

    if height:
        d["height"] = height

    d.update(kw)
    return d


def ax(**kw):
    d = dict(
        gridcolor=GRID,
        linecolor="#d1d5db",
        zerolinecolor="#e5e7eb",
        tickfont=dict(size=11, color="#6b7280"),
        title=dict(font=dict(size=12, color="#374151"))
    )

    d.update(kw)
    return d


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/dashboard")
def index():
    return render_template("index.html")


@app.route("/api/stats")
@app.route("/api/kpis")
def kpis():
    wm = fights_df["Win_Method"].value_counts(normalize=True) * 100

    qualified = fighter_stats_df[fighter_stats_df["Total_Fights"] >= 10].copy()

    if not qualified.empty and "Win_Rate" in qualified.columns:
        qualified["Win_Rate_Normalized"] = qualified["Win_Rate"].apply(normalize_rate)
        top = qualified.nlargest(1, "Win_Rate_Normalized").iloc[0]
        best_fighter = str(top.get("Full Name", "N/A"))
    else:
        best_fighter = "N/A"

    avg_wr = fighters_df["Win_Rate"].dropna().apply(normalize_rate).mean()
    avg_wr = avg_wr * 100 if not pd.isna(avg_wr) else 0

    return jsonify({
        "fighters": int(len(fighters_df)),
        "fights": int(len(fights_df)),
        "events": int(len(events_df)),
        "weight_classes": int(fighter_stats_df["Weight_Class_Std"].nunique()) if "Weight_Class_Std" in fighter_stats_df.columns else 0,
        "ko_rate": round(float(wm.get("KO/TKO", 0)), 1),
        "sub_rate": round(float(wm.get("Submission", 0)), 1),
        "dec_rate": round(float(wm.get("Decision", 0)), 1),
        "avg_win_rate": round(float(avg_wr), 1),
        "best_fighter": best_fighter,
    })


# ── Overview Charts ───────────────────────────────────────────────────────────
@app.route("/api/charts/overview")
def ch_overview():
    cols = [
        c for c in [
            "height_cm",
            "weight_kg",
            "reach_cm",
            "Win_Rate",
            "Strike_Acc",
            "KO_Rate",
            "Sub_Rate",
            "Avg_Takedowns",
            "Avg_Sub_Attempts"
        ]
        if c in fighter_stats_df.columns
    ]

    df = fighter_stats_df[cols].copy()

    for col in ["Win_Rate", "Strike_Acc", "KO_Rate", "Sub_Rate"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_rate)

    labels = {
        "height_cm": "Height",
        "weight_kg": "Weight",
        "reach_cm": "Reach",
        "Win_Rate": "Win Rate",
        "Strike_Acc": "Strike Acc",
        "KO_Rate": "KO Rate",
        "Sub_Rate": "Sub Rate",
        "Avg_Takedowns": "Takedowns",
        "Avg_Sub_Attempts": "Submissions"
    }

    corr = df.corr(numeric_only=True, min_periods=10)
    corr = corr.dropna(axis=0, how="all").dropna(axis=1, how="all")

    z = np.round(corr.values, 2).tolist()
    disp = [labels.get(c, c) for c in corr.columns]

    hm = go.Figure(go.Heatmap(
        z=z,
        x=disp,
        y=disp,
        colorscale=[[0, "#3b82f6"], [0.5, "#f3f4f6"], [1, "#d20000"]],
        zmid=0,
        text=z,
        texttemplate="%{text:.2f}",
        textfont=dict(size=10, color="#374151"),
        colorbar=dict(
            title=dict(text="r", font=dict(color="#374151")),
            tickfont=dict(color="#6b7280")
        ),
    ))

    hm.update_layout(**L(
        title="Correlation Matrix — Physical Attributes vs Performance Metrics",
        height=460,
        xaxis=ax(tickangle=-35),
        yaxis=ax()
    ))

    mc = fights_df["Win_Method"].value_counts()

    pie = go.Figure(go.Pie(
        labels=mc.index.tolist(),
        values=mc.values.tolist(),
        hole=0.44,
        marker=dict(
            colors=["#d20000", "#ef4444", "#6b7280", "#9ca3af"][:len(mc)],
            line=dict(color="#ffffff", width=2)
        ),
        textfont=dict(color="#374151", size=13),
        textinfo="label+percent",
    ))

    pie.update_layout(**L(title="Overall Win Method Distribution", height=360))

    return jsonify({
        "heatmap": jfig(hm),
        "pie": jfig(pie)
    })


# ── Physical Charts ───────────────────────────────────────────────────────────
@app.route("/api/charts/physical")
def ch_physical():
    df = fighter_stats_df.dropna(
        subset=["height_cm", "weight_kg", "reach_cm", "Win_Rate"]
    ).copy()

    df["Win_Rate"] = df["Win_Rate"].apply(normalize_rate)

    if "Strike_Acc" in df.columns:
        df["Strike_Acc"] = df["Strike_Acc"].apply(normalize_rate)

    attrs = [
        ("height_cm", "Height (cm)"),
        ("reach_cm", "Reach (cm)"),
        ("weight_kg", "Weight (kg)")
    ]

    charts = []

    for metric_col, metric_lbl in [("Win_Rate", "Win Rate"), ("Strike_Acc", "Striking Accuracy")]:
        if metric_col not in df.columns:
            continue

        dm = df.dropna(subset=[metric_col])

        if dm.empty:
            continue

        fig = make_subplots(
            1,
            3,
            horizontal_spacing=0.08
        )

        for i, (ac, al) in enumerate(attrs, 1):
            da = dm.dropna(subset=[ac])

            if da.empty:
                continue

            try:
                c = np.polyfit(da[ac].values, da[metric_col].values, 1)
                xs = np.linspace(da[ac].min(), da[ac].max(), 80)

                fig.add_trace(go.Scatter(
                    x=xs.tolist(),
                    y=np.polyval(c, xs).tolist(),
                    mode="lines",
                    line=dict(color="#f5a623", width=2, dash="dash"),
                    name="Trend",
                    showlegend=(i == 1),
                    legendgroup="trend"
                ), row=1, col=i)
            except Exception:
                pass

            fig.add_trace(go.Scatter(
                x=da[ac].tolist(),
                y=da[metric_col].tolist(),
                mode="markers",
                marker=dict(
                    size=5,
                    color=da[metric_col].tolist(),
                    colorscale=[[0, "#3b82f6"], [0.5, "#8b5cf6"], [1, "#d20000"]],
                    opacity=0.65,
                    showscale=(i == 3),
                    colorbar=dict(
                        title=dict(text=metric_lbl, font=dict(color="#374151", size=10)),
                        tickfont=dict(color="#6b7280", size=9),
                        x=1.02,
                        len=0.8,
                        thickness=12,
                        tickformat=".0%"
                    ) if i == 3 else None
                ),
                text=da["Full Name"].astype(str).tolist(),
                hovertemplate=f"<b>%{{text}}</b><br>{al}: %{{x:.1f}}<br>{metric_lbl}: %{{y:.1%}}<extra></extra>",
                showlegend=False
            ), row=1, col=i)

            fig.update_xaxes(title_text=al, row=1, col=i, **ax())
            fig.update_yaxes(
                title_text=(metric_lbl if i == 1 else ""),
                tickformat=".0%",
                range=[0, 1],
                row=1,
                col=i,
                **ax()
            )

        fig.update_layout(**L(
            title=f"Physical Attributes vs {metric_lbl}",
            height=380,
            showlegend=True,
            margin=dict(t=60, r=90, b=50, l=55),
            legend=dict(
                bgcolor="rgba(255,255,255,0.95)",
                font=dict(color="#374151", size=10),
                x=0.98,
                y=0.98,
                xanchor="right",
                yanchor="top",
                bordercolor="rgba(0,0,0,0.08)",
                borderwidth=1
            )
        ))

        charts.append(jfig(fig))

    return jsonify({"charts": charts})


# ── Stance Charts ─────────────────────────────────────────────────────────────
@app.route("/api/charts/stance")
def ch_stance():
    MAIN = ["Orthodox", "Southpaw", "Switch"]

    df = fighter_stats_df.dropna(subset=["Stance", "Win_Rate"]).copy()
    df = df[df["Stance"].isin(MAIN)].copy()

    for col in ["Win_Rate", "KO_Rate", "Sub_Rate", "Strike_Acc"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_rate)

    ss = df.groupby("Stance").agg(
        Win_Rate=("Win_Rate", "mean"),
        Count=("Win_Rate", "count"),
        KO_Rate=("KO_Rate", "mean"),
        Sub_Rate=("Sub_Rate", "mean"),
        Strike_Acc=("Strike_Acc", "mean")
    ).reset_index()

    bar = go.Figure()

    metrics = [
        ("Win_Rate", "Win Rate", "#d20000"),
        ("KO_Rate", "KO Rate", "#ef4444"),
        ("Sub_Rate", "Sub Rate", "#8b5cf6"),
        ("Strike_Acc", "Strike Acc", "#3b82f6")
    ]

    for col, lbl, color in metrics:
        if col in ss.columns:
            bar.add_trace(go.Bar(
                name=lbl,
                x=ss["Stance"].astype(str).tolist(),
                y=ss[col].tolist(),
                marker_color=color,
                text=ss[col].apply(lambda v: f"{v:.1%}").tolist(),
                textposition="outside",
                textfont=dict(color="#374151", size=11)
            ))

    bar.update_layout(**L(
        title="Performance Metrics by Fighting Stance",
        height=420,
        barmode="group",
        showlegend=True,
        xaxis=ax(title="Fighting Stance"),
        yaxis=ax(title="Rate", tickformat=".0%", range=[0, 1])
    ))

    sc = df["Stance"].value_counts()

    pie = go.Figure(go.Pie(
        labels=sc.index.tolist(),
        values=sc.values.tolist(),
        hole=0.5,
        marker=dict(
            colors=["#d20000", "#ef4444", "#f87171"],
            line=dict(color="#ffffff", width=2)
        ),
        textfont=dict(color="#374151", size=13),
        textinfo="label+percent"
    ))

    pie.update_layout(**L(title="Fighter Distribution by Stance", height=380))

    box = go.Figure()

    colors = {
        "Orthodox": "#d20000",
        "Southpaw": "#ef4444",
        "Switch": "#f87171"
    }

    for stance in MAIN:
        sdf = df[df["Stance"] == stance]

        if not sdf.empty:
            box.add_trace(go.Box(
                y=sdf["Win_Rate"].tolist(),
                name=stance,
                marker=dict(color=colors.get(stance, "#6b7280"), size=4),
                line=dict(color=colors.get(stance, "#6b7280")),
                boxmean=True
            ))

    box.update_layout(**L(
        title="Win Rate Distribution by Stance",
        height=400,
        yaxis=ax(title="Win Rate", tickformat=".0%", range=[0, 1]),
        xaxis=ax(title="Fighting Stance")
    ))

    return jsonify({
        "bar": jfig(bar),
        "pie": jfig(pie),
        "box": jfig(box)
    })


# ── Experience Charts ─────────────────────────────────────────────────────────
@app.route("/api/charts/experience")
def ch_experience():
    df = fighter_stats_df.dropna(subset=["Total_Fights", "Win_Rate"]).copy()
    df["Win_Rate"] = df["Win_Rate"].apply(normalize_rate)

    for col in ["KO_Rate", "Sub_Rate"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_rate)

    bins = [0, 5, 10, 15, 20, 25, float("inf")]
    blbls = ["1-5", "6-10", "11-15", "16-20", "21-25", "26+"]

    df["Exp"] = pd.cut(df["Total_Fights"], bins=bins, labels=blbls)

    es = df.groupby("Exp", observed=True).agg(
        Win_Rate=("Win_Rate", "mean"),
        Count=("Win_Rate", "count"),
        KO_Rate=("KO_Rate", "mean"),
        Sub_Rate=("Sub_Rate", "mean")
    ).reset_index()

    fig_bar = make_subplots(specs=[[{"secondary_y": True}]])

    colors = ["#d20000", "#dc2626", "#ef4444", "#f87171", "#fca5a5", "#6b7280"]

    fig_bar.add_trace(go.Bar(
        x=es["Exp"].astype(str).tolist(),
        y=es["Win_Rate"].tolist(),
        name="Avg Win Rate",
        marker=dict(color=colors[:len(es)], line=dict(width=0)),
        text=es["Win_Rate"].apply(lambda v: f"{v:.1%}").tolist(),
        textposition="outside",
        textfont=dict(color="#374151", size=11)
    ), secondary_y=False)

    fig_bar.add_trace(go.Scatter(
        x=es["Exp"].astype(str).tolist(),
        y=es["Count"].tolist(),
        name="Fighter Count",
        mode="lines+markers",
        line=dict(color="#f5a623", width=2.5),
        marker=dict(size=10, color="#f5a623", line=dict(color="white", width=2))
    ), secondary_y=True)

    fig_bar.update_layout(**L(
        title="Win Rate & Fighter Count by Career Experience",
        height=420,
        showlegend=True,
        xaxis=ax(title="Total Career Fights"),
        legend=dict(
            bgcolor="rgba(255,255,255,0.9)",
            font=dict(color="#374151"),
            orientation="h",
            x=0.5,
            xanchor="center",
            y=1.1
        )
    ))

    fig_bar.update_yaxes(
        title_text="Average Win Rate",
        tickformat=".0%",
        range=[0, 1],
        secondary_y=False,
        **ax()
    )

    fig_bar.update_yaxes(
        title_text="Number of Fighters",
        secondary_y=True,
        **ax()
    )

    sc = go.Figure()

    try:
        c = np.polyfit(df["Total_Fights"].values, df["Win_Rate"].values, 1)
        xs = np.linspace(df["Total_Fights"].min(), df["Total_Fights"].max(), 200)

        sc.add_trace(go.Scatter(
            x=xs.tolist(),
            y=np.polyval(c, xs).tolist(),
            mode="lines",
            line=dict(color="#f5a623", width=2.5, dash="dash"),
            name="Trend",
            showlegend=True
        ))
    except Exception:
        pass

    sc.add_trace(go.Scatter(
        x=df["Total_Fights"].tolist(),
        y=df["Win_Rate"].tolist(),
        mode="markers",
        marker=dict(
            size=6,
            color=df["Win_Rate"].tolist(),
            colorscale=[[0, "#3b82f6"], [0.5, "#8b5cf6"], [1, "#d20000"]],
            opacity=0.7,
            showscale=True,
            colorbar=dict(
                title=dict(text="Win Rate", font=dict(color="#374151")),
                tickfont=dict(color="#6b7280"),
                tickformat=".0%"
            )
        ),
        text=df["Full Name"].astype(str).tolist(),
        hovertemplate="<b>%{text}</b><br>Fights: %{x}<br>Win Rate: %{y:.1%}<extra></extra>",
        showlegend=False
    ))

    sc.update_layout(**L(
        title="Career Experience vs Win Rate",
        height=420,
        showlegend=True,
        xaxis=ax(title="Total Career Fights"),
        yaxis=ax(title="Win Rate", tickformat=".0%", range=[0, 1])
    ))

    return jsonify({
        "bar": jfig(fig_bar),
        "scatter": jfig(sc)
    })


# ── Fight Outcomes Charts ─────────────────────────────────────────────────────
@app.route("/api/charts/outcomes")
def ch_outcomes():
    perf = fights_df.groupby("Win_Method").agg(
        KD=("KD_1", "mean"),
        TD=("TD_1", "mean"),
        SUB=("SUB_1", "mean"),
        SA=("Sig. Str. %_1", "mean"),
        Ctrl=("Ctrl_1", "mean"),
        STR=("STR_1", "mean"),
        Count=("Fight_Id", "count")
    ).reset_index()

    if "SA" in perf.columns:
        perf["SA"] = perf["SA"].apply(normalize_rate)

    methods = perf["Win_Method"].astype(str).tolist()

    method_colors = {
        "KO/TKO": "#d20000",
        "Submission": "#8b5cf6",
        "Decision": "#3b82f6",
        "Other": "#6b7280",
        "Unknown": "#9ca3af"
    }

    colors = [method_colors.get(m, "#9ca3af") for m in methods]

    fig = make_subplots(
        2,
        2,
        subplot_titles=[
            "Avg Knockdowns per Fight",
            "Avg Takedowns per Fight",
            "Strike Accuracy",
            "Avg Significant Strikes"
        ],
        vertical_spacing=0.18,
        horizontal_spacing=0.12
    )

    metrics = [
        ("KD", 1, 1, ".1f"),
        ("TD", 1, 2, ".1f"),
        ("SA", 2, 1, ".1%"),
        ("STR", 2, 2, ".0f")
    ]

    for col, row, colnum, fmt in metrics:
        if col not in perf.columns:
            continue

        fig.add_trace(go.Bar(
            x=methods,
            y=perf[col].tolist(),
            marker=dict(color=colors, line=dict(width=0)),
            text=perf[col].apply(lambda v: f"{v:{fmt}}").tolist(),
            textposition="outside",
            textfont=dict(color="#374151", size=11),
            showlegend=False
        ), row=row, col=colnum)

        fig.update_xaxes(tickangle=-20, **ax(), row=row, col=colnum)

        yaxis_args = ax()

        if col == "SA":
            yaxis_args["tickformat"] = ".0%"
            yaxis_args["range"] = [0, 1]

        fig.update_yaxes(**yaxis_args, row=row, col=colnum)

    fig.update_layout(**L(title="Performance Metrics by Win Method", height=520))

    wmy = fights_df.groupby(["Year", "Win_Method"]).size().reset_index(name="n")
    wmy = wmy[wmy["Year"].notna()].copy()
    wmy["Year"] = wmy["Year"].astype(int)
    wmy = wmy[wmy["Year"] >= 2010]

    tf = go.Figure()

    for method in ["KO/TKO", "Submission", "Decision", "Other", "Unknown"]:
        d = wmy[wmy["Win_Method"] == method].sort_values("Year")

        if not d.empty:
            tf.add_trace(go.Scatter(
                x=d["Year"].tolist(),
                y=d["n"].tolist(),
                name=method,
                mode="lines+markers",
                stackgroup="one",
                line=dict(width=2, color=method_colors.get(method, "#9ca3af")),
                marker=dict(size=6)
            ))

    tf.update_layout(**L(
        title="Win Method Distribution Over Time (2010-Present)",
        height=400,
        showlegend=True,
        xaxis=ax(title="Year", dtick=2),
        yaxis=ax(title="Number of Fights"),
        legend=dict(
            bgcolor="rgba(255,255,255,0.9)",
            font=dict(color="#374151"),
            orientation="h",
            x=0.5,
            xanchor="center",
            y=1.1
        )
    ))

    return jsonify({
        "metrics": jfig(fig),
        "time": jfig(tf)
    })


# ── Weight Class Charts ───────────────────────────────────────────────────────
@app.route("/api/charts/weight")
def ch_weight():
    wc = fighter_stats_df.groupby("Weight_Class_Std").agg(
        height=("height_cm", "mean"),
        weight=("weight_kg", "mean"),
        reach=("reach_cm", "mean"),
        win_rate=("Win_Rate", "mean"),
        strike_acc=("Strike_Acc", "mean"),
        ko_rate=("KO_Rate", "mean"),
        sub_rate=("Sub_Rate", "mean"),
        count=("Fighter_Id", "count")
    ).reset_index()

    wc = wc.dropna(subset=["Weight_Class_Std"])

    for col in ["win_rate", "strike_acc", "ko_rate", "sub_rate"]:
        if col in wc.columns:
            wc[col] = wc[col].apply(normalize_rate)

    cat = pd.CategoricalDtype(categories=WC_ORDER, ordered=True)
    wc["Weight_Class_Std"] = wc["Weight_Class_Std"].astype(cat)
    wc = wc.sort_values("Weight_Class_Std")

    wlbls = wc["Weight_Class_Std"].astype(str).tolist()

    phys = go.Figure()

    for attr, color, lbl in [
        ("height", "#3b82f6", "Height (cm)"),
        ("reach", "#8b5cf6", "Reach (cm)"),
        ("weight", "#d20000", "Weight (kg)")
    ]:
        phys.add_trace(go.Scatter(
            x=wlbls,
            y=wc[attr].tolist(),
            mode="lines+markers",
            name=lbl,
            line=dict(color=color, width=2.5),
            marker=dict(size=10, color=color, line=dict(color="white", width=2))
        ))

    phys.update_layout(**L(
        title="Average Physical Attributes by Weight Class",
        height=420,
        showlegend=True,
        xaxis=ax(title="", tickangle=-35),
        yaxis=ax(title="Measurement"),
        legend=dict(
            bgcolor="rgba(255,255,255,0.9)",
            font=dict(color="#374151"),
            orientation="h",
            x=0.5,
            xanchor="center",
            y=1.1
        )
    ))

    rates = go.Figure()

    for col, color, lbl in [
        ("win_rate", "#d20000", "Win Rate"),
        ("ko_rate", "#ef4444", "KO Rate"),
        ("sub_rate", "#8b5cf6", "Sub Rate")
    ]:
        if col in wc.columns:
            rates.add_trace(go.Bar(
                name=lbl,
                y=wlbls,
                x=wc[col].tolist(),
                orientation="h",
                marker_color=color,
                text=wc[col].apply(lambda v: f"{v:.1%}").tolist(),
                textposition="outside",
                textfont=dict(color="#374151", size=10)
            ))

    rates.update_layout(**L(
        title="Win / KO / Submission Rates by Weight Class",
        height=500,
        barmode="group",
        showlegend=True,
        yaxis=ax(title=""),
        xaxis=ax(title="Rate", tickformat=".0%", range=[0, 1]),
        legend=dict(
            bgcolor="rgba(255,255,255,0.9)",
            font=dict(color="#374151"),
            orientation="h",
            x=0.5,
            xanchor="center",
            y=1.05
        )
    ))

    sa = go.Figure(go.Bar(
        y=wlbls,
        x=wc["strike_acc"].tolist(),
        orientation="h",
        marker=dict(
            color=wc["strike_acc"].tolist(),
            cmin=0,
            cmax=1,
            colorscale=[[0, "#3b82f6"], [0.5, "#8b5cf6"], [1, "#d20000"]],
            showscale=True,
            colorbar=dict(
                title=dict(text="Strike Acc.", font=dict(color="#374151")),
                tickfont=dict(color="#6b7280"),
                tickformat=".0%"
            )
        ),
        text=wc["strike_acc"].apply(lambda v: f"{v:.1%}").tolist(),
        textposition="outside",
        textfont=dict(color="#374151", size=10)
    ))

    sa.update_layout(**L(
        title="Striking Accuracy by Weight Class",
        height=450,
        yaxis=ax(title=""),
        xaxis=ax(title="Strike Accuracy", tickformat=".0%", range=[0, 1])
    ))

    return jsonify({
        "physical": jfig(phys),
        "rates": jfig(rates),
        "strike": jfig(sa)
    })


# ── Trends Charts ─────────────────────────────────────────────────────────────
@app.route("/api/charts/trends")
def ch_trends():
    yr = fights_df.groupby("Year").agg(
        KD=("KD_1", "mean"),
        TD=("TD_1", "mean"),
        SUB=("SUB_1", "mean"),
        SA=("Sig. Str. %_1", "mean"),
        Ctrl=("Ctrl_1", "mean"),
        Total=("Fight_Id", "count")
    ).reset_index()

    yr = yr[yr["Year"].notna()].copy()
    yr["Year"] = yr["Year"].astype(int)
    yr = yr[yr["Year"] >= 2010].sort_values("Year")

    yr["SA"] = yr["SA"].apply(normalize_rate)

    mets = [
        ("KD", "#d20000", "Avg Knockdowns / Fight"),
        ("TD", "#ef4444", "Avg Takedowns / Fight"),
        ("SA", "#f87171", "Strike Accuracy"),
        ("Ctrl", "#8b5cf6", "Avg Control Time"),
        ("Total", "#3b82f6", "Total Fights / Year"),
        ("SUB", "#6b7280", "Avg Sub Attempts / Fight"),
    ]

    fig = make_subplots(
        2,
        3,
        subplot_titles=[m[2] for m in mets],
        vertical_spacing=0.18,
        horizontal_spacing=0.10
    )

    for idx, (col, color, lbl) in enumerate(mets):
        r, c = idx // 3 + 1, idx % 3 + 1
        fc = FILL.get(color, "rgba(0,212,255,0.12)")

        fig.add_trace(go.Scatter(
            x=yr["Year"].tolist(),
            y=yr[col].tolist(),
            mode="lines+markers",
            name=lbl,
            line=dict(color=color, width=2.5),
            marker=dict(size=8, color=color, line=dict(color="white", width=2)),
            fill="tozeroy",
            fillcolor=fc,
            showlegend=False
        ), row=r, col=c)

        fig.update_xaxes(**ax(), dtick=3, title_text="", row=r, col=c)

        yaxis_args = ax()

        if col == "SA":
            yaxis_args["tickformat"] = ".0%"
            yaxis_args["range"] = [0, 1]

        fig.update_yaxes(**yaxis_args, row=r, col=c)

    fig.update_layout(**L(
        title="UFC Performance Trends Over Time (2010 - Present)",
        height=550
    ))

    return jsonify({"trends": jfig(fig)})


# ── Fighter Search ────────────────────────────────────────────────────────────
@app.route("/api/search")
def search():
    q = request.args.get("q", "").strip().lower()

    cols = [
        "Fighter_Id",
        "Full Name",
        "Stance",
        "height_cm",
        "weight_kg",
        "reach_cm",
        "W",
        "L",
        "D",
        "Win_Rate"
    ]

    available_cols = [c for c in cols if c in fighters_df.columns]

    if not q:
        results = fighters_df[available_cols].head(100).fillna("N/A").to_dict("records")
        return jsonify({"results": results})

    mask = fighters_df["Full Name"].astype(str).str.lower().str.contains(q, na=False)
    results = fighters_df[mask][available_cols].head(50).fillna("N/A").to_dict("records")

    return jsonify({"results": results})


# ── Fighter Detail ────────────────────────────────────────────────────────────
@app.route("/api/fighter/<fid>")
def fighter_detail(fid):
    row = fighters_df[fighters_df["Fighter_Id"] == fid]

    if row.empty:
        return jsonify({"error": "Not found"}), 404

    sr = fighter_stats_df[fighter_stats_df["Fighter_Id"] == fid]

    d = row.iloc[0].fillna("N/A").to_dict()

    if not sr.empty:
        d.update(sr.iloc[0].fillna("N/A").to_dict())

    for col in ["Win_Rate", "Strike_Acc", "KO_Rate", "Sub_Rate"]:
        if col in d and d[col] != "N/A":
            d[col] = normalize_rate(d[col])

    stars = {}

    rating_map = [
        ("Strike_Acc", "striking"),
        ("KO_Rate", "ko_power"),
        ("Sub_Rate", "grappling"),
        ("Win_Rate", "win_rate"),
        ("Total_Fights", "experience")
    ]

    for col, lbl in rating_map:
        val = d.get(col)

        if val != "N/A":
            try:
                stars[lbl] = star_rating(float(val), col)
            except Exception:
                stars[lbl] = 3
        else:
            stars[lbl] = 3

    d["stars"] = stars

    radar = {
        "labels": ["Striking", "Power", "Grappling", "Win Rate", "Experience"],
        "values": []
    }

    for col in ["Strike_Acc", "KO_Rate", "Sub_Rate", "Win_Rate", "Total_Fights"]:
        val = d.get(col)

        try:
            v = float(val)

            if col == "Total_Fights":
                v = min(v / 40.0, 1.0) * 100
            else:
                v = min(normalize_rate(v), 1.0) * 100

            radar["values"].append(round(v, 1))

        except Exception:
            radar["values"].append(50)

    d["radar"] = radar

    return jsonify(d)


# ── Fighter Yearly Charts ─────────────────────────────────────────────────────
@app.route("/api/fighter/<fid>/charts")
def fighter_charts(fid):
    f1 = fights_df[fights_df["Fighter_Id_1"] == fid][
        ["Year", "Win_Method", "KD_1", "STR_1", "TD_1", "Result_1"]
    ].copy()

    f1.rename(columns={
        "KD_1": "KD",
        "STR_1": "STR",
        "TD_1": "TD",
        "Result_1": "Result"
    }, inplace=True)

    f2 = fights_df[fights_df["Fighter_Id_2"] == fid][
        ["Year", "Win_Method", "KD_2", "STR_2", "TD_2", "Result_2"]
    ].copy()

    f2.rename(columns={
        "KD_2": "KD",
        "STR_2": "STR",
        "TD_2": "TD",
        "Result_2": "Result"
    }, inplace=True)

    all_f = pd.concat([f1, f2], ignore_index=True)

    if all_f.empty:
        return jsonify({
            "wins": {},
            "strikes": {},
            "methods": {},
            "radar": {}
        })

    all_f["Win"] = (all_f["Result"] == "W").astype(int)
    all_f["Loss"] = (all_f["Result"] == "L").astype(int)

    yr = all_f.groupby("Year").agg(
        Fights=("Win", "count"),
        Wins=("Win", "sum"),
        Losses=("Loss", "sum"),
        KD=("KD", "mean"),
        STR=("STR", "mean"),
        TD=("TD", "mean")
    ).reset_index()

    yr = yr[yr["Year"].notna()].copy()
    yr["Year"] = yr["Year"].astype(int)
    yr = yr.sort_values("Year")

    won = all_f[all_f["Win"] == 1]
    wm = won["Win_Method"].value_counts().to_dict()

    wins_fig = go.Figure()

    wins_fig.add_trace(go.Bar(
        x=yr["Year"].tolist(),
        y=yr["Wins"].tolist(),
        name="Wins",
        marker_color="#d20000",
        marker_line_width=0
    ))

    wins_fig.add_trace(go.Bar(
        x=yr["Year"].tolist(),
        y=yr["Losses"].tolist(),
        name="Losses",
        marker_color="#6b7280",
        marker_line_width=0
    ))

    wins_fig.update_layout(**L(
        title="Fights Per Year",
        height=220,
        barmode="group",
        showlegend=True,
        margin=dict(t=40, r=10, b=30, l=40),
        legend=dict(
            font=dict(size=10, color="#374151"),
            orientation="h",
            x=0,
            y=1.15
        ),
        xaxis=ax(title=""),
        yaxis=ax(title="Fights")
    ))

    str_fig = go.Figure(go.Bar(
        x=yr["Year"].tolist(),
        y=yr["STR"].tolist(),
        name="Avg Strikes",
        marker=dict(
            color=yr["STR"].tolist(),
            colorscale=[[0, "#3b82f6"], [1, "#d20000"]],
            showscale=False
        ),
        marker_line_width=0
    ))

    str_fig.update_layout(**L(
        title="Avg Strikes / Fight",
        height=220,
        margin=dict(t=40, r=10, b=30, l=40),
        xaxis=ax(title=""),
        yaxis=ax(title="Strikes")
    ))

    if wm:
        wm_keys = list(wm.keys())
        wm_vals = [wm[k] for k in wm_keys]

        wm_colors = [
            {
                "KO/TKO": "#d20000",
                "Submission": "#8b5cf6",
                "Decision": "#3b82f6",
                "Other": "#6b7280",
                "Unknown": "#9ca3af"
            }.get(k, "#9ca3af")
            for k in wm_keys
        ]

        method_fig = go.Figure(go.Pie(
            labels=wm_keys,
            values=wm_vals,
            hole=0.5,
            marker=dict(colors=wm_colors, line=dict(color="#ffffff", width=2)),
            textfont=dict(color="#374151", size=11),
            textinfo="label+percent"
        ))

        method_fig.update_layout(**L(
            title="",
            height=220,
            margin=dict(t=15, r=10, b=10, l=10),
            showlegend=False
        ))

    else:
        method_fig = go.Figure()
        method_fig.update_layout(**L(title="", height=220))

    sr = fighter_stats_df[fighter_stats_df["Fighter_Id"] == fid]

    radar_vals = []
    radar_lbls = ["Striking", "Power", "Grappling", "Win Rate", "Experience"]
    cols_r = ["Strike_Acc", "KO_Rate", "Sub_Rate", "Win_Rate", "Total_Fights"]

    for col in cols_r:
        val = sr[col].values[0] if not sr.empty and col in sr.columns else 0.5

        try:
            v = float(val)

            if col == "Total_Fights":
                v = min(v / 40, 1) * 100
            else:
                v = normalize_rate(v) * 100

            radar_vals.append(round(min(v, 100), 1))

        except Exception:
            radar_vals.append(50)

    rv = radar_vals + [radar_vals[0]]
    rl = radar_lbls + [radar_lbls[0]]

    radar_fig = go.Figure(go.Scatterpolar(
        r=rv,
        theta=rl,
        fill="toself",
        fillcolor="rgba(210,0,0,0.10)",
        line=dict(color="#d20000", width=2),
        marker=dict(color="#d20000", size=6)
    ))

    radar_fig.update_layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        polar=dict(
            bgcolor="#fafafa",
            radialaxis=dict(
                visible=True,
                color="#e5e7eb",
                tickfont=dict(color="#9ca3af", size=9),
                range=[0, 100]
            ),
            angularaxis=dict(
                color="#d1d5db",
                tickfont=dict(color="#374151", size=11)
            )
        ),
        font=dict(color="#374151", family="Inter, sans-serif"),
        margin=dict(t=15, r=30, b=30, l=30),
        height=220,
        showlegend=False
    )

    return jsonify({
        "wins": jfig(wins_fig),
        "strikes": jfig(str_fig),
        "methods": jfig(method_fig),
        "radar": jfig(radar_fig)
    })


# ── Fighter Compare + Win Probability ─────────────────────────────────────────
@app.route("/api/compare")
def compare():
    f1_id = request.args.get("f1", "").strip()
    f2_id = request.args.get("f2", "").strip()

    if not f1_id or not f2_id:
        return jsonify({"error": "Need f1 and f2 IDs"}), 400

    def get_stats(fid):
        row = fighters_df[fighters_df["Fighter_Id"] == fid]

        if row.empty:
            return None

        sr = fighter_stats_df[fighter_stats_df["Fighter_Id"] == fid]

        d = row.iloc[0].fillna(0).to_dict()

        if not sr.empty:
            d.update(sr.iloc[0].fillna(0).to_dict())

        return d

    s1 = get_stats(f1_id)
    s2 = get_stats(f2_id)

    if s1 is None or s2 is None:
        return jsonify({"error": "Fighter not found"}), 404

    def prob_score(s):
        win_rate = normalize_rate(s.get("Win_Rate"), 0.5)
        ko_rate = normalize_rate(s.get("KO_Rate"), 0.3)
        strike_acc = normalize_rate(s.get("Strike_Acc"), 0.45)
        sub_rate = normalize_rate(s.get("Sub_Rate"), 0.15)
        experience = min(safe_float(s.get("Total_Fights"), 10) / 40.0, 1.0)

        return (
            win_rate * 0.35 +
            ko_rate * 0.20 +
            strike_acc * 0.20 +
            sub_rate * 0.15 +
            experience * 0.10
        )

    sc1 = prob_score(s1)
    sc2 = prob_score(s2)

    total_score = sc1 + sc2

    p1 = round(sc1 / total_score * 100, 1) if total_score > 0 else 50.0
    p2 = round(100 - p1, 1)

    def fmt(s, prob):
        return {
            "Fighter_Id": str(s.get("Fighter_Id", "")),
            "name": str(s.get("Full Name", "Unknown")),
            "stance": str(s.get("Stance", "Unknown")),
            "height": safe_float(s.get("height_cm", 0)),
            "weight": safe_float(s.get("weight_kg", 0)),
            "reach": safe_float(s.get("reach_cm", 0)),
            "wins": int(safe_float(s.get("W", 0))),
            "losses": int(safe_float(s.get("L", 0))),
            "draws": int(safe_float(s.get("D", 0))),
            "total_fights": int(safe_float(s.get("Total_Fights", 0))),
            "win_rate": normalize_rate(s.get("Win_Rate", 0)),
            "ko_rate": normalize_rate(s.get("KO_Rate", 0)),
            "sig_str": normalize_rate(s.get("Strike_Acc", 0)),
            "sub_rate": normalize_rate(s.get("Sub_Rate", 0)),
            "td_acc": normalize_rate(s.get("TD Acc.", 0)),
            "weight_class": str(s.get("Weight_Class_Std", s.get("Weight_Class", "N/A"))),
            "win_prob": prob,
            "stars": {
                "striking": star_rating(normalize_rate(s.get("Strike_Acc", 0.45)), "Strike_Acc"),
                "ko_power": star_rating(normalize_rate(s.get("KO_Rate", 0.3)), "KO_Rate"),
                "grappling": star_rating(normalize_rate(s.get("Sub_Rate", 0.15)), "Sub_Rate"),
                "win_rate": star_rating(normalize_rate(s.get("Win_Rate", 0.5)), "Win_Rate"),
                "experience": star_rating(safe_float(s.get("Total_Fights", 10)), "Total_Fights"),
            }
        }

    lbls = ["Striking", "KO Power", "Grappling", "Win Rate", "Experience"]
    cols_r = ["Strike_Acc", "KO_Rate", "Sub_Rate", "Win_Rate", "Total_Fights"]

    def radar_vals(s):
        out = []

        for col in cols_r:
            v = safe_float(s.get(col), 0)

            if col == "Total_Fights":
                score = min(v / 40.0, 1.0) * 100
            else:
                score = normalize_rate(v) * 100

            out.append(round(min(score, 100), 1))

        return out

    r1 = radar_vals(s1)
    r2 = radar_vals(s2)

    n1 = str(s1.get("Full Name", "Fighter 1"))
    n2 = str(s2.get("Full Name", "Fighter 2"))

    radar_fig = go.Figure()

    for rv, name, lc, fc in [
        (r1, n1, "#d20000", "rgba(210,0,0,0.12)"),
        (r2, n2, "#3b82f6", "rgba(59,130,246,0.10)")
    ]:
        rl = lbls + [lbls[0]]
        rv2 = rv + [rv[0]]

        radar_fig.add_trace(go.Scatterpolar(
            r=rv2,
            theta=rl,
            fill="toself",
            name=name,
            fillcolor=fc,
            line=dict(color=lc, width=2.5),
            marker=dict(color=lc, size=6)
        ))

    radar_fig.update_layout(
        paper_bgcolor="#ffffff",
        polar=dict(
            bgcolor="#fafafa",
            radialaxis=dict(
                visible=True,
                color="#e5e7eb",
                tickfont=dict(color="#9ca3af", size=8),
                range=[0, 100]
            ),
            angularaxis=dict(
                color="#d1d5db",
                tickfont=dict(color="#374151", size=11)
            )
        ),
        font=dict(color="#374151", family="Inter, sans-serif"),
        legend=dict(
            bgcolor="rgba(255,255,255,0.9)",
            font=dict(color="#374151", size=11),
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.05,
            bordercolor="#e5e7eb",
            borderwidth=1
        ),
        margin=dict(t=20, r=30, b=30, l=30),
        height=320,
        showlegend=True
    )

    return jsonify({
        "fighter1": fmt(s1, p1),
        "fighter2": fmt(s2, p2),
        "radar": jfig(radar_fig)
    })


# ── Debug Routes ──────────────────────────────────────────────────────────────
@app.route("/api/debug")
def debug():
    return jsonify({
        "fighters_rows": int(len(fighters_df)),
        "fighter_stats_rows": int(len(fighter_stats_df)),
        "fights_rows": int(len(fights_df)),
        "events_rows": int(len(events_df)),
        "fighters_columns": fighters_df.columns.tolist(),
        "fighter_stats_columns": fighter_stats_df.columns.tolist(),
        "fights_columns": fights_df.columns.tolist(),
        "events_columns": events_df.columns.tolist()
    })


@app.route("/api/version")
def version():
    return jsonify({
        "version": "REAL_FIXED_APP_RUNNING_NO_BDATA",
        "fighters_rows": int(len(fighters_df)),
        "fights_rows": int(len(fights_df)),
        "methods": fights_df["Win_Method"].value_counts().to_dict()
    })




# ── Official UFC Men's Champions + Top 15 Per Division ───────────────────────
DIVISION_ORDER = [
    "Flyweight",
    "Bantamweight",
    "Featherweight",
    "Lightweight",
    "Welterweight",
    "Middleweight",
    "Light Heavyweight",
    "Heavyweight",
]

MENS_UFC_CHAMPIONS = {
    "Flyweight": "Joshua Van",
    "Bantamweight": "Petr Yan",
    "Featherweight": "Alexander Volkanovski",
    "Lightweight": "Ilia Topuria",
    "Welterweight": "Islam Makhachev",
    "Middleweight": "Sean Strickland",
    "Light Heavyweight": "Carlos Ulberg",
    "Heavyweight": "Tom Aspinall",
}

MENS_UFC_RANKINGS = {
    "Flyweight": [
        {"rank": 1, "name": "Alexandre Pantoja"},
        {"rank": 2, "name": "Manel Kape"},
        {"rank": 3, "name": "Tatsuro Taira"},
        {"rank": 4, "name": "Brandon Royval"},
        {"rank": 5, "name": "Kyoji Horiguchi"},
        {"rank": 6, "name": "Lone'er Kavanagh"},
        {"rank": 7, "name": "Amir Albazi"},
        {"rank": 8, "name": "Asu Almabayev"},
        {"rank": 9, "name": "Brandon Moreno"},
        {"rank": 10, "name": "Steve Erceg"},
        {"rank": 11, "name": "Alex Perez"},
        {"rank": 12, "name": "Tim Elliott"},
        {"rank": 13, "name": "Tagir Ulanbekov"},
        {"rank": 14, "name": "Charles Johnson"},
        {"rank": 15, "name": "Bruno Silva"},
    ],
    "Bantamweight": [
        {"rank": 1, "name": "Merab Dvalishvili"},
        {"rank": 2, "name": "Umar Nurmagomedov"},
        {"rank": 2, "name": "Sean O'Malley"},
        {"rank": 4, "name": "Cory Sandhagen"},
        {"rank": 5, "name": "Song Yadong"},
        {"rank": 6, "name": "Aiemann Zahabi"},
        {"rank": 7, "name": "Deiveson Figueiredo"},
        {"rank": 8, "name": "Mario Bautista"},
        {"rank": 9, "name": "David Martinez"},
        {"rank": 10, "name": "Marlon Vera"},
        {"rank": 11, "name": "Payton Talbott"},
        {"rank": 12, "name": "Vinicius Oliveira"},
        {"rank": 13, "name": "Raul Rosas Jr."},
        {"rank": 14, "name": "Raoni Barcelos"},
        {"rank": 15, "name": "Farid Basharat"},
    ],
    "Featherweight": [
        {"rank": 1, "name": "Movsar Evloev"},
        {"rank": 2, "name": "Diego Lopes"},
        {"rank": 3, "name": "Lerone Murphy"},
        {"rank": 4, "name": "Aljamain Sterling"},
        {"rank": 5, "name": "Yair Rodriguez"},
        {"rank": 6, "name": "Jean Silva"},
        {"rank": 7, "name": "Arnold Allen"},
        {"rank": 8, "name": "Youssef Zalal"},
        {"rank": 9, "name": "Steve Garcia"},
        {"rank": 10, "name": "Kevin Vallejos"},
        {"rank": 11, "name": "Brian Ortega"},
        {"rank": 12, "name": "Melquizael Costa"},
        {"rank": 13, "name": "Aaron Pico"},
        {"rank": 14, "name": "David Onama"},
        {"rank": 15, "name": "Josh Emmett"},
    ],
    "Lightweight": [
        {"rank": 1, "name": "Justin Gaethje"},
        {"rank": 2, "name": "Arman Tsarukyan"},
        {"rank": 3, "name": "Charles Oliveira"},
        {"rank": 4, "name": "Max Holloway"},
        {"rank": 5, "name": "Benoit Saint Denis"},
        {"rank": 6, "name": "Paddy Pimblett"},
        {"rank": 7, "name": "Mateusz Gamrot"},
        {"rank": 8, "name": "Dan Hooker"},
        {"rank": 9, "name": "Renato Moicano"},
        {"rank": 9, "name": "Mauricio Ruffy"},
        {"rank": 11, "name": "Rafael Fiziev"},
        {"rank": 12, "name": "Quillan Salkilld"},
        {"rank": 13, "name": "Michael Chandler"},
        {"rank": 14, "name": "Fares Ziam"},
        {"rank": 15, "name": "Beneil Dariush"},
    ],
    "Welterweight": [
        {"rank": 1, "name": "Ian Machado Garry"},
        {"rank": 2, "name": "Carlos Prates"},
        {"rank": 3, "name": "Michael Morales"},
        {"rank": 4, "name": "Jack Della Maddalena"},
        {"rank": 5, "name": "Belal Muhammad"},
        {"rank": 6, "name": "Sean Brady"},
        {"rank": 7, "name": "Leon Edwards"},
        {"rank": 8, "name": "Kamaru Usman"},
        {"rank": 9, "name": "Joaquin Buckley"},
        {"rank": 10, "name": "Yaroslav Amosov"},
        {"rank": 11, "name": "Gabriel Bonfim"},
        {"rank": 12, "name": "Mike Malott"},
        {"rank": 13, "name": "Michael Venom Page"},
        {"rank": 13, "name": "Uros Medic"},
        {"rank": 15, "name": "Daniel Rodriguez"},
    ],
    "Middleweight": [
        {"rank": 1, "name": "Khamzat Chimaev"},
        {"rank": 2, "name": "Dricus Du Plessis"},
        {"rank": 3, "name": "Nassourdine Imavov"},
        {"rank": 4, "name": "Caio Borralho"},
        {"rank": 4, "name": "Brendan Allen"},
        {"rank": 6, "name": "Anthony Hernandez"},
        {"rank": 6, "name": "Joe Pyfer"},
        {"rank": 8, "name": "Reinier de Ridder"},
        {"rank": 9, "name": "Israel Adesanya"},
        {"rank": 10, "name": "Robert Whittaker"},
        {"rank": 11, "name": "Jared Cannonier"},
        {"rank": 12, "name": "Gregory Rodrigues"},
        {"rank": 13, "name": "Christian Leroy Duncan"},
        {"rank": 14, "name": "Paulo Costa"},
        {"rank": 15, "name": "Roman Dolidze"},
    ],
    "Light Heavyweight": [
        {"rank": 1, "name": "Magomed Ankalaev"},
        {"rank": 2, "name": "Alex Pereira"},
        {"rank": 3, "name": "Jiri Prochazka"},
        {"rank": 4, "name": "Jan Blachowicz"},
        {"rank": 5, "name": "Khalil Rountree Jr."},
        {"rank": 6, "name": "Jamahal Hill"},
        {"rank": 7, "name": "Paulo Costa"},
        {"rank": 8, "name": "Azamat Murzakanov"},
        {"rank": 9, "name": "Volkan Oezdemir"},
        {"rank": 10, "name": "Bogdan Guskov"},
        {"rank": 11, "name": "Dominick Reyes"},
        {"rank": 12, "name": "Aleksandar Rakic"},
        {"rank": 13, "name": "Nikita Krylov"},
        {"rank": 14, "name": "Johnny Walker"},
        {"rank": 15, "name": "Alonzo Menifield"},
    ],
    "Heavyweight": [
        {"rank": 1, "name": "Ciryl Gane"},
        {"rank": 2, "name": "Alexander Volkov"},
        {"rank": 3, "name": "Sergei Pavlovich"},
        {"rank": 4, "name": "Waldo Cortes Acosta"},
        {"rank": 5, "name": "Josh Hokit"},
        {"rank": 6, "name": "Serghei Spivac"},
        {"rank": 7, "name": "Curtis Blaydes"},
        {"rank": 8, "name": "Rizvan Kuniev"},
        {"rank": 9, "name": "Derrick Lewis"},
        {"rank": 10, "name": "Tyrell Fortune"},
        {"rank": 11, "name": "Ante Delija"},
        {"rank": 12, "name": "Marcin Tybura"},
        {"rank": 13, "name": "Valter Walker"},
        {"rank": 14, "name": "Brando Pericic"},
        {"rank": 15, "name": "Tallison Teixeira"},
    ],
}


def normalize_fighter_name(name):
    name = unicodedata.normalize("NFKD", str(name or ""))
    name = "".join(ch for ch in name if not unicodedata.combining(ch))
    name = name.lower().replace("'", "").replace("`", "")
    name = re.sub(r"[^a-z0-9]+", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def fighter_image_key(value):
    value = os.path.splitext(str(value or ""))[0]
    value = re.sub(r"_[LR](?:_|$).*", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"_BELT.*|_BMF.*|_MOCK.*", " ", value, flags=re.IGNORECASE)
    return normalize_fighter_name(value)


FIGHTER_IMAGE_FILES = {}
FIGHTER_IMAGE_DIR = os.path.join(BASE_DIR, "static", "fighters")
FIGHTER_IMAGE_ALIASES = {
    "Ciryl Gane": "Cyril Gane.avif",
    "Vinicius Oliveira": "OLIVIEIRA_VINICIUS_L_03-02.avif",
}

if os.path.isdir(FIGHTER_IMAGE_DIR):
    for filename in os.listdir(FIGHTER_IMAGE_DIR):
        if filename.lower().endswith((".avif", ".jpg", ".jpeg", ".png", ".webp")):
            FIGHTER_IMAGE_FILES[fighter_image_key(filename)] = filename


def image_url_for_fighter(name):
    alias_filename = FIGHTER_IMAGE_ALIASES.get(name)
    if alias_filename:
        alias_path = os.path.join(FIGHTER_IMAGE_DIR, alias_filename)
        if os.path.exists(alias_path):
            return f"/static/fighters/{alias_filename}"

    target_tokens = set(normalize_fighter_name(name).split())
    if not target_tokens:
        return ""

    best_filename = ""
    best_score = 0

    for image_key, filename in FIGHTER_IMAGE_FILES.items():
        image_tokens = set(image_key.split())
        if not image_tokens:
            continue

        shared = target_tokens & image_tokens
        covers_name = shared == target_tokens
        covers_image = shared == image_tokens
        score = len(shared) * 2 + int(covers_name) + int(covers_image)

        if score > best_score:
            best_score = score
            best_filename = filename

    min_score = max(2, min(len(target_tokens), 2) * 2)
    if best_score < min_score:
        return ""

    return f"/static/fighters/{best_filename}"


def fighter_lookup_row(name):
    target = normalize_fighter_name(name)
    for df in [fighter_stats_df, fighters_df]:
        if "Full Name" not in df.columns:
            continue
        matches = df[df["Full Name"].apply(normalize_fighter_name) == target]
        if not matches.empty:
            return matches.iloc[0]
    return None


def build_ranked_fighter(entry, is_champion=False):
    row = fighter_lookup_row(entry["name"])
    if row is None:
        row = pd.Series(dtype=object)

    wr = normalize_rate(safe_float(row.get("Win_Rate"), 0))
    rank = "C" if is_champion else int(entry["rank"])

    return {
        "rank":         rank,
        "rank_label":   "Champion" if is_champion else f"#{rank}",
        "Fighter_Id":   str(row.get("Fighter_Id", "")),
        "name":         entry["name"],
        "nickname":     str(row.get("Nickname", "")),
        "W":            int(safe_float(row.get("W", 0))),
        "L":            int(safe_float(row.get("L", 0))),
        "D":            int(safe_float(row.get("D", 0))),
        "win_rate":     round(wr * 100, 1),
        "ko_rate":      round(display_rate(row.get("KO_Rate", row.get("KO Rate", 0))), 1),
        "sig_str":      round(display_rate(row.get("Strike_Acc", row.get("Sig. Str. %", 0))), 1),
        "total_fights": int(safe_float(row.get("Total_Fights"), 0)),
        "belt":         1 if is_champion else 0,
        "image":        image_url_for_fighter(entry["name"]),
        "source":       "official_ufc_rankings",
    }


@app.route("/api/top15")
def top15_all():
    return jsonify({
        "divisions": DIVISION_ORDER,
        "source": "official_ufc_rankings",
        "updated": "2026-05-19",
    })


@app.route("/api/top15/<division>")
def top15_division(division):
    official_rankings = MENS_UFC_RANKINGS.get(division)
    if official_rankings is None:
        return jsonify({"fighters": [], "division": division}), 404

    fighters = [build_ranked_fighter(
        {"name": MENS_UFC_CHAMPIONS[division]},
        is_champion=True
    )]
    fighters.extend(build_ranked_fighter(entry) for entry in official_rankings)

    return jsonify({
        "division": division,
        "fighters": fighters,
        "source": "official_ufc_rankings",
        "updated": "2026-05-19",
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
