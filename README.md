# IPL CRUNCH '26 — Analysis Documentation

> **Wooble Online Data Analytics Challenge**
>
> Registration Deadline: 29 May 2026 · Prize Pool: ₹3,000 + Certificate + Swag

---

## Table of Contents

1. [Project Overview](https://claude.ai/chat/8a31fec4-c71e-420d-b1cf-1dc0343e724c#1-project-overview)
2. [Dataset Description](https://claude.ai/chat/8a31fec4-c71e-420d-b1cf-1dc0343e724c#2-dataset-description)
3. [Setup &amp; Installation](https://claude.ai/chat/8a31fec4-c71e-420d-b1cf-1dc0343e724c#3-setup--installation)
4. [Script Structure](https://claude.ai/chat/8a31fec4-c71e-420d-b1cf-1dc0343e724c#4-script-structure)
5. [Analysis Modules](https://claude.ai/chat/8a31fec4-c71e-420d-b1cf-1dc0343e724c#5-analysis-modules)
   * [Q1 · Toss Advantage](https://claude.ai/chat/8a31fec4-c71e-420d-b1cf-1dc0343e724c#q1--toss-advantage)
   * [Q2 · Phase Impact on Victory](https://claude.ai/chat/8a31fec4-c71e-420d-b1cf-1dc0343e724c#q2--phase-impact-on-victory)
   * [Q3 · Top Batters](https://claude.ai/chat/8a31fec4-c71e-420d-b1cf-1dc0343e724c#q3--top-batters)
   * [Q4 · Top Bowlers](https://claude.ai/chat/8a31fec4-c71e-420d-b1cf-1dc0343e724c#q4--top-bowlers)
   * [Bonus · Season &amp; Venue Trends](https://claude.ai/chat/8a31fec4-c71e-420d-b1cf-1dc0343e724c#bonus--season--venue-trends)
6. [Output Files](https://claude.ai/chat/8a31fec4-c71e-420d-b1cf-1dc0343e724c#6-output-files)
7. [Methodology Notes](https://claude.ai/chat/8a31fec4-c71e-420d-b1cf-1dc0343e724c#7-methodology-notes)
8. [How to Run](https://claude.ai/chat/8a31fec4-c71e-420d-b1cf-1dc0343e724c#8-how-to-run)
9. [Extending the Analysis](https://claude.ai/chat/8a31fec4-c71e-420d-b1cf-1dc0343e724c#9-extending-the-analysis)

---

## 1. Project Overview

This project provides a complete, reproducible Python solution for the **IPL CRUNCH '26** data analytics challenge. It ingests real ball-by-ball IPL data and answers four core questions that mirror how analysts work in sports, product, and business environments.

| Question | Focus Area                                                              |
| -------- | ----------------------------------------------------------------------- |
| Q1       | Does winning the toss translate to winning matches?                     |
| Q2       | Which batting phase (Powerplay / Middle / Death) drives victories?      |
| Q3       | Who are the all-time top batters by runs, average, and strike rate?     |
| Q4       | Who are the most effective bowlers by wickets, economy, and dot-ball %? |
| Bonus    | How have first-innings totals trended across seasons?                   |

---

## 2. Dataset Description

The script expects two CSV files in  **Cricsheet / Kaggle IPL format** :

### `matches.csv` — One row per match

| Column            | Description                 |
| ----------------- | --------------------------- |
| `match_id`      | Unique match identifier     |
| `season`        | IPL season year (e.g. 2024) |
| `toss_winner`   | Team that won the toss      |
| `toss_decision` | `bat`or `field`         |
| `match_winner`  | Team that won the match     |
| `venue`         | Stadium name                |

> Alternate column names like `id`, `winner` are auto-remapped by the loader.

### `deliveries.csv` — One row per ball

| Column                             | Description                          |
| ---------------------------------- | ------------------------------------ |
| `match_id`                       | Links to `matches.csv`             |
| `inning`                         | 1 (batting first) or 2 (chasing)     |
| `over`                           | Over number (0-indexed or 1-indexed) |
| `ball`                           | Ball within the over                 |
| `batter`/`batsman`/`striker` | Batter name (any variant accepted)   |
| `bowler`                         | Bowler name                          |
| `batsman_runs`                   | Runs scored off bat                  |
| `total_runs`                     | Total runs incl. extras              |
| `player_dismissed`               | Name if wicket fell, else blank      |

> **Recommended source:** [Kaggle — IPL Dataset](https://www.kaggle.com/datasets/ramjidoolla/ipl-data-set) or [Cricsheet](https://cricsheet.org/downloads/)

---

## 3. Setup & Installation

### Prerequisites

* Python 3.8 or higher
* pip

### Install dependencies

```bash
pip install pandas numpy matplotlib seaborn scipy
```

### One-liner install

```bash
pip install pandas numpy matplotlib seaborn scipy && echo "✅ Ready"
```

### Directory layout

```
project/
├── ipl_analysis.py     ← main script
├── matches.csv         ← dataset (you provide)
├── deliveries.csv      ← dataset (you provide)
└── ipl_charts/         ← auto-created; charts saved here
    ├── q1_toss_advantage.png
    ├── q2_phase_impact.png
    ├── q3_top_batters.png
    ├── q4_top_bowlers.png
    └── bonus_season_venue.png
```

---

## 4. Script Structure

```
ipl_analysis.py
│
├── load_data()              # 0. Load & normalise both CSVs
│
├── q1_toss_advantage()      # 1. Chi-square test + bar charts
├── q2_phase_impact()        # 2. Point-biserial correlation + box/bar plots
├── q3_top_batters()         # 3. Batter leaderboard + scatter/bar plots
├── q4_top_bowlers()         # 4. Bowler leaderboard + scatter/bar plots
├── bonus_season_trends()    # 5. Season avg score trend + venue bar
│
└── print_summary()          # 6. Console summary of key findings
```

Each analysis function:

* Prints results to the console
* Saves a PNG chart to `ipl_charts/`
* Returns a dictionary or DataFrame for downstream use

---

## 5. Analysis Modules

### Q1 · Toss Advantage

**Question:** Do teams that win the toss actually win more matches?

**Method:**

1. Compare `toss_winner` to `match_winner` row by row.
2. Compute win percentage for toss-winning teams.
3. Run a **chi-square goodness-of-fit test** against the null hypothesis that toss outcome has no effect (expected 50/50 split).
4. Break down win % further by toss decision (`bat` vs `field`).

**Interpretation guide:**

| p-value | Conclusion                                            |
| ------- | ----------------------------------------------------- |
| < 0.05  | Toss winner has a statistically significant advantage |
| ≥ 0.05 | No significant advantage — coin flip                 |

**Visualisations produced:**

* Bar chart: matches won/lost after winning the toss
* Horizontal bar: win % segmented by toss decision (bat / field)

---

### Q2 · Phase Impact on Victory

**Question:** Which phase impacts victory most — Powerplay (1–6), Middle Overs (7–15), or Death Overs (16–20)?

**Method:**

1. Tag every delivery with its phase using `pandas.cut()`.
2. Compute **run rate** (runs per 6 balls) per phase per match per team.
3. Calculate **point-biserial correlation** between run rate and match outcome (won = 1 / lost = 0) for each phase.
4. The phase with the highest absolute correlation coefficient is deemed most impactful.

**Why point-biserial?** It measures the relationship between a continuous variable (run rate) and a binary outcome (win/loss), making it ideal here.

**Visualisations produced:**

* Box plot: run-rate distribution (winners vs losers) across all three phases
* Horizontal bar: correlation coefficient per phase

---

### Q3 · Top Batters

**Question:** Who are the best batters in IPL history?

**Metrics computed:**

| Metric             | Formula                             |
| ------------------ | ----------------------------------- |
| Total Runs         | Sum of `batsman_runs`             |
| Batting Average    | Total runs ÷ innings played        |
| Strike Rate        | (Runs ÷ balls faced) × 100        |
| Boundary %         | (4s + 6s) × 4 ÷ total runs × 100 |
| Fifties / Hundreds | Innings with ≥ 50 / ≥ 100 runs    |

**Filter:** Minimum 20 innings (removes small-sample noise).

**Visualisations produced:**

* Horizontal bar chart: top 10 batters by total runs
* Scatter plot: batting average vs strike rate (bubble size = total runs)

---

### Q4 · Top Bowlers

**Question:** Who are the most effective bowlers?

**Metrics computed:**

| Metric              | Formula                         |
| ------------------- | ------------------------------- |
| Wickets             | Count of `is_wicket == 1`     |
| Economy Rate        | (Runs ÷ balls bowled) × 6     |
| Bowling Average     | Runs conceded ÷ wickets        |
| Bowling Strike Rate | Balls bowled ÷ wickets         |
| Dot-Ball %          | Dot balls ÷ total balls × 100 |

**Filter:** Minimum 20 wickets.

**Note:** The economy axis is **inverted** on the scatter plot — lower economy (better) appears on the right, making elite bowlers cluster at the top-right.

**Visualisations produced:**

* Horizontal bar chart: top 10 bowlers by wickets
* Scatter plot: economy vs dot-ball % (bubble size = wickets)

---

### Bonus · Season & Venue Trends

**What it shows:**

* Line chart of average first-innings totals by season (tracks scoring evolution over IPL history)
* Horizontal bar of the most-used venues by match count

**Requires:** `season` column in `matches.csv` (skips gracefully if absent).

---

## 6. Output Files

All charts are saved as **150 DPI PNG** files in the `ipl_charts/` directory.

| File                       | Content                                   |
| -------------------------- | ----------------------------------------- |
| `q1_toss_advantage.png`  | Toss win/loss + decision breakdown        |
| `q2_phase_impact.png`    | Phase run-rate box plot + correlation bar |
| `q3_top_batters.png`     | Run totals bar + avg vs SR scatter        |
| `q4_top_bowlers.png`     | Wickets bar + econ vs dot% scatter        |
| `bonus_season_venue.png` | Season scoring trend + venue frequency    |

---

## 7. Methodology Notes

### Column name flexibility

The loader auto-remaps common Cricsheet and Kaggle column variants (e.g. `striker` → `batter`, `id` → `match_id`) so the script works with both major data sources without manual editing.

### Phase classification

```
Over 1–6   → Powerplay
Over 7–15  → Middle Overs
Over 16–20 → Death Overs
```

The script uses `pandas.cut()` on the `over` column with correct bin edges.

### Wicket detection

`is_wicket` is derived from whether `player_dismissed` is non-null (works regardless of whether a dedicated `is_wicket` binary column exists in the source data).

### Statistical tests used

| Test                       | Where Used | Why                                                         |
| -------------------------- | ---------- | ----------------------------------------------------------- |
| Chi-square goodness-of-fit | Q1         | Tests if observed toss-win distribution deviates from 50/50 |
| Point-biserial correlation | Q2         | Continuous variable (run rate) vs binary outcome (win/loss) |

---

## 8. How to Run

### Default (looks for CSVs in current directory)

```bash
python ipl_analysis.py
```

### Custom paths

```bash
python ipl_analysis.py path/to/matches.csv path/to/deliveries.csv
```

### Expected console output

```
=================================================================
  IPL CRUNCH '26  –  Loading Data
=================================================================
  Matches   : 1,095
  Deliveries: 243,200
  Seasons   : [2008, 2009, ..., 2024]

─────────────────────────────────────────────────────────────────
Q1 · Toss Advantage Analysis
  Toss winner also won match : 574 / 1,095  (52.4%)
  Chi-square statistic       : 2.441,  p-value = 0.1183
  Conclusion: NO significant advantage (α = 0.05)
  ...
```

---

## 9. Extending the Analysis

Here are ideas to go beyond the base questions and impress the judges:

### Head-to-head matchup matrix

```python
h2h = matches.groupby(["team1", "team2"])["match_winner"].value_counts()
```

### Best death-over specialists

```python
death = deliveries[deliveries["phase"] == "Death Overs (16-20)"]
death.groupby("bowler")[["is_wicket","total_runs"]].agg({"is_wicket":"sum","total_runs":"sum"})
```

### Chasing vs defending win rates by venue

```python
matches.groupby(["venue", "toss_decision"])["match_winner"].apply(
    lambda x: (x == matches.loc[x.index, "toss_winner"]).mean()
)
```

### Partnership analysis

```python
# Group consecutive balls per batting pair to find key partnerships
```

### Predictive model (stretch goal)

Train a logistic regression or gradient boosting model on phase-wise run-rates to predict match outcome from the first innings alone.

---

*Built for IPL CRUNCH '26 by Wooble · connect@wooble.org*
