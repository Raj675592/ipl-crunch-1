"""
IPL CRUNCH '26 - Data Analytics Challenge
==========================================
Wooble | Online Data Analytics Challenge
Author  : [Your Name]
Dataset : Ball-by-ball IPL match data (Kaggle / Cricsheet format)

Required CSV files (place in same directory):
  - matches.csv   : one row per match (toss, winner, venue, season …)
  - deliveries.csv: one row per ball  (match_id, over, ball, batsman,
                    bowler, runs_batsman, runs_extras, wicket_kind …)

Install dependencies:
  pip install pandas numpy matplotlib seaborn scipy
"""

import os
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats

warnings.filterwarnings("ignore")

# ── Aesthetics ────────────────────────────────────────────────────────────────
PALETTE   = ["#1B4F72", "#F39C12", "#1E8449", "#C0392B", "#8E44AD"]
BG_COLOR  = "#F8F9FA"
GRID_CLR  = "#DEE2E6"
OUTPUT_DIR = "ipl_charts-1"
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams.update({
    "figure.facecolor": BG_COLOR,
    "axes.facecolor"  : BG_COLOR,
    "axes.grid"       : True,
    "grid.color"      : GRID_CLR,
    "grid.linewidth"  : 0.7,
    "font.family"     : "DejaVu Sans",
    "axes.spines.top" : False,
    "axes.spines.right": False,
})


# ═══════════════════════════════════════════════════════════════════════════════
# 0.  DATA LOADING & VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def load_data(matches_path: str = "matches.csv",
              deliveries_path: str = "deliveries.csv"):
    """Load and validate IPL datasets."""
    print("=" * 65)
    print("  IPL CRUNCH '26  –  Loading Data")
    print("=" * 65)

    matches    = pd.read_csv(matches_path)
    deliveries = pd.read_csv(deliveries_path)

    # ── Normalise common column name variants ──────────────────────────────
    matches.columns    = matches.columns.str.strip().str.lower()
    deliveries.columns = deliveries.columns.str.strip().str.lower()

    # Rename common Cricsheet / Kaggle column variants
    col_map_m = {"id": "match_id", "winner": "match_winner",
                 "toss_winner": "toss_winner", "toss_decision": "toss_decision"}
    col_map_d = {"match_id": "match_id", "batting_team": "batting_team",
                 "batsman_runs": "batsman_runs", "total_runs": "total_runs",
                 "player_dismissed": "player_dismissed",
                 "batsman": "batter", "striker": "batter",
                 "bowler": "bowler", "over": "over", "ball": "ball"}

    for old, new in col_map_m.items():
        if old in matches.columns and new not in matches.columns:
            matches.rename(columns={old: new}, inplace=True)
    for old, new in col_map_d.items():
        if old in deliveries.columns and new not in deliveries.columns:
            deliveries.rename(columns={old: new}, inplace=True)

    # ── Derived columns ────────────────────────────────────────────────────
    deliveries["phase"] = pd.cut(
        deliveries["over"],
        bins=[-1, 5, 14, 19],
        labels=["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"]
    )
    deliveries["is_wicket"] = deliveries["player_dismissed"].notna().astype(int)

    print(f"  Matches   : {len(matches):,}")
    print(f"  Deliveries: {len(deliveries):,}")
    print(f"  Seasons   : {sorted(matches['season'].unique()) if 'season' in matches.columns else 'N/A'}")
    print()
    return matches, deliveries


# ═══════════════════════════════════════════════════════════════════════════════
# 1.  TOSS WIN vs MATCH WIN
# ═══════════════════════════════════════════════════════════════════════════════

