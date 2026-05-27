import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

# Set paths
DATA_DIR = '../data'
OUTPUT_DIR = '../output'

# Load data
print("Loading data...")
events_df = pd.read_csv(f'{DATA_DIR}/Cleaned_Events.csv')
fighter_stats_df = pd.read_csv(f'{DATA_DIR}/Cleaned_Fighter_Stats.csv')
fights_df = pd.read_csv(f'{DATA_DIR}/Cleaned_Fights.csv')
fighters_df = pd.read_csv(f'{DATA_DIR}/Fixed_Cleaned_Fighters.csv')

print(f"Events: {len(events_df)}")
print(f"Fighter Stats: {len(fighter_stats_df)}")
print(f"Fights: {len(fights_df)}")
print(f"Fighters: {len(fighters_df)}")

# Data preprocessing
print("\nPreprocessing data...")

# Convert date
events_df['Date'] = pd.to_datetime(events_df['Date'])

# Merge fighter physical attributes with stats
fighter_stats_df = fighter_stats_df.merge(
    fighters_df[['Fighter_Id', 'height_cm', 'weight_kg', 'reach_cm']], 
    on='Fighter_Id', 
    how='left'
)

# Clean weight class names
fights_df['Weight_Class'] = fights_df['Weight_Class'].str.upper().str.strip()
fighter_stats_df['Weight_Class'] = fighter_stats_df['Weight_Class'].str.upper().str.strip()

# Standardize weight class names
weight_class_mapping = {
    'BANTAMWEIGHT': 'Bantamweight',
    'FEATHERWEIGHT': 'Featherweight',
    'FLYWEIGHT': 'Flyweight',
    'HEAVYWEIGHT': 'Heavyweight',
    'LIGHT HEAVYWEIGHT': 'Light Heavyweight',
    'LIGHTWEIGHT': 'Lightweight',
    'MIDDLEWEIGHT': 'Middleweight',
    'WELTERWEIGHT': 'Welterweight',
    "WOMEN'S BANTAMWEIGHT": "Women's Bantamweight",
    "WOMEN'S FEATHERWEIGHT": "Women's Featherweight",
    "WOMEN'S FLYWEIGHT": "Women's Flyweight",
    "WOMEN'S STRAWWEIGHT": "Women's Strawweight",
}

fights_df['Weight_Class_Standard'] = fights_df['Weight_Class'].map(weight_class_mapping)
fighter_stats_df['Weight_Class_Standard'] = fighter_stats_df['Weight_Class'].map(weight_class_mapping)

# Merge events with fights to get dates
fights_df = fights_df.merge(events_df[['Event_Id', 'Date']], on='Event_Id', how='left')
fights_df['Year'] = fights_df['Date'].dt.year

print("Data preprocessing complete.")

# ============================================
# ANALYSIS 1: Physical Attributes vs Performance Metrics
# ============================================
print("\nGenerating Physical Attributes vs Performance Metrics analysis...")

# Filter fighters with complete data
physical_data = fighter_stats_df[
    (fighter_stats_df['height_cm'].notna()) & 
    (fighter_stats_df['weight_kg'].notna()) & 
    (fighter_stats_df['reach_cm'].notna()) &
    (fighter_stats_df['Win_Rate'].notna())
].copy()

# Create scatter plots for physical attributes vs performance
fig1 = make_subplots(
    rows=2, cols=3,
    subplot_titles=('Height vs Win Rate', 'Weight vs Win Rate', 'Reach vs Win Rate',
                    'Height vs Striking Accuracy', 'Weight vs Striking Accuracy', 'Reach vs Striking Accuracy'),
    specs=[[{'type': 'scatter'}, {'type': 'scatter'}, {'type': 'scatter'}],
           [{'type': 'scatter'}, {'type': 'scatter'}, {'type': 'scatter'}]]
)

