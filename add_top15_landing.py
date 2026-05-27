#!/usr/bin/env python3
"""Add Men's Top 15 Rankings section to landing.html."""

import os

LANDING = os.path.join(os.path.dirname(__file__), "templates", "landing.html")

with open(LANDING, encoding="utf-8") as f:
    content = f.read()


# ── 1. Add CSS ──────────────────────────────────────────────────────────────
TOP15_CSS = """
/* ── Top 15 Men's Rankings Section ── */
.top15-section {
  background: var(--dark);
  padding: 80px 0;
  position: relative;
  overflow: hidden;
}

.top15-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--red), transparent);
}

.top15-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 40px;
}

.top15-header {
  text-align: center;
  margin-bottom: 40px;
}

.top15-badge {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.top15-badge-line {
  width: 40px;
  height: 1px;
  background: var(--red);
}

.top15-badge-text {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: var(--red);
}

.top15-title {
  font-family: 'Oswald', sans-serif;
  font-size: 42px;
  font-weight: 700;
  color: var(--white);
  line-height: 1.1;
  margin-bottom: 12px;
}

.top15-title span {
  color: var(--red);
}

.top15-subtitle {
  font-size: 16px;
  color: var(--white-60);
  max-width: 560px;
  margin: 0 auto;
}

.top15-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-bottom: 36px;
}

.top15-tab {
  padding: 8px 18px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border: 1.5px solid var(--white-20);
  background: transparent;
  color: var(--white-60);
  transition: all 0.2s;
  white-space: nowrap;
  letter-spacing: 0.5px;
}

.top15-tab:hover {
  border-color: var(--red);
  color: var(--white);
}

.top15-tab.active {
  background: var(--red);
  border-color: var(--red);
  color: var(--white);
}

.top15-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

@media (max-width: 1300px) {
  .top15-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 1000px) {
  .top15-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 700px) {
  .top15-container {
    padding: 0 24px;
  }

  .top15-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.t15-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.25s;
  position: relative;
}

.t15-card:hover {
  border-color: var(--red);
  background: rgba(210,0,0,0.07);
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(210,0,0,0.2);
}

.t15-rank {
  position: absolute;
  top: 10px;
  left: 10px;
  width: 28px;
  height: 28px;
  background: var(--red);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 12px;
  z-index: 2;
  box-shadow: 0 2px 8px rgba(210,0,0,0.5);
}

.t15-photo {
  height: 180px;
  background: linear-gradient(180deg, #1a1a1a 0%, #111 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}

.t15-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: top center;
}

.t15-silhouette {
  width: 65px;
  height: 88px;
  opacity: 0.25;
  color: var(--white);
}

.t15-photo::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: linear-gradient(to top, rgba(10,10,10,0.9), transparent);
  pointer-events: none;
}

.t15-info {
  padding: 10px 14px 14px;
}

.t15-name {
  font-family: 'Oswald', sans-serif;
  font-size: 15px;
  font-weight: 600;
  color: var(--white);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.t15-nickname {
  font-size: 11px;
  color: var(--white-40);
  font-style: italic;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-height: 16px;
}

.t15-record {
  font-size: 12px;
  color: var(--white-60);
  margin-bottom: 8px;
}

.t15-record strong {
  color: var(--red-light);
  font-size: 14px;
}

.t15-stats {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.t15-stat {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 4px;
  background: rgba(255,255,255,0.07);
  color: var(--white-60);
}

.t15-stat.red {
  background: rgba(210,0,0,0.2);
  color: #ff6666;
}

.top15-loader {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: var(--white-40);
  gap: 12px;
  font-size: 14px;
}

.top15-loader .ld-spin {
  width: 28px;
  height: 28px;
  border: 2px solid rgba(255,255,255,0.1);
  border-top-color: var(--red);
  border-radius: 50%;
  animation: t15spin 0.7s linear infinite;
}

@keyframes t15spin {
  to {
    transform: rotate(360deg);
  }
}

.top15-cta {
  text-align: center;
  margin-top: 36px;
}

.top15-cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: var(--red);
  color: white;
  padding: 14px 32px;
  border-radius: 6px;
  text-decoration: none;
  font-family: 'Oswald', sans-serif;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 1px;
  transition: background 0.2s, transform 0.2s;
}

.top15-cta-btn:hover {
  background: var(--red-light);
  transform: translateY(-2px);
}

.top15-cta-btn svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
"""

