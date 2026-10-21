# Market Analytics: Risk and Return Across 18 US Stocks

An end-to-end data analytics project: pull market data, store it in SQL, explore it, measure risk and return, test whether sectors really differ, and publish the results as an interactive dashboard.

## Live dashboard

**[Open the dashboard](https://market-analytic.streamlit.app/)**

**[Read the case study](Case_study.md)**

The app has two tabs. _Performance_ shows growth of 100 invested, best and worst performers, and volatility, filterable by sector, stock and date range. _Risk metrics_ shows CAGR, volatility, Sharpe ratio and max drawdown for each stock, a ranking chart with a metric picker, and a statistical test of whether sectors differ in volatility.

![Dashboard screenshot](visuals/dashboard.svg)

## The question

Do stocks in different sectors carry meaningfully different risk, and does higher risk actually bring higher compounded returns?

## The data

18 US-listed stocks, 6 in each of three sectors, with daily prices from January 2019 via `yfinance` (split- and dividend-adjusted).

| Sector             | Stocks                         |
| ------------------ | ------------------------------ |
| Technology         | NVDA, AMD, MU, SNOW, CRM, DDOG |
| Healthcare         | NVS, LLY, BIIB, UNH, MOH, ALHC |
| Financial Services | JPM, WFC, BX, KKR, V, AXP      |

The basket was hand-picked, so results describe this basket, not whole sectors. SNOW, DDOG and ALHC listed later and have shorter histories.

## Method

1. **Ingest:** `scripts/fetch_data.py` downloads OHLCV data per ticker.
2. **Store:** `scripts/load_to_sql.py` loads it into a SQLite database (`symbols` and `prices` tables).
3. **Query:** SQL window functions (`LAG`, rolling `AVG`, `RANK`, CTEs) for daily returns, moving averages and rankings.
4. **Explore:** distributions, fat tails, correlations, and outlier detection with both z-scores and modified z-scores (median/MAD).
5. **Measure risk:** annualised return, CAGR, volatility, Sharpe ratio (arithmetic and CAGR-based), and maximum drawdown.
6. **Test:** do sectors differ in volatility? One value per stock, Kruskal-Wallis test, pairwise exact Mann-Whitney U tests, Holm correction for multiple comparisons.
7. **Stress-test:** rerun the sector test without NVDA, then drop each stock in turn (leave-one-out) to see how fragile the result is.
8. **Publish:** a Streamlit dashboard reading the processed CSVs.

Assumptions: 252 trading days per year and a flat 4% risk-free rate.

## Key findings

- **Compounded return is not the same as average return.** Volatile stocks lose growth to "volatility drag", so CAGR can differ a lot from the simple annualised average. The dashboard shows both, and the Sharpe ratio is computed both ways.
- **Risk-adjusted returns vary widely.** On a CAGR basis, NVDA has a Sharpe ratio of about 1.35 and LLY about 1.00, while ALHC is about -0.26.
- **Correlation within a sub-sector is high.** The semiconductor stocks (NVDA, AMD, MU) have pairwise correlations of roughly 0.57 to 0.67, so holding all three gives less diversification than holding three different sectors.
- **Sector volatility differs, but only just.** A Kruskal-Wallis test across the three sectors gives p = 0.039. After Holm correction only one pair, Technology vs Financial Services, is significant (adjusted p = 0.026).
- **The sector result is fragile.** Without NVDA, the Kruskal-Wallis p-value rises from 0.039 to 0.065 and the Technology vs Financial Services Holm-adjusted p-value from 0.026 to 0.052. NVDA is not a volatility outlier; the result is lost because six stocks per sector leaves little statistical power. It stays significant in only 9 of 18 leave-one-out runs, so I treat it as suggestive, not confirmed.

## Limitations

- Six stocks per sector gives the tests low power. Removing any single Technology stock takes the result above the 5% line (see notebook 05), and "not significant" means this basket cannot tell the sectors apart, not that they are the same.
- The basket was hand-picked and is US-only, so there is selection bias. Surviving, well-known companies tend to look better than the full universe.
- Past performance and a flat 4% risk-free rate are simplifications.
- Stocks with shorter histories (SNOW, DDOG, ALHC) are measured over different windows, so their metrics are not strictly comparable to the rest.

## Project structure

```
├── scripts/
│   ├── fetch_data.py                          # download prices from yfinance
│   ├── load_to_sql.py                         # build and fill the SQLite database
│   └── export_dashboard_data.py               # export prices for the dashboard
├── notebooks/
│   ├── 01_sql_exploration.ipynb               # Basic SQL tables queries
│   ├── 02_window_functions.ipynb              # SQL window functions
│   ├── 03_eda.ipynb                           # exploratory analysis and outliers
│   ├── 04_risk_metrics.ipynb                  # risk metrics and significance test
│   └── 05_robustness_without_nvda.ipynb       # risk metrics and significance test
├── dashboard/
│   └── app.py                                 # Streamlit app
├── data/processed/                            # CSVs used by the dashboard
├── visuals/                                   # saved charts
├── Case_study.md                              # written case study
└── requirements.txt
```

## Tools

Python, pandas, NumPy, SQLite, SciPy, Matplotlib, Seaborn, Plotly, Streamlit.
