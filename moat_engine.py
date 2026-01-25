# moat_engine.py
import yfinance as yf
import pandas as pd
import numpy as np
import os
import time
from scipy.stats import linregress

YEARS = 5
WACC_PROXY = 0.08
CACHE_DIR = "moat_cache"

os.makedirs(CACHE_DIR, exist_ok=True)

SECTOR_RULES = {
    "Technology": {"rd_high": 0.06, "capex_low": 0.08, "roe_good": 0.15, "margin_std_good": 0.10},
    "Healthcare": {"rd_high": 0.08, "capex_low": 0.10, "roe_good": 0.12, "margin_std_good": 0.12},
    "Consumer Defensive": {"rd_high": 0.02, "capex_low": 0.12, "roe_good": 0.14, "margin_std_good": 0.08},
    "Industrials": {"rd_high": 0.03, "capex_low": 0.15, "roe_good": 0.13, "margin_std_good": 0.12},
    "Financial Services": {"rd_high": 0.00, "capex_low": 0.05, "roe_good": 0.14, "margin_std_good": 0.15},
    "Utilities": {"rd_high": 0.00, "capex_low": 0.20, "roe_good": 0.10, "margin_std_good": 0.05},
}

DEFAULT_RULES = {"rd_high": 0.04, "capex_low": 0.12, "roe_good": 0.13, "margin_std_good": 0.10}


# =========================
# TREND
# =========================

def moat_trend(scores):
    if len(scores) < 3:
        return 0
    x = np.arange(len(scores))
    slope, _, _, _, _ = linregress(x, scores)
    return slope


def moat_trend_label(slope):
    if slope > 1.5:
        return "🟢 Expansion"
    elif slope > -1:
        return "🟡 Stable"
    else:
        return "🔴 Érosion"


# =========================
# CORE CALCULATIONS
# =========================

def compute_moat_history(ticker):
    cache_path = f"{CACHE_DIR}/{ticker}.csv"
    if os.path.exists(cache_path):
        return pd.read_csv(cache_path)

    stock = yf.Ticker(ticker)

    income = stock.financials
    balance = stock.balance_sheet
    cashflow = stock.cashflow
    info = stock.info

    if income.empty or balance.empty or cashflow.empty:
        return None

    sector = info.get("sector", "Unknown")
    rules = SECTOR_RULES.get(sector, DEFAULT_RULES)

    years_available = min(YEARS, income.shape[1])
    scores = []

    for i in range(years_available):
        try:
            revenue = income.loc["Total Revenue"].iloc[i]
            op_income = income.loc["Operating Income"].iloc[i]
            net_income = income.loc["Net Income"].iloc[i]
            equity = balance.loc["Stockholders Equity"].iloc[i]
            debt = balance.loc["Total Debt"].iloc[i]

            fcf = cashflow.loc["Free Cash Flow"].iloc[i]
            capex = abs(cashflow.loc["Capital Expenditure"].iloc[i])

            rd = income.loc["Research Development"].iloc[i] if "Research Development" in income.index else 0

            margin = op_income / revenue if revenue != 0 else 0
            roe = net_income / equity if equity != 0 else 0
            capex_ratio = capex / revenue if revenue != 0 else 1
            rd_ratio = rd / revenue if revenue != 0 else 0

            score = 0

            # Rentabilité
            score += 6 if op_income > 0 else 0
            score += 6 if fcf > 0 else 0
            score += 8 if abs(margin) < rules["margin_std_good"] else 4

            # Avantage structurel
            score += 8 if roe > rules["roe_good"] else 4
            score += 7 if rd_ratio > rules["rd_high"] else 0
            score += 6 if capex_ratio < rules["capex_low"] else 3

            # Résilience
            score += 4 if debt / equity < 0.5 else 2

            scores.append(score)

        except Exception:
            continue

    df = pd.DataFrame({
        "YearIndex": list(range(len(scores))),
        "MoatScore": scores
    })

    df.to_csv(cache_path, index=False)
    time.sleep(0.2)  # limite Yahoo

    return df


# =========================
# SP500 RUNNER
# =========================

def compute_sp500_moat(progress_callback=None):
    df = pd.read_excel("sp500_constituents.xlsx")
    tickers = df["Symbol"].dropna().unique()

    results = []

    total = len(tickers)

    for i, ticker in enumerate(tickers):
        if progress_callback:
            progress_callback(i + 1, total, ticker)

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

    return pd.DataFrame(results)
