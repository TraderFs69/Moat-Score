# moat_engine.py
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import linregress

YEARS = 5
WACC_PROXY = 0.08

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
    if slope > 1.5:
        return "🟢 Expansion"
    elif slope > -1:
        return "🟡 Stable"
    else:
        return "🔴 Érosion"
