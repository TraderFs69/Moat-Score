# app.py
import streamlit as st
import pandas as pd
import os
from moat_engine import compute_sp500_moat

st.set_page_config(page_title="Moat Scanner – S&P 500", layout="wide")
st.title("🏰 Moat Scanner – S&P 500")

DATA_PATH = "moat_sp500.csv"

progress_bar = st.progress(0)
status = st.empty()

def progress_callback(current, total, ticker):
    progress_bar.progress(current / total)
    status.text(f"Analyse {ticker} ({current}/{total})")

@st.cache_data(show_spinner=False)
def load_data():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)

    st.warning("📊 Calcul initial en cours (1 seule fois)…")
    df = compute_sp500_moat(progress_callback)
    df.to_csv(DATA_PATH, index=False)
    return df

df = load_data()

st.success("✅ Données prêtes")

# =========================
# FILTRES
# =========================

st.sidebar.header("Filtres")

min_score = st.sidebar.slider("Moat Score minimum", 0, 100, 70)
trend_choice = st.sidebar.multiselect(
    "Moat Trend",
    ["🟢 Expansion", "🟡 Stable", "🔴 Érosion"],
    default=["🟢 Expansion", "🟡 Stable"]
)

filtered = df[
    (df["MoatScore"] >= min_score) &
    (df["MoatLabel"].isin(trend_choice))
]

# Core Holding
filtered["CoreHolding"] = (filtered["MoatScore"] >= 80) & (filtered["MoatTrend"] > 0)

# =========================
# AFFICHAGE
# =========================

st.subheader("📊 Résultats")
st.dataframe(
    filtered.sort_values("MoatScore", ascending=False),
    use_container_width=True
)

col1, col2, col3 = st.columns(3)
col1.metric("Titres", len(filtered))
col2.metric("Moat moyen", round(filtered["MoatScore"].mean(), 1))
col3.metric("Core Holdings", filtered["CoreHolding"].sum())

st.download_button(
    "📥 Télécharger CSV",
    filtered.to_csv(index=False),
    "moat_filtered.csv",
    "text/csv"
)
