#!/usr/bin/env python3
"""One-time script to insert the men's UFC top15 endpoint into app.py"""

TOP15_CODE = r'''

# ── Men's UFC Top 15 Per Division ────────────────────────────────────────────
# This endpoint uses the current men's UFC ranking list provided manually.
# It removes all women's divisions and only shows men's divisions on the landing page.

import re
from difflib import SequenceMatcher


DIVISION_ORDER = [
    "Flyweight",
    "Bantamweight",
    "Featherweight",
    "Lightweight",
    "Welterweight",
    "Middleweight",
    "Light Heavyweight",
    "Heavyweight"
]


MENS_UFC_RANKINGS = {
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
}


def clean_text(value):
    """Clean text values safely."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_name(name):
    """Normalize fighter names for matching."""
    name = clean_text(name).lower()
    name = name.replace("’", "'")
    name = name.replace("á", "a").replace("č", "c").replace("ć", "c")
    name = name.replace("é", "e").replace("í", "i").replace("ó", "o")
    name = name.replace("ú", "u").replace("ã", "a").replace("ö", "o")
    name = re.sub(r"[^a-z0-9\s']", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def name_similarity(a, b):
    """Return similarity score between two fighter names."""
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()


def find_local_fighter_by_name(name):
    """
    Match UFC ranking name with your local fighter dataset.
    This allows your landing page to still show local stats/images if available.
    """
    if not name:
        return None

    try:
        local = fighter_stats_df.merge(
            fighters_df,
            on="Fighter_Id",
            how="left",
            suffixes=("", "_fighter")
        ).copy()
    except Exception:
        local = fighter_stats_df.copy()

    if "Full Name" not in local.columns:
        return None

    target_norm = normalize_name(name)

    local["_norm_name"] = local["Full Name"].apply(normalize_name)

    exact = local[local["_norm_name"] == target_norm]
    if not exact.empty:
        return exact.iloc[0]

    best_row = None
    best_score = 0

    for _, row in local.iterrows():
        score = name_similarity(name, row.get("Full Name", ""))

        if score > best_score:
            best_score = score
            best_row = row

    if best_score >= 0.82:
        return best_row

    return None


def build_fighter_payload(rank, official_name, division):
    """
    Build fighter response using ranking name and local dataset stats.
    If fighter is not found in your dataset, it still displays the ranking name.
    """
    local_row = find_local_fighter_by_name(official_name)

    if local_row is None:
        return {
            "rank": rank,
            "Fighter_Id": "",
            "name": official_name,
            "nickname": "",
            "W": 0,
            "L": 0,
            "D": 0,
            "win_rate": 0,
            "ko_rate": 0,
            "sig_str": 0,
            "total_fights": 0,
            "belt": 0,
            "score": 0,
            "division": division,
            "source": "manual_current_mens_ufc_ranking"
        }

    wr = safe_float(local_row.get("Win_Rate"), 0)
    ko = safe_float(local_row.get("KO Rate"), 0)
    sig = safe_float(local_row.get("Sig. Str. %"), 0)

    wr = normalize_rate(wr)
    ko = normalize_rate(ko)
    sig = normalize_rate(sig)

    w_val = local_row.get("W_fighter") if "W_fighter" in local_row.index else local_row.get("W", 0)
    l_val = local_row.get("L_fighter") if "L_fighter" in local_row.index else local_row.get("L", 0)
    d_val = local_row.get("D_fighter") if "D_fighter" in local_row.index else local_row.get("D", 0)

    nickname = local_row.get("Nickname", "")

    if str(nickname).lower() in ["nan", "none", "no nickname"]:
        nickname = ""

    return {
        "rank": rank,
        "Fighter_Id": str(local_row.get("Fighter_Id", "")),
        "name": official_name,
        "nickname": str(nickname),
        "W": int(safe_float(w_val, 0)),
        "L": int(safe_float(l_val, 0)),
        "D": int(safe_float(d_val, 0)),
        "win_rate": round(wr * 100, 1),
        "ko_rate": round(ko * 100, 1),
        "sig_str": round(sig * 100, 1),
        "total_fights": int(safe_float(local_row.get("Total_Fights"), 0)),
        "belt": int(safe_float(local_row.get("Belt"), 0)),
        "score": 0,
        "division": division,
        "source": "manual_current_mens_ufc_ranking"
    }


@app.route("/api/top15")
def top15_all():
    """
    Return only men's UFC divisions.
    This removes all women's divisions from the frontend tabs.
    """
    return jsonify({
        "divisions": DIVISION_ORDER,
        "source": "manual_current_mens_ufc_ranking"
    })


@app.route("/api/top15/<division>")
def top15_division(division):
    """
    Return current men's top 15 fighters for selected division.
    """
    if division not in MENS_UFC_RANKINGS:
        return jsonify({
            "division": division,
            "fighters": [],
            "source": "manual_current_mens_ufc_ranking"
        })

    fighters = []

    for rank, fighter_name in enumerate(MENS_UFC_RANKINGS[division], start=1):
        fighters.append(
            build_fighter_payload(rank, fighter_name, division)
        )

    return jsonify({
        "division": division,
        "fighters": fighters[:15],
        "source": "manual_current_mens_ufc_ranking"
    })

'''

MARKER = 'if __name__ == "__main__":'

with open("app.py", encoding="utf-8") as f:
    content = f.read()

if "/api/top15" in content:
    print("top15 already present.")
    print("Remove the old Top 15 block from app.py first, then run this script again.")
else:
    content = content.replace(MARKER, TOP15_CODE + "\n" + MARKER)

    with open("app.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("Done - men's UFC top15 endpoint added")