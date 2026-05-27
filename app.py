from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import json, os, warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# ── Data Loading ───────────────────────────────────────────────────────────────
print("Loading UFC data…")
events_df        = pd.read_csv(os.path.join(DATA_DIR, 'Cleaned_Events.csv'))
fighter_stats_df = pd.read_csv(os.path.join(DATA_DIR, 'Cleaned_Fighter_Stats.csv'))
fights_df        = pd.read_csv(os.path.join(DATA_DIR, 'Cleaned_Fights.csv'))
fighters_df      = pd.read_csv(os.path.join(DATA_DIR, 'Fixed_Cleaned_Fighters.csv'))

events_df['Date'] = pd.to_datetime(events_df['Date'])
fights_df = fights_df.merge(events_df[['Event_Id', 'Date']], on='Event_Id', how='left')
fights_df['Year'] = fights_df['Date'].dt.year

fighter_stats_df = fighter_stats_df.merge(
    fighters_df[['Fighter_Id', 'height_cm', 'weight_kg', 'reach_cm']],
    on='Fighter_Id', how='left'
)

WC_MAP = {
    'BANTAMWEIGHT': 'Bantamweight', 'FEATHERWEIGHT': 'Featherweight',
    'FLYWEIGHT': 'Flyweight', 'HEAVYWEIGHT': 'Heavyweight',
    'LIGHT HEAVYWEIGHT': 'Light Heavyweight', 'LIGHTWEIGHT': 'Lightweight',
    'MIDDLEWEIGHT': 'Middleweight', 'WELTERWEIGHT': 'Welterweight',
    "WOMEN'S BANTAMWEIGHT": "Women's Bantamweight",
    "WOMEN'S FEATHERWEIGHT": "Women's Featherweight",
    "WOMEN'S FLYWEIGHT": "Women's Flyweight",
    "WOMEN'S STRAWWEIGHT": "Women's Strawweight",
}
WC_ORDER = [
    "Women's Strawweight", "Women's Flyweight", "Women's Bantamweight",
    "Women's Featherweight", "Flyweight", "Bantamweight", "Featherweight",
    "Lightweight", "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"
]

for df in [fights_df, fighter_stats_df]:
    if 'Weight_Class' in df.columns:
        df['Weight_Class'] = df['Weight_Class'].astype(str).str.upper().str.strip()
        df['Weight_Class_Std'] = df['Weight_Class'].map(WC_MAP)

def categorize_method(m):
    if pd.isna(m): return 'Unknown'
    m = str(m).upper()
    if 'KO' in m or 'TKO' in m: return 'KO/TKO'
    if 'SUB' in m or 'CHOKE' in m: return 'Submission'
    if 'DEC' in m: return 'Decision'
    return 'Other'

fights_df['Win_Method'] = fights_df['Method'].apply(categorize_method)

# ── Precompute percentile thresholds for star ratings ─────────────────────────
PCTILES = {}
for col in ['Sig. Str. %', 'KO Rate', 'SUB Rate', 'Win_Rate', 'Total_Fights', 'TD']:
    if col in fighter_stats_df.columns:
        vals = fighter_stats_df[col].dropna()
        PCTILES[col] = [float(vals.quantile(q)) for q in [0.2, 0.4, 0.6, 0.8]]

def star_rating(value, col):
    if col not in PCTILES or pd.isna(value):
        return 3
    thresholds = PCTILES[col]
    for i, t in enumerate(thresholds):
        if float(value) <= t:
            return i + 1
    return 5

print("Data ready.")

# ── Chart Theme ────────────────────────────────────────────────────────────────
PAL  = ['#d20000', '#ff4444', '#cccccc', '#888888', '#cc4400', '#ff8800', '#aa0000', '#ff6666']
GRID = 'rgba(255,255,255,0.05)'
FILL = {
    '#d20000': 'rgba(210,0,0,0.15)', '#ff4444': 'rgba(255,68,68,0.12)',
    '#cccccc': 'rgba(204,204,204,0.08)', '#888888': 'rgba(136,136,136,0.10)',
    '#cc4400': 'rgba(204,68,0,0.12)', '#ff8800': 'rgba(255,136,0,0.12)',
    '#aa0000': 'rgba(170,0,0,0.12)', '#ff6666': 'rgba(255,102,102,0.12)',
}

def L(height=None, title=None, **kw):
    d = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(10,10,10,1)',
        font=dict(color='#999999', family='Inter, sans-serif', size=12),
        hoverlabel=dict(bgcolor='#1a1a1a', bordercolor='rgba(210,0,0,0.5)',
                        font=dict(color='#ffffff', size=12)),
        margin=dict(t=55, r=20, b=45, l=60),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#999999'),
                    bordercolor='rgba(210,0,0,0.2)'),
    )
    if title:
        d['title'] = dict(text=title, font=dict(size=15, color='#ffffff',
                          family='Oswald, sans-serif'), x=0.01)
    if height:
        d['height'] = height
    d.update(kw)
    return d

