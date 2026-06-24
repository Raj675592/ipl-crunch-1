"""
IPL CRUNCH '26  —  Wooble Data Analytics Challenge
====================================================
Answers exactly three questions:
  1. Do toss winners win more matches?
  2. Which phase (Powerplay / Middle / Death) is most linked to winning?
  3. Top 5 batters by runs, top 5 bowlers by wickets (last 5 seasons)

Produces:
  chart1_toss.png      — bar chart: win rate toss winner vs loser
  chart2_phases.png    — bar chart: avg runs per phase, winners vs losers
  ipl_crunch26_results.xlsx — tables + surprising finding

Usage:
  python ipl_crunch26.py                     # looks for ipl_matches.csv
  python ipl_crunch26.py mydata.csv          # custom filename
"""

import sys
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

warnings.filterwarnings("ignore")

# ── Config ────────────────────────────────────────────────────────────────────
FILE      = sys.argv[1] if len(sys.argv) > 1 else "ipl_matches.csv"
BLUE      = "#1B4F72"
ORANGE    = "#F39C12"
GREEN     = "#1E8449"
RED       = "#C0392B"
BG        = "#FAFAFA"

plt.rcParams.update({
    "figure.facecolor" : BG,
    "axes.facecolor"   : BG,
    "axes.spines.top"  : False,
    "axes.spines.right": False,
    "font.family"      : "DejaVu Sans",
    "axes.grid"        : True,
    "grid.color"       : "#E0E0E0",
    "grid.linewidth"   : 0.6,
})


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Load & normalise
# ═══════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("  IPL CRUNCH '26  |  Loading data …")
print("=" * 60)

df = pd.read_csv(FILE, low_memory=False)
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

print(f"  Rows      : {len(df):,}")
print(f"  Columns   : {list(df.columns)}\n")

# ── Map common column name variants ──────────────────────────────────────────
RENAMES = {
    # striker / batter
    "striker"            : "batter",
    "batsman"            : "batter",
    # runs
    "runs_off_bat"       : "batsman_runs",
    "runs_batter"        : "batsman_runs",
    "batter_runs"        : "batsman_runs",
    # total runs
    "runs_total"         : "total_runs",
    # wicket
    "wicket_type"        : "wicket_kind",
    "player_dismissed"   : "dismissed",
    "dismissal_kind"     : "wicket_kind",
    # match outcome
    "winner"             : "match_winner",
    # toss
    "toss_winner"        : "toss_winner",   # already fine
    "toss_decision"      : "toss_decision",
    # over
    "ball"               : "over_ball",     # cricsheet "new" CSV uses ball=X.Y
}
df.rename(columns={k: v for k, v in RENAMES.items() if k in df.columns},
          inplace=True)

# Derive over number if stored as X.Y float (e.g. 0.1 = over 1 ball 1)
if "over_ball" in df.columns and "over" not in df.columns:
    df["over"] = df["over_ball"].apply(lambda x: int(str(x).split(".")[0]) + 1)
elif "over" in df.columns:
    # ensure 1-indexed
    if df["over"].min() == 0:
        df["over"] = df["over"] + 1

# is_wicket flag
if "dismissed" in df.columns:
    df["is_wicket"] = df["dismissed"].notna().astype(int)
elif "wicket_kind" in df.columns:
    df["is_wicket"] = df["wicket_kind"].notna().astype(int)
else:
    df["is_wicket"] = 0

# batsman_runs fallback
if "batsman_runs" not in df.columns and "total_runs" in df.columns:
    df["batsman_runs"] = df["total_runs"]   # rough fallback
elif "batsman_runs" in df.columns and df["batsman_runs"].sum() == 0 and "total_runs" in df.columns:
    # CSV was generated with old csv-json.py bug (runs.get("batsman") instead of "batter")
    # total_runs includes extras so slightly inflated, but far better than all zeros
    df["batsman_runs"] = df["total_runs"]
    print("  [WARN] batsman_runs was all zeros — falling back to total_runs. "
          "Re-run csv-json.py to regenerate ipl_matches.csv with the correct batter runs.")

# Phase
df["phase"] = pd.cut(df["over"], bins=[0, 6, 15, 20],
                     labels=["Powerplay\n(1–6)", "Middle\n(7–15)", "Death\n(16–20)"])

# Last 5 seasons
if "season" in df.columns:
    seasons = sorted(df["season"].dropna().unique(), key=str)[-5:]
    df5 = df[df["season"].isin(seasons)].copy()
    season_label = f"{seasons[0]}–{seasons[-1]}"
else:
    df5 = df.copy()
    season_label = "All seasons"