# Height vs Win Rate
fig1.add_trace(
    go.Scatter(
        x=physical_data['height_cm'],
        y=physical_data['Win_Rate'],
        mode='markers',
        marker=dict(size=5, color=physical_data['Win_Rate'], colorscale='Viridis', showscale=False),
        text=physical_data['Full Name'],
        name='Height vs Win Rate'
    ),
    row=1, col=1
)

# Weight vs Win Rate
fig1.add_trace(
    go.Scatter(
        x=physical_data['weight_kg'],
        y=physical_data['Win_Rate'],
        mode='markers',
        marker=dict(size=5, color=physical_data['Win_Rate'], colorscale='Viridis', showscale=False),
        text=physical_data['Full Name'],
        name='Weight vs Win Rate'
    ),
    row=1, col=2
)

# Reach vs Win Rate
fig1.add_trace(
    go.Scatter(
        x=physical_data['reach_cm'],
        y=physical_data['Win_Rate'],
        mode='markers',
        marker=dict(size=5, color=physical_data['Win_Rate'], colorscale='Viridis', showscale=False),
        text=physical_data['Full Name'],
        name='Reach vs Win Rate'
    ),
    row=1, col=3
)

# Height vs Striking Accuracy
fig1.add_trace(
    go.Scatter(
        x=physical_data['height_cm'],
        y=physical_data['Sig. Str. %'],
        mode='markers',
        marker=dict(size=5, color=physical_data['Sig. Str. %'], colorscale='Plasma', showscale=False),
        text=physical_data['Full Name'],
        name='Height vs Striking Accuracy'
    ),
    row=2, col=1
)

# Weight vs Striking Accuracy
fig1.add_trace(
    go.Scatter(
        x=physical_data['weight_kg'],
        y=physical_data['Sig. Str. %'],
        mode='markers',
        marker=dict(size=5, color=physical_data['Sig. Str. %'], colorscale='Plasma', showscale=False),
        text=physical_data['Full Name'],
        name='Weight vs Striking Accuracy'
    ),
    row=2, col=2
)

# Reach vs Striking Accuracy
fig1.add_trace(
    go.Scatter(
        x=physical_data['reach_cm'],
        y=physical_data['Sig. Str. %'],
        mode='markers',
        marker=dict(size=5, color=physical_data['Sig. Str. %'], colorscale='Plasma', showscale=False),
        text=physical_data['Full Name'],
        name='Reach vs Striking Accuracy'
    ),
    row=2, col=3
)

fig1.update_xaxes(title_text="Height (cm)", row=1, col=1)
fig1.update_xaxes(title_text="Weight (kg)", row=1, col=2)
fig1.update_xaxes(title_text="Reach (cm)", row=1, col=3)
fig1.update_xaxes(title_text="Height (cm)", row=2, col=1)
fig1.update_xaxes(title_text="Weight (kg)", row=2, col=2)
fig1.update_xaxes(title_text="Reach (cm)", row=2, col=3)

fig1.update_yaxes(title_text="Win Rate", row=1, col=1)
fig1.update_yaxes(title_text="Win Rate", row=1, col=2)
fig1.update_yaxes(title_text="Win Rate", row=1, col=3)
fig1.update_yaxes(title_text="Striking Accuracy %", row=2, col=1)
fig1.update_yaxes(title_text="Striking Accuracy %", row=2, col=2)
fig1.update_yaxes(title_text="Striking Accuracy %", row=2, col=3)

fig1.update_layout(
    height=800,
    title_text="Physical Attributes vs Performance Metrics",
    showlegend=False
)

fig1.write_html(f'{OUTPUT_DIR}/physical_attributes_vs_performance.html')
print("Saved: physical_attributes_vs_performance.html")

# Correlation heatmap for physical attributes and performance
corr_metrics = ['height_cm', 'weight_kg', 'reach_cm', 'Win_Rate', 'Sig. Str. %', 'KO Rate', 'SUB Rate', 'TD', 'SUB']
corr_data = physical_data[corr_metrics].corr()