def ax(**kw):
    d = dict(gridcolor=GRID, linecolor='rgba(210,0,0,0.15)',
             zerolinecolor='rgba(210,0,0,0.1)',
             tickfont=dict(size=11, color='#888888'))
    d.update(kw)
    return d

def jfig(fig):
    return json.loads(pio.to_json(fig))

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/dashboard')
def index():
    return render_template('index.html')

@app.route('/api/stats')
@app.route('/api/kpis')
def kpis():
    wm = fights_df['Win_Method'].value_counts(normalize=True) * 100
    top = (fighter_stats_df[fighter_stats_df['Total_Fights'] >= 10]
           .nlargest(1, 'Win_Rate').iloc[0])
    return jsonify({
        'fighters': int(len(fighters_df)),
        'fights':   int(len(fights_df)),
        'events':   int(len(events_df)),
        'weight_classes': int(fighter_stats_df['Weight_Class_Std'].nunique()),
        'ko_rate':  round(float(wm.get('KO/TKO', 0)), 1),
        'sub_rate': round(float(wm.get('Submission', 0)), 1),
        'dec_rate': round(float(wm.get('Decision', 0)), 1),
        'avg_win_rate': round(float(fighters_df['Win_Rate'].mean() * 100), 1),
        'best_fighter': str(top['Full Name']),
    })

# ── Overview ───────────────────────────────────────────────────────────────────
@app.route('/api/charts/overview')
def ch_overview():
    cols = [c for c in ['height_cm','weight_kg','reach_cm','Win_Rate',
                         'Sig. Str. %','KO Rate','SUB Rate','TD','SUB']
            if c in fighter_stats_df.columns]
    labels = {'height_cm':'Height','weight_kg':'Weight','reach_cm':'Reach',
              'Win_Rate':'Win Rate','Sig. Str. %':'Strike Acc','KO Rate':'KO Rate',
              'SUB Rate':'Sub Rate','TD':'Takedowns','SUB':'Submissions'}
    corr = fighter_stats_df[cols].dropna().corr()
    z    = np.round(corr.values, 2)
    disp = [labels.get(c, c) for c in corr.columns]
    hm = go.Figure(go.Heatmap(
        z=z, x=disp, y=disp,
        colorscale=[[0,'#4a9eff'], [0.5,'rgba(5,15,35,1)'], [1,'#00d4ff']],
        zmid=0,
        text=z, texttemplate='%{text:.2f}', textfont=dict(size=10, color='white'),
        colorbar=dict(title=dict(text='r', font=dict(color='#6a9ec0')),
                      tickfont=dict(color='#6a9ec0')),
    ))
    hm.update_layout(**L(title='Correlation Matrix — Physical Attributes vs Performance Metrics',
                          height=460, xaxis=ax(tickangle=-35), yaxis=ax()))
    mc  = fights_df['Win_Method'].value_counts()
    pie = go.Figure(go.Pie(
        labels=mc.index, values=mc.values, hole=0.44,
        marker=dict(colors=PAL[:len(mc)], line=dict(color='rgba(0,0,0,0.3)', width=2)),
        textfont=dict(color='white', size=13), textinfo='label+percent',
    ))
    pie.update_layout(**L(title='Overall Win Method Distribution', height=360))
    return jsonify({'heatmap': jfig(hm), 'pie': jfig(pie)})