print(f"  5-season window : {season_label}")
print(f"  Balls in window : {len(df5):,}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# Q1 — TOSS vs MATCH WIN
# ═══════════════════════════════════════════════════════════════════════════════
print("─" * 60)
print("Q1  Toss Advantage")
print("─" * 60)

# One row per match (keep first ball of each match)
if "match_id" in df.columns:
    matches = df.drop_duplicates("match_id")[
        ["match_id", "toss_winner", "match_winner", "batting_team",
         "toss_decision"] if "batting_team" in df.columns
        else ["match_id", "toss_winner", "match_winner", "toss_decision"]
    ].copy()
else:
    # No match_id — dedupe on toss_winner + match_winner combo
    matches = (df[["toss_winner", "match_winner"] +
                  (["toss_decision"] if "toss_decision" in df.columns else [])]
               .drop_duplicates().copy())

matches = matches.dropna(subset=["toss_winner", "match_winner"])
matches["toss_won"] = (matches["toss_winner"] == matches["match_winner"])

total         = len(matches)
toss_win_pct  = matches["toss_won"].mean() * 100
toss_lose_pct = 100 - toss_win_pct

print(f"  Total matches       : {total}")
print(f"  Toss winner won     : {toss_win_pct:.1f}%")
print(f"  Toss winner lost    : {toss_lose_pct:.1f}%")

# Decision breakdown
if "toss_decision" in matches.columns:
    dec = (matches.groupby(["toss_decision", "toss_won"])
           .size().unstack(fill_value=0))
    dec["win_pct"] = dec.get(True, 0) / dec.sum(axis=1) * 100
    print("\n  By decision:")
    print(dec[["win_pct"]].round(1).to_string())

# ── Chart 1 ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(["Toss Winner", "Toss Loser"],
              [toss_win_pct, toss_lose_pct],
              color=[BLUE, ORANGE], width=0.45, edgecolor="white", linewidth=1.5)

for bar, val in zip(bars, [toss_win_pct, toss_lose_pct]):
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.8,
            f"{val:.1f}%", ha="center", va="bottom",
            fontsize=14, fontweight="bold")

ax.axhline(50, color="grey", linestyle="--", linewidth=1.2, alpha=0.7)
ax.text(1.42, 51, "50% baseline", color="grey", fontsize=9)
ax.set_ylim(0, 75)
ax.set_ylabel("Win Rate (%)", fontsize=12)
ax.set_title("Does Winning the Toss Help?\nIPL Win Rate: Toss Winner vs Toss Loser",
             fontsize=13, fontweight="bold", pad=14)
ax.tick_params(axis="x", labelsize=12)

plt.tight_layout()
plt.savefig("chart1_toss.png", dpi=150, bbox_inches="tight")
plt.close()
print("\n  ✅  chart1_toss.png saved\n")


# ═══════════════════════════════════════════════════════════════════════════════
# Q2 — PHASE IMPACT
# ═══════════════════════════════════════════════════════════════════════════════
print("─" * 60)
print("Q2  Phase Impact on Winning")
print("─" * 60)

# Only innings 1 batting team (they set the score)
if "innings" in df.columns:
    inn1 = df[df["innings"] == 1].copy()
elif "inning" in df.columns:
    inn1 = df[df["inning"] == 1].copy()
else:
    inn1 = df.copy()   # fallback: use all

# Tag won/lost
if "batting_team" in inn1.columns and "match_winner" in inn1.columns:
    inn1["won"] = (inn1["batting_team"] == inn1["match_winner"]).astype(int)
else:
    inn1["won"] = np.nan

phase_stats = (inn1.groupby(["phase", "won"])["batsman_runs"]
               .agg(["sum", "count"])
               .reset_index())
phase_stats["avg_runs_per_over"] = (phase_stats["sum"] /
                                    phase_stats["count"] * 6).round(2)
phase_stats["outcome"] = phase_stats["won"].map({1.0: "Won", 0.0: "Lost"})

print(phase_stats[["phase", "outcome", "avg_runs_per_over"]].to_string(index=False))

# ── Chart 2 ───────────────────────────────────────────────────────────────────
phases  = ["Powerplay\n(1–6)", "Middle\n(7–15)", "Death\n(16–20)"]
won_rr  = []
lost_rr = []

for ph in phases:
    sub = phase_stats[phase_stats["phase"] == ph]
    won_rr.append(sub[sub["outcome"] == "Won"]["avg_runs_per_over"].values[0]
                  if len(sub[sub["outcome"] == "Won"]) else 0)
    lost_rr.append(sub[sub["outcome"] == "Lost"]["avg_runs_per_over"].values[0]
                   if len(sub[sub["outcome"] == "Lost"]) else 0)

x     = np.arange(len(phases))
width = 0.35

fig, ax = plt.subplots(figsize=(9, 5))
b1 = ax.bar(x - width/2, won_rr,  width, color=GREEN,  label="Winners", edgecolor="white")
b2 = ax.bar(x + width/2, lost_rr, width, color=RED,    label="Losers",  edgecolor="white")

for bar in list(b1) + list(b2):
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.1,
            f"{bar.get_height():.1f}", ha="center", va="bottom", fontsize=10)

