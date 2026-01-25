# app.py
import streamlit as st
import pandas as pd
import os
import requests

from moat_engine import (
    compute_moat_history,
    compute_final_moat_score,
    moat_trend,
    moat_trend_label,
)

# =========================
# CONFIG
# =========================

st.set_page_config(page_title="Moat Scanner – S&P 500", layout="wide")
st.title("🏰 Moat Scanner – S&P 500")

DATA_PATH = "moat_sp500.csv"
EXCEL_PATH = "sp500_constituents.xlsx"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# =========================
# DISCORD
# =========================

def build_top10_message(df):
    top10 = df.sort_values("MoatScore", ascending=False).head(10)

    lines = []
    for i, row in enumerate(top10.itertuples(), start=1):
        lines.append(
            f"{i}. **{row.Ticker}** — {round(row.MoatScore,1)} {row.MoatLabel.split()[0]}"
        )

    return (
        "🏰 **Moat Scanner – S&P 500**\n"
        "📊 Scan complété\n\n"
        "🔝 **Top 10 – Moat long terme**\n"
        + "\n".join(lines)
        + "\n\n📎 CSV complet en pièce jointe"
    )


def send_to_discord(df):
    if not DISCORD_WEBHOOK_URL:
        return False

    with open(DATA_PATH, "rb") as f:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            data={"content": build_top10_message(df)},
            files={"file": ("moat_sp500.csv", f, "text/csv")},
            timeout=20,
        )

    return response.status_code in (200, 204)

# =========================
# SCAN ENGINE (ROBUSTE)
# =========================

def run_scan(progress_bar, status_text):
    df = pd.read_excel(EXCEL_PATH)
    tickers = df["Symbol"].dropna().unique()

    results = []
    total = len(tickers)

    for i, ticker in enumerate(tickers):
        progress_bar.progress((i + 1) / total)
        status_text.text(f"Analyse {ticker} ({i+1}/{total})")

        history = compute_moat_history(ticker)
        if history is None or history.empty:
            continue

        # ✅ Supporte ANCIEN cache (MoatScore) et NOUVEAU (YearScore)
        if "YearScore" in history.columns:
            yearly_scores = history["YearScore"].tolist()
        elif "MoatScore" in history.columns:
            yearly_scores = history["MoatScore"].tolist()
        else:
            continue

        final_score = compute_final_moat_score(yearly_scores)
        trend = moat_trend(yearly_scores)

        results.append(
            {
                "Ticker": ticker,
                "MoatScore": final_score,
                "MoatTrend": round(trend, 2),
                "MoatLabel": moat_trend_label(trend),
            }
        )

    out = pd.DataFrame(results)
    out.to_csv(DATA_PATH, index=False)
    return out

# =========================
# SESSION STATE
# =========================

if "data" not in st.session_state:
    st.session_state.data = None

# =========================
# ACTIONS
# =========================

if st.button("🚀 Lancer le scan S&P 500"):
    progress_bar = st.progress(0)
    status_text = st.empty()

    with st.spinner("📊 Scan en cours (Moat long terme)…"):
        st.session_state.data = run_scan(progress_bar, status_text)

    progress_bar.empty()
    status_text.empty()

# Charger un CSV existant si présent
if st.session_state.data is None and os.path.exists(DATA_PATH):
    st.session_state.data = pd.read_csv(DATA_PATH)

# =========================
# AFFICHAGE
# =========================

if st.session_state.data is not None:
    df = st.session_state.data

    st.sidebar.header("Filtres")

    min_score = st.sidebar.slider(
        "Moat Score minimum",
        0,
        100,
        60,
    )

    trend_choice = st.sidebar.multiselect(
        "Tendance du Moat",
        ["🟢 Expansion", "🟡 Stable", "🔴 Érosion"],
        default=["🟢 Expansion", "🟡 Stable"],
    )

    filtered = df[
        (df["MoatScore"] >= min_score)
        & (df["MoatLabel"].isin(trend_choice))
    ]

    filtered["CoreHolding"] = (
        (filtered["MoatScore"] >= 75) & (filtered["MoatTrend"] > 0)
    )

    st.subheader("📊 Résultats – Moat long terme")
    st.dataframe(
        filtered.sort_values("MoatScore", ascending=False),
        use_container_width=True,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Titres retenus", len(filtered))
    col2.metric(
        "Moat moyen",
        round(filtered["MoatScore"].mean(), 1) if len(filtered) else 0,
    )
    col3.metric("Core Holdings", filtered["CoreHolding"].sum())

    colA, colB = st.columns(2)

    with colA:
        st.download_button(
            "📥 Télécharger le CSV filtré",
            filtered.to_csv(index=False),
            "moat_filtered.csv",
            "text/csv",
        )

    with colB:
        if st.button("📨 Envoyer Top 10 + CSV sur Discord"):
            if send_to_discord(df):
                st.success("✅ Résumé + CSV envoyés sur Discord")
            else:
                st.error("❌ Envoi Discord impossible")

else:
    st.info("👉 Clique sur **Lancer le scan S&P 500** pour commencer.")
