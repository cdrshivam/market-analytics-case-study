from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from scipy import stats

st.set_page_config(page_title="Market Analytics Dashboard", layout="wide")

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
SECTOR_COLORS = {"Technology": "#1f77b4", "Healthcare": "#ff7f0e", "Financial Services": "#2ca02c"}


@st.cache_data
def load_prices():
    return pd.read_csv(DATA_DIR / "dashboard_prices.csv", parse_dates=["date"])


@st.cache_data
def load_metrics():
    return pd.read_csv(DATA_DIR / "risk_metrics.csv")


@st.cache_data
def sector_volatility_tests(m):
    """Same test as notebook 04, section 5: one annualised-volatility value per stock."""
    groups = {s: g["ann_vol"].to_numpy() for s, g in m.groupby("sector")}
    h_stat, p_kw = stats.kruskal(*groups.values())

    pairs = [("Technology", "Financial Services"), ("Technology", "Healthcare"), ("Healthcare", "Financial Services")]
    rows = []
    for a, b in pairs:
        u, p = stats.mannwhitneyu(groups[a], groups[b], alternative="two-sided", method="exact")
        rows.append({
            "Comparison": f"{a} vs {b}",
            "Median vol A (%)": pd.Series(groups[a]).median(),
            "Median vol B (%)": pd.Series(groups[b]).median(),
            "p (raw)": p,
            "Effect size": 2 * u / (len(groups[a]) * len(groups[b])) - 1,
        })
    res = pd.DataFrame(rows)

    # Holm correction: smallest p x 3, next x 2, largest x 1; adjusted values never decrease
    running_max, holm = 0, {}
    for rank, idx in enumerate(res["p (raw)"].sort_values().index):
        running_max = max(running_max, min(1, (len(res) - rank) * res.loc[idx, "p (raw)"]))
        holm[idx] = running_max
    res["p (Holm)"] = pd.Series(holm)
    res["Significant (Holm < 0.05)"] = res["p (Holm)"] < 0.05
    return h_stat, p_kw, res


prices = load_prices()
metrics = load_metrics()

st.title("Market Analytics Dashboard")
st.caption("18 US stocks across Technology, Healthcare and Financial Services · daily data from 2019")

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")

all_sectors = sorted(prices["sector"].unique())
sectors = st.sidebar.multiselect("Sector", all_sectors, default=all_sectors)

available = sorted(prices[prices["sector"].isin(sectors)]["ticker"].unique())
tickers = st.sidebar.multiselect("Stock", available, default=available)

min_d, max_d = prices["date"].min().date(), prices["date"].max().date()
date_range = st.sidebar.date_input("Date range", (min_d, max_d), min_value=min_d, max_value=max_d)

if len(date_range) != 2:      # user has picked a start date but not an end date yet
    st.stop()
if not tickers:
    st.warning("Select at least one stock in the sidebar.")
    st.stop()

start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
filtered = prices[prices["ticker"].isin(tickers) & prices["date"].between(start, end)]
if filtered.empty:
    st.warning("No data in that date range.")
    st.stop()

tab_perf, tab_metrics = st.tabs(["Performance", "Risk metrics"])

# =====================================================================
# TAB 1: PERFORMANCE (responds to the date range)
# =====================================================================
with tab_perf:
    def summarise(g):
        return pd.Series({
            "total_return_pct": (g["close"].iloc[-1] / g["close"].iloc[0] - 1) * 100,
            "ann_vol_pct": g["daily_return"].std() * (252 ** 0.5) * 100,
        })

    summary = filtered.groupby("ticker").apply(summarise, include_groups=False)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stocks selected", filtered["ticker"].nunique())
    c2.metric("Trading days", f"{filtered['date'].nunique():,}")
    best, worst = summary["total_return_pct"].idxmax(), summary["total_return_pct"].idxmin()
    c3.metric("Best performer", best, f"{summary.loc[best, 'total_return_pct']:+.1f}%")
    c4.metric("Worst performer", worst, f"{summary.loc[worst, 'total_return_pct']:+.1f}%")

    st.subheader("Growth of 100 invested at the start of the selected range")
    opt1, opt2 = st.columns(2)
    log_scale = opt1.toggle("Log scale", value=True, help="Equal vertical distances = equal % changes. Much easier to read when one stock grows far more than the rest.")
    colour_by = opt2.radio("Colour lines by", ["Stock", "Sector"], horizontal=True)

    norm = filtered.copy()
    norm["indexed"] = norm.groupby("ticker")["close"].transform(lambda s: s / s.iloc[0] * 100)
    if colour_by == "Stock":
        fig = px.line(norm, x="date", y="indexed", color="ticker")
    else:
        fig = px.line(norm, x="date", y="indexed", color="sector", line_group="ticker", hover_name="ticker",
                      color_discrete_map=SECTOR_COLORS)
    fig.update_layout(legend_title_text="", hovermode="closest" if colour_by == "Sector" else "x unified",
                      yaxis_title="Value (start = 100)", xaxis_title="")
    if log_scale:
        fig.update_yaxes(type="log")
    st.plotly_chart(fig, width="stretch")
    st.caption("Stocks that start later (SNOW, DDOG, ALHC) are indexed to 100 on their own first day in the range.")

    st.subheader("Selected-range summary")
    st.dataframe(summary.round(1).rename(columns={"total_return_pct": "Total return (%)", "ann_vol_pct": "Annualised vol (%)"})
                 .sort_values("Total return (%)", ascending=False), width="stretch")