def q1_toss_advantage(matches: pd.DataFrame) -> dict:
    """
    Q1: Do teams that win the toss actually win more matches?
    Returns a results dict and saves a bar chart.
    """
    print("─" * 65)
    print("Q1 · Toss Advantage Analysis")
    print("─" * 65)

    df = matches.dropna(subset=["toss_winner", "match_winner"]).copy()
    df["toss_won_match"] = (df["toss_winner"] == df["match_winner"])

    total      = len(df)
    toss_wins  = df["toss_won_match"].sum()
    win_pct    = toss_wins / total * 100

    # Chi-square test
    counts   = df["toss_won_match"].value_counts()
    expected = [total / 2, total / 2]
    chi2, p  = stats.chisquare(f_obs=[counts.get(True, 0), counts.get(False, 0)],
                                f_exp=expected)

    print(f"  Toss winner also won match : {toss_wins:,} / {total:,}  ({win_pct:.1f}%)")
    print(f"  Chi-square statistic       : {chi2:.3f},  p-value = {p:.4f}")
    print(f"  Conclusion: {'SIGNIFICANT advantage' if p < 0.05 else 'NO significant advantage'} "
          f"(α = 0.05)")

    # Decision breakdown
    dec_grp = df.groupby(["toss_decision", "toss_won_match"]).size().unstack(fill_value=0)
    dec_grp["win_pct"] = dec_grp.get(True, 0) / dec_grp.sum(axis=1) * 100

    print("\n  Win % by toss decision:")
    print(dec_grp[["win_pct"]].round(1).to_string())

    # ── Plot ──────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Q1 · Toss Advantage", fontsize=15, fontweight="bold", y=1.01)

    # Bar: overall
    bars = axes[0].bar(["Won Toss\n& Won Match", "Won Toss\n& Lost Match"],
                       [toss_wins, total - toss_wins],
                       color=[PALETTE[2], PALETTE[3]], width=0.5, edgecolor="white")
    axes[0].bar_label(bars, fmt="%d", padding=4, fontsize=11)
    axes[0].set_title("Overall Toss vs Match Outcome", fontweight="bold")
    axes[0].set_ylabel("Number of Matches")

    # Bar: by decision
    dec_data = dec_grp["win_pct"].reset_index()
    axes[1].barh(dec_data["toss_decision"], dec_data["win_pct"],
                 color=PALETTE[:len(dec_data)], edgecolor="white")
    axes[1].axvline(50, color="grey", linestyle="--", linewidth=1.2, label="50% baseline")
    axes[1].set_title("Win % by Toss Decision", fontweight="bold")
    axes[1].set_xlabel("Win Percentage (%)")
    axes[1].legend()

    plt.tight_layout()
    path = f"{OUTPUT_DIR}/q1_toss_advantage.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Chart → {path}\n")

    return {"win_pct": win_pct, "chi2": chi2, "p_value": p,
            "significant": p < 0.05, "chart": path}


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  PHASE IMPACT ON VICTORY
# ═══════════════════════════════════════════════════════════════════════════════

