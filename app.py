import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="CYA Tactical", layout="wide")
# ===== SESSION STATE =====
if 'pink_zones' not in st.session_state:
    st.session_state.pink_zones = []
if 'momentum_line' not in st.session_state:
    st.session_state.momentum_line = [0]
if 'rounds' not in st.session_state:
    st.session_state.rounds = []
if 'danger_zones' not in st.session_state:
    st.session_state.danger_zones = []
if "roundsc" not in st.session_state:
    st.session_state.roundsc = []

# ===== CONFIG =====
WINDOW_SIZE = st.sidebar.slider("MSI Window Size", 10, 100, 20)
PINK_THRESHOLD = st.sidebar.number_input("Pink Threshold (default = 10.0x)", value=10.0)
STRICT_RTT = st.sidebar.checkbox("Strict RTT Mode", value=True)

# ===== SCORING =====
def score_round(multiplier):
    if multiplier < 1.5:
        return -1.5
    return np.interp(multiplier, [1.5, 2.0, 5.0, 10.0, 20.0], [-1.0, 1.0, 1.5, 2.0, 3.0])

def detect_dangers():
    st.session_state.danger_zones = [
        i for i in range(4, len(st.session_state.rounds))
        if sum(m < 2.0 for m in st.session_state.rounds[i-4:i+1]) >= 4
    ]

# ===== VISUALIZATION =====
def create_battle_chart():
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12,6))
    momentum = pd.Series(st.session_state.momentum_line)
    ax.plot(momentum.ewm(alpha=0.75).mean(), color='#00fffa', lw=2, marker='o',
            markersize=8, markerfacecolor='white', markeredgecolor='white', zorder=4)

    for idx in st.session_state.pink_zones:
        if idx < len(momentum):
            ax.hlines(momentum[idx], 0, len(momentum)-1, colors='#ff00ff', linestyles=':', alpha=0.4)
            ax.axvline(idx, color='#ff00ff', linestyle='--', alpha=0.6)

    for zone in st.session_state.danger_zones:
        ax.axvspan(zone-0.5, zone+0.5, color='#d50000', alpha=0.15)

    ax.set_title("CYA TACTICAL OVERLAY v5.1", color='#00fffa', fontsize=18, weight='bold')
    ax.set_facecolor('#000000')
    return fig

# ===== UI - SECTION 1: MOMENTUM CHART =====
#st.set_page_config(page_title="CYA Tactical", layout="wide")
st.title("🔥 CYA BATTLE MATRIX")

col1, col2 = st.columns([3,1])
with col1:
    mult = st.number_input("Enter Multiplier", 1.0, 1000.0, 1.0, 0.1, key='mult_input')
with col2:
    if st.button("🚀 Analyze"):
        st.session_state.rounds.append(mult)
        st.session_state.momentum_line.append(
            st.session_state.momentum_line[-1] + score_round(mult))
        if mult >= PINK_THRESHOLD:
            st.session_state.pink_zones.append(len(st.session_state.rounds)-1)
        detect_dangers()

    if st.button("🔄 Full Reset"):
        for k in ['rounds','momentum_line','pink_zones','danger_zones','roundsc']:
            st.session_state[k] = [] if k != 'momentum_line' else [0]
        st.rerun()

st.pyplot(create_battle_chart())

cols = st.columns(3)
cols[0].metric("TOTAL ROUNDS", len(st.session_state.rounds))
cols[1].progress(min(100, len(st.session_state.danger_zones)*20),
                 text=f"DANGER SCORE: {len(st.session_state.danger_zones)*20}%")

if st.session_state.danger_zones:
    st.error(f"⚠️ FIBONACCI TRAP PATTERNS DETECTED ({len(st.session_state.danger_zones)})")

# ===== UI - SECTION 2: MSI SNIPER TRACKER =====
st.title("Momentum Tracker v2: MSI + Sniper Logic")

st.subheader("Manual Round Entry (MSI Mode)")
multiplierval = st.number_input("Enter multiplier", min_value=0.01, step=0.01, key="manual_input")
if st.button("Add Round"):
    st.session_state.roundsc.append({
        "timestamp": datetime.now(),
        "multiplier": multiplierval,
        "score": 2 if multiplierval >= PINK_THRESHOLD else (1 if multiplierval >= 2 else -1)
    })

df = pd.DataFrame(st.session_state.roundsc)
if not df.empty:
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["msi"] = df["score"].rolling(WINDOW_SIZE).sum()
    df["type"] = df["multiplier"].apply(lambda x: "Pink" if x >= PINK_THRESHOLD else ("Purple" if x >= 2 else "Blue"))

    st.subheader("Recent Round Log")
    edited = st.data_editor(df.tail(30), num_rows="dynamic", use_container_width=True)
    st.session_state.roundsc = edited.to_dict('records')

    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(df["timestamp"], df["msi"], label="MSI", color="white")
    ax.axhline(0, color="gray", linestyle="--")
    ax.fill_between(df["timestamp"], df["msi"], where=(df["msi"] >= 6), color="pink", alpha=0.3, label="Burst Zone")
    ax.fill_between(df["timestamp"], df["msi"], where=(df["msi"] <= -6), color="red", alpha=0.2, label="Red Zone")
    ax.fill_between(df["timestamp"], df["msi"], where=((df["msi"] > 0) & (df["msi"] < 6)), color="#00ffff", alpha=0.3, label="Surge Zone")
    ax.legend()
    ax.set_title("Momentum Score Index (MSI)")
    st.pyplot(fig)

    st.subheader("Sniper Pink Projections")
    df["projected_by"] = None
    projections = []
    for i, row in df.iterrows():
        if row["type"] == "Pink":
            for j, prior in df.iloc[:i].iterrows():
                diff = (row["timestamp"] - prior["timestamp"]).total_seconds() / 60
                if prior["type"] == "Pink" and (8 <= diff <= 12 or 18 <= diff <= 22):
                    df.at[i, "projected_by"] = prior["timestamp"].strftime("%H:%M:%S")
                    projections.append((prior["timestamp"], row["timestamp"]))

    st.dataframe(df[df["type"] == "Pink"][["timestamp", "multiplier", "projected_by"]].tail(10))

    st.subheader("Entry Decision Assistant")
    latest_msi = df["msi"].iloc[-1]
    if latest_msi >= 6:
        st.success("✅ PINK Entry Zone")
    elif 3 <= latest_msi < 6:
        st.info("🟣 PURPLE Entry Zone")
    elif latest_msi <= -3:
        st.warning("❌ Pullback Zone - Avoid Entry")
    else:
        st.info("⏳ Neutral Zone - Wait")
else:
    st.info("Enter multipliers to begin MSI sniper tracking.")