# ── Physical Q1 ────────────────────────────────────────────────────────────────
@app.route('/api/charts/physical')
def ch_physical():
    df = fighter_stats_df.dropna(subset=['height_cm','weight_kg','reach_cm','Win_Rate']).copy()
    attrs = [('height_cm','Height (cm)'), ('reach_cm','Reach (cm)'), ('weight_kg','Weight (kg)')]
    charts = []
    for metric_col, metric_lbl in [('Win_Rate','Win Rate'), ('Sig. Str. %','Striking Accuracy %')]:
        if metric_col not in df.columns: continue
        dm = df.dropna(subset=[metric_col])
        fig = make_subplots(1, 3,
            subplot_titles=[f'{al} vs {metric_lbl}' for _, al in attrs],
            horizontal_spacing=0.09)
        for i, (ac, al) in enumerate(attrs, 1):
            da = dm.dropna(subset=[ac])
            try:
                c  = np.polyfit(da[ac].values, da[metric_col].values, 1)
                xs = np.linspace(da[ac].min(), da[ac].max(), 80)
                fig.add_trace(go.Scatter(x=xs, y=np.polyval(c, xs), mode='lines',
                    line=dict(color='#f5a623', width=1.8, dash='dash'),
                    name='Trend', showlegend=(i == 1), legendgroup='trend'), row=1, col=i)
            except Exception: pass
            fig.add_trace(go.Scatter(x=da[ac], y=da[metric_col], mode='markers',
                marker=dict(size=5, color=da[metric_col],
                    colorscale=[[0,'#4a9eff'],[0.5,'#00d4ff'],[1,'#22c55e']],
                    opacity=0.65, showscale=(i==3),
                    colorbar=dict(title=dict(text=metric_lbl, font=dict(color='#6a9ec0',size=10)),
                                  tickfont=dict(color='#6a9ec0',size=10), x=1.02,
                                  tickformat='.0%') if i==3 else None),
                text=da['Full Name'],
                hovertemplate=f'<b>%{{text}}</b><br>{al}: %{{x:.1f}}<br>{metric_lbl}: %{{y:.1%}}<extra></extra>',
                showlegend=False), row=1, col=i)
            fig.update_xaxes(title_text=al, row=1, col=i, **ax())
            fig.update_yaxes(title_text=(metric_lbl if i==1 else ''), tickformat='.0%', row=1, col=i, **ax())
        fig.update_layout(**L(title=f'Physical Attributes vs {metric_lbl}', height=370, showlegend=True,
            legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#6a9ec0'), x=0, y=1.08, orientation='h')))
        charts.append(jfig(fig))
    return jsonify({'charts': charts})

# ── Stance Q2 ─────────────────────────────────────────────────────────────────
@app.route('/api/charts/stance')
def ch_stance():
    MAIN = ['Orthodox', 'Southpaw', 'Switch']
    df = fighter_stats_df.dropna(subset=['Stance','Win_Rate'])
    df = df[df['Stance'].isin(MAIN)].copy()
    ss = df.groupby('Stance').agg(Win_Rate=('Win_Rate','mean'), Count=('Win_Rate','count'),
        KO_Rate=('KO Rate','mean'), Sub_Rate=('SUB Rate','mean'),
        Strike_Acc=('Sig. Str. %','mean')).reset_index()
    bar = go.Figure()
    for col, lbl, color in [('Win_Rate','Win Rate','#22c55e'),('KO_Rate','KO Rate','#00d4ff'),
                              ('Sub_Rate','Sub Rate','#8b5cf6'),('Strike_Acc','Strike Acc','#4a9eff')]:
        bar.add_trace(go.Bar(name=lbl, x=ss['Stance'], y=ss[col], marker_color=color,
            text=ss[col].apply(lambda v: f'{v:.1%}'), textposition='outside',
            textfont=dict(color='white', size=11)))
    max_val = ss[['Win_Rate','KO_Rate','Sub_Rate','Strike_Acc']].max().max()
    bar.update_layout(**L(title='Performance Metrics by Fighting Stance', height=390,
        barmode='group', showlegend=True, xaxis=ax(title='Fighting Stance'),
        yaxis=ax(title='Rate', tickformat='.0%', range=[0, max_val*1.22])))
    sc = df['Stance'].value_counts()
    pie = go.Figure(go.Pie(labels=sc.index, values=sc.values, hole=0.44,
        marker=dict(colors=['#00d4ff','#4a9eff','#22c55e'], line=dict(color='rgba(0,0,0,0.3)',width=2)),
        textfont=dict(color='white', size=13), textinfo='label+percent'))
    pie.update_layout(**L(title='Fighter Distribution by Stance', height=360))
    box = go.Figure()
    for stance, color in zip(MAIN, ['#00d4ff','#4a9eff','#22c55e']):
        sdf = df[df['Stance']==stance]
        box.add_trace(go.Box(y=sdf['Win_Rate'], name=stance, marker=dict(color=color,size=4),
            line=dict(color=color), boxmean=True))
    box.update_layout(**L(title='Win Rate Distribution by Stance', height=380,
        yaxis=ax(title='Win Rate', tickformat='.0%'), xaxis=ax(title='Fighting Stance')))
    return jsonify({'bar': jfig(bar), 'pie': jfig(pie), 'box': jfig(box)})

# ── Experience Q3 ─────────────────────────────────────────────────────────────
@app.route('/api/charts/experience')
def ch_experience():
    df = fighter_stats_df.dropna(subset=['Total_Fights','Win_Rate']).copy()
    bins  = [0,5,10,15,20,25,float('inf')]
    blbls = ['1–5','6–10','11–15','16–20','21–25','26+']
    df['Exp'] = pd.cut(df['Total_Fights'], bins=bins, labels=blbls)
    es = df.groupby('Exp', observed=True).agg(Win_Rate=('Win_Rate','mean'),
        Count=('Win_Rate','count'), KO_Rate=('KO Rate','mean'),
        Sub_Rate=('SUB Rate','mean')).reset_index()
    fig_bar = make_subplots(specs=[[{'secondary_y': True}]])
    fig_bar.add_trace(go.Bar(x=es['Exp'].astype(str), y=es['Win_Rate'], name='Avg Win Rate',
        marker=dict(color=PAL[:len(es)], line=dict(width=0)),
        text=es['Win_Rate'].apply(lambda v: f'{v:.1%}'),
        textposition='outside', textfont=dict(color='white')), secondary_y=False)
    fig_bar.add_trace(go.Scatter(x=es['Exp'].astype(str), y=es['Count'], name='Fighter Count',
        mode='lines+markers', line=dict(color='#f5a623',width=2,dash='dot'),
        marker=dict(size=8,color='#f5a623',line=dict(color='white',width=1))), secondary_y=True)
    fig_bar.update_layout(**L(title='Win Rate & Fighter Count by Career Experience', height=390,
        showlegend=True, xaxis=ax(title='Total Career Fights')))
    fig_bar.update_yaxes(title_text='Average Win Rate', tickformat='.0%', secondary_y=False, **ax())
    fig_bar.update_yaxes(title_text='Number of Fighters', secondary_y=True, **ax())
    sc = go.Figure()
    try:
        c  = np.polyfit(df['Total_Fights'].values, df['Win_Rate'].values, 1)
        xs = np.linspace(df['Total_Fights'].min(), df['Total_Fights'].max(), 200)
        sc.add_trace(go.Scatter(x=xs, y=np.polyval(c,xs), mode='lines',
            line=dict(color='#f5a623',width=2,dash='dash'), name='Trend', showlegend=True))
    except Exception: pass
    sc.add_trace(go.Scatter(x=df['Total_Fights'], y=df['Win_Rate'], mode='markers',
        marker=dict(size=5, color=df['Win_Rate'],
            colorscale=[[0,'#4a9eff'],[0.5,'#00d4ff'],[1,'#22c55e']],
            opacity=0.6, showscale=True,
            colorbar=dict(title=dict(text='Win Rate',font=dict(color='#6a9ec0')),
                          tickfont=dict(color='#6a9ec0'), tickformat='.0%')),
        text=df['Full Name'],
        hovertemplate='<b>%{text}</b><br>Fights: %{x}<br>Win Rate: %{y:.1%}<extra></extra>',
        showlegend=False))
    sc.update_layout(**L(title='Career Experience vs Win Rate', height=420, showlegend=True,
        xaxis=ax(title='Total Career Fights'), yaxis=ax(title='Win Rate', tickformat='.0%')))
    return jsonify({'bar': jfig(fig_bar), 'scatter': jfig(sc)})

# ── Fight Outcomes ─────────────────────────────────────────────────────────────
@app.route('/api/charts/outcomes')
def ch_outcomes():
    perf = fights_df.groupby('Win_Method').agg(
        KD=('KD_1','mean'), TD=('TD_1','mean'), SUB=('SUB_1','mean'),
        SA=('Sig. Str. %_1','mean'), Ctrl=('Ctrl_1','mean'), STR=('STR_1','mean')).reset_index()
    mets    = [('KD','Avg Knockdowns'),('TD','Avg Takedowns'),('SUB','Avg Sub Attempts'),
               ('SA','Strike Accuracy'),('Ctrl','Avg Control (s)'),('STR','Avg Total Strikes')]
    methods = perf['Win_Method'].tolist()
    mcolors = [PAL[i%len(PAL)] for i in range(len(methods))]
    fig = make_subplots(2,3, subplot_titles=[m[1] for m in mets],
                        vertical_spacing=0.2, horizontal_spacing=0.09)
    for idx,(col,lbl) in enumerate(mets):
        if col not in perf.columns: continue
        r,c = idx//3+1, idx%3+1
        fig.add_trace(go.Bar(x=methods, y=perf[col],
            marker=dict(color=mcolors, line=dict(width=0)),
            text=perf[col].apply(lambda v: f'{v:.2f}' if col!='SA' else f'{v:.1%}'),
            textposition='outside', textfont=dict(color='white',size=10),
            showlegend=False), row=r, col=c)
        fig.update_xaxes(**ax(), row=r, col=c)
        fig.update_yaxes(tickformat='.0%' if col=='SA' else '', **ax(), row=r, col=c)
    fig.update_layout(**L(title='Average Performance Metrics by Win Method', height=580))
    wmy = fights_df.groupby(['Year','Win_Method']).size().reset_index(name='n')
    wmy = wmy[wmy['Year'].notna()].copy()
    wmy['Year'] = wmy['Year'].astype(int)
    tf = go.Figure()
    for i,method in enumerate(['KO/TKO','Submission','Decision','Other']):
        d = wmy[wmy['Win_Method']==method]
        tf.add_trace(go.Bar(x=d['Year'], y=d['n'], name=method, marker_color=PAL[i]))
    tf.update_layout(**L(title='Win Method Distribution Over Time', height=370,
        barmode='stack', showlegend=True, xaxis=ax(title='Year',dtick=2),
        yaxis=ax(title='Number of Fights')))
    return jsonify({'metrics': jfig(fig), 'time': jfig(tf)})

# ── Weight Classes ─────────────────────────────────────────────────────────────
@app.route('/api/charts/weight')
def ch_weight():
    wc = fighter_stats_df.groupby('Weight_Class_Std').agg(
        height=('height_cm','mean'), weight=('weight_kg','mean'), reach=('reach_cm','mean'),
        win_rate=('Win_Rate','mean'), strike_acc=('Sig. Str. %','mean'),
        ko_rate=('KO Rate','mean'), sub_rate=('SUB Rate','mean')).reset_index()
    wc = wc.dropna(subset=['Weight_Class_Std'])
    cat   = pd.CategoricalDtype(categories=WC_ORDER, ordered=True)
    wc['Weight_Class_Std'] = wc['Weight_Class_Std'].astype(cat)
    wc    = wc.sort_values('Weight_Class_Std')
    wlbls = wc['Weight_Class_Std'].astype(str).tolist()
    phys = go.Figure()
    for attr,color,lbl in [('height','#4a9eff','Height (cm)'),('reach','#00d4ff','Reach (cm)'),('weight','#22c55e','Weight (kg)')]:
        phys.add_trace(go.Scatter(x=wlbls, y=wc[attr], mode='lines+markers', name=lbl,
            line=dict(color=color,width=2.5), marker=dict(size=9,color=color,line=dict(color='white',width=1.5))))
    phys.update_layout(**L(title='Average Physical Attributes by Weight Class', height=390,
        showlegend=True, xaxis=ax(title='Weight Class',tickangle=-30), yaxis=ax(title='Measurement')))
    rates = go.Figure()
    for col,color,lbl in [('win_rate','#22c55e','Win Rate'),('ko_rate','#00d4ff','KO Rate'),('sub_rate','#8b5cf6','Sub Rate')]:
        rates.add_trace(go.Bar(name=lbl, x=wlbls, y=wc[col], marker_color=color))
    rates.update_layout(**L(title='Win / KO / Submission Rates by Weight Class', height=390,
        barmode='group', showlegend=True, xaxis=ax(title='Weight Class',tickangle=-30),
        yaxis=ax(title='Rate', tickformat='.0%')))
    sa = go.Figure(go.Bar(x=wlbls, y=wc['strike_acc'],
        marker=dict(color=wc['strike_acc'],
            colorscale=[[0,'#4a9eff'],[0.5,'#00d4ff'],[1,'#22c55e']],
            showscale=True,
            colorbar=dict(title=dict(text='Strike Acc.',font=dict(color='#6a9ec0')),
                          tickfont=dict(color='#6a9ec0'), tickformat='.0%')),
        text=wc['strike_acc'].apply(lambda v: f'{v:.1%}'),
        textposition='outside', textfont=dict(color='white')))
    sa.update_layout(**L(title='Striking Accuracy by Weight Class', height=370,
        xaxis=ax(title='Weight Class',tickangle=-30), yaxis=ax(title='Strike Accuracy',tickformat='.0%')))
    return jsonify({'physical': jfig(phys), 'rates': jfig(rates), 'strike': jfig(sa)})

# ── Trends ─────────────────────────────────────────────────────────────────────
@app.route('/api/charts/trends')
def ch_trends():
    yr = fights_df.groupby('Year').agg(
        KD=('KD_1','mean'), TD=('TD_1','mean'), SUB=('SUB_1','mean'),
        SA=('Sig. Str. %_1','mean'), Ctrl=('Ctrl_1','mean'),
        Total=('Fight_Id','count')).reset_index()
    yr = yr[yr['Year'].notna()].copy()
    yr['Year'] = yr['Year'].astype(int)
    yr = yr.sort_values('Year')
    mets = [
        ('KD','#00d4ff','Avg Knockdowns / Fight'), ('TD','#4a9eff','Avg Takedowns / Fight'),
        ('SA','#f5a623','Striking Accuracy'),       ('Ctrl','#14b8a6','Avg Control Time (s)'),
        ('Total','#8b5cf6','Total Fights / Year'),  ('SUB','#22c55e','Avg Sub Attempts / Fight'),
    ]
    fig = make_subplots(2,3, subplot_titles=[m[2] for m in mets],
                        vertical_spacing=0.22, horizontal_spacing=0.09)
    for idx,(col,color,lbl) in enumerate(mets):
        r,c = idx//3+1, idx%3+1
        fc  = FILL.get(color,'rgba(0,212,255,0.12)')
        fig.add_trace(go.Scatter(x=yr['Year'], y=yr[col], mode='lines+markers', name=lbl,
            line=dict(color=color,width=2.2),
            marker=dict(size=7,color=color,line=dict(color='white',width=1.2)),
            fill='tozeroy', fillcolor=fc, showlegend=False), row=r, col=c)
        fig.update_xaxes(**ax(), dtick=4, title_text='Year', row=r, col=c)
        fig.update_yaxes(tickformat='.0%' if col=='SA' else '', **ax(), row=r, col=c)
    fig.update_layout(**L(title='UFC Performance Trends Over Time (2016 – Present)', height=580))
    return jsonify({'trends': jfig(fig)})

# ── Fighter Search ─────────────────────────────────────────────────────────────
@app.route('/api/search')
def search():
    q = request.args.get('q','').strip().lower()
    if len(q) < 2: return jsonify([])
    mask = fighters_df['Full Name'].str.lower().str.contains(q, na=False)
    cols = ['Fighter_Id','Full Name','Stance','height_cm','weight_kg','reach_cm','W','L','D','Win_Rate']
    return jsonify(fighters_df[mask][cols].head(15).fillna('N/A').to_dict('records'))

# ── Fighter Detail (with star ratings) ────────────────────────────────────────
@app.route('/api/fighter/<fid>')
def fighter_detail(fid):
    row = fighters_df[fighters_df['Fighter_Id']==fid]
    if row.empty: return jsonify({'error':'Not found'}), 404
    sr  = fighter_stats_df[fighter_stats_df['Fighter_Id']==fid]
    d   = row.iloc[0].fillna('N/A').to_dict()
    if not sr.empty: d.update(sr.iloc[0].fillna('N/A').to_dict())

    # Star ratings
    stars = {}
    rating_map = [('Sig. Str. %','striking'), ('KO Rate','ko_power'),
                  ('SUB Rate','grappling'), ('Win_Rate','win_rate'), ('Total_Fights','experience')]
    for col, lbl in rating_map:
        val = d.get(col)
        if val != 'N/A':
            try: stars[lbl] = star_rating(float(val), col)
            except Exception: stars[lbl] = 3
        else: stars[lbl] = 3
    d['stars'] = stars

    # Radar values (0–100 scale)
    radar = {'labels': ['Striking','Power','Grappling','Win Rate','Experience'], 'values': []}
    for col in ['Sig. Str. %','KO Rate','SUB Rate','Win_Rate','Total_Fights']:
        val = d.get(col)
        try:
            v = float(val)
            if col == 'Total_Fights':
                v = min(v / 40.0, 1.0) * 100
            else:
                v = v * 100
            radar['values'].append(round(v, 1))
        except Exception:
            radar['values'].append(50)
    d['radar'] = radar
    return jsonify(d)

# ── Per-fighter yearly charts ──────────────────────────────────────────────────
@app.route('/api/fighter/<fid>/charts')
def fighter_charts(fid):
    # Fights where fighter is side 1
    f1 = fights_df[fights_df['Fighter_Id_1']==fid][
        ['Year','Win_Method','KD_1','STR_1','TD_1','Result_1']].copy()
    f1.rename(columns={'KD_1':'KD','STR_1':'STR','TD_1':'TD','Result_1':'Result'}, inplace=True)
    # Fights where fighter is side 2
    f2 = fights_df[fights_df['Fighter_Id_2']==fid][
        ['Year','Win_Method','KD_2','STR_2','TD_2','Result_2']].copy()
    f2.rename(columns={'KD_2':'KD','STR_2':'STR','TD_2':'TD','Result_2':'Result'}, inplace=True)
    all_f = pd.concat([f1, f2], ignore_index=True)
    if all_f.empty:
        return jsonify({'yearly':[], 'win_methods':{}})

    all_f['Win']  = (all_f['Result']=='W').astype(int)
    all_f['Loss'] = (all_f['Result']=='L').astype(int)

    yr = all_f.groupby('Year').agg(
        Fights=('Win','count'), Wins=('Win','sum'), Losses=('Loss','sum'),
        KD=('KD','mean'), STR=('STR','mean'), TD=('TD','mean')).reset_index()
    yr = yr[yr['Year'].notna()].copy()
    yr['Year'] = yr['Year'].astype(int)
    yr = yr.sort_values('Year')

    won = all_f[all_f['Win']==1]
    wm  = won['Win_Method'].value_counts().to_dict()

    # Charts JSON
    # 1) Fights per year (wins vs losses)
    wins_fig = go.Figure()
    wins_fig.add_trace(go.Bar(x=yr['Year'], y=yr['Wins'], name='Wins',
        marker_color='#00d4ff', marker_line_width=0))
    wins_fig.add_trace(go.Bar(x=yr['Year'], y=yr['Losses'], name='Losses',
        marker_color='rgba(255,100,100,0.6)', marker_line_width=0))
    wins_fig.update_layout(**L(title='Fights Per Year', height=220, barmode='group',
        showlegend=True, margin=dict(t=40,r=10,b=30,l=40),
        legend=dict(font=dict(size=10,color='#6a9ec0'), orientation='h', x=0, y=1.15),
        xaxis=ax(title=''), yaxis=ax(title='Fights')))

    # 2) Strikes per fight by year
    str_fig = go.Figure(go.Bar(x=yr['Year'], y=yr['STR'], name='Avg Strikes',
        marker=dict(color=yr['STR'], colorscale=[[0,'#4a9eff'],[1,'#00d4ff']], showscale=False),
        marker_line_width=0))
    str_fig.update_layout(**L(title='Avg Strikes / Fight', height=220,
        margin=dict(t=40,r=10,b=30,l=40),
        xaxis=ax(title=''), yaxis=ax(title='Strikes')))

    # 3) Win methods pie
    if wm:
        wm_keys = list(wm.keys())
        wm_vals = [wm[k] for k in wm_keys]
        wm_colors = [{'KO/TKO':'#00d4ff','Submission':'#8b5cf6',
                       'Decision':'#22c55e','Other':'#f5a623'}.get(k,'#6a9ec0') for k in wm_keys]
        method_fig = go.Figure(go.Pie(labels=wm_keys, values=wm_vals, hole=0.5,
            marker=dict(colors=wm_colors, line=dict(color='rgba(0,0,0,0.3)',width=1)),
            textfont=dict(color='white', size=11), textinfo='label+percent'))
        method_fig.update_layout(**L(title='Win Methods', height=220,
            margin=dict(t=40,r=10,b=10,l=10), showlegend=False))
    else:
        method_fig = go.Figure()
        method_fig.update_layout(**L(title='Win Methods', height=220))

    # 4) Radar (ability)
    sr = fighter_stats_df[fighter_stats_df['Fighter_Id']==fid]
    radar_vals = []
    radar_lbls = ['Striking','Power','Grappling','Win Rate','Experience']
    cols_r = ['Sig. Str. %','KO Rate','SUB Rate','Win_Rate','Total_Fights']
    for col in cols_r:
        val = sr[col].values[0] if not sr.empty and col in sr.columns else 0.5
        try:
            v = float(val)
            if col == 'Total_Fights': v = min(v/40,1)*100
            else: v = v*100
            radar_vals.append(round(v,1))
        except Exception:
            radar_vals.append(50)

    rv = radar_vals + [radar_vals[0]]
    rl = radar_lbls + [radar_lbls[0]]
    radar_fig = go.Figure(go.Scatterpolar(r=rv, theta=rl, fill='toself',
        fillcolor='rgba(0,212,255,0.12)',
        line=dict(color='#00d4ff', width=2),
        marker=dict(color='#4a9eff', size=6)))
    radar_fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        polar=dict(bgcolor='rgba(0,212,255,0.02)',
            radialaxis=dict(visible=True, color='rgba(0,212,255,0.2)',
                            tickfont=dict(color='#4a7a9b',size=9), range=[0,100]),
            angularaxis=dict(color='rgba(0,212,255,0.2)',
                             tickfont=dict(color='#a0d4f0',size=11))),
        font=dict(color='#6a9ec0', family='Inter, sans-serif'),
        margin=dict(t=40,r=30,b=30,l=30), height=220,
        title=dict(text='Ability Radar', font=dict(size=13,color='#e0f4ff',
                   family='Oswald, sans-serif'), x=0.05),
        showlegend=False)

    return jsonify({
        'wins':    jfig(wins_fig),
        'strikes': jfig(str_fig),
        'methods': jfig(method_fig),
        'radar':   jfig(radar_fig),
    })

# ── Fighter Comparison + Win Probability ──────────────────────────────────────
@app.route('/api/compare')
def compare():
    f1_id = request.args.get('f1', '').strip()
    f2_id = request.args.get('f2', '').strip()
    if not f1_id or not f2_id:
        return jsonify({'error': 'Need f1 and f2 IDs'}), 400

    def get_stats(fid):
        row = fighters_df[fighters_df['Fighter_Id'] == fid]
        if row.empty: return None
        sr = fighter_stats_df[fighter_stats_df['Fighter_Id'] == fid]
        d = row.iloc[0].fillna(0).to_dict()
        if not sr.empty:
            d.update({k: v for k, v in sr.iloc[0].fillna(0).to_dict().items()
                      if (v not in (0, '0')) or k not in d})
        return d

    s1, s2 = get_stats(f1_id), get_stats(f2_id)
    if s1 is None or s2 is None:
        return jsonify({'error': 'Fighter not found'}), 404

    def sf(val, default=0.0):
        try:
            v = float(val)
            return default if (v != v) else v  # NaN guard
        except (ValueError, TypeError):
            return default

    def prob_score(s):
        return (sf(s.get('Win_Rate'), 0.5)       * 0.35 +
                sf(s.get('KO Rate'), 0.3)          * 0.20 +
                sf(s.get('Sig. Str. %'), 0.45)     * 0.20 +
                sf(s.get('SUB Rate'), 0.15)         * 0.15 +
                min(sf(s.get('Total_Fights'), 10) / 40.0, 1.0) * 0.10)

    sc1, sc2 = prob_score(s1), prob_score(s2)
    t = sc1 + sc2
    p1 = round(sc1 / t * 100, 1) if t > 0 else 50.0
    p2 = round(100 - p1, 1)

    def fmt(s, prob):
        return {
            'Fighter_Id':   str(s.get('Fighter_Id', '')),
            'name':         str(s.get('Full Name', 'Unknown')),
            'stance':       str(s.get('Stance', 'Unknown')),
            'height':       sf(s.get('height_cm', s.get('Ht.', 0))),
            'weight':       sf(s.get('weight_kg', s.get('Wt.', 0))),
            'reach':        sf(s.get('reach_cm',  s.get('Reach', 0))),
            'wins':         int(sf(s.get('W', 0))),
            'losses':       int(sf(s.get('L', 0))),
            'draws':        int(sf(s.get('D', 0))),
            'total_fights': int(sf(s.get('Total_Fights', 0))),
            'win_rate':     sf(s.get('Win_Rate', 0)),
            'ko_rate':      sf(s.get('KO Rate', 0)),
            'sig_str':      sf(s.get('Sig. Str. %', 0)),
            'sub_rate':     sf(s.get('SUB Rate', 0)),
            'td_acc':       sf(s.get('TD Acc.', 0)),
            'weight_class': str(s.get('Weight_Class_Std', s.get('Weight_Class', 'N/A'))),
            'win_prob':     prob,
            'stars': {
                'striking':   star_rating(s.get('Sig. Str. %', 0.45), 'Sig. Str. %'),
                'ko_power':   star_rating(s.get('KO Rate', 0.3),      'KO Rate'),
                'grappling':  star_rating(s.get('SUB Rate', 0.15),    'SUB Rate'),
                'win_rate':   star_rating(s.get('Win_Rate', 0.5),     'Win_Rate'),
                'experience': star_rating(s.get('Total_Fights', 10),  'Total_Fights'),
            }
        }

    # Radar overlay chart
    lbls = ['Striking', 'KO Power', 'Grappling', 'Win Rate', 'Experience']
    cols_r = ['Sig. Str. %', 'KO Rate', 'SUB Rate', 'Win_Rate', 'Total_Fights']

    def radar_vals(s):
        out = []
        for col in cols_r:
            v = sf(s.get(col), 0)
            out.append(round(min(v / 40.0, 1.0) * 100 if col == 'Total_Fights' else v * 100, 1))
        return out

    r1, r2 = radar_vals(s1), radar_vals(s2)
    n1, n2 = str(s1.get('Full Name', 'F1')), str(s2.get('Full Name', 'F2'))

    radar_fig = go.Figure()
    for rv, name, lc, fc in [
        (r1, n1, '#d20000', 'rgba(210,0,0,0.15)'),
        (r2, n2, '#cccccc', 'rgba(200,200,200,0.08)')
    ]:
        rl = lbls + [lbls[0]]
        rv2 = rv + [rv[0]]
        radar_fig.add_trace(go.Scatterpolar(
            r=rv2, theta=rl, fill='toself', name=name,
            fillcolor=fc, line=dict(color=lc, width=2.5),
            marker=dict(color=lc, size=6)))

    radar_fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        polar=dict(
            bgcolor='rgba(10,10,10,1)',
            radialaxis=dict(visible=True, color='rgba(255,255,255,0.12)',
                            tickfont=dict(color='#666', size=8), range=[0, 100]),
            angularaxis=dict(color='rgba(255,255,255,0.12)',
                             tickfont=dict(color='#cccccc', size=11))),
        font=dict(color='#aaaaaa', family='Inter, sans-serif'),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#cccccc', size=11),
                    orientation='h', x=0.5, xanchor='center', y=-0.05),
        margin=dict(t=20, r=30, b=30, l=30), height=320, showlegend=True)

    return jsonify({'fighter1': fmt(s1, p1), 'fighter2': fmt(s2, p2), 'radar': jfig(radar_fig)})

if __name__ == '__main__':
    app.run(debug=False, port=5050, host='127.0.0.1')