def q2_phase_impact(matches: pd.DataFrame, deliveries: pd.DataFrame) -> dict:
    """
    Q2: Which phase impacts victory the most — Powerplay, Middle, or Death?
    Uses correlation between phase run-rate and match win.
    """
    print("─" * 65)
    print("Q2 · Phase Impact on Victory")
    print("─" * 65)

    # Runs per ball per phase per innings (innings 1)
    inn1 = deliveries[deliveries["inning"] == 1] if "inning" in deliveries.columns \
        else deliveries[deliveries.get("innings", deliveries.get("inning", 1)) == 1]

    phase_runs = (inn1.groupby(["match_id", "batting_team", "phase"])["total_runs"]
                  .sum().reset_index())
    phase_balls = (inn1.groupby(["match_id", "batting_team", "phase"])
                   .size().reset_index(name="balls"))
    phase_df = phase_runs.merge(phase_balls, on=["match_id", "batting_team", "phase"])
    phase_df["run_rate"] = phase_df["total_runs"] / phase_df["balls"] * 6

    # Merge with winner
    df = phase_df.merge(
        matches[["match_id", "match_winner"]].dropna(),
        on="match_id"
    )
    df["won"] = (df["batting_team"] == df["match_winner"]).astype(int)

    # Point-biserial correlation per phase
    results = {}
    for phase in df["phase"].dropna().unique():
        sub = df[df["phase"] == phase].dropna(subset=["run_rate", "won"])
        r, p = stats.pointbiserialr(sub["won"], sub["run_rate"])
        results[str(phase)] = {"correlation": r, "p_value": p}
        print(f"  {phase:<28} r = {r:+.3f}  (p = {p:.4f})")

    best_phase = max(results, key=lambda k: abs(results[k]["correlation"]))
    print(f"\n  Most impactful phase: {best_phase}")

    # ── Plot ──────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("Q2 · Phase Impact on Victory", fontsize=15, fontweight="bold")

    # Box plot: run-rate distribution by phase & outcome
    win_labels = {0: "Lost", 1: "Won"}
    df["outcome"] = df["won"].map(win_labels)
    sns.boxplot(data=df.dropna(subset=["phase"]), x="phase", y="run_rate",
                hue="outcome", palette=[PALETTE[3], PALETTE[2]],
                ax=axes[0], width=0.5)
    axes[0].set_title("Run Rate per Phase — Winners vs Losers", fontweight="bold")
    axes[0].set_xlabel("Phase")
    axes[0].set_ylabel("Run Rate (per over)")
    axes[0].tick_params(axis="x", rotation=15)

    # Bar: correlation magnitude
    phases = list(results.keys())
    corrs  = [results[p]["correlation"] for p in phases]
    colors = [PALETTE[2] if c > 0 else PALETTE[3] for c in corrs]
    axes[1].barh(phases, corrs, color=colors, edgecolor="white")
    axes[1].axvline(0, color="grey", linewidth=1)
    axes[1].set_title("Correlation with Winning", fontweight="bold")
    axes[1].set_xlabel("Point-Biserial r")

    plt.tight_layout()
    path = f"{OUTPUT_DIR}/q2_phase_impact.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Chart → {path}\n")

    return {"phase_results": results, "most_impactful": best_phase, "chart": path}


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  TOP BATTERS
# ═══════════════════════════════════════════════════════════════════════════════

def q3_top_batters(deliveries: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """Q3: Who are the top batters? (runs, SR, 50s, 100s, boundary %)"""
    print("─" * 65)
    print("Q3 · Top Batters")
    print("─" * 65)

    batter_col = "batter" if "batter" in deliveries.columns else "batsman"

    g = deliveries.groupby(batter_col)

    runs  = g["batsman_runs"].sum()
    balls = g["batsman_runs"].count()
    fours = deliveries[deliveries["batsman_runs"] == 4].groupby(batter_col).size()
    sixes = deliveries[deliveries["batsman_runs"] == 6].groupby(batter_col).size()

    # Innings & milestones
    inning_scores = (deliveries.groupby([batter_col, "match_id"])["batsman_runs"]
                     .sum().reset_index())
    fifties  = (inning_scores[inning_scores["batsman_runs"] >= 50]
                .groupby(batter_col).size())
    hundreds = (inning_scores[inning_scores["batsman_runs"] >= 100]
                .groupby(batter_col).size())
    innings  = inning_scores.groupby(batter_col).size()

    # Dismissals (needed for a correct batting average — NOT innings played,
    # since not-out innings shouldn't count in the denominator)
    dismissals = (deliveries["player_dismissed"].dropna()
                  .value_counts().reindex(runs.index).fillna(0).astype(int))

    df = pd.DataFrame({
        "runs"      : runs,
        "balls"     : balls,
        "fours"     : fours.fillna(0).astype(int),
        "sixes"     : sixes.fillna(0).astype(int),
        "innings"   : innings,
        "fifties"   : fifties.fillna(0).astype(int),
        "hundreds"  : hundreds.fillna(0).astype(int),
        "dismissals": dismissals,
    }).reset_index()
    df.rename(columns={batter_col: "batter"}, inplace=True)

    df["strike_rate"]   = (df["runs"] / df["balls"] * 100).round(2)
    df["avg"]           = (df["runs"] / df["dismissals"].replace(0, np.nan)).round(2)
    df["boundary_pct"]  = ((df["fours"] + df["sixes"]) * 4 /
                           df["runs"].replace(0, np.nan) * 100).round(1)

    top = (df[df["innings"] >= 20]
           .sort_values("runs", ascending=False)
           .head(top_n)
           .reset_index(drop=True))
    top.index += 1

    print(top[["batter", "runs", "avg", "strike_rate",
               "fifties", "hundreds", "boundary_pct"]].to_string())

    # ── Plot ──────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Q3 · Top Batters (min 20 innings)", fontsize=15, fontweight="bold")

    top10 = top.head(10)

    # Horizontal bar: total runs
    bars = axes[0].barh(top10["batter"][::-1], top10["runs"][::-1],
                        color=PALETTE[0], edgecolor="white")
    axes[0].bar_label(bars, fmt="%d", padding=4, fontsize=9)
    axes[0].set_title("Total Runs", fontweight="bold")
    axes[0].set_xlabel("Runs")

    # Scatter: avg vs strike rate
    sc = axes[1].scatter(top10["avg"], top10["strike_rate"],
                         s=top10["runs"] / 50, c=PALETTE[1],
                         edgecolors=PALETTE[0], linewidth=0.8, alpha=0.85)
    for _, row in top10.iterrows():
        axes[1].annotate(row["batter"].split()[-1],
                         (row["avg"], row["strike_rate"]),
                         fontsize=8, ha="left", va="bottom")
    axes[1].set_title("Average vs Strike Rate\n(bubble = total runs)", fontweight="bold")
    axes[1].set_xlabel("Batting Average")
    axes[1].set_ylabel("Strike Rate")

    plt.tight_layout()
    path = f"{OUTPUT_DIR}/q3_top_batters.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Chart → {path}\n")
    return top


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  TOP BOWLERS
# ═══════════════════════════════════════════════════════════════════════════════

