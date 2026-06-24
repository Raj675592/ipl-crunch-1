"""
app.py — IPL Crunch '26  |  Streamlit Analytics Dashboard
Loads real matches.csv + deliveries.csv and runs all five analyses live.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy.stats import chi2_contingency, pointbiserialr
import os, sys

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IPL Crunch '26",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── GLOBAL CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: #0b0f14; color: #d1d5db; }

section[data-testid="stSidebar"] {
    background: #0f1923 !important;
    border-right: 1px solid #1e2d3d;
}
section[data-testid="stSidebar"] * { color: #94a3b8 !important; }
section[data-testid="stSidebar"] .stRadio label { color: #cbd5e1 !important; }

/* Hero */
.hero {
    background: linear-gradient(120deg, #0f1923 0%, #132032 60%, #0f2235 100%);
    border: 1px solid #1e3a5f;
    border-radius: 14px;
    padding: 32px 36px 24px;
    margin-bottom: 28px;
}
.hero-title {
    font-size: 30px; font-weight: 800; color: #e2e8f0;
    letter-spacing: -0.5px; margin: 0 0 6px;
}
.hero-title span { color: #38bdf8; }
.hero-sub { font-size: 14px; color: #64748b; margin: 0; }

/* KPI cards */
.kpi-row { display: flex; gap: 16px; margin-bottom: 28px; flex-wrap: wrap; }
.kpi {
    flex: 1; min-width: 130px;
    background: #0f1923;
    border: 1px solid #1e2d3d;
    border-top: 3px solid #38bdf8;
    border-radius: 10px;
    padding: 18px 20px;
}
.kpi-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1.2px; color: #475569; font-weight: 600; margin-bottom: 6px; }
.kpi-value { font-size: 26px; font-weight: 800; color: #f1f5f9; font-family: 'JetBrains Mono', monospace; }
.kpi-note  { font-size: 11px; color: #34d399; margin-top: 4px; font-weight: 500; }

/* Section title */
.sec-title {
    font-size: 17px; font-weight: 700; color: #f1f5f9;
    border-left: 3px solid #38bdf8;
    padding-left: 12px; margin: 24px 0 14px;
}

/* Finding box */
.finding {
    background: #0f1923; border: 1px solid #1e3a5f;
    border-left: 4px solid #38bdf8;
    border-radius: 8px; padding: 14px 18px; margin-top: 14px;
    font-size: 13.5px; color: #94a3b8; line-height: 1.6;
}
.finding strong { color: #e2e8f0; }

/* Insight pill */
.pill {
    display: inline-block;
    background: #132032; border: 1px solid #1e3a5f;
    color: #38bdf8; border-radius: 20px;
    padding: 3px 12px; font-size: 12px; font-weight: 600;
    margin: 4px 4px 0 0;
}
</style>
""", unsafe_allow_html=True)


# ─── DATA LOADING ────────────────────────────────────────────────────────────
MATCHES_PATH    = "matches.csv"
DELIVERIES_PATH = "deliveries.csv"

@st.cache_data(show_spinner="Loading match data…")
def load_data(mp=MATCHES_PATH, dp=DELIVERIES_PATH):
    matches    = pd.read_csv(mp)
    deliveries = pd.read_csv(dp)

    # Normalize matches column names
    matches.rename(columns={
        "id": "match_id", "Season": "season",
        "winner": "match_winner",
    }, inplace=True)

    # Normalize deliveries column names
    deliveries.rename(columns={
        "batsman": "batter", "striker": "batter",
        "is_wicket": "wicket",
    }, inplace=True)

    # Derive wicket flag from player_dismissed if needed
    if "wicket" not in deliveries.columns:
        deliveries["wicket"] = deliveries["player_dismissed"].notna().astype(int)

    # Phase labels
    deliveries["phase"] = pd.cut(
        deliveries["over"],
        bins=[0, 6, 15, 20],
        labels=["Powerplay\n(1–6)", "Middle\n(7–15)", "Death\n(16–20)"],
    )

    # Merge season into deliveries
    deliveries = deliveries.merge(
        matches[["match_id", "season", "match_winner", "toss_winner", "toss_decision"]],
        on="match_id", how="left",
    )

    return matches, deliveries


