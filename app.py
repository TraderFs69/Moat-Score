# app.py
import streamlit as st
import pandas as pd
import os
import requests

from moat_engine import compute_moat_history, moat_trend, moat_trend_label

st.set_page_config(page_title="Moat Scanner – S&P 500", layout="wide")
st.title("🏰 Moat Scanner – S&P 500")

DATA_PATH = "moat_sp500.csv"
EXCEL_PATH = "sp500_constituents.xlsx"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def build_top10_message(df):
    top10 = df.sort_values("MoatScore", ascending=False).head(10)
    lines = []
    for i, row in enumerate(top10.itertuples(), start=1):
        lines.append(f"{i}. **{row.Ticker}** — {row.MoatScore} {row.MoatLabel.split()[0]}")

    return (
        "🏰 **Moat Scanner – S&P 500**\n"
        "📊 Scan complété\n\n"
        "🔝 **Top 10 – Moat Score**\n"
        + "\n".join(lines)
        + "\n\n📎 CSV complet en pièce jointe"
    )


def send_to_discord(df, csv_path):
    if not DISCORD_WEBHOOK_URL:
        return False

    with open(csv_path, "rb") as f:
        r = requests.post(
            DISCORD_WEBHOOK_URL,
            data={"content": build_top10_message(df)},
            files={"file": ("moat_sp500.csv", f, "text/csv")},
            timeout=20
        )

    return r.status_code in (200, 204)


def run_scan(progress_bar, status):
    df = pd.read_excel(EXCEL_PATH)
    tickers = df["Symbol"].dropna().unique()

    results = []
    total = len(tickers)

    for i, ticker in enumerate(tickers):
        progress_bar.progress((i + 1) / total)
        status.text(f"Analyse {ticker} ({i+1}/{total})")

        history = compute_moat_history(ticker)
        if history is None or history.empty:
            continue

        scores = history["MoatScore"].tolist()
        trend = moat_trend(scores)

        results.append({
            "Ticker": ticker,
            "MoatScore": round(scores[0], 1),
            "MoatTrend": round(trend, 2),
            "MoatLabel": moat_trend_label(trend)
        })

    out = pd.DataFrame(results)
    out.to_csv(DATA_PATH, index=False)
    return out


if "data" not in st.session_state:
    st.session_state.data = None

if st.button("🚀 Lancer le scan S&P 500"):
    progress_bar = st.progress(0)
    status = st.empty()
    with st.spinner("📊 Scan en cours…"):
        st.session_state.data = run_scan(progress_bar, status)
    progress_bar.empty()
    status.empty()

if st.session_state.data is None and os.path.exists(DATA_PATH):
    st.session_state.data = pd.read_csv(DATA_PATH)

if st.session_state.data is not None:
    df = st.session_state.data

    st.sidebar.header("Filtres")
    min_score = st.sidebar.slider("Moat Score minimum", 0, 100, 40)
    trend_choice = st.sidebar.multiselect(
        "Moat Trend",
        ["🟢 Expansion", "🟡 Stable", "🔴 Érosion"],
        default=["🟢 Expansion", "🟡 Stable", "🔴 Érosion"]
    )

    filtered = df[
        (df["MoatScore"] >= min_score) &
        (df["MoatLabel"].isin(trend_choice))
    ]

    filtered["CoreHolding"] = (filtered["MoatScore"] >= 80) & (filtered["MoatTrend"] > 0)

    st.subheader("📊 Résultats")
    st.dataframe(filtered.sort_values("MoatScore", ascending=False), use_container_width=True)

    if st.button("📨 Envoyer Top 10 + CSV sur Discord"):
        if send_to_discord(df, DATA_PATH):
            st.success("✅ Envoyé sur Discord")
        else:
            st.error("❌ Erreur Discord")
else:
    st.info("👉 Clique sur **Lancer le scan S&P 500** pour commencer.")
