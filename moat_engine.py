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
    "Technology": {"rd_high": 0.05, "capex_low": 0.10, "roe_good": 0.15},
    "Healthcare": {"rd_high": 0.07, "capex_low": 0.12, "roe_good": 0.12},
    "Consumer Defensive": {"rd_high": 0.02, "capex_low": 0.15, "roe_good": 0.14},
    "Industrials": {"rd_high": 0.03, "capex_low": 0.18, "roe_good": 0.13},
    "Financial Services": {"rd_high": 0.00, "capex_low": 0.08, "roe_good": 0.14},
    "Utilities": {"rd_high": 0.00, "capex_low": 0.25, "roe_good": 0.10},
}
DEFAULT_RULES = {"rd_high": 0.03, "capex_low": 0.15, "roe_good": 0.13}


def moat_trend(scores):
    if len(scores) < 3:
        return 0
    x = np.arange(len(scores))
    slope, _, _, _, _ = linregress(x, scores)
    return slope


def moat_trend_label(slope):
    if slope > 0.5:
        return "🟢 Expansion"
    elif slope > -0.3:
        return "🟡 Stable"
    else:
        return "🔴 Érosion"


def compute_moat_history(ticker):
    cache_path = f"{CACHE_DIR}/{ticker}.csv"
    if os.path.exists(cache_path):
        return pd.read_csv(cache_path)

   try:
    stock = yf.Ticker(ticker)

    income = stock.financials
    balance = stock.balance_sheet
    cashflow = stock.cashflow
    info = stock.info

except Exception as e:
    print(f"{ticker}: {e}")
    return None

if income.empty or "Total Revenue" not in income.index:
    return None

    sector = info.get("sector", "Unknown")
    rules = SECTOR_RULES.get(sector, DEFAULT_RULES)

    yearly_scores = []
    years = min(YEARS, income.shape[1])

    for i in range(years):
        try:
            revenue = income.loc["Total Revenue"].iloc[i]
            op_income = income.loc["Operating Income"].iloc[i] if "Operating Income" in income.index else 0
            net_income = income.loc["Net Income"].iloc[i] if "Net Income" in income.index else 0

            equity = balance.loc["Stockholders Equity"].iloc[i] if "Stockholders Equity" in balance.index else 1
            debt = balance.loc["Total Debt"].iloc[i] if "Total Debt" in balance.index else 0

            fcf = cashflow.loc["Free Cash Flow"].iloc[i] if "Free Cash Flow" in cashflow.index else 0
            capex = abs(cashflow.loc["Capital Expenditure"].iloc[i]) if "Capital Expenditure" in cashflow.index else 0
            rd = income.loc["Research Development"].iloc[i] if "Research Development" in income.index else 0

            margin = op_income / revenue if revenue else 0
            roe = net_income / equity if equity else 0
            rd_ratio = rd / revenue if revenue else 0
            capex_ratio = capex / revenue if revenue else 1

            score = 0
            score += 15 if op_income > 0 else 5
            score += 15 if fcf > 0 else 5
            score += 15 if margin > 0.15 else 8
            score += 15 if roe > rules["roe_good"] else 8
            score += 10 if rd_ratio > rules["rd_high"] else 5
            score += 10 if capex_ratio < rules["capex_low"] else 5
            score += 10 if debt / equity < 1 else 5

            yearly_scores.append(score)

        except Exception:
            continue

    if not yearly_scores:
        return None

    df = pd.DataFrame({"YearScore": yearly_scores})
    df["Sector"] = sector
    df.to_csv(cache_path, index=False)
    time.sleep(0.50)
    return df