ax.set_xticks(x)
ax.set_xticklabels(phases, fontsize=11)
ax.set_ylabel("Average Runs per Over", fontsize=12)
ax.set_title("Which Phase Separates Winners from Losers?\nAvg Runs/Over by Phase — 1st Innings",
             fontsize=13, fontweight="bold", pad=14)
ax.legend(fontsize=11)

# Annotate the biggest gap
gaps    = [w - l for w, l in zip(won_rr, lost_rr)]
max_gap = max(gaps)
max_idx = gaps.index(max_gap)
ax.annotate(f"Biggest gap: +{max_gap:.1f}",
            xy=(x[max_idx], won_rr[max_idx] + 0.3),
            fontsize=10, color=GREEN, fontweight="bold",
            ha="center")

plt.tight_layout()
plt.savefig("chart2_phases.png", dpi=150, bbox_inches="tight")
plt.close()
print("\n  ✅  chart2_phases.png saved\n")


# ═══════════════════════════════════════════════════════════════════════════════
# Q3 — TOP 5 BATTERS & BOWLERS (last 5 seasons)
# ═══════════════════════════════════════════════════════════════════════════════
print("─" * 60)
print(f"Q3  Top 5 Batters & Bowlers  [{season_label}]")
print("─" * 60)

batter_col = "batter" if "batter" in df5.columns else "batsman"

# Top 5 Batters by runs
top_batters = (df5.groupby(batter_col)["batsman_runs"]
               .sum()
               .sort_values(ascending=False)
               .head(5)
               .reset_index())
top_batters.columns  = ["Batter", "Runs"]
top_batters["Rank"]  = range(1, 6)
top_batters = top_batters[["Rank", "Batter", "Runs"]]

# Top 5 Bowlers by wickets
top_bowlers = (df5.groupby("bowler")["is_wicket"]
               .sum()
               .sort_values(ascending=False)
               .head(5)
               .reset_index())
top_bowlers.columns  = ["Bowler", "Wickets"]
top_bowlers["Rank"]  = range(1, 6)
top_bowlers = top_bowlers[["Rank", "Bowler", "Wickets"]]

print("\n  TOP 5 BATTERS")
print(top_batters.to_string(index=False))
print("\n  TOP 5 BOWLERS")
print(top_bowlers.to_string(index=False))


# ═══════════════════════════════════════════════════════════════════════════════
# SURPRISING FINDING
# ═══════════════════════════════════════════════════════════════════════════════
phase_labels = ["Powerplay\n(1–6)", "Middle\n(7–15)", "Death\n(16–20)"]
clean        = ["Powerplay (1–6)", "Middle (7–15)", "Death (16–20)"]
max_phase    = clean[gaps.index(max_gap)]

surprising = (
    f"Surprisingly, the {max_phase} phase shows the biggest run-rate gap "
    f"between winners and losers (+{max_gap:.1f} runs/over), not the Death Overs "
    f"as most fans assume — meaning the match is often decided long before the "
    f"final slog."
)

if toss_win_pct < 52:
    surprising = (
        f"Surprisingly, toss winners win only {toss_win_pct:.1f}% of matches — "
        f"barely above a coin flip — proving that team quality matters far more "
        f"than the toss, despite how much captains agonise over the decision."
    )

print(f"\n  💡 SURPRISING FINDING:\n  {surprising}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# SAVE EXCEL SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
with pd.ExcelWriter("ipl_crunch26_results.xlsx", engine="openpyxl") as xl:

    # Sheet 1: Toss
    toss_df = pd.DataFrame({
        "Outcome"   : ["Toss Winner Won", "Toss Winner Lost"],
        "Matches"   : [int(total * toss_win_pct/100),
                       int(total * toss_lose_pct/100)],
        "Win Rate %": [round(toss_win_pct, 1), round(toss_lose_pct, 1)]
    })
    toss_df.to_excel(xl, sheet_name="Q1 Toss", index=False)

    # Sheet 2: Phase
    phase_out = pd.DataFrame({
        "Phase"             : clean,
        "Winners Runs/Over" : [round(r, 2) for r in won_rr],
        "Losers Runs/Over"  : [round(r, 2) for r in lost_rr],
        "Gap"               : [round(g, 2) for g in gaps],
    })
    phase_out.to_excel(xl, sheet_name="Q2 Phases", index=False)

    # Sheet 3: Players
    top_batters.to_excel(xl, sheet_name="Q3 Players", index=False, startrow=0)
    top_bowlers.to_excel(xl, sheet_name="Q3 Players", index=False, startrow=8)

    # Sheet 4: Surprising finding
    pd.DataFrame({"Surprising Finding": [surprising]}).to_excel(
        xl, sheet_name="Finding", index=False)

print("  ✅  ipl_crunch26_results.xlsx saved")
print("\n" + "=" * 60)
print("  Done! Upload to Wooble:")
print("    📊 chart1_toss.png")
print("    📊 chart2_phases.png")
print("    📋 ipl_crunch26_results.xlsx")
print("=" * 60)