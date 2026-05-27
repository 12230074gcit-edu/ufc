#!/usr/bin/env python3
"""Patch index.html: add Top 15, clean sidebar, fix charts."""
import re, os

HTML = os.path.join(os.path.dirname(__file__), "templates", "index.html")

with open(HTML, encoding="utf-8") as f:
    html = f.read()

# ─────────────────────────────────────────────────────────────────────────────
# 1. Sidebar: replace nav with clean version
# ─────────────────────────────────────────────────────────────────────────────
OLD_NAV = '''  <nav class="sb-nav">
    <div class="sb-section-label">Analytics</div>
    <div class="sb-item active" onclick="showSection(\'overview\',this)">
      <i data-lucide="layout-dashboard"></i> Overview
    </div>
    <div class="sb-item" onclick="showSection(\'physical\',this)">
      <i data-lucide="ruler"></i> Physical Attributes
    </div>
    <div class="sb-item" onclick="showSection(\'stance\',this)">
      <i data-lucide="shield"></i> Stance Analysis
    </div>
    <div class="sb-item" onclick="showSection(\'experience\',this)">
      <i data-lucide="star"></i> Experience
    </div>
    <div class="sb-item" onclick="showSection(\'outcomes\',this)">
      <i data-lucide="target"></i> Fight Outcomes
    </div>
    <div class="sb-item" onclick="showSection(\'weight\',this)">
      <i data-lucide="scale"></i> Weight Classes
    </div>
    <div class="sb-item" onclick="showSection(\'trends\',this)">
      <i data-lucide="trending-up"></i> Trends
    </div>
    <div class="sb-section-label">Fighters</div>
    <div class="sb-item" onclick="showSection(\'fighters\',this)">
      <i data-lucide="users"></i> Fighter Search
    </div>
    <div class="sb-item" onclick="showSection(\'compare\',this)" id="compare-nav-item">
      <i data-lucide="git-compare"></i> Compare Fighters
    </div>
  </nav>'''

NEW_NAV = '''  <nav class="sb-nav">
    <div class="sb-section-label">Analytics</div>
    <div class="sb-item active" onclick="showSection(\'overview\',this)">
      <i data-lucide="layout-dashboard"></i> Overview
    </div>
    <div class="sb-item" onclick="showSection(\'outcomes\',this)">
      <i data-lucide="target"></i> Fight Outcomes
    </div>
    <div class="sb-item" onclick="showSection(\'weight\',this)">
      <i data-lucide="scale"></i> Weight Classes
    </div>
    <div class="sb-section-label">Rankings</div>
    <div class="sb-item" onclick="showSection(\'top15\',this)" id="top15-nav-item">
      <i data-lucide="trophy"></i> Top 15 Rankings
    </div>
    <div class="sb-section-label">Fighters</div>
    <div class="sb-item" onclick="showSection(\'fighters\',this)">
      <i data-lucide="users"></i> Fighter Search
    </div>
    <div class="sb-item" onclick="showSection(\'compare\',this)" id="compare-nav-item">
      <i data-lucide="git-compare"></i> Compare Fighters
    </div>
  </nav>'''

html = html.replace(OLD_NAV, NEW_NAV)

