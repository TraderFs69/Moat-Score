import os
import pandas as pd
import requests

from moat_engine import (
    compute_moat_history,
    moat_trend,
    moat_trend_label,
)

DATA_PATH = "moat_sp500.csv"
EXCEL_PATH = "sp500_constituents.xlsx"

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def build_results_message(df, top_n=10):

    top = (
        df.sort_values(
            "MoatPercentile",
            ascending=False
        )
        .head(top_n)
    )

    lines = []

    for i, row in enumerate(top.itertuples(), start=1):

        lines.append(
            f"{i}. **{row.Ticker}** ({row.Sector}) — "
            f"{round(row.MoatPercentile,1)}% {row.MoatLabel}"
        )

    return (
        "🏰 **Moat Scanner – S&P 500**\n"
        f"📊 Titres analysés : {len(df)}\n\n"
        f"🔝 Top {top_n}\n"
        + "\n".join(lines)
        + "\n\n📎 CSV complet en pièce jointe"
    )


def send_results_to_discord(df, csv_path):

    if not DISCORD_WEBHOOK_URL:
        print("Webhook Discord manquant")
        return False

    message = build_results_message(df)

    with open(csv_path, "rb") as f:

        response = requests.post(
            DISCORD_WEBHOOK_URL,
            data={"content": message},
            files={
                "file": (
                    "moat_sp500.csv",
                    f,
                    "text/csv"
                )
            },
            timeout=30
        )

    print("Discord:", response.status_code)

    return response.status_code in (200, 204)


def run_scan():

    tickers = (
        pd.read_excel(EXCEL_PATH)["Symbol"]
        .dropna()
        .unique()
    )

    results = []

    total = len(tickers)

    for i, ticker in enumerate(tickers):

        print(f"{ticker} ({i+1}/{total})")

        history = compute_moat_history(ticker)

        if history is None or history.empty:
            continue

        if "YearScore" in history.columns:
            yearly_scores = history["YearScore"].tolist()
        elif "MoatScore" in history.columns:
            yearly_scores = history["MoatScore"].tolist()
        else:
            continue

        sector = (
            history["Sector"].iloc[0]
            if "Sector" in history.columns
            else "Unknown"
        )

        raw_score = (
            sum(yearly_scores)
            / len(yearly_scores)
        )

        trend = moat_trend(yearly_scores)

        results.append({
            "Ticker": ticker,
            "Sector": sector,
            "MoatRaw": round(raw_score, 1),
            "MoatTrend": round(trend, 2),
            "MoatLabel": moat_trend_label(trend),
        })

    df = pd.DataFrame(results)

    df["MoatPercentile"] = (
        df.groupby("Sector")["MoatRaw"]
        .rank(pct=True)
        * 100
    )

    df.to_csv(
        DATA_PATH,
        index=False
    )

    return df


if __name__ == "__main__":

    print("Début du scan Moat")

    df = run_scan()

    print(
        f"{len(df)} résultats trouvés"
    )

    ok = send_results_to_discord(
        df,
        DATA_PATH
    )

    if ok:
        print("Discord OK")
    else:
        print("Erreur Discord")
