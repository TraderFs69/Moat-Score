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

# =========================
# CONFIG
# =========================

st.set_page_config(page_title="Moat Scanner – S&P 500", layout="wide")
st.title("🏰 Moat Scanner – S&P 500 (Moat relatif sectoriel)")

DATA_PATH = "moat_sp500.csv"
EXCEL_PATH = "sp500_constituents.xlsx"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# =========================
# DISCORD – CONSTRUCTION MESSAGE
# =========================

def build_results_message(df, top_n=10):
    top = df.sort_values("MoatPercentile", ascending=False).head(top_n)

    lines = []
    for i, row in enumerate(top.itertuples(), start=1):
        lines.append(
            f"{i}. **{row.Ticker}** ({row.Sector}) — "
            f"{round(row.MoatPercentile,1)}% {row.MoatLabel}"
        )

    message = (
        "🏰 **Moat Scanner – S&P 500**\n"
        f"📊 Titres analysés : {len(df)}\n\n"
        f"🔝 **Top {top_n} – Moat relatif (percentile sectoriel)**\n"
        + "\n".join(lines)
        + "\n\n📎 Fichier CSV complet en pièce jointe"
    )

    return message


def send_results_to_discord(df, csv_path):
    if not DISCORD_WEBHOOK_URL:
        return False

    message = build_results_message(df)

    with open(csv_path, "rb") as f:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            data={"content": message},
            files={"file": ("moat_sp500.csv", f, "text/csv")},
            timeout=20
        )

    return response.status_code in (200, 204)

# =========================
# SCAN ENGINE (ROBUSTE)
# =========================

def run_scan(progress, status):
    tickers = pd.read_excel(EXCEL_PATH)["Symbol"].dropna().unique()
    results = []

    total = len(tickers)

    for i, ticker in enumerate(tickers):
        progress.progress((i + 1) / total)
        status.text(f"{ticker} ({i+1}/{total})")

        history = compute_moat_history(ticker)
        if history is None or history.empty:
            continue

        # Support ancien / nouveau cache
        if "YearScore" in history.columns:
            yearly_scores = history["YearScore"].tolist()
        elif "MoatScore" in history.columns:
            yearly_scores = history["MoatScore"].tolist()
        else:
            continue

        sector = history["Sector"].iloc[0] if "Sector" in history.columns else "Unknown"

        raw_score = sum(yearly_scores) / len(yearly_scores)
        trend = moat_trend(yearly_scores)

        results.append({
            "Ticker": ticker,
            "Sector": sector,
            "MoatRaw": round(raw_score, 1),
            "MoatTrend": round(trend, 2),
            "MoatLabel": moat_trend_label(trend),
        })

    df = pd.DataFrame(results)

    # ===== MOAT RELATIF (PERCENTILE SECTORIEL) =====
    df["MoatPercentile"] = (
        df.groupby("Sector")["MoatRaw"]
          .rank(pct=True) * 100
    )

    df.to_csv(DATA_PATH, index=False)
    return df

# =========================
# SESSION STATE
# =========================

if "data" not in st.session_state:
    st.session_state.data = None

# =========================
# ACTIONS
# =========================

if st.button("🚀 Lancer le scan S&P 500"):
    bar = st.progress(0)
    status = st.empty()

    with st.spinner("📊 Scan en cours…"):
        st.session_state.data = run_scan(bar, status)

    bar.empty()
    status.empty()

# Charger CSV existant si présent
if st.session_state.data is None and os.path.exists(DATA_PATH):
    st.session_state.data = pd.read_csv(DATA_PATH)

# =========================
# AFFICHAGE + DISCORD
# =========================

if st.session_state.data is not None:
    df = st.session_state.data

    st.sidebar.header("Filtres")

    min_pct = st.sidebar.slider(
        "Moat percentile minimum (vs secteur)",
        0, 100, 80
    )

    trend_choice = st.sidebar.multiselect(
        "Tendance du Moat",
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
    col2.metric(
        "Percentile moyen",
        round(filtered["MoatPercentile"].mean(), 1) if len(filtered) else 0
    )
    col3.metric("Core Holdings", filtered["CoreHolding"].sum())

    st.divider()

    # ===== BOUTON DISCORD =====
    if st.button("📨 Envoyer les résultats sur Discord"):
        ok = send_results_to_discord(df, DATA_PATH)
        if ok:
            st.success("✅ Résultats envoyés sur Discord")
        else:
            st.error("❌ Envoi Discord impossible")

else:
    st.info("👉 Clique sur **Lancer le scan S&P 500** pour commencer.")
