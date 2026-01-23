import yfinance as yf
import numpy as np

prices = (
    yf.Ticker("SPY")
    .history(period="max")["Close"]
    .dropna()
)

daily_returns = prices.pct_change().dropna()
annual_risk_pct = daily_returns.std() * np.sqrt(252) * 100

avg_annual_return = daily_returns.mean() * 25

print(f"Annual risk percentage: {annual_risk_pct:.2f}%")