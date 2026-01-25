import streamlit as st
import pandas as pd
from moat_engine import moat_trend, moat_trend_label

st.set_page_config(page_title="Moat Scanner – S&P 500", layout="wide")

st.title("🏰 Moat Scanner – S&P 500")
st.caption("Moat Score • Moat Trend • Core Holdings")

# =========================
# LOAD DATA
# =========================

@st.cache_data
def load_data():
    return pd.read_csv("output/moat_sp500.csv")

df = load_data()

# =========================
# SIDEBAR FILTERS
# =========================

st.sidebar.header("Filtres")

min_moat = st.sidebar.slider("Moat Score minimum", 0, 100, 70)
trend_filter = st.sidebar.multiselect(
    "Moat Trend",
    ["🟢 Expansion", "🟡 Stable", "🔴 Érosion"],
    default=["🟢 Expansion", "🟡 Stable"]
)

# =========================
# COMPUTED LABELS
# =========================

df["MoatLabel"] = df["MoatTrend"].apply(moat_trend_label)

filtered = df[
    (df["MoatScore"] >= min_moat) &
    (df["MoatLabel"].isin(trend_filter))
]

# =========================
# CORE HOLDING LOGIC
# =========================

filtered["CoreHolding"] = (
    (filtered["MoatScore"] >= 80) &
    (filtered["MoatTrend"] > 0)
)

# =========================
# DISPLAY
# =========================

st.subheader("📊 Résultats filtrés")

st.dataframe(
    filtered.sort_values("MoatScore", ascending=False),
    use_container_width=True
)

# =========================
# SUMMARY
# =========================

col1, col2, col3 = st.columns(3)

col1.metric("Titres sélectionnés", len(filtered))
col2.metric("Moat moyen", round(filtered["MoatScore"].mean(), 1))
col3.metric("Core Holdings", filtered["CoreHolding"].sum())

# =========================
# DOWNLOAD
# =========================

st.download_button(
    "📥 Télécharger en CSV",
    filtered.to_csv(index=False),
    file_name="moat_filtered.csv",
    mime="text/csv"
)