# ─────────────────────────────────────────────────────────────────────────────
# 2. Add Top 15 CSS before </style>
# ─────────────────────────────────────────────────────────────────────────────
TOP15_CSS = """
/* ── Top 15 Rankings ── */
.division-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 24px;
}
.div-tab {
  padding: 7px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border: 1.5px solid var(--gray-200);
  background: var(--white);
  color: var(--gray-600);
  transition: all 0.2s;
  white-space: nowrap;
}
.div-tab:hover { border-color: var(--red); color: var(--red); }
.div-tab.active { background: var(--red); border-color: var(--red); color: white; }

.rankings-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}
@media (max-width: 1400px) { .rankings-grid { grid-template-columns: repeat(4, 1fr); } }
@media (max-width: 1100px) { .rankings-grid { grid-template-columns: repeat(3, 1fr); } }

.rank-card {
  background: var(--white);
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  box-shadow: var(--shadow-sm);
}
.rank-card:hover {
  border-color: var(--red);
  transform: translateY(-3px);
  box-shadow: 0 8px 24px var(--red-glow);
}
.rank-card.champ { border-color: #f59e0b; }
.rank-card.champ:hover { border-color: #f59e0b; box-shadow: 0 8px 24px rgba(245,158,11,0.2); }

.rank-badge {
  position: absolute;
  top: 10px; left: 10px;
  width: 28px; height: 28px;
  background: var(--red);
  color: white;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700;
  font-size: 12px;
  z-index: 2;
  box-shadow: 0 2px 8px rgba(210,0,0,0.4);
}
.rank-badge.gold {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  box-shadow: 0 2px 8px rgba(245,158,11,0.4);
}
.rank-badge i { width: 14px; height: 14px; }

.rank-photo {
  height: 180px;
  background: linear-gradient(180deg, var(--gray-100) 0%, var(--gray-200) 100%);
  display: flex; align-items: center; justify-content: center;
  overflow: hidden;
  position: relative;
}
.rank-photo img {
  width: 100%; height: 100%;
  object-fit: cover;
  object-position: top center;
}
.rank-photo .silhouette {
  width: 70px; height: 95px;
  color: var(--gray-400);
}
.rank-photo::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 50px;
  background: linear-gradient(to top, var(--white), transparent);
}
.rank-card.champ .rank-photo::after {
  background: linear-gradient(to top, #fffbeb, transparent);
}
.rank-card.champ .rank-photo {
  background: linear-gradient(180deg, #fef3c7 0%, #fde68a 100%);
}

.rank-info {
  padding: 10px 14px 14px;
}
.rank-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--gray-900);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 3px;
}
.rank-nickname {
  font-size: 11px;
  color: var(--gray-500);
  font-style: italic;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.rank-record {
  font-size: 12px;
  color: var(--gray-600);
  margin-bottom: 8px;
}
.rank-record strong { color: var(--red); font-size: 14px; }
.rank-stats {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.rank-stat {
  font-size: 10px;
  font-weight: 600;
  padding: 3px 7px;
  border-radius: 4px;
  background: var(--gray-100);
  color: var(--gray-600);
}
.rank-stat.red { background: var(--red-bg); color: var(--red); }
.rank-stat.gold-bg { background: #fef3c7; color: #92400e; }
.belt-icon { color: #f59e0b; margin-left: 4px; }

.div-loading {
  grid-column: 1 / -1;
  display: flex; align-items: center; justify-content: center;
  padding: 60px;
  color: var(--gray-400);
  gap: 12px;
  font-size: 14px;
}
.div-loading .spinner {
  width: 28px; height: 28px;
  border: 2px solid var(--gray-200);
  border-top-color: var(--red);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
"""

html = html.replace("</style>", TOP15_CSS + "\n</style>")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Add Top 15 section HTML (after sec-compare closing div + one blank line)
#    We inject before the fighter overlay
# ─────────────────────────────────────────────────────────────────────────────
TOP15_SECTION = """
    <!-- Top 15 Rankings -->
    <div class="section" id="sec-top15">
      <div class="section-header">
        <div class="section-icon"><i data-lucide="trophy"></i></div>
        <div>
          <div class="section-title">Top 15 Rankings</div>
          <div class="section-sub">Best performers per division ranked by composite score</div>
        </div>
      </div>
      <div class="division-tabs" id="div-tabs"></div>
      <div class="rankings-grid" id="rankings-grid">
        <div class="div-loading"><div class="spinner"></div> Select a division above</div>
      </div>
    </div>

"""

# Insert before the fighter overlay
OVERLAY_MARKER = "<!-- Fighter overlay -->"
html = html.replace(OVERLAY_MARKER, TOP15_SECTION + OVERLAY_MARKER)