def _fig():
    """Return a pre-styled dark figure + axes."""
    fig, ax = plt.subplots(figsize=(9, 3.8))
    fig.patch.set_facecolor("#0b0f14")
    ax.set_facecolor("#0f1923")
    for sp in ax.spines.values():
        sp.set_edgecolor("#1e2d3d")
    ax.tick_params(colors="#64748b", labelsize=9)
    ax.yaxis.label.set_color("#64748b")
    ax.xaxis.label.set_color("#64748b")
    ax.title.set_color("#f1f5f9")
    ax.grid(axis="y", color="#1e2d3d", linewidth=0.7)
    return fig, ax


def _fig2():
    """Two-panel figure."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    fig.patch.set_facecolor("#0b0f14")
    for ax in axes:
        ax.set_facecolor("#0f1923")
        for sp in ax.spines.values():
            sp.set_edgecolor("#1e2d3d")
        ax.tick_params(colors="#64748b", labelsize=9)
        ax.yaxis.label.set_color("#64748b")
        ax.xaxis.label.set_color("#64748b")
        ax.title.set_color("#f1f5f9")
        ax.grid(axis="y", color="#1e2d3d", linewidth=0.7)
    return fig, axes


ACCENT  = "#38bdf8"
ACCENT2 = "#818cf8"
GREEN   = "#34d399"
CORAL   = "#f87171"
AMBER   = "#fbbf24"


# ─── LOAD ────────────────────────────────────────────────────────────────────
try:
    matches, deliveries = load_data()
except FileNotFoundError as e:
    st.error(f"**CSV not found:** {e}\n\nMake sure `matches.csv` and `deliveries.csv` are in the same folder as `app.py`.")
    st.stop()


# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
st.sidebar.markdown("## 🏏 IPL Crunch '26")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate",
    ["🏠  Overview", "🪙  Q1 · Toss", "⚡  Q2 · Phases", "🏏  Q3 · Batters", "🎯  Q4 · Bowlers", "📈  Bonus · Seasons"],
)
st.sidebar.markdown("---")
st.sidebar.markdown(
    f"<small style='color:#334155'>Matches: **{len(matches):,}**<br>"
    f"Deliveries: **{len(deliveries):,}**<br>"
    f"Seasons: **{matches['season'].nunique()}**</small>",
    unsafe_allow_html=True,
)


# ─── HERO ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
  <p class="hero-title">🏏 IPL <span>Crunch '26</span></p>
  <p class="hero-sub">Ball-by-ball analytics across {matches['season'].nunique()} IPL seasons &nbsp;·&nbsp;
  Wooble Online Data Analytics Challenge</p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🏠  Overview":
    total_runs  = int(deliveries["total_runs"].sum())
    total_wkts  = int(deliveries["wicket"].sum())
    total_bndry = int(((deliveries["batsman_runs"] == 4) | (deliveries["batsman_runs"] == 6)).sum())
    seasons_str = f"{matches['season'].min()} – {matches['season'].max()}"

    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi"><div class="kpi-label">Matches</div><div class="kpi-value">{len(matches):,}</div><div class="kpi-note">▲ Complete dataset</div></div>
      <div class="kpi"><div class="kpi-label">Deliveries</div><div class="kpi-value">{len(deliveries):,}</div><div class="kpi-note">Ball-by-ball</div></div>
      <div class="kpi"><div class="kpi-label">Total Runs</div><div class="kpi-value">{total_runs:,}</div><div class="kpi-note">All innings</div></div>
      <div class="kpi"><div class="kpi-label">Wickets</div><div class="kpi-value">{total_wkts:,}</div><div class="kpi-note">All dismissals</div></div>
      <div class="kpi"><div class="kpi-label">Boundaries</div><div class="kpi-value">{total_bndry:,}</div><div class="kpi-note">4s + 6s</div></div>
      <div class="kpi"><div class="kpi-label">Seasons</div><div class="kpi-value">{matches['season'].nunique()}</div><div class="kpi-note">{seasons_str}</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="sec-title">What this dashboard covers</p>', unsafe_allow_html=True)
    rows = [
        ("🪙", "Q1 · Toss Advantage",    "Does winning the toss actually win matches? Chi-square test vs 50/50 null."),
        ("⚡", "Q2 · Phase Impact",       "Which batting phase — Powerplay, Middle, Death — most separates winners from losers?"),
        ("🏏", "Q3 · Top Batters",        "All-time leaders by runs, average, and strike rate (min. 20 innings)."),
        ("🎯", "Q4 · Top Bowlers",        "Most effective bowlers by wickets, economy, and dot-ball % (min. 20 wickets)."),
        ("📈", "Bonus · Season Trends",   "How first-innings scoring has evolved across seasons, plus the busiest venues."),
    ]
    for icon, title, desc in rows:
        st.markdown(f"""
        <div class="finding">
          <strong>{icon} {title}</strong><br>{desc}
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: Q1 — TOSS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🪙  Q1 · Toss":
    st.markdown('<p class="sec-title">🪙 Q1 · Does Winning the Toss Win Matches?</p>', unsafe_allow_html=True)

    valid = matches.dropna(subset=["toss_winner", "match_winner"]).copy()
    valid["toss_won_match"] = valid["toss_winner"] == valid["match_winner"]

    won  = valid["toss_won_match"].sum()
    lost = (~valid["toss_won_match"]).sum()
    pct  = round(won / len(valid) * 100, 1)

    # Chi-square
    ct = np.array([[won, lost], [len(valid) // 2, len(valid) // 2]])
    chi2, p, *_ = chi2_contingency(ct)
    sig = "✅ Statistically significant" if p < 0.05 else "❌ Not statistically significant"

    # Win % by decision
    by_dec = valid.groupby("toss_decision")["toss_won_match"].mean() * 100

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = _fig()
        bars = ax.bar(["Toss Winner", "Toss Loser"], [pct, 100 - pct],
                      color=[ACCENT, "#1e3a5f"], width=0.38)
        ax.axhline(50, color="#475569", linestyle="--", linewidth=1, label="50% baseline")
        ax.set_ylim(0, 70)
        ax.set_ylabel("Win Rate (%)")
        ax.set_title("Toss Winner vs Loser — Match Win Rate", fontsize=11, fontweight="bold", pad=12)
        for b in bars:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, h + 1.2, f"{h:.1f}%",
                    ha="center", fontsize=11, fontweight="bold", color="#f1f5f9")
        ax.legend(facecolor="#0f1923", edgecolor="#1e2d3d", labelcolor="#64748b", fontsize=8)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col2:
        fig2, ax2 = _fig()
        labels = [f"Bat First\n({by_dec.get('bat', 0):.1f}%)", f"Field First\n({by_dec.get('field', 0):.1f}%)"]
        vals   = [by_dec.get("bat", 0), by_dec.get("field", 0)]
        colors = [ACCENT2, AMBER]
        ax2.barh(labels, vals, color=colors, height=0.4)
        ax2.axvline(50, color="#475569", linestyle="--", linewidth=1)
        ax2.set_xlim(0, 80)
        ax2.set_xlabel("Win Rate (%)")
        ax2.set_title("Win Rate by Toss Decision", fontsize=11, fontweight="bold", pad=12)
        for i, v in enumerate(vals):
            ax2.text(v + 1, i, f"{v:.1f}%", va="center", fontsize=11, fontweight="bold", color="#f1f5f9")
        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    decision_text = "field first" if by_dec.get("field", 0) > by_dec.get("bat", 0) else "bat first"
    st.markdown(f"""
    <div class="finding">
      <strong>Finding:</strong> Toss winners convert to match winners <strong>{pct}%</strong> of the time —
      barely above a coin flip. Chi-square p-value = <strong>{p:.4f}</strong> ({sig}).
      When teams do win the toss, choosing to <strong>{decision_text}</strong> gives a noticeably better win rate
      (<strong>{by_dec.get('field', 0):.1f}%</strong> vs <strong>{by_dec.get('bat', 0):.1f}%</strong>).
    </div>
    """, unsafe_allow_html=True)

    # Raw table
    with st.expander("View raw numbers"):
        summary = pd.DataFrame({
            "Scenario": ["Toss Winner → Won Match", "Toss Winner → Lost Match"],
            "Count":    [int(won), int(lost)],
            "Rate (%)": [pct, round(100 - pct, 1)],
        })
        st.dataframe(summary, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: Q2 — PHASES
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⚡  Q2 · Phases":
    st.markdown('<p class="sec-title">⚡ Q2 · Which Phase Separates Winners from Losers?</p>', unsafe_allow_html=True)

    inn1 = deliveries[(deliveries["inning"] == 1) & deliveries["phase"].notna()].copy()
    inn1["won"] = (inn1["batting_team"] == inn1["match_winner"]).astype(int)

    # RPO per phase per match per team
    phase_match = (
        inn1.groupby(["match_id", "phase", "won"])["total_runs"]
        .sum()
        .reset_index()
    )
    phase_match["over_count"] = inn1.groupby(["match_id", "phase", "won"])["over"].nunique().values
    phase_match["rpo"] = phase_match["total_runs"] / phase_match["over_count"].clip(lower=1)

    # Avg RPO winners vs losers
    avg_rpo = phase_match.groupby(["phase", "won"])["rpo"].mean().unstack(fill_value=0)
    avg_rpo.columns = ["Losers", "Winners"]

    # Correlation per phase
    corr_rows = []
    for phase, grp in phase_match.groupby("phase"):
        r, p = pointbiserialr(grp["won"], grp["rpo"])
        corr_rows.append({"Phase": str(phase), "r": round(r, 3), "p": round(p, 4)})
    corr_df = pd.DataFrame(corr_rows)

    col1, col2 = st.columns([3, 2])

    with col1:
        fig, ax = _fig()
        phases = [str(p) for p in avg_rpo.index]
        x = np.arange(len(phases))
        w = 0.3
        ax.bar(x - w / 2, avg_rpo["Winners"], width=w, color=GREEN,   label="Winners", zorder=3)
        ax.bar(x + w / 2, avg_rpo["Losers"],  width=w, color=CORAL,   label="Losers",  zorder=3)
        ax.set_xticks(x)
        ax.set_xticklabels(phases, fontsize=9)
        ax.set_ylabel("Avg Runs Per Over")
        ax.set_title("Avg RPO by Phase — Winners vs Losers (1st Innings)", fontsize=11, fontweight="bold", pad=12)
        ax.legend(facecolor="#0f1923", edgecolor="#1e2d3d", labelcolor="#94a3b8", fontsize=9)
        ax.grid(axis="y", color="#1e2d3d", linewidth=0.7, zorder=0)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col2:
        fig2, ax2 = _fig()
        corr_vals  = corr_df["r"].tolist()
        corr_cols  = [GREEN if v > 0 else CORAL for v in corr_vals]
        ax2.barh(corr_df["Phase"].tolist(), corr_vals, color=corr_cols, height=0.4)
        ax2.axvline(0, color="#475569", linewidth=1)
        ax2.set_xlabel("Point-Biserial r")
        ax2.set_title("Phase–Outcome Correlation", fontsize=11, fontweight="bold", pad=12)
        for i, (v, p) in enumerate(zip(corr_df["r"], corr_df["p"])):
            sig = "*" if p < 0.05 else ""
            ax2.text(v + 0.002 if v >= 0 else v - 0.002, i,
                     f"r={v}{sig}", va="center", fontsize=9, color="#f1f5f9",
                     ha="left" if v >= 0 else "right")
        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    best = corr_df.loc[corr_df["r"].abs().idxmax()]
    st.markdown(f"""
    <div class="finding">
      <strong>Finding:</strong> The <strong>{best['Phase']}</strong> phase has the highest correlation with match outcome
      (r = <strong>{best['r']}</strong>{'*, p < 0.05' if float(best['p']) < 0.05 else ''}).
      Death-over run rate shows the starkest gap between winning and losing teams —
      teams that accelerate late consistently separate themselves.
    </div>
    """, unsafe_allow_html=True)

    with st.expander("View correlation table"):
        st.dataframe(corr_df.rename(columns={"r": "Point-Biserial r", "p": "p-value"}),
                     use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: Q3 — BATTERS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🏏  Q3 · Batters":
    st.markdown('<p class="sec-title">🏏 Q3 · All-Time Top Batters</p>', unsafe_allow_html=True)

    min_inn = st.slider("Minimum innings played", 10, 60, 20, 5)

    batters = (
        deliveries.groupby("batter")
        .agg(
            total_runs   = ("batsman_runs", "sum"),
            balls_faced  = ("batsman_runs", "count"),
            innings      = ("match_id",     "nunique"),
            fours        = ("batsman_runs", lambda x: (x == 4).sum()),
            sixes        = ("batsman_runs", lambda x: (x == 6).sum()),
        )
        .query(f"innings >= {min_inn}")
        .copy()
    )
    batters["average"]      = (batters["total_runs"] / batters["innings"]).round(1)
    batters["strike_rate"]  = (batters["total_runs"] / batters["balls_faced"] * 100).round(1)
    batters["boundary_pct"] = ((batters["fours"] * 4 + batters["sixes"] * 6) / batters["total_runs"] * 100).round(1)
    batters = batters.sort_values("total_runs", ascending=False)

    top10 = batters.head(10)

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = _fig()
        colors = [ACCENT if i == 0 else "#1e3a5f" for i in range(len(top10))]
        ax.barh(top10.index[::-1], top10["total_runs"][::-1], color=colors[::-1], height=0.6)
        ax.set_xlabel("Total Runs")
        ax.set_title("Top 10 Batters — Career Runs", fontsize=11, fontweight="bold", pad=12)
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
        for i, (name, row) in enumerate(top10[::-1].iterrows()):
            ax.text(row["total_runs"] + 30, i, f"{row['total_runs']:,}",
                    va="center", fontsize=8, color="#94a3b8")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col2:
        fig2, ax2 = _fig()
        scatter = ax2.scatter(
            top10["strike_rate"], top10["average"],
            s=top10["total_runs"] / 12,
            c=top10["total_runs"],
            cmap="Blues", alpha=0.85, linewidths=0.5, edgecolors="#38bdf8",
        )
        for name, row in top10.iterrows():
            ax2.annotate(name.split()[-1], (row["strike_rate"], row["average"]),
                         fontsize=7.5, color="#94a3b8",
                         xytext=(3, 3), textcoords="offset points")
        ax2.set_xlabel("Strike Rate")
        ax2.set_ylabel("Batting Average")
        ax2.set_title("Strike Rate vs Average\n(bubble size ∝ runs)", fontsize=11, fontweight="bold", pad=12)
        ax2.grid(color="#1e2d3d", linewidth=0.5)
        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    # Table
    st.markdown('<p class="sec-title">Full Leaderboard</p>', unsafe_allow_html=True)
    display_cols = ["total_runs", "innings", "balls_faced", "average", "strike_rate", "fours", "sixes", "boundary_pct"]
    col_names    = ["Runs", "Innings", "Balls", "Average", "SR", "4s", "6s", "Boundary %"]
    st.dataframe(
        batters[display_cols].head(30).rename(columns=dict(zip(display_cols, col_names))),
        use_container_width=True,
    )

    top1 = batters.index[0]
    st.markdown(f"""
    <div class="finding">
      <strong>Finding:</strong> <strong>{top1}</strong> leads all-time with
      <strong>{int(batters.loc[top1,'total_runs']):,}</strong> runs from
      <strong>{int(batters.loc[top1,'innings'])}</strong> innings
      (avg <strong>{batters.loc[top1,'average']}</strong>, SR <strong>{batters.loc[top1,'strike_rate']}</strong>).
      Top right of the scatter reveals batters who combine elite average <em>and</em> strike rate — the
      true match-winners.
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: Q4 — BOWLERS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🎯  Q4 · Bowlers":
    st.markdown('<p class="sec-title">🎯 Q4 · Most Effective Bowlers</p>', unsafe_allow_html=True)

    min_wkts = st.slider("Minimum wickets", 10, 60, 20, 5)

    wkts = (deliveries[deliveries["wicket"] == 1]
            .groupby("bowler").size().rename("wickets"))
    agg  = deliveries.groupby("bowler").agg(
        balls    = ("total_runs", "count"),
        runs     = ("total_runs", "sum"),
        dot_balls= ("total_runs", lambda x: (x == 0).sum()),
    )
    bowlers = pd.concat([wkts, agg], axis=1).dropna(subset=["wickets"])
    bowlers = bowlers[bowlers["wickets"] >= min_wkts].copy()
    bowlers["economy"]   = (bowlers["runs"] / bowlers["balls"] * 6).round(2)
    bowlers["avg"]       = (bowlers["runs"] / bowlers["wickets"]).round(1)
    bowlers["sr"]        = (bowlers["balls"] / bowlers["wickets"]).round(1)
    bowlers["dot_pct"]   = (bowlers["dot_balls"] / bowlers["balls"] * 100).round(1)
    bowlers = bowlers.sort_values("wickets", ascending=False)

    top10b = bowlers.head(10)

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = _fig()
        colors = [CORAL if i == 0 else "#2d1e2f" for i in range(len(top10b))]
        ax.barh(top10b.index[::-1], top10b["wickets"][::-1], color=colors[::-1], height=0.6)
        ax.set_xlabel("Wickets")
        ax.set_title("Top 10 Bowlers — Career Wickets", fontsize=11, fontweight="bold", pad=12)
        for i, (name, row) in enumerate(top10b[::-1].iterrows()):
            ax.text(row["wickets"] + 1.5, i, str(int(row["wickets"])),
                    va="center", fontsize=8, color="#94a3b8")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col2:
        fig2, ax2 = _fig()
        ax2.scatter(
            top10b["economy"], top10b["dot_pct"],
            s=top10b["wickets"] * 2.5,
            c=top10b["wickets"], cmap="Reds",
            alpha=0.85, linewidths=0.5, edgecolors=CORAL,
        )
        for name, row in top10b.iterrows():
            ax2.annotate(name.split()[-1], (row["economy"], row["dot_pct"]),
                         fontsize=7.5, color="#94a3b8",
                         xytext=(3, 3), textcoords="offset points")
        ax2.invert_xaxis()  # lower economy (better) → right
        ax2.set_xlabel("Economy  ← Better")
        ax2.set_ylabel("Dot Ball %")
        ax2.set_title("Economy vs Dot Ball %\n(bubble = wickets, x-axis inverted)", fontsize=11, fontweight="bold", pad=12)
        ax2.grid(color="#1e2d3d", linewidth=0.5)
        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    st.markdown('<p class="sec-title">Full Leaderboard</p>', unsafe_allow_html=True)
    d_cols    = ["wickets", "balls", "runs", "economy", "avg", "sr", "dot_pct"]
    d_labels  = ["Wkts", "Balls", "Runs", "Economy", "Avg", "SR", "Dot %"]
    st.dataframe(
        bowlers[d_cols].head(30).rename(columns=dict(zip(d_cols, d_labels))),
        use_container_width=True,
    )

    top1b = bowlers.index[0]
    st.markdown(f"""
    <div class="finding">
      <strong>Finding:</strong> <strong>{top1b}</strong> leads with
      <strong>{int(bowlers.loc[top1b,'wickets'])}</strong> wickets
      (economy <strong>{bowlers.loc[top1b,'economy']}</strong>,
      dot ball% <strong>{bowlers.loc[top1b,'dot_pct']}</strong>%).
      Top-right of the scatter (low economy + high dot%) reveals the most suffocating bowlers —
      those who don't just take wickets but strangle scoring too.
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: BONUS — SEASONS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📈  Bonus · Seasons":
    st.markdown('<p class="sec-title">📈 Bonus · Season Scoring Trends & Venue Frequency</p>', unsafe_allow_html=True)

    if "season" not in deliveries.columns:
        st.warning("Season column not found in deliveries — skipping season trend.")
    else:
        inn1 = deliveries[deliveries["inning"] == 1]
        season_totals = (
            inn1.groupby(["match_id", "season"])["total_runs"]
            .sum().reset_index()
        )
        season_avg = season_totals.groupby("season")["total_runs"].mean().round(1)
        season_avg = season_avg.sort_index()

        venue_counts = matches["venue"].value_counts().head(12)

        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        fig.patch.set_facecolor("#0b0f14")

        # Season trend
        ax = axes[0]
        ax.set_facecolor("#0f1923")
        for sp in ax.spines.values(): sp.set_edgecolor("#1e2d3d")
        ax.plot(range(len(season_avg)), season_avg.values,
                color=ACCENT, linewidth=2.2, marker="o",
                markersize=5, markerfacecolor=ACCENT2, markeredgecolor=ACCENT)
        ax.fill_between(range(len(season_avg)), season_avg.values,
                         season_avg.min() - 5, alpha=0.12, color=ACCENT)
        ax.set_xticks(range(len(season_avg)))
        ax.set_xticklabels(season_avg.index.tolist(), rotation=45, ha="right", fontsize=8, color="#64748b")
        ax.tick_params(colors="#64748b", labelsize=9)
        ax.set_ylabel("Avg 1st-Innings Total", color="#64748b", fontsize=9)
        ax.set_title("1st Innings Avg Total by Season", fontsize=11, fontweight="bold", color="#f1f5f9", pad=12)
        ax.grid(axis="y", color="#1e2d3d", linewidth=0.7)
        for i, (s, v) in enumerate(zip(season_avg.index, season_avg.values)):
            ax.text(i, v + 1.5, f"{v:.0f}", ha="center", fontsize=7, color="#94a3b8")

        # Venue bar
        ax2 = axes[1]
        ax2.set_facecolor("#0f1923")
        for sp in ax2.spines.values(): sp.set_edgecolor("#1e2d3d")
        short_names = [v.split(",")[0].replace(" Stadium", "").replace(" Cricket", "")[:28] for v in venue_counts.index]
        ax2.barh(short_names[::-1], venue_counts.values[::-1], color=AMBER, height=0.6)
        ax2.set_xlabel("Matches Played", color="#64748b", fontsize=9)
        ax2.tick_params(colors="#64748b", labelsize=8)
        ax2.set_title("Most-Used Venues", fontsize=11, fontweight="bold", color="#f1f5f9", pad=12)
        ax2.grid(axis="x", color="#1e2d3d", linewidth=0.7)

        fig.tight_layout(pad=2.5)
        st.pyplot(fig)
        plt.close(fig)

        best_s  = season_avg.idxmax()
        worst_s = season_avg.idxmin()
        top_v   = venue_counts.index[0]
        st.markdown(f"""
        <div class="finding">
          <strong>Finding:</strong> Scoring has trended upward — <strong>{best_s}</strong> had the highest average
          1st-innings total (<strong>{season_avg[best_s]:.0f}</strong> runs),
          while <strong>{worst_s}</strong> was the lowest-scoring season (<strong>{season_avg[worst_s]:.0f}</strong>).
          <strong>{top_v.split(',')[0]}</strong> has hosted the most IPL matches
          (<strong>{int(venue_counts.iloc[0])}</strong>), giving home teams a consistent crowd advantage.
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Season-by-season table"):
            st.dataframe(
                season_avg.reset_index().rename(columns={"season": "Season", "total_runs": "Avg 1st Innings Score"}),
                use_container_width=True, hide_index=True,
            )

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("🏁 IPL Crunch '26  ·  Wooble Online Data Analytics Challenge  ·  Data: Kaggle / Cricsheet")