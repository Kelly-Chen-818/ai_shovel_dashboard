# Product and Technical Specification
## AI Shovel Stocks Tracker

---

## 1. Product Objective

Build a dashboard that tracks the performance and correlation structure of AI infrastructure stocks.

The dashboard should help users answer:

1. Which AI infrastructure sectors are outperforming?
2. Which sectors move most like NVDA or AMD?
3. Which stocks are outperforming within each sector?
4. How does the AI infrastructure basket compare against SPY and QQQ?
5. How does the answer change across different time windows?

---

## 2. Target User

Primary user:

- Individual investor or researcher
- Risk / finance / data professional
- Someone monitoring AI infrastructure and "picks-and-shovels" companies

Secondary user:

- Analyst preparing AI infrastructure market notes
- Portfolio watcher tracking AI-related sector rotation
- Risk professional monitoring concentration and theme beta

---

## 3. Core Concept

The dashboard uses a layered structure:

### Layer 1: Benchmark Layer

The four benchmarks are:

- NVDA
- AMD
- SPY
- QQQ

These represent:

- AI GPU leader
- AI chip peer
- Broad U.S. equity market
- Growth / technology market

### Layer 2: Industry Index Layer

Each industry group is converted into an equal-weight index.

Example:

```text
Power / Cooling / Electrical Index
= average daily return of VRT, ETN, GEV, JCI, CARR, MOD
```

### Layer 3: Peer Layer

Each industry group has its own chart showing member stocks.

This avoids overcrowded charts and improves peer comparison.

### Layer 4: Correlation Layer

The dashboard calculates daily-return correlations versus the four benchmarks.

This identifies which stocks behave like:

- NVDA beta
- AMD / semiconductor beta
- Nasdaq / growth beta
- Broad market beta

---

## 4. Functional Requirements

### 4.1 Window Selection

User must be able to select:

- 3M
- 6M
- 1Y
- 2Y
- 3Y
- 5Y
- Max

Changing the window should refresh:

- Benchmark chart
- Industry index overview
- Industry index vs benchmark charts
- Peer comparison charts
- Correlation heatmap
- Correlation table
- Raw data tables

### 4.2 Industry Group Selection

User can select industry groups from the sidebar.

Default groups:

- AI Chips / Semis
- Networking / Optical
- Power / Cooling / Electrical
- Servers / Hardware
- Engineering / Construction
- Software / Security

Optional groups:

- Data Center / REIT
- Storage / Memory

### 4.3 Custom Tickers

User can edit the ticker list through a comma-separated sidebar field.

The app should:

- Normalize tickers to uppercase
- Remove blank entries
- Remove duplicates
- Ignore unavailable tickers gracefully

### 4.4 Benchmark Selection

User can select benchmark targets:

- Nvidia
- AMD
- S&P 500 ETF
- Nasdaq 100 ETF

### 4.5 Data Download

Use `yfinance`:

```python
yf.download(
    tickers=tickers,
    period=period,
    interval="1d",
    auto_adjust=True
)
```

### 4.6 Return Calculations

Daily return:

```python
daily_returns = prices.pct_change()
```

Cumulative return:

```python
cumulative_returns = (1 + daily_returns).cumprod() - 1
```

### 4.7 Industry Index Calculation

Each industry index is calculated using an equal-weight average of available member daily returns.

Formula:

```python
industry_daily_return = daily_returns[group_members].mean(axis=1)
industry_cumulative_return = (1 + industry_daily_return).cumprod() - 1
```

Reason:

- Simple
- Transparent
- Easy to explain
- Does not require market cap data

Future enhancement:

- Add market-cap weighted index option
- Add custom user-defined weights

### 4.8 Correlation Calculation

Correlation is calculated from daily returns.

```python
correlation = daily_returns.corr()
```

The output table should show correlation versus:

- NVDA
- AMD
- SPY
- QQQ

### 4.9 Export

The dashboard should allow CSV export for:

- Correlation table
- Adjusted close prices
- Industry index cumulative returns

---

## 5. Page Architecture

### Top Header

Content:

- Eyebrow label: AI Infrastructure Equity Monitor
- Dashboard title
- Short description
- Sidebar controls

### KPI Cards

Four cards:

1. Tracking Window
2. Best Stock Return
3. Worst Stock Return
4. Best Industry Index

### Section 1: Benchmark Overview

Chart:

- NVDA
- AMD
- SPY
- QQQ

Purpose:

- Understand market context before sector analysis

### Section 2: Industry Index Overview vs Benchmarks

Chart:

- All selected industry indexes
- NVDA
- AMD
- SPY
- QQQ

Purpose:

- Compare industry-level performance to major benchmarks

### Section 3: Industry Index vs Four Benchmarks

One panel per industry.

Each panel includes:

- The industry equal-weight index
- NVDA
- AMD
- SPY
- QQQ

Purpose:

- See whether an industry is outperforming or lagging core AI and market benchmarks

### Section 4: Industry Peer Comparison

One panel per industry.

Each panel includes only member stocks.

Purpose:

- Clean peer comparison within the same business segment

### Section 5: Correlation Heatmap and Tables

Tabs:

1. Correlation Heatmap
2. Correlation Table
3. Price Data
4. Industry Index Data

---

## 6. Non-Functional Requirements

### Performance

- Use Streamlit cache for price data
- Cache TTL: 1 hour
- Avoid redundant yfinance calls

### Usability

- Avoid overcrowding charts
- Use industry panels instead of one chart with all stocks
- Keep benchmark overview at the top
- Use dark theme for visual consistency

### Reliability

- Handle missing tickers gracefully
- Drop columns where all data is missing
- Forward-fill prices where appropriate
- Stop with user-readable error if no data is returned

### Maintainability

Code should be organized into:

- Configuration
- Styling
- Helper functions
- Sidebar controls
- Data pipeline
- Rendering sections

---

## 7. Future Enhancements

Potential additions:

1. Market-cap weighted industry index
2. P/E and valuation overlay
3. Drawdown chart
4. Rolling correlation
5. Rolling beta vs NVDA and QQQ
6. Volatility and Sharpe ratio
7. Momentum ranking
8. Watchlist persistence
9. SQLite database storage
10. Scheduled refresh
11. Portfolio weighting simulator
12. News and earnings event overlay
13. PDF export
14. GitHub Pages static report output

---

## 8. Success Criteria

The dashboard is successful if it allows the user to quickly answer:

- Which AI shovel sectors are leading?
- Which sectors are lagging?
- Which individual stocks are driving each sector?
- Which stocks behave most like NVDA?
- Is the AI infrastructure theme outperforming SPY and QQQ?
- How do these relationships change across different time windows?