def q4_top_bowlers(deliveries: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """Q4: Who are the top bowlers? (wickets, econ, avg, SR, dot%)"""
    print("─" * 65)
    print("Q4 · Top Bowlers")
    print("─" * 65)

    g = deliveries.groupby("bowler")

    wickets = g["is_wicket"].sum()
    runs    = g["total_runs"].sum()
    balls   = g["total_runs"].count()
    dots    = deliveries[deliveries["total_runs"] == 0].groupby("bowler").size()

    df = pd.DataFrame({
        "wickets": wickets,
        "runs"   : runs,
        "balls"  : balls,
        "dots"   : dots.fillna(0).astype(int),
    }).reset_index()

    df["economy"]  = (df["runs"] / df["balls"] * 6).round(2)
    df["bowl_avg"] = (df["runs"] / df["wickets"].replace(0, np.nan)).round(2)
    df["bowl_sr"]  = (df["balls"] / df["wickets"].replace(0, np.nan)).round(2)
    df["dot_pct"]  = (df["dots"] / df["balls"] * 100).round(1)

    top = (df[df["wickets"] >= 20]
           .sort_values("wickets", ascending=False)
           .head(top_n)
           .reset_index(drop=True))
    top.index += 1

    print(top[["bowler", "wickets", "economy", "bowl_avg", "bowl_sr", "dot_pct"]].to_string())

    # ── Plot ──────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Q4 · Top Bowlers (min 20 wickets)", fontsize=15, fontweight="bold")

    top10 = top.head(10)

    bars = axes[0].barh(top10["bowler"][::-1], top10["wickets"][::-1],
                        color=PALETTE[4], edgecolor="white")
    axes[0].bar_label(bars, fmt="%d", padding=4, fontsize=9)
    axes[0].set_title("Total Wickets", fontweight="bold")
    axes[0].set_xlabel("Wickets")

    sc = axes[1].scatter(top10["economy"], top10["dot_pct"],
                         s=top10["wickets"] * 5, c=PALETTE[4],
                         edgecolors="#5B2C6F", linewidth=0.8, alpha=0.85)
    for _, row in top10.iterrows():
        axes[1].annotate(row["bowler"].split()[-1],
                         (row["economy"], row["dot_pct"]),
                         fontsize=8, ha="left", va="bottom")
    axes[1].set_title("Economy vs Dot-Ball %\n(bubble = wickets)", fontweight="bold")
    axes[1].set_xlabel("Economy Rate")
    axes[1].set_ylabel("Dot-Ball %")
    axes[1].invert_xaxis()   # lower economy = better → left

    plt.tight_layout()
    path = f"{OUTPUT_DIR}/q4_top_bowlers.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Chart → {path}\n")
    return top


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  BONUS — SEASON TRENDS & VENUE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def bonus_season_trends(matches: pd.DataFrame, deliveries: pd.DataFrame):
    """Bonus: Average first-innings score trend by season + top venues."""
    print("─" * 65)
    print("BONUS · Season Trends & Venue Analysis")
    print("─" * 65)

    if "season" not in matches.columns:
        print("  'season' column not found — skipping bonus.\n")
        return

    # Avg first innings total per season
    if "inning" in deliveries.columns:
        inn1 = deliveries[deliveries["inning"] == 1]
    else:
        inn1 = deliveries

    totals = (inn1.groupby("match_id")["total_runs"]
              .sum().reset_index(name="total"))
    totals = totals.merge(matches[["match_id", "season"]], on="match_id")
    season_avg = totals.groupby("season")["total"].mean().reset_index()

    # Top venues by matches played
    venue_col = "venue" if "venue" in matches.columns else None

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("BONUS · Season Trends & Venue Analysis",
                 fontsize=15, fontweight="bold")

    # Line: season avg score
    axes[0].plot(season_avg["season"], season_avg["total"],
                 marker="o", color=PALETTE[0], linewidth=2)
    axes[0].fill_between(season_avg["season"], season_avg["total"],
                         alpha=0.15, color=PALETTE[0])
    axes[0].set_title("Avg 1st-Innings Total by Season", fontweight="bold")
    axes[0].set_xlabel("Season")
    axes[0].set_ylabel("Average Runs")
    axes[0].xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    # Bar: top venues
    if venue_col:
        top_venues = matches[venue_col].value_counts().head(8)
        axes[1].barh(top_venues.index[::-1], top_venues.values[::-1],
                     color=PALETTE[1], edgecolor="white")
        axes[1].set_title("Most-Used Venues", fontweight="bold")
        axes[1].set_xlabel("Matches Played")
    else:
        axes[1].text(0.5, 0.5, "No venue data", ha="center", transform=axes[1].transAxes)

    plt.tight_layout()
    path = f"{OUTPUT_DIR}/bonus_season_venue.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Chart → {path}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# 6.  SUMMARY REPORT (console)
