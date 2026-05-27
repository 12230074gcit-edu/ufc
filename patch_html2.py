#!/usr/bin/env python3
"""Second patch: add sec-top15 HTML + fix weight grid overlap."""
import os

HTML = os.path.join(os.path.dirname(__file__), "templates", "index.html")

with open(HTML, encoding="utf-8") as f:
    lines = f.readlines()

# ── 1. Fix weight section grid-3 → grid-2 + full-width (lines 1694-1723, 0-indexed 1693-1722)
# Find the exact grid-3 line inside weight section
grid3_line = None
for i, l in enumerate(lines):
    if 'class="grid-3"' in l and i > 1680 and i < 1730:
        grid3_line = i
        break

if grid3_line is not None:
    # Replace the grid-3 block (lines 1694-1724) with 2-col + full-width layout
    NEW_WEIGHT = '''      <div class="grid-2" style="margin-bottom:16px">
        <div class="card">
          <div class="card-header"><div class="card-title"><i data-lucide="ruler"></i> Physical Stats by Division</div></div>
          <div class="card-body">
            <div class="chart-wrap" id="wrap-wc-phys">
              <div class="chart-loader"><div class="spinner"></div>Loading chart...</div>
              <div class="chart-inner" id="chart-wc-phys"></div>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-header"><div class="card-title"><i data-lucide="percent"></i> Win &amp; KO Rates</div></div>
          <div class="card-body">
            <div class="chart-wrap" id="wrap-wc-rates">
              <div class="chart-loader"><div class="spinner"></div>Loading chart...</div>
              <div class="chart-inner" id="chart-wc-rates"></div>
            </div>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-header"><div class="card-title"><i data-lucide="crosshair"></i> Strike Accuracy by Division</div></div>
        <div class="card-body">
          <div class="chart-wrap" id="wrap-wc-str">
            <div class="chart-loader"><div class="spinner"></div>Loading chart...</div>
            <div class="chart-inner" id="chart-wc-str"></div>
          </div>
        </div>
      </div>
'''
    # Find end of grid-3 block (next </div> after the 3 cards)
    end_line = grid3_line
    depth = 0
    for i in range(grid3_line, min(grid3_line + 40, len(lines))):
        depth += lines[i].count('<div') - lines[i].count('</div')
        if i > grid3_line and depth <= 0:
            end_line = i
            break
    lines = lines[:grid3_line] + [NEW_WEIGHT] + lines[end_line+1:]
    print(f"Weight grid fixed at line {grid3_line+1}")
else:
    print("WARNING: Could not find weight grid-3 block")

# ── 2. Add sec-top15 HTML before <!-- Fighter Overlay -->
TOP15_HTML = """
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

overlay_line = None
for i, l in enumerate(lines):
    if '<!-- Fighter Overlay -->' in l:
        overlay_line = i
        break

if overlay_line is not None:
    lines = lines[:overlay_line] + [TOP15_HTML] + lines[overlay_line:]
    print(f"sec-top15 inserted at line {overlay_line+1}")
else:
    print("WARNING: Could not find <!-- Fighter Overlay --> marker")

with open(HTML, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Patch 2 done.")
