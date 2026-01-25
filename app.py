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

# =========================
# DISCORD FUNCTIONS
# =========================

def build_top10_message(df):
    top10 = df.sort_values("MoatScore", ascending=False).head(10)

    lines = []
    for i, row in enumerate(top10.itertuples(), start=1):
        emoji = row.MoatLabel.split()[0]
        lines.append(f"{i}. **{row.Ticker}** — {row.MoatScore} {emoji}")

    return (
        "🏰 **Moat Scanner – S&P 500**\n"
        "📊 Scan complété\n\n"
        "🔝 **Top 10 – Moat Score**\n"
        + "\n".join(lines)
        + "\n\n📎 Fichier CSV complet en pièce jointe"
    )


def send_to_discord(df, csv_path):
    if not DISCORD_WEBHOOK_URL:
        return False

    message = build_top10_message(df)

    with open(csv_path, "rb") as f:
        files = {"file": ("moat_sp500.csv", f, "text/csv")}
        payload = {"content": message}
        r = requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files, timeout=20)

    return r.status_code in (200, 204)


# =========================
# SCAN FUNCTION
# =========================

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
            "MoatScore": scores[0],
            "MoatTrend": round(trend, 2),
            "MoatLabel": moat_trend_label(trend)
        })

    out = pd.DataFrame(results)
    out.to_csv(DATA_PATH, index=False)
    return out


# =========================
# UI
# =========================

if "data" not in st.session_state:
    st.session_state.data = None

col1, col2 = st.columns([1, 3])

with col1:
    start_scan = st.button("🚀 Lancer le scan S&P 500")

with col2:
    if st.session_state.data is not None:
        st.success("✅ Scan complété")

# =========================
# RUN SCAN
# =========================

if start_scan:
    progress_bar = st.progress(0)
    status = st.empty()

    with st.spinner("📊 Scan en cours…"):
        df = run_scan(progress_bar, status)
        st.session_state.data = df

    progress_bar.empty()
    status.empty()

# =========================
# LOAD EXISTING DATA
# =========================

if st.session_state.data is None and os.path.exists(DATA_PATH):
    st.session_state.data = pd.read_csv(DATA_PATH)

# =========================
# DISPLAY
# =========================

if st.session_state.data is not None:
    df = st.session_state.data

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

    filtered["CoreHolding"] = (filtered["MoatScore"] >= 80) & (filtered["MoatTrend"] > 0)

    st.subheader("📊 Résultats")
    st.dataframe(filtered.sort_values("MoatScore", ascending=False), use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Titres", len(filtered))
    col2.metric("Moat moyen", round(filtered["MoatScore"].mean(), 1))
    col3.metric("Core Holdings", filtered["CoreHolding"].sum())

    colA, colB = st.columns(2)

    with colA:
        st.download_button(
            "📥 Télécharger CSV",
            filtered.to_csv(index=False),
            "moat_filtered.csv",
            "text/csv"
        )

    with colB:
        if st.button("📨 Envoyer résumé + Top 10 sur Discord"):
            ok = send_to_discord(df, DATA_PATH)
            if ok:
                st.success("✅ Résumé + CSV envoyés sur Discord")
            else:
                st.error("❌ Erreur d’envoi Discord")

else:
    st.info("👉 Clique sur **Lancer le scan S&P 500** pour commencer.")