fig2 = go.Figure(data=go.Heatmap(
    z=corr_data.values,
    x=corr_metrics,
    y=corr_metrics,
    colorscale='RdBu',
    zmid=0,
    text=np.round(corr_data.values, 2),
    texttemplate="%{text}",
    textfont={"size": 10},
    colorbar=dict(title="Correlation")
))

fig2.update_layout(
    title="Correlation Matrix: Physical Attributes vs Performance Metrics",
    width=800,
    height=800
)

fig2.write_html(f'{OUTPUT_DIR}/correlation_heatmap.html')
print("Saved: correlation_heatmap.html")

# ============================================
# ANALYSIS 2: Fight Outcomes Analysis
# ============================================
print("\nGenerating Fight Outcomes analysis...")

# Analyze fight outcomes by performance metrics
fight_outcomes = fights_df.copy()
fight_outcomes['Method_Category'] = fight_outcomes['Method'].str.upper()

# Categorize methods
def categorize_method(method):
    if pd.isna(method):
        return 'Unknown'
    method = str(method).upper()
    if 'KO' in method or 'TKO' in method:
        return 'KO/TKO'
    elif 'SUB' in method or 'CHOKE' in method or 'ARM' in method:
        return 'Submission'
    elif 'DEC' in method:
        return 'Decision'
    else:
        return 'Other'

# Add Win_Method to fights_df for use in later analysis
fights_df['Win_Method'] = fights_df['Method'].apply(categorize_method)
fight_outcomes['Win_Method'] = fight_outcomes['Method'].apply(categorize_method)

# Calculate average performance metrics by win method
performance_by_method = fight_outcomes.groupby('Win_Method').agg({
    'KD_1': 'mean',
    'STR_1': 'mean',
    'TD_1': 'mean',
    'SUB_1': 'mean',
    'Sig. Str. %_1': 'mean',
    'Ctrl_1': 'mean'
}).reset_index()