# =====================================================================
# TAB 2: RISK METRICS (full history, from notebook 04)
# =====================================================================
with tab_metrics:
    st.caption("Calculated over each stock's whole history in notebook 04, so these do not change with the date range. "
               "The Sector and Stock filters still apply. SNOW, DDOG and ALHC cover shorter windows (see the 'Years' column).")

    m = metrics[metrics["ticker"].isin(tickers)].copy()

    # ----- Risk vs return scatter -----
    st.subheader("Risk vs compounded return")
    fig2 = px.scatter(m, x="ann_vol", y="cagr", color="sector", text="ticker", color_discrete_map=SECTOR_COLORS,
                      labels={"ann_vol": "Annualised volatility (%)", "cagr": "CAGR (%)"})
    fig2.update_traces(textposition="top center", marker_size=11)
    fig2.add_hline(y=0, line_dash="dash", line_color="gray")
    fig2.update_layout(legend_title_text="")
    st.plotly_chart(fig2, width="stretch")

    # ----- Ranking chart with a metric picker -----
    st.subheader("Rank the stocks")
    options = {
        "Sharpe ratio (CAGR basis)": ("sharpe_cagr", "Higher is better. Uses the compounded return, which accounts for volatility drag."),
        "Sharpe ratio (arithmetic)": ("sharpe", "Higher is better. Uses the average daily return, which flatters very volatile stocks."),
        "CAGR (%)": ("cagr", "Higher is better. What a buy-and-hold investor actually earned per year."),
        "Annualised volatility (%)": ("ann_vol", "Lower means calmer."),
        "Max drawdown (%)": ("max_drawdown", "Closer to zero is better. The worst peak-to-trough fall."),
    }
    choice = st.selectbox("Metric", list(options))
    col, note = options[choice]
    st.caption(note)

    ranked = m.sort_values(col, ascending=True)      # ascending, because horizontal bars plot the first row at the bottom
    fig3 = px.bar(ranked, x=col, y="ticker", color="sector", orientation="h", color_discrete_map=SECTOR_COLORS,
                  labels={col: choice, "ticker": ""}, height=max(320, 26 * len(ranked) + 110))
    fig3.update_layout(legend_title_text="", yaxis={"categoryorder": "array", "categoryarray": ranked["ticker"].tolist()})
    st.plotly_chart(fig3, width="stretch")

    # ----- Full table -----
    st.subheader("All metrics")
    table = m.set_index("ticker")[["sector", "sub_sector", "years_of_data", "cagr", "ann_return", "ann_vol",
                                   "sharpe_cagr", "sharpe", "max_drawdown"]]
    st.dataframe(
        table.sort_values("sharpe_cagr", ascending=False),
        width="stretch",
        height=35 * (len(table) + 1) + 3,        # tall enough to show every row without an inner scrollbar
        column_config={
            "sector": "Sector", "sub_sector": "Sub-sector",
            "years_of_data": st.column_config.NumberColumn("Years", format="%.1f"),
            "cagr": st.column_config.NumberColumn("CAGR", format="%.1f%%"),
            "ann_return": st.column_config.NumberColumn("Simple return", format="%.1f%%"),
            "ann_vol": st.column_config.NumberColumn("Volatility", format="%.1f%%"),
            "sharpe_cagr": st.column_config.NumberColumn("Sharpe (CAGR)", format="%.2f"),
            "sharpe": st.column_config.NumberColumn("Sharpe (simple)", format="%.2f"),
            "max_drawdown": st.column_config.NumberColumn("Max drawdown", format="%.1f%%"),
        },
    )
    with st.expander("What do these columns mean?"):
        st.markdown(
            "- **CAGR**: the single yearly growth rate that turns the first price into the last. What a buy-and-hold investor earned.\n"
            "- **Simple return**: average daily return × 252. Overstates growth for volatile stocks (volatility drag).\n"
            "- **Volatility**: standard deviation of daily returns × √252.\n"
            "- **Sharpe** (CAGR and simple versions): (return − 4% risk-free rate) ÷ volatility. The CAGR version is the more conservative one.\n"
            "- **Max drawdown**: the worst fall from a running high.\n\n"
            "Assumptions: 252 trading days a year and a flat 4% risk-free rate."
        )

    # ----- Statistical test (always all 18 stocks) -----
    st.subheader("Do the sectors really differ in volatility?")
    st.caption("Always uses all 18 stocks, whatever the filters say. One volatility value per stock (six per sector), "
               "tested with rank-based tests. Same method as notebook 04, section 5.")
    h_stat, p_kw, res = sector_volatility_tests(metrics)

    k1, k2 = st.columns(2)
    k1.metric("Kruskal-Wallis p-value (all three sectors)", f"{p_kw:.3f}")
    sig = res.loc[res["Significant (Holm < 0.05)"], "Comparison"].tolist()
    k2.metric("Pairs significant after Holm correction", len(sig))

    st.dataframe(
        res.set_index("Comparison"), width="stretch",
        column_config={
            "Median vol A (%)": st.column_config.NumberColumn(format="%.1f"),
            "Median vol B (%)": st.column_config.NumberColumn(format="%.1f"),
            "p (raw)": st.column_config.NumberColumn(format="%.3f"),
            "p (Holm)": st.column_config.NumberColumn(format="%.3f"),
            "Effect size": st.column_config.NumberColumn("Effect size (rank-biserial)", format="%.2f"),
        },
    )
    if sig:
        st.success("Significant after Holm correction: " + "; ".join(sig) + ".")
    st.caption("With six stocks per sector the tests have limited power, so 'not significant' means this basket cannot tell the "
               "sectors apart, not that they are the same. The stocks were hand-picked, so this describes this basket, "
               "not every stock in each sector.")