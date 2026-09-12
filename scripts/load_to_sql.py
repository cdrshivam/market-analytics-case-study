import pandas as pd
import sqlite3
import os

DB_PATH = "market_data.db"
RAW_DATA_DIR = "data/raw"

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

def create_tables(conn):
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS symbols (
            ticker TEXT PRIMARY KEY,
            sector TEXT,
            sub_sector TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            ticker TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            FOREIGN KEY (ticker) REFERENCES symbols(ticker)
        )
    """)

    conn.commit()
    print("Symbols and prices tables created successfully.")


def load_symbols(conn):
    cursor = conn.cursor()
    for ticker, info in TICKERS.items():
        cursor.execute("""
            INSERT OR REPLACE INTO symbols (ticker, sector, sub_sector)
            VALUES (?, ?, ?)
        """, (ticker, info["sector"], info["sub_sector"]))
    conn.commit()
    print(f"Loaded {len(TICKERS)} symbols.")


def load_prices(conn):

    cursor = conn.cursor()
    cursor.execute("DELETE FROM prices")
    conn.commit()

    for ticker in TICKERS:
        filepath = os.path.join(RAW_DATA_DIR, f"{ticker}.csv")

        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found, skipping.")
            continue

        df = pd.read_csv(filepath)
        df["ticker"] = ticker
        df = df.rename(columns={
            "Date": "date", "Open": "open", "High": "high",
            "Low": "low", "Close": "close", "Volume": "volume"
        })

        df = df[["ticker", "date", "open", "high", "low", "close", "volume"]]
        df.to_sql("prices", conn, if_exists="append", index=False)
        print(f"Loaded {len(df)} rows for {ticker}.")

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    load_symbols(conn)
    load_prices(conn)
    conn.close()
    print("\nDatabase build complete.")





