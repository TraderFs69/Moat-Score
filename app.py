# app.py
import streamlit as st
import pandas as pd
import os
import requests

from moat_engine import (
    compute_moat_history,
    moat_trend,
    moat_trend_label,
)

st.set_page_config(page_title="Moat Scanner – S&P 500", layout="wide")
st.title("🏰 Moat Scanner – S&P 500 (Relative Moat)")

DATA_PATH = "moat_sp500.csv"
EXCEL_PATH = "sp500_constituents.xlsx"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# =========================
# SCAN
# =========================

def run_scan(progress, status):
    tickers = pd.read_excel(EXCEL_PATH)["Symbol"].dropna().unique()
    results = []

    for i, ticker in enumerate(tickers):
        progress.progress((i + 1) / len(tickers))
        status.text(f"{ticker} ({i+1}/{len(tickers)})")

        history = compute_moat_history(ticker)
        if history is None or history.empty:
            continue

        scores = history["YearScore"].tolist()
        sector = history["Sector"].iloc[0]

        results.append({
            "Ticker": ticker,
            "Sector": sector,
            "MoatRaw": round(sum(scores) / len(scores), 1),
            "MoatTrend": moat_trend(scores),
            "MoatLabel": moat_trend_label(moat_trend(scores)),
        })

    df = pd.DataFrame(results)

    # 🔥 MOAT RELATIF PAR SECTEUR
    df["MoatPercentile"] = (
        df.groupby("Sector")["MoatRaw"]
          .rank(pct=True) * 100
    )

    df.to_csv(DATA_PATH, index=False)
    return df

# =========================
# UI
# =========================

if "data" not in st.session_state:
    st.session_state.data = None

if st.button("🚀 Lancer le scan S&P 500"):
    bar = st.progress(0)
    status = st.empty()
    st.session_state.data = run_scan(bar, status)
    bar.empty()
    status.empty()

if st.session_state.data is None and os.path.exists(DATA_PATH):
    st.session_state.data = pd.read_csv(DATA_PATH)

if st.session_state.data is not None:
    df = st.session_state.data

    st.sidebar.header("Filtres")

    min_pct = st.sidebar.slider(
        "Moat percentile (vs secteur)",
        0, 100, 80
    )

    trend_choice = st.sidebar.multiselect(
        "Tendance",
        ["🟢 Expansion", "🟡 Stable", "🔴 Érosion"],
        default=["🟢 Expansion", "🟡 Stable"],
    )

    filtered = df[
        (df["MoatPercentile"] >= min_pct) &
        (df["MoatLabel"].isin(trend_choice))
    ]

    filtered["CoreHolding"] = filtered["MoatPercentile"] >= 90

    st.subheader("📊 Résultats – Moat relatif sectoriel")
    st.dataframe(
        filtered.sort_values("MoatPercentile", ascending=False),
        use_container_width=True,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Titres retenus", len(filtered))
    col2.metric("Percentile moyen", round(filtered["MoatPercentile"].mean(), 1) if len(filtered) else 0)
    col3.metric("Core Holdings", filtered["CoreHolding"].sum())

else:
    st.info("👉 Clique sur **Lancer le scan S&P 500** pour commencer.")