if "/* ── Top 15 Men's Rankings Section ── */" not in content:
    content = content.replace("</style>", TOP15_CSS + "\n</style>")


# ── 2. Add HTML section ─────────────────────────────────────────────────────
TOP15_HTML = """
<!-- Top 15 Men's Rankings -->
<section class="top15-section">
  <div class="top15-container">
    <div class="top15-header">
      <div class="top15-badge">
        <div class="top15-badge-line"></div>
        <span class="top15-badge-text">Men's Division Rankings</span>
        <div class="top15-badge-line"></div>
      </div>

      <h2 class="top15-title">Top 15 <span>Men's Fighters</span></h2>
      <p class="top15-subtitle">
        Current men's UFC ranked fighters across Flyweight, Bantamweight, Featherweight,
        Lightweight, Welterweight, Middleweight, Light Heavyweight, and Heavyweight.
      </p>
    </div>

    <div class="top15-tabs" id="landing-div-tabs">
      <div class="top15-loader">
        <div class="ld-spin"></div>
        Loading men's divisions...
      </div>
    </div>

    <div class="top15-grid" id="landing-rankings-grid"></div>

    <div class="top15-cta">
      <a href="/dashboard#sec-top15" class="top15-cta-btn">
        <svg viewBox="0 0 24 24">
          <path d="M5 12h14M12 5l7 7-7 7"/>
        </svg>
        View Full Rankings
      </a>
    </div>
  </div>
</section>

"""

CTA_MARKER = "<!-- CTA Banner -->"

if "<!-- Top 15 Men's Rankings -->" not in content:
    content = content.replace(CTA_MARKER, TOP15_HTML + CTA_MARKER)


