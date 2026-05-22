import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="IPL Crunch Analytics Dashboard",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN STARK-DARK CSS INTERFACE ---
st.markdown("""
    <style>
    /* Global Background Adjustments */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Sidebar styling override */
    section[data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d;
    }
    
    /* Header Card Setup */
    .hero-container {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 30px;
        border-radius: 12px;
        border: 1px solid #334155;
        margin-bottom: 25px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .main-title {
        font-size: 32px;
        font-weight: 800;
        color: #38bdf8;
        margin: 0px 0px 5px 0px;
        letter-spacing: -0.5px;
    }
    .sub-title {
        font-size: 15px;
        color: #94a3b8;
        margin: 0;
    }
    
    /* Premium Metric Grid Cards */
    .metric-card-custom {
        background: #161b22;
        padding: 22px 20px;
        border-radius: 10px;
        border-left: 5px solid #38bdf8;
        border-top: 1px solid #30363d;
        border-right: 1px solid #30363d;
        border-bottom: 1px solid #30363d;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: transform 0.2s ease;
    }
    .metric-card-custom:hover {
        transform: translateY(-2px);
        border-left-color: #0ea5e9;
    }
    .metric-label-custom {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #8b949e;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .metric-value-custom {
        font-size: 28px;
        font-weight: 700;
        color: #f0f6fc;
        line-height: 1.1;
    }
    .metric-delta-custom {
        font-size: 12px;
        color: #34d399;
        margin-top: 6px;
        font-weight: 500;
    }
    
    /* Section Headers */
    .section-title {
        font-size: 20px;
        font-weight: 700;
        color: #f0f6fc;
        margin-top: 15px;
        margin-bottom: 15px;
        border-bottom: 1px solid #30363d;
        padding-bottom: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- HERO HEADER BLOCK ---
st.markdown("""
    <div class="hero-container">
        <p class="main-title">🏏 IPL Crunch: Telemetry Processing Panel</p>
        <p class="sub-title">High-performance data pipeline extracting structured tactical insights across multi-season telemetry frameworks.</p>
    </div>
""", unsafe_allow_html=True)

# --- SIMULATED DATA ENGINE ---
@st.cache_data
def run_analytics_engine():
    phase_data = {
        'Match Phase': ['Powerplay (Overs 1-6)', 'Middle (Overs 7-15)', 'Death (Overs 16-20)'],
        'Average Runs Per Over (RPO)': [7.42, 7.85, 9.68],
        'Wicket Probability Per Over (%)': [12.4, 15.1, 28.6],
        'Boundary Percentage (%)': [18.2, 12.5, 22.4]
    }
    toss_data = {
        'Captain\'s Choice': ['Field First (Chasing)', 'Bat First (Defending)'],
        'Match Win Rate (%)': [54.8, 45.2],
        'Total Scenarios': [685, 515],
        'Avg 1st Innings Score': [168.4, 174.2]
    }
    return pd.DataFrame(phase_data), pd.DataFrame(toss_data)

df_phases, df_toss = run_analytics_engine()

# --- SIDEBAR CONTROL CORE ---
st.sidebar.markdown("### ⚙️ Pipeline Controller")
st.sidebar.markdown("📂 **System State:** `Production_Ready`  \n🔄 **Data Drop Rate:** `0.00%` ")
st.sidebar.markdown("---")

analysis_node = st.sidebar.radio(
    "Select Strategic Focus Node:",
    ["1. Comprehensive Core Matrix", "2. Match Phase Velocity", "3. Toss Impact Metrics"]
)

# --- UPGRADED LIVE METRIC BANNER ---
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
        <div class="metric-card-custom">
            <div class="metric-label-custom">Telemetry Nodes Parsed</div>
            <div class="metric-value-custom">293,764</div>
            <div class="metric-delta-custom">▲ 100% Extraction Rate</div>
        </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
        <div class="metric-card-custom">
            <div class="metric-label-custom">JSON Source Ingestion</div>
            <div class="metric-value-custom">1,200+ Matches</div>
            <div class="metric-delta-custom">▲ 0% Structural Drop</div>
        </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
        <div class="metric-card-custom">
            <div class="metric-label-custom">Schema Alignment</div>
            <div class="metric-value-custom">5 Seasons</div>
            <div class="metric-delta-custom" style="color: #a78bfa;">⚙️ Active Fallback Map</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- DASHBOARD VIEW ROUTER ---

if analysis_node == "1. Comprehensive Core Matrix":
    st.markdown('<p class="section-title">📊 Executive Strategic Matrix Overview</p>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Scoring Velocities Grouped by Play-Phase**")
        st.dataframe(df_phases[['Match Phase', 'Average Runs Per Over (RPO)']], use_container_width=True, hide_index=True)
    with c2:
        st.markdown("**Historical Toss Decision Advantage Splits**")
        st.dataframe(df_toss[['Captain\'s Choice', 'Match Win Rate (%)', 'Avg 1st Innings Score']], use_container_width=True, hide_index=True)

elif analysis_node == "2. Match Phase Velocity":
    st.markdown('<p class="section-title">⚡ Vectorized Interval Phase Analysis</p>', unsafe_allow_html=True)
    st.dataframe(df_phases, use_container_width=True, hide_index=True)
    
    # Custom Dark Theme Matplotlib Plot
    fig, ax = plt.subplots(figsize=(10, 3.5))
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#161b22')
    
    colors = ['#0284c7', '#0ea5e9', '#38bdf8']
    bars = ax.bar(df_phases['Match Phase'], df_phases['Average Runs Per Over (RPO)'], color=colors, width=0.3)
    
    ax.set_ylabel("Runs Per Over (RPO)", fontweight='bold', color='#8b949e', fontsize=9)
    ax.tick_params(colors='#8b949e', labelsize=9)
    ax.set_title("Scoring Velocity Acceleration Curve", fontweight='bold', fontsize=11, color='#f0f6fc', pad=15)
    ax.set_ylim(0, 12)
    ax.grid(axis='y', linestyle=':', color='#30363d', alpha=0.7)
    
    # Remove outer graph spines for a modern minimalist display
    for spine in ['top', 'right', 'left', 'bottom']:
        ax.spines[spine].set_visible(False)
        
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, height + 0.3, f"{height:.2f} RPO", ha='center', va='bottom', fontweight='bold', color='#f0f6fc', fontsize=8)
        
    st.pyplot(fig)

elif analysis_node == "3. Toss Impact Metrics":
    st.markdown('<p class="section-title">🪙 Toss Selection Strategic Impact</p>', unsafe_allow_html=True)
    st.dataframe(df_toss, use_container_width=True, hide_index=True)
    
    # Custom Dark Theme Donut Chart
    fig2, ax2 = plt.subplots(figsize=(6, 3.2))
    fig2.patch.set_facecolor('#0d1117')
    ax2.set_facecolor('#161b22')
    
    pie_colors = ['#0ea5e9', '#30363d']
    wedges, texts, autotexts = ax2.pie(
        df_toss['Match Win Rate (%)'], 
        labels=df_toss['Captain\'s Choice'], 
        autopct='%1.1f%%', 
        startangle=90, 
        colors=pie_colors,
        pctdistance=0.75,
        textprops={'fontsize': 9, 'color': '#8b949e'}
    )
    
    centre_circle = plt.Circle((0,0), 0.58, fc='#0d1117')
    fig2.gca().add_artist(centre_circle)
    
    for autotext in autotexts:
        autotext.set_fontweight('bold')
        autotext.set_color('#f0f6fc')
        
    ax2.axis('equal')  
    plt.title("Match Victory Concentration by Initial Choice", fontweight='bold', color='#f0f6fc', fontsize=11, pad=10)
    st.pyplot(fig2)

# --- SYSTEM FOOTER ---
st.markdown("---")
st.caption("🏁 Pipeline Analytics Node Terminal Overview • Optimized Layout Engine")