# ─────────────────────────────────────────────────────────────────────────────
# 4. Fix weight section charts - change grid-3 to grid-2 to prevent overlap
# ─────────────────────────────────────────────────────────────────────────────
OLD_WEIGHT_GRID = '''      <div class="grid-3">
        <div class="card">
          <div class="card-header"><div class="card-title"><i data-lucide="ruler"></i> Physical Stats</div></div>
          <div class="card-body">
            <div class="chart-wrap" id="wrap-wc-phys">
              <div class="chart-loader"><div class="spinner"></div>Loading...</div>
              <div class="chart-inner" id="chart-wc-phys"></div>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-header"><div class="card-title"><i data-lucide="percent"></i> Win/KO Rates</div></div>
          <div class="card-body">
            <div class="chart-wrap" id="wrap-wc-rates">
              <div class="chart-loader"><div class="spinner"></div>Loading...</div>
              <div class="chart-inner" id="chart-wc-rates"></div>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-header"><div class="card-title"><i data-lucide="crosshair"></i> Strike Stats</div></div>
          <div class="card-body">
            <div class="chart-wrap" id="wrap-wc-str">
              <div class="chart-loader"><div class="spinner"></div>Loading...</div>
              <div class="chart-inner" id="chart-wc-str"></div>
            </div>
          </div>
        </div>
      </div>'''

NEW_WEIGHT_GRID = '''      <div class="grid-2" style="margin-bottom:16px">
        <div class="card">
          <div class="card-header"><div class="card-title"><i data-lucide="ruler"></i> Physical Stats by Division</div></div>
          <div class="card-body">
            <div class="chart-wrap" id="wrap-wc-phys">
              <div class="chart-loader"><div class="spinner"></div>Loading...</div>
              <div class="chart-inner" id="chart-wc-phys"></div>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-header"><div class="card-title"><i data-lucide="percent"></i> Win &amp; KO Rates</div></div>
          <div class="card-body">
            <div class="chart-wrap" id="wrap-wc-rates">
              <div class="chart-loader"><div class="spinner"></div>Loading...</div>
              <div class="chart-inner" id="chart-wc-rates"></div>
            </div>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-header"><div class="card-title"><i data-lucide="crosshair"></i> Strike Accuracy by Division</div></div>
        <div class="card-body">
          <div class="chart-wrap" id="wrap-wc-str">
            <div class="chart-loader"><div class="spinner"></div>Loading...</div>
            <div class="chart-inner" id="chart-wc-str"></div>
          </div>
        </div>
      </div>'''

html = html.replace(OLD_WEIGHT_GRID, NEW_WEIGHT_GRID)

# ─────────────────────────────────────────────────────────────────────────────
# 5. Update JS: loadSection + add loadTop15 + add image support to fighter cards
# ─────────────────────────────────────────────────────────────────────────────
OLD_LOAD_SECTION = """// ── Section loader dispatch ──
function loadSection(id) {
  if (id === 'overview')   return loadOverview();
  if (id === 'physical')   return loadPhysical();
  if (id === 'stance')     return loadCharts('/api/charts/stance',    [['chart-stance-bar','bar'],['chart-stance-pie','pie'],['chart-stance-box','box']]);
  if (id === 'experience') return loadCharts('/api/charts/experience', [['chart-exp-bar','bar'],['chart-exp-scatter','scatter']]);
  if (id === 'outcomes')   return loadCharts('/api/charts/outcomes',  [['chart-outcomes-multi','metrics'],['chart-outcomes-stacked','time']]);
  if (id === 'weight')     return loadCharts('/api/charts/weight',    [['chart-wc-phys','physical'],['chart-wc-rates','rates'],['chart-wc-str','strike']]);
  if (id === 'trends')     return loadCharts('/api/charts/trends',    [['chart-trends','trends']]);
  if (id === 'fighters')   return initFighters();
}"""

