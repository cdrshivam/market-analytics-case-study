import yfinance as yf
import pandas as pd
import os

TICKERS = {
    "NVDA": {"sector": "Technology", "sub_sector": "Semiconductors"},
    "AMD": {"sector": "Technology", "sub_sector": "Semiconductors"},
    "MU": {"sector": "Technology", "sub_sector": "Semiconductors"},
    "SNOW": {"sector": "Technology", "sub_sector": "Software"},
    "CRM": {"sector": "Technology", "sub_sector": "Software"},
    "DDOG": {"sector": "Technology", "sub_sector": "Software"},

    "NVS": {"sector": "Healthcare", "sub_sector": "Drug Manufacturers"},
    "LLY": {"sector": "Healthcare", "sub_sector": "Drug Manufacturers"},
    "BIIB": {"sector": "Healthcare", "sub_sector": "Drug Manufacturers"},
    "UNH": {"sector": "Healthcare", "sub_sector": "Healthcare Plans"},
    "MOH": {"sector": "Healthcare", "sub_sector": "Healthcare Plans"},
    "ALHC": {"sector": "Healthcare", "sub_sector": "Healthcare Plans"},

    "JPM": {"sector": "Financial Services", "sub_sector": "Banks"},
    "WFC": {"sector": "Financial Services", "sub_sector": "Banks"},
    "BX": {"sector": "Financial Services", "sub_sector": "Asset Management"},
    "KKR": {"sector": "Financial Services", "sub_sector": "Asset Management"},
    "V": {"sector": "Financial Services", "sub_sector": "Credit Services"},
    "AXP": {"sector": "Financial Services", "sub_sector": "Credit Services"},
}

START_DATE = "2019-01-01"

RAW_DATA_DIR = "data/raw"
os.makedirs(RAW_DATA_DIR, exist_ok=True)


def fetch_and_save (ticker, start_date, output_dir):
    print(f"Fetching {ticker}...")
    data = yf.download(ticker, start=start_date)
    if data.empty:
        print(f"Warning: No data returned for {ticker}")
        return
    data.columns = data.columns.get_level_values(0)
    filepath = os.path.join(output_dir, f"{ticker}.csv")
    data.to_csv(filepath)
    print(f"Saved {len(data)} rows to {filepath}")


if __name__ == "__main__":
    for ticker in TICKERS:
        fetch_and_save(ticker, START_DATE, RAW_DATA_DIR)
    print("\n DONE! All tickers processed")