fig3 = make_subplots(
    rows=2, cols=3,
    subplot_titles=('Avg Knockdowns', 'Avg Strikes', 'Avg Takedowns',
                    'Avg Submissions', 'Striking Accuracy %', 'Control Time'),
    specs=[[{'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}],
           [{'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}]]
)

methods = performance_by_method['Win_Method']

# Knockdowns
fig3.add_trace(
    go.Bar(x=methods, y=performance_by_method['KD_1'], name='Knockdowns', marker_color='lightblue'),
    row=1, col=1
)

# Strikes
fig3.add_trace(
    go.Bar(x=methods, y=performance_by_method['STR_1'], name='Strikes', marker_color='lightgreen'),
    row=1, col=2
)

# Takedowns
fig3.add_trace(
    go.Bar(x=methods, y=performance_by_method['TD_1'], name='Takedowns', marker_color='lightcoral'),
    row=1, col=3
)

# Submissions
fig3.add_trace(
    go.Bar(x=methods, y=performance_by_method['SUB_1'], name='Submissions', marker_color='lightyellow'),
    row=2, col=1
)

# Striking Accuracy
fig3.add_trace(
    go.Bar(x=methods, y=performance_by_method['Sig. Str. %_1'], name='Striking Accuracy', marker_color='lightpink'),
    row=2, col=2
)

# Control Time
fig3.add_trace(
    go.Bar(x=methods, y=performance_by_method['Ctrl_1'], name='Control Time', marker_color='lavender'),
    row=2, col=3
)

fig3.update_layout(
    height=700,
    title_text="Average Performance Metrics by Win Method",
    showlegend=False
)

fig3.write_html(f'{OUTPUT_DIR}/fight_outcomes_analysis.html')
print("Saved: fight_outcomes_analysis.html")

# ============================================
# ANALYSIS 3: Weight Class Patterns
# ============================================
print("\nGenerating Weight Class Patterns analysis...")

# Analyze patterns across weight classes
weight_class_stats = fighter_stats_df.groupby('Weight_Class_Standard').agg({
    'height_cm': 'mean',
    'weight_kg': 'mean',
    'reach_cm': 'mean',
    'Win_Rate': 'mean',
    'Sig. Str. %': 'mean',
    'KO Rate': 'mean',
    'SUB Rate': 'mean',
    'TD': 'mean',
    'SUB': 'mean'
}).reset_index()

weight_class_stats = weight_class_stats.sort_values('weight_kg')

fig4 = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Physical Attributes by Weight Class', 'Win Rates by Weight Class',
                    'KO/TKO Rates by Weight Class', 'Submission Rates by Weight Class'),
    specs=[[{'type': 'scatter'}, {'type': 'bar'}],
           [{'type': 'bar'}, {'type': 'bar'}]]
)

# Physical attributes
fig4.add_trace(
    go.Scatter(x=weight_class_stats['Weight_Class_Standard'], y=weight_class_stats['height_cm'],
               mode='lines+markers', name='Height (cm)', line=dict(color='blue')),
    row=1, col=1
)
fig4.add_trace(
    go.Scatter(x=weight_class_stats['Weight_Class_Standard'], y=weight_class_stats['weight_kg'],
               mode='lines+markers', name='Weight (kg)', line=dict(color='red')),
    row=1, col=1
)
fig4.add_trace(
    go.Scatter(x=weight_class_stats['Weight_Class_Standard'], y=weight_class_stats['reach_cm'],
               mode='lines+markers', name='Reach (cm)', line=dict(color='green')),
    row=1, col=1
)

# Win rates
fig4.add_trace(
    go.Bar(x=weight_class_stats['Weight_Class_Standard'], y=weight_class_stats['Win_Rate'],
           name='Win Rate', marker_color='purple'),
    row=1, col=2
)

# KO Rates
fig4.add_trace(
    go.Bar(x=weight_class_stats['Weight_Class_Standard'], y=weight_class_stats['KO Rate'],
           name='KO Rate', marker_color='orange'),
    row=2, col=1
)

# Submission Rates
fig4.add_trace(
    go.Bar(x=weight_class_stats['Weight_Class_Standard'], y=weight_class_stats['SUB Rate'],
           name='Submission Rate', marker_color='teal'),
    row=2, col=2
)

fig4.update_xaxes(title_text="Weight Class", row=1, col=1)
fig4.update_xaxes(title_text="Weight Class", row=1, col=2)
fig4.update_xaxes(title_text="Weight Class", row=2, col=1)
fig4.update_xaxes(title_text="Weight Class", row=2, col=2)

fig4.update_yaxes(title_text="Measurement", row=1, col=1)
fig4.update_yaxes(title_text="Win Rate", row=1, col=2)
fig4.update_yaxes(title_text="KO Rate", row=2, col=1)
fig4.update_yaxes(title_text="Submission Rate", row=2, col=2)

fig4.update_layout(
    height=800,
    title_text="Weight Class Patterns Analysis",
    showlegend=True
)

fig4.write_html(f'{OUTPUT_DIR}/weight_class_patterns.html')
print("Saved: weight_class_patterns.html")

# ============================================
# ANALYSIS 4: Win Methods Correlation with Physical Attributes
# ============================================
print("\nGenerating Win Methods Correlation analysis...")

# Merge fight data with fighter physical attributes
fights_with_physical = fights_df.merge(
    fighters_df[['Fighter_Id', 'height_cm', 'weight_kg', 'reach_cm']],
    left_on='Fighter_Id_1',
    right_on='Fighter_Id',
    how='left'
)

fights_with_physical['Win_Method'] = fights_with_physical['Method'].apply(categorize_method)

# Calculate average physical attributes by win method
physical_by_method = fights_with_physical.groupby('Win_Method').agg({
    'height_cm': 'mean',
    'weight_kg': 'mean',
    'reach_cm': 'mean'
}).reset_index()

fig5 = make_subplots(
    rows=1, cols=3,
    subplot_titles=('Avg Height by Win Method', 'Avg Weight by Win Method', 'Avg Reach by Win Method')
)

# Height
fig5.add_trace(
    go.Bar(x=physical_by_method['Win_Method'], y=physical_by_method['height_cm'],
           name='Height (cm)', marker_color='skyblue'),
    row=1, col=1
)

# Weight
fig5.add_trace(
    go.Bar(x=physical_by_method['Win_Method'], y=physical_by_method['weight_kg'],
           name='Weight (kg)', marker_color='lightcoral'),
    row=1, col=2
)

# Reach
fig5.add_trace(
    go.Bar(x=physical_by_method['Win_Method'], y=physical_by_method['reach_cm'],
           name='Reach (cm)', marker_color='lightgreen'),
    row=1, col=3
)

fig5.update_xaxes(title_text="Win Method", row=1, col=1)
fig5.update_xaxes(title_text="Win Method", row=1, col=2)
fig5.update_xaxes(title_text="Win Method", row=1, col=3)

fig5.update_yaxes(title_text="Height (cm)", row=1, col=1)
fig5.update_yaxes(title_text="Weight (kg)", row=1, col=2)
fig5.update_yaxes(title_text="Reach (cm)", row=1, col=3)

fig5.update_layout(
    height=400,
    title_text="Physical Attributes by Win Method",
    showlegend=False
)

fig5.write_html(f'{OUTPUT_DIR}/win_methods_correlation.html')
print("Saved: win_methods_correlation.html")

# ============================================
# ANALYSIS 5: Performance Trends Over Time
# ============================================
print("\nGenerating Performance Trends Over Time analysis...")

# Calculate yearly averages
yearly_stats = fights_df.groupby('Year').agg({
    'KD_1': 'mean',
    'STR_1': 'mean',
    'TD_1': 'mean',
    'SUB_1': 'mean',
    'Sig. Str. %_1': 'mean',
    'Ctrl_1': 'mean'
}).reset_index()

yearly_stats = yearly_stats.sort_values('Year')

fig6 = make_subplots(
    rows=2, cols=3,
    subplot_titles=('Avg Knockdowns Over Time', 'Avg Strikes Over Time', 'Avg Takedowns Over Time',
                    'Avg Submissions Over Time', 'Striking Accuracy Over Time', 'Control Time Over Time'),
    specs=[[{'type': 'scatter'}, {'type': 'scatter'}, {'type': 'scatter'}],
           [{'type': 'scatter'}, {'type': 'scatter'}, {'type': 'scatter'}]]
)

# Knockdowns
fig6.add_trace(
    go.Scatter(x=yearly_stats['Year'], y=yearly_stats['KD_1'],
               mode='lines+markers', name='Knockdowns', line=dict(color='blue')),
    row=1, col=1
)

# Strikes
fig6.add_trace(
    go.Scatter(x=yearly_stats['Year'], y=yearly_stats['STR_1'],
               mode='lines+markers', name='Strikes', line=dict(color='red')),
    row=1, col=2
)

# Takedowns
fig6.add_trace(
    go.Scatter(x=yearly_stats['Year'], y=yearly_stats['TD_1'],
               mode='lines+markers', name='Takedowns', line=dict(color='green')),
    row=1, col=3
)

# Submissions
fig6.add_trace(
    go.Scatter(x=yearly_stats['Year'], y=yearly_stats['SUB_1'],
               mode='lines+markers', name='Submissions', line=dict(color='purple')),
    row=2, col=1
)

# Striking Accuracy
fig6.add_trace(
    go.Scatter(x=yearly_stats['Year'], y=yearly_stats['Sig. Str. %_1'],
               mode='lines+markers', name='Striking Accuracy', line=dict(color='orange')),
    row=2, col=2
)

# Control Time
fig6.add_trace(
    go.Scatter(x=yearly_stats['Year'], y=yearly_stats['Ctrl_1'],
               mode='lines+markers', name='Control Time', line=dict(color='brown')),
    row=2, col=3
)

fig6.update_xaxes(title_text="Year", row=1, col=1)
fig6.update_xaxes(title_text="Year", row=1, col=2)
fig6.update_xaxes(title_text="Year", row=1, col=3)
fig6.update_xaxes(title_text="Year", row=2, col=1)
fig6.update_xaxes(title_text="Year", row=2, col=2)
fig6.update_xaxes(title_text="Year", row=2, col=3)

fig6.update_yaxes(title_text="Avg Knockdowns", row=1, col=1)
fig6.update_yaxes(title_text="Avg Strikes", row=1, col=2)
fig6.update_yaxes(title_text="Avg Takedowns", row=1, col=3)
fig6.update_yaxes(title_text="Avg Submissions", row=2, col=1)
fig6.update_yaxes(title_text="Striking Accuracy %", row=2, col=2)
fig6.update_yaxes(title_text="Control Time", row=2, col=3)

fig6.update_layout(
    height=800,
    title_text="Performance Trends Over Time",
    showlegend=False
)

fig6.write_html(f'{OUTPUT_DIR}/performance_trends_over_time.html')
print("Saved: performance_trends_over_time.html")

# Win method distribution over time
win_method_yearly = fights_df.groupby(['Year', 'Win_Method']).size().reset_index(name='Count')

fig7 = px.bar(
    win_method_yearly,
    x='Year',
    y='Count',
    color='Win_Method',
    title='Win Method Distribution Over Time',
    labels={'Count': 'Number of Fights', 'Year': 'Year'}
)

fig7.update_layout(height=500, width=1000)
fig7.write_html(f'{OUTPUT_DIR}/win_method_distribution_over_time.html')
print("Saved: win_method_distribution_over_time.html")

# ============================================
# COMPREHENSIVE DASHBOARD
# ============================================
print("\nCreating comprehensive interactive dashboard...")

# Create a comprehensive dashboard with multiple tabs
dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>UFC Fighter Analysis Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
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
            0% { transform: translateY(0) rotate(0deg); }
            100% { transform: translateY(-100px) rotate(360deg); }
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
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
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
            <button class="tab active" onclick="showTab('overview')">Overview</button>
            <button class="tab" onclick="showTab('physical')">Physical Attributes</button>
            <button class="tab" onclick="showTab('outcomes')">Fight Outcomes</button>
            <button class="tab" onclick="showTab('weight')">Weight Classes</button>
            <button class="tab" onclick="showTab('trends')">Trends Over Time</button>
        </div>

        <div id="overview" class="content active">
            <h2>📊 Dashboard Overview</h2>
            <div class="summary">
                <h3>🔍 Key Findings Summary</h3>
                <p>This dashboard provides comprehensive analysis of UFC fighters' physical attributes and their impact on performance metrics.</p>
                <ul>
                    <li><strong>Physical Attributes:</strong> Height, weight, and reach correlations with win rates and striking accuracy</li>
                    <li><strong>Fight Outcomes:</strong> Performance metrics (knockdowns, strikes, takedowns, submissions) by win method</li>
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
                <p>Examination of fight outcomes in relation to striking accuracy, takedown success, and submission rates across different win methods.</p>
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
        function showTab(tabName) {
            // Hide all content
            var contents = document.getElementsByClassName('content');
            for (var i = 0; i < contents.length; i++) {
                contents[i].classList.remove('active');
            }
            
            // Remove active class from all tabs
            var tabs = document.getElementsByClassName('tab');
            for (var i = 0; i < tabs.length; i++) {
                tabs[i].classList.remove('active');
            }
            
            // Show selected content and activate tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
"""

with open(f'{OUTPUT_DIR}/ufc_analysis_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(dashboard_html)

print("Saved: ufc_analysis_dashboard.html")

print("\n" + "="*50)
print("DASHBOARD GENERATION COMPLETE")
print("="*50)
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