NEW_LOAD_SECTION = """// ── Section loader dispatch ──
function loadSection(id) {
  if (id === 'overview')   return loadOverview();
  if (id === 'outcomes')   return loadCharts('/api/charts/outcomes',  [['chart-outcomes-multi','metrics'],['chart-outcomes-stacked','time']]);
  if (id === 'weight')     return loadCharts('/api/charts/weight',    [['chart-wc-phys','physical'],['chart-wc-rates','rates'],['chart-wc-str','strike']]);
  if (id === 'top15')      return initTop15();
  if (id === 'fighters')   return initFighters();
}

// ── Top 15 Rankings ──
let top15Divisions = [];
let top15ActiveDiv = '';

async function initTop15() {
  try {
    const resp = await fetch('/api/top15');
    const data = await resp.json();
    top15Divisions = data.divisions || [];
    const tabs = document.getElementById('div-tabs');
    tabs.innerHTML = top15Divisions.map(d =>
      `<div class="div-tab" onclick="loadDivision('${d}')">${d}</div>`
    ).join('');
    if (top15Divisions.length > 0) loadDivision(top15Divisions[0]);
  } catch(e) {
    document.getElementById('rankings-grid').innerHTML = '<div class="div-loading">Failed to load divisions</div>';
  }
}

async function loadDivision(division) {
  top15ActiveDiv = division;
  // Update tabs
  document.querySelectorAll('.div-tab').forEach(t => {
    t.classList.toggle('active', t.textContent === division);
  });
  const grid = document.getElementById('rankings-grid');
  grid.innerHTML = '<div class="div-loading"><div class="spinner"></div> Loading ' + division + '...</div>';
  try {
    const resp = await fetch('/api/top15/' + encodeURIComponent(division));
    const data = await resp.json();
    renderRankings(data.fighters || []);
  } catch(e) {
    grid.innerHTML = '<div class="div-loading">Failed to load rankings</div>';
  }
}

function fighterImgHTML(fid, classes) {
  return `<img src="/static/fighters/${fid}.jpg" class="${classes}" onerror="this.style.display='none';this.nextElementSibling.style.display='block'" alt="">
          <span style="display:none">${SVG_SIL}</span>`;
}

function renderRankings(fighters) {
  const grid = document.getElementById('rankings-grid');
  if (!fighters.length) {
    grid.innerHTML = '<div class="div-loading">No fighters found for this division</div>';
    return;
  }
  grid.innerHTML = fighters.map(f => {
    const isChamp = f.belt === 1 || f.rank === 1;
    const badgeContent = f.rank === 1
      ? `<i data-lucide="crown"></i>`
      : f.rank;
    const nickname = f.nickname && f.nickname !== 'No Nickname' && f.nickname !== 'nan'
      ? `"${f.nickname}"` : '';
    return `
    <div class="rank-card${isChamp ? ' champ' : ''}" onclick="openFighter('${f.Fighter_Id}')">
      <div class="rank-badge${f.rank === 1 ? ' gold' : ''}">${badgeContent}</div>
      <div class="rank-photo">
        <img src="/static/fighters/${f.Fighter_Id}.jpg"
             onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"
             style="width:100%;height:100%;object-fit:cover;object-position:top center"
             alt="${f.name}">
        <div style="display:none;width:100%;height:100%;align-items:center;justify-content:center">
          ${SVG_SIL}
        </div>
      </div>
      <div class="rank-info">
        <div class="rank-name">${f.name}${f.belt ? '<span class="belt-icon">&#x1F3C6;</span>' : ''}</div>
        ${nickname ? `<div class="rank-nickname">${nickname}</div>` : ''}
        <div class="rank-record"><strong>${f.W}</strong>-${f.L}-${f.D}</div>
        <div class="rank-stats">
          <span class="rank-stat red">${f.win_rate}% W</span>
          ${f.ko_rate > 0 ? `<span class="rank-stat">KO ${f.ko_rate}%</span>` : ''}
          <span class="rank-stat">${f.total_fights} fights</span>
        </div>
      </div>
    </div>`;
  }).join('');
  lucide.createIcons({ el: grid });
}"""

