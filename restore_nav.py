#!/usr/bin/env python3
"""Restore all original nav items + keep Top 15."""
import os

HTML = os.path.join(os.path.dirname(__file__), "templates", "index.html")

with open(HTML, encoding="utf-8") as f:
    content = f.read()

# The current (broken) nav
OLD_NAV = """  <nav class="sb-nav">
    <div class="sb-section-label">Analytics</div>
    <div class="sb-item active" onclick="showSection('overview',this)">
      <i data-lucide="layout-dashboard"></i> Overview
    </div>
    <div class="sb-item" onclick="showSection('outcomes',this)">
      <i data-lucide="target"></i> Fight Outcomes
    </div>
    <div class="sb-item" onclick="showSection('weight',this)">
      <i data-lucide="scale"></i> Weight Classes
    </div>
    <div class="sb-section-label">Rankings</div>
    <div class="sb-item" onclick="showSection('top15',this)" id="top15-nav-item">
      <i data-lucide="trophy"></i> Top 15 Rankings
    </div>
    <div class="sb-section-label">Fighters</div>
    <div class="sb-item" onclick="showSection('fighters',this)">
      <i data-lucide="users"></i> Fighter Search
    </div>
    <div class="sb-item" onclick="showSection('compare',this)" id="compare-nav-item">
      <i data-lucide="git-compare"></i> Compare Fighters
    </div>
  </nav>"""

# Full restored nav with all original items + Top 15
NEW_NAV = """  <nav class="sb-nav">
    <div class="sb-section-label">Analytics</div>
    <div class="sb-item active" onclick="showSection('overview',this)">
      <i data-lucide="layout-dashboard"></i> Overview
    </div>
    <div class="sb-item" onclick="showSection('physical',this)">
      <i data-lucide="ruler"></i> Physical Attributes
    </div>
    <div class="sb-item" onclick="showSection('stance',this)">
      <i data-lucide="shield"></i> Stance Analysis
    </div>
    <div class="sb-item" onclick="showSection('experience',this)">
      <i data-lucide="star"></i> Experience
    </div>
    <div class="sb-item" onclick="showSection('outcomes',this)">
      <i data-lucide="target"></i> Fight Outcomes
    </div>
    <div class="sb-item" onclick="showSection('weight',this)">
      <i data-lucide="scale"></i> Weight Classes
    </div>
    <div class="sb-item" onclick="showSection('trends',this)">
      <i data-lucide="trending-up"></i> Trends
    </div>
    <div class="sb-section-label">Rankings</div>
    <div class="sb-item" onclick="showSection('top15',this)" id="top15-nav-item">
      <i data-lucide="trophy"></i> Top 15 Rankings
    </div>
    <div class="sb-section-label">Fighters</div>
    <div class="sb-item" onclick="showSection('fighters',this)">
      <i data-lucide="users"></i> Fighter Search
    </div>
    <div class="sb-item" onclick="showSection('compare',this)" id="compare-nav-item">
      <i data-lucide="git-compare"></i> Compare Fighters
    </div>
  </nav>"""

# Also fix loadSection to include all original dispatches
OLD_LOAD = """// ── Section loader dispatch ──
function loadSection(id) {
  if (id === 'overview')   return loadOverview();
  if (id === 'outcomes')   return loadCharts('/api/charts/outcomes',  [['chart-outcomes-multi','metrics'],['chart-outcomes-stacked','time']]);
  if (id === 'weight')     return loadCharts('/api/charts/weight',    [['chart-wc-phys','physical'],['chart-wc-rates','rates'],['chart-wc-str','strike']]);
  if (id === 'top15')      return initTop15();
  if (id === 'fighters')   return initFighters();
}"""

NEW_LOAD = """// ── Section loader dispatch ──
function loadSection(id) {
  if (id === 'overview')   return loadOverview();
  if (id === 'physical')   return loadPhysical();
  if (id === 'stance')     return loadCharts('/api/charts/stance',    [['chart-stance-bar','bar'],['chart-stance-pie','pie'],['chart-stance-box','box']]);
  if (id === 'experience') return loadCharts('/api/charts/experience', [['chart-exp-bar','bar'],['chart-exp-scatter','scatter']]);
  if (id === 'outcomes')   return loadCharts('/api/charts/outcomes',  [['chart-outcomes-multi','metrics'],['chart-outcomes-stacked','time']]);
  if (id === 'weight')     return loadCharts('/api/charts/weight',    [['chart-wc-phys','physical'],['chart-wc-rates','rates'],['chart-wc-str','strike']]);
  if (id === 'trends')     return loadCharts('/api/charts/trends',    [['chart-trends','trends']]);
  if (id === 'top15')      return initTop15();
  if (id === 'fighters')   return initFighters();
}"""

if OLD_NAV in content:
    content = content.replace(OLD_NAV, NEW_NAV)
    print("Nav restored")
else:
    print("WARNING: nav string not matched exactly")

if OLD_LOAD in content:
    content = content.replace(OLD_LOAD, NEW_LOAD)
    print("loadSection restored")
else:
    print("WARNING: loadSection string not matched")

with open(HTML, "w", encoding="utf-8") as f:
    f.write(content)

print("Done")