# ── 3. Add JS ───────────────────────────────────────────────────────────────
TOP15_JS = """
// ── Men's Top 15 Rankings Landing Page ──

const MEN_DIVISIONS = [
  "Flyweight",
  "Bantamweight",
  "Featherweight",
  "Lightweight",
  "Welterweight",
  "Middleweight",
  "Light Heavyweight",
  "Heavyweight"
];

const FALLBACK_MENS_RANKINGS = {
  "Flyweight": [
    "Alexandre Pantoja",
    "Manel Kape",
    "Tatsuro Taira",
    "Brandon Royval",
    "Kyoji Horiguchi",
    "Lone'er Kavanagh",
    "Amir Albazi",
    "Asu Almabayev",
    "Brandon Moreno",
    "Steve Erceg",
    "Alex Perez",
    "Tim Elliott",
    "Tagir Ulanbekov",
    "Charles Johnson",
    "Bruno Silva"
  ],

  "Bantamweight": [
    "Merab Dvalishvili",
    "Umar Nurmagomedov",
    "Sean O'Malley",
    "Cory Sandhagen",
    "Song Yadong",
    "Aiemann Zahabi",
    "Deiveson Figueiredo",
    "Mario Bautista",
    "David Martinez",
    "Marlon Vera",
    "Payton Talbott",
    "Vinicius Oliveira",
    "Raul Rosas Jr.",
    "Raoni Barcelos",
    "Farid Basharat"
  ],

  "Featherweight": [
    "Movsar Evloev",
    "Diego Lopes",
    "Lerone Murphy",
    "Aljamain Sterling",
    "Yair Rodriguez",
    "Jean Silva",
    "Arnold Allen",
    "Youssef Zalal",
    "Steve Garcia",
    "Kevin Vallejos",
    "Brian Ortega",
    "Melquizael Costa",
    "Aaron Pico",
    "David Onama",
    "Josh Emmett"
  ],

  "Lightweight": [
    "Justin Gaethje",
    "Arman Tsarukyan",
    "Charles Oliveira",
    "Max Holloway",
    "Benoit Saint Denis",
    "Paddy Pimblett",
    "Mateusz Gamrot",
    "Dan Hooker",
    "Renato Moicano",
    "Mauricio Ruffy",
    "Rafael Fiziev",
    "Quillan Salkilld",
    "Michael Chandler",
    "Fares Ziam",
    "Beneil Dariush"
  ],

  "Welterweight": [
    "Ian Machado Garry",
    "Carlos Prates",
    "Michael Morales",
    "Jack Della Maddalena",
    "Belal Muhammad",
    "Sean Brady",
    "Leon Edwards",
    "Kamaru Usman",
    "Joaquin Buckley",
    "Yaroslav Amosov",
    "Gabriel Bonfim",
    "Mike Malott",
    "Uros Medic",
    "Michael Venom Page",
    "Daniel Rodriguez"
  ],

  "Middleweight": [
    "Khamzat Chimaev",
    "Dricus Du Plessis",
    "Nassourdine Imavov",
    "Caio Borralho",
    "Brendan Allen",
    "Joe Pyfer",
    "Anthony Hernandez",
    "Reinier De Ridder",
    "Israel Adesanya",
    "Robert Whittaker",
    "Jared Cannonier",
    "Gregory Rodrigues",
    "Christian Leroy Duncan",
    "Roman Dolidze",
    "Ikram Aliskerov"
  ],

  "Light Heavyweight": [
    "Magomed Ankalaev",
    "Alex Pereira",
    "Jiri Prochazka",
    "Jan Blachowicz",
    "Khalil Rountree Jr.",
    "Jamahal Hill",
    "Paulo Costa",
    "Azamat Murzakanov",
    "Volkan Oezdemir",
    "Bogdan Guskov",
    "Dominick Reyes",
    "Aleksandar Rakic",
    "Nikita Krylov",
    "Johnny Walker",
    "Alonzo Menifield"
  ],

  "Heavyweight": [
    "Ciryl Gane",
    "Alexander Volkov",
    "Sergei Pavlovich",
    "Waldo Cortes Acosta",
    "Josh Hokit",
    "Serghei Spivac",
    "Curtis Blaydes",
    "Rizvan Kuniev",
    "Derrick Lewis",
    "Tyrell Fortune",
    "Ante Delija",
    "Marcin Tybura",
    "Valter Walker",
    "Brando Pericic",
    "Tallison Teixeira"
  ]
};

const SVG_SIL_LANDING = `<svg viewBox="0 0 80 110" fill="currentColor" class="t15-silhouette">
  <ellipse cx="42" cy="13" rx="11" ry="12"/>
  <path d="M37 24 L47 24 L49 31 L35 31 Z"/>
  <path d="M22 33 Q42 29 62 34 L60 77 Q42 82 22 75 Z"/>
  <path d="M22 40 L6 58 Q4 62 8 63 L12 60 L25 48Z"/>
  <path d="M62 40 L78 54 Q80 57 78 60 L74 58 L62 48Z"/>
  <path d="M30 76 Q26 96 22 110 L34 110 L40 77Z"/>
  <path d="M52 77 Q58 96 62 110 L50 110 L44 77Z"/>
</svg>`;

let landingDivisions = [];
let landingActiveDivision = "";


function escapeAttr(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}


function buildFallbackFighters(division) {
  const names = FALLBACK_MENS_RANKINGS[division] || [];

  return names.map((name, index) => ({
    rank: index + 1,
    Fighter_Id: "",
    name: name,
    nickname: "",
    W: 0,
    L: 0,
    D: 0,
    win_rate: 0,
    ko_rate: 0,
    sig_str: 0,
    total_fights: 0,
    belt: 0,
    source: "fallback_mens_ranking"
  }));
}


async function initLandingTop15() {
  const tabsEl = document.getElementById("landing-div-tabs");

  try {
    const resp = await fetch("/api/top15");
    const data = await resp.json();

    const apiDivisions = data.divisions || [];

    landingDivisions = MEN_DIVISIONS.filter(d => apiDivisions.includes(d));

    if (!landingDivisions.length) {
      landingDivisions = MEN_DIVISIONS;
    }
  } catch (e) {
    landingDivisions = MEN_DIVISIONS;
  }

  if (!tabsEl) return;

  tabsEl.innerHTML = landingDivisions.map(d =>
    `<button class="top15-tab" type="button" onclick="loadLandingDivision('${d}')">${d}</button>`
  ).join("");

  if (landingDivisions.length > 0) {
    loadLandingDivision(landingDivisions[0]);
  }
}


async function loadLandingDivision(division) {
  landingActiveDivision = division;

  document.querySelectorAll(".top15-tab").forEach(tab => {
    tab.classList.toggle("active", tab.textContent === division);
  });

  const grid = document.getElementById("landing-rankings-grid");

  if (!grid) return;

  grid.innerHTML = `
    <div class="top15-loader">
      <div class="ld-spin"></div>
      Loading ${division}...
    </div>
  `;

  try {
    const resp = await fetch("/api/top15/" + encodeURIComponent(division));
    const data = await resp.json();

    let fighters = data.fighters || [];

    if (!fighters.length) {
      fighters = buildFallbackFighters(division);
    }

    renderLandingRankings(fighters.slice(0, 15));
  } catch (e) {
    renderLandingRankings(buildFallbackFighters(division));
  }
}


function renderLandingRankings(fighters) {
  const grid = document.getElementById("landing-rankings-grid");

  if (!grid) return;

  if (!fighters.length) {
    grid.innerHTML = `<div class="top15-loader">No fighters found</div>`;
    return;
  }

  grid.innerHTML = fighters.map(f => {
    const nickname =
      f.nickname &&
      f.nickname !== "No Nickname" &&
      f.nickname !== "nan" &&
      f.nickname !== "None"
        ? `"${f.nickname}"`
        : "";

    const fighterImage = f.Fighter_Id
      ? `/static/fighters/${f.Fighter_Id}.jpg`
      : "";

    const recordHtml =
      Number(f.W) > 0 || Number(f.L) > 0 || Number(f.D) > 0
        ? `<div class="t15-record"><strong>${f.W}</strong>-${f.L}-${f.D}</div>`
        : `<div class="t15-record">Current UFC Ranking</div>`;

    const statsHtml =
      Number(f.win_rate) > 0
        ? `
          <div class="t15-stats">
            <span class="t15-stat red">${f.win_rate}% W</span>
            ${Number(f.ko_rate) > 0 ? `<span class="t15-stat">${f.ko_rate}% KO</span>` : ""}
          </div>
        `
        : `
          <div class="t15-stats">
            <span class="t15-stat red">Rank #${f.rank}</span>
          </div>
        `;

    return `
      <div class="t15-card" onclick="window.location='/dashboard#sec-top15'">
        <div class="t15-rank">${f.rank}</div>

        <div class="t15-photo">
          ${
            fighterImage
              ? `
                <img src="${fighterImage}"
                     alt="${escapeAttr(f.name)}"
                     onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
              `
              : ""
          }

          <div style="${fighterImage ? "display:none;" : "display:flex;"}width:100%;height:100%;align-items:center;justify-content:center">
            ${SVG_SIL_LANDING}
          </div>
        </div>

        <div class="t15-info">
          <div class="t15-name">${f.name}</div>
          <div class="t15-nickname">${nickname}</div>
          ${recordHtml}
          ${statsHtml}
        </div>
      </div>
    `;
  }).join("");
}


document.addEventListener("DOMContentLoaded", () => {
  initLandingTop15();
});
"""

if "// ── Men's Top 15 Rankings Landing Page ──" not in content:
    content = content.replace("</body>", f"<script>{TOP15_JS}</script>\n</body>")


with open(LANDING, "w", encoding="utf-8") as f:
    f.write(content)

print("Landing page updated with men's Top 15 rankings section!")
print("Women's divisions removed from landing rankings.")
print(f"Total length: {len(content)} chars")