html = html.replace(OLD_LOAD_SECTION, NEW_LOAD_SECTION)

# ─────────────────────────────────────────────────────────────────────────────
# 6. Fix fighter grid - add image support
# ─────────────────────────────────────────────────────────────────────────────
OLD_FIGHTER_IMG = '''    const name = f[\'Full Name\'] || \'Unknown\';
    const w = f.W || 0, l = f.L || 0, d = f.D || 0;
    const stance = f.Stance || \'\';
    // Handle win rate - ensure it\'s a proper percentage
    let winRate = \'\';
    if (f.Win_Rate != null) {
      const rate = f.Win_Rate <= 1 ? f.Win_Rate * 100 : f.Win_Rate;
      winRate = rate.toFixed(0) + \'% wins\';
    }
    return `
    <div class="fighter-card" onclick="openFighter(\'${f.Fighter_Id}\')">
      <div class="fighter-card-img">
        ${SVG_SIL}
      </div>'''

NEW_FIGHTER_IMG = '''    const name = f[\'Full Name\'] || \'Unknown\';
    const w = f.W || 0, l = f.L || 0, d = f.D || 0;
    const stance = f.Stance || \'\';
    let winRate = \'\';
    if (f.Win_Rate != null) {
      const rate = f.Win_Rate <= 1 ? f.Win_Rate * 100 : f.Win_Rate;
      winRate = rate.toFixed(0) + \'% wins\';
    }
    return `
    <div class="fighter-card" onclick="openFighter(\'${f.Fighter_Id}\')">
      <div class="fighter-card-img">
        <img src="/static/fighters/${f.Fighter_Id}.jpg"
             style="width:100%;height:100%;object-fit:cover;object-position:top center"
             onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'"
             alt="${name}">
        <div style="display:none;width:100%;height:100%;align-items:center;justify-content:center">
          ${SVG_SIL}
        </div>
      </div>'''

html = html.replace(OLD_FIGHTER_IMG, NEW_FIGHTER_IMG)

# ─────────────────────────────────────────────────────────────────────────────
# 7. Also fix fighter overlay photo to try image
# ─────────────────────────────────────────────────────────────────────────────
OLD_OV_PHOTO = "    const photo = document.getElementById('ov-photo');\n    photo.innerHTML = SVG_SIL;"
NEW_OV_PHOTO = """    const photo = document.getElementById('ov-photo');
    const imgEl = photo.querySelector('img');
    const silEl = photo.querySelector('.silhouette');
    const fidClean = (info['Fighter_Id'] || info.Fighter_Id || '').toString();
    if (fidClean && imgEl) {
      imgEl.src = '/static/fighters/' + fidClean + '.jpg';
      imgEl.style.display = '';
      if (silEl) silEl.style.display = 'none';
      imgEl.onerror = () => { imgEl.style.display = 'none'; if(silEl) silEl.style.display = ''; };
    } else {
      if (imgEl) imgEl.style.display = 'none';
      if (silEl) silEl.style.display = '';
    }"""

html = html.replace(OLD_OV_PHOTO, NEW_OV_PHOTO)

# ─────────────────────────────────────────────────────────────────────────────
# Save
# ─────────────────────────────────────────────────────────────────────────────
with open(HTML, "w", encoding="utf-8") as f:
    f.write(html)

print("Done. Changes applied:")
print(" - Sidebar: simplified to Overview, Outcomes, Weight, Top 15, Fighters, Compare")
print(" - Top 15 section added with division tabs and ranking cards")
print(" - Weight section: 3-col changed to 2-col + full-width to fix overlap")
print(" - Fighter cards: image support added (/static/fighters/{id}.jpg)")
print(" - Fighter overlay: image support added")
