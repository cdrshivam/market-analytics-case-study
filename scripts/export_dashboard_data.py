import sqlite3
import pandas as pd

conn = sqlite3.connect("market_data.db")

query = """
SELECT prices.ticker, prices.date, prices.close, prices.volume,
       symbols.sector, symbols.sub_sector
FROM prices
JOIN symbols ON prices.ticker = symbols.ticker
"""
df = pd.read_sql(query, conn)
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values(["ticker", "date"])
df["daily_return"] = df.groupby("ticker")["close"].pct_change()

df["close"] = df["close"].round(4)
df["daily_return"] = df["daily_return"].round(6)

df.to_csv("data/processed/dashboard_prices.csv", index=False)
print(f"Exported {len(df):,} rows")