# ═══════════════════════════════════════════════════════════════════════════════

def print_summary(q1_res, q2_res, top_batters, top_bowlers):
    print("=" * 65)
    print("  FINAL SUMMARY — IPL CRUNCH '26")
    print("=" * 65)

    sig = "YES — statistically significant" if q1_res["significant"] else "NO"
    print(f"\n  Q1 · Toss advantage   : {q1_res['win_pct']:.1f}% win rate  (Significant: {sig})")

    best = q2_res["most_impactful"]
    r    = q2_res["phase_results"][best]["correlation"]
    print(f"  Q2 · Most impactful   : {best}  (r = {r:+.3f})")

    print(f"  Q3 · #1 Batter        : {top_batters.iloc[0]['batter']}"
          f"  ({top_batters.iloc[0]['runs']} runs, "
          f"SR {top_batters.iloc[0]['strike_rate']})")

    print(f"  Q4 · #1 Bowler        : {top_bowlers.iloc[0]['bowler']}"
          f"  ({top_bowlers.iloc[0]['wickets']} wkts, "
          f"Econ {top_bowlers.iloc[0]['economy']})")

    print(f"\n  All charts saved to → ./{OUTPUT_DIR}/")
    print("=" * 65)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    matches_path    = sys.argv[1] if len(sys.argv) > 1 else "matches.csv"
    deliveries_path = sys.argv[2] if len(sys.argv) > 2 else "deliveries.csv"

    matches, deliveries = load_data(matches_path, deliveries_path)

    q1  = q1_toss_advantage(matches)
    q2  = q2_phase_impact(matches, deliveries)
    tb  = q3_top_batters(deliveries)
    bwl = q4_top_bowlers(deliveries)
    bonus_season_trends(matches, deliveries)

    print_summary(q1, q2, tb, bwl)