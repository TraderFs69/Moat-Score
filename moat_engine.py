# moat_engine.py
import yfinance as yf
import pandas as pd
import numpy as np
import os
import time
from scipy.stats import linregress

YEARS = 5
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


def moat_trend(scores):
    if len(scores) < 3:
        return 0
    x = np.arange(len(scores))
    slope, _, _, _, _ = linregress(x, scores)
    return slope


def moat_trend_label(slope):
    if slope > 1:
        return "🟢 Expansion"
    elif slope > -0.5:
        return "🟡 Stable"
    else:
        return "🔴 Érosion"


def compute_moat_history(ticker):
    cache_path = f"{CACHE_DIR}/{ticker}.csv"
    if os.path.exists(cache_path):
        return pd.read_csv(cache_path)

    stock = yf.Ticker(ticker)

    income = stock.financials
    balance = stock.balance_sheet
    cashflow = stock.cashflow
    info = stock.info

    # ⬇️ CORRECTION 1 : seulement le revenu est obligatoire
    if income.empty or "Total Revenue" not in income.index:
        return None

    sector = info.get("sector", "Unknown")
    rules = SECTOR_RULES.get(sector, DEFAULT_RULES)

    scores = []
    years = min(YEARS, income.shape[1])

    for i in range(years):
        try:
            revenue = income.loc["Total Revenue"].iloc[i]

            op_income = income.loc["Operating Income"].iloc[i] if "Operating Income" in income.index else 0
            net_income = income.loc["Net Income"].iloc[i] if "Net Income" in income.index else 0

            equity = (
                balance.loc["Stockholders Equity"].iloc[i]
                if not balance.empty and "Stockholders Equity" in balance.index
                else 1
            )

            debt = (
                balance.loc["Total Debt"].iloc[i]
                if not balance.empty and "Total Debt" in balance.index
                else 0
            )

            fcf = (
                cashflow.loc["Free Cash Flow"].iloc[i]
                if not cashflow.empty and "Free Cash Flow" in cashflow.index
                else 0
            )

            capex = (
                abs(cashflow.loc["Capital Expenditure"].iloc[i])
                if not cashflow.empty and "Capital Expenditure" in cashflow.index
                else 0
            )

            rd = (
                income.loc["Research Development"].iloc[i]
                if "Research Development" in income.index
                else 0
            )

            margin = op_income / revenue if revenue else 0
            roe = net_income / equity if equity else 0
            capex_ratio = capex / revenue if revenue else 1
            rd_ratio = rd / revenue if revenue else 0

            score = 0
            score += 5 if op_income > 0 else 2
            score += 5 if fcf > 0 else 2
            score += 8 if abs(margin) < rules["margin_std_good"] else 4
            score += 8 if roe > rules["roe_good"] else 4
            score += 7 if rd_ratio > rules["rd_high"] else 3
            score += 6 if capex_ratio < rules["capex_low"] else 3
            score += 4 if equity and debt / equity < 0.8 else 2

            scores.append(score)

        except Exception:
            continue

    if not scores:
        return None

    df = pd.DataFrame({"MoatScore": scores})

    # ⬇️ CORRECTION 2 : jamais de score nul
    df["MoatScore"] = df["MoatScore"].clip(lower=10)

    df.to_csv(cache_path, index=False)
    time.sleep(0.15)

    return df
