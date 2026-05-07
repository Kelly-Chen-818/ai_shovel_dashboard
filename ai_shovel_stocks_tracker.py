"""
AI Shovel Stocks Tracker
========================

A Streamlit + ECharts dashboard for tracking AI infrastructure / "AI shovel"
stocks by industry group.

Key features:
- Adjustable tracking window: 3M, 6M, 1Y, 2Y, 3Y, 5Y, Max
- Benchmark overview: NVDA, AMD, SPY, QQQ
- Equal-weight industry index comparison vs benchmarks
- Industry-level peer comparison charts
- Daily-return correlation heatmap
- Correlation table and price data export

Run:
    streamlit run ai_shovel_stocks_tracker.py
"""

from __future__ import annotations

from dataclasses import dataclass
import textwrap
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from streamlit_echarts import JsCode, st_echarts


# =========================================================
# Page Config
# =========================================================

st.set_page_config(
    page_title="AI Shovel Stocks Tracker",
    page_icon="📈",
    layout="wide",
)


# =========================================================
# Dashboard Universe
# =========================================================

BENCHMARKS: Dict[str, str] = {
    "Nvidia": "NVDA",
    "AMD": "AMD",
    "S&P 500 ETF": "SPY",
    "Nasdaq 100 ETF": "QQQ",
}

DEFAULT_GROUPS: Dict[str, List[str]] = {
    "AI Chips / Semis": ["AVGO", "MU", "TSM", "ASML", "AMAT", "LRCX", "KLAC"],
    "Networking / Optical": ["ANET", "CSCO", "APH", "COHR", "LITE"],
    "Power / Cooling / Electrical": ["VRT", "ETN", "GEV", "JCI", "CARR", "MOD"],
    "Data Center / REIT": ["EQIX", "DLR", "AMT"],
    "Servers / Hardware": ["SMCI", "DELL", "HPE"],
    "Engineering / Construction": ["PWR", "EME", "ACM", "FIX", "J", "FLR"],
    "Storage / Memory": ["MU", "WDC", "STX", "NTAP", "PSTG"],
    "Software / Security": ["PLTR", "PANW", "NOW", "NET", "CRWD", "ZS", "OKTA"],
}

PERIOD_MAP: Dict[str, str] = {
    "3M": "3mo",
    "6M": "6mo",
    "1Y": "1y",
    "2Y": "2y",
    "3Y": "3y",
    "5Y": "5y",
    "Max": "max",
}

DEFAULT_TRACKING_WINDOW = "3M"
YFINANCE_CHUNK_SIZE = 8
YFINANCE_CHUNK_PAUSE_SECONDS = 1.0
CHART_MODE_CHANGE = "Change %"
CHART_MODE_PRICE = "Price"
CHART_MODE_LEVEL = "Price Level"


# =========================================================
# Styling
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(59,130,246,.18), transparent 30%),
            radial-gradient(circle at top right, rgba(168,85,247,.16), transparent 28%),
            linear-gradient(135deg, #07111f 0%, #0b1020 50%, #111827 100%);
        color: #f8fafc;
    }

    section[data-testid="stSidebar"] {
        background: rgba(2, 6, 23, 0.72);
        border-right: 1px solid rgba(255,255,255,.08);
    }

    .dashboard-eyebrow {
        color: #7dd3fc;
        font-size: 12px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .12em;
        margin-bottom: 8px;
    }

    .dashboard-title {
        font-size: 38px;
        font-weight: 800;
        letter-spacing: -0.045em;
        line-height: 1.05;
        margin-bottom: 8px;
    }

    .dashboard-subtitle {
        color: #94a3b8;
        font-size: 14px;
        line-height: 1.55;
        margin-bottom: 18px;
    }

    .metric-card {
        padding: 18px;
        border: 1px solid rgba(255,255,255,.12);
        border-radius: 22px;
        background: linear-gradient(180deg, rgba(255,255,255,.105), rgba(255,255,255,.06));
        box-shadow: 0 22px 55px rgba(0,0,0,.28);
        min-height: 118px;
    }

    .metric-label {
        font-size: 12px;
        color: #94a3b8;
        margin-bottom: 7px;
    }

    .metric-value {
        font-size: 25px;
        font-weight: 780;
        letter-spacing: -0.035em;
        color: #f8fafc;
    }

    .metric-note {
        font-size: 12px;
        color: #94a3b8;
        margin-top: 7px;
    }

    .section-title {
        font-size: 18px;
        font-weight: 760;
        margin-top: 10px;
        margin-bottom: 4px;
        color: #f8fafc;
    }

    .section-subtitle {
        color: #94a3b8;
        font-size: 13px;
        margin-bottom: 12px;
    }

    .module-label {
        font-size: 13px;
        font-weight: 800;
        letter-spacing: .06em;
        text-transform: uppercase;
        color: #dbeafe;
        margin-top: 14px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Helpers
# =========================================================

def unique_in_order(items: List[str]) -> List[str]:
    seen = set()
    output = []
    for item in items:
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output


def flatten_groups(groups: Dict[str, List[str]]) -> List[str]:
    names: List[str] = []
    for group_tickers in groups.values():
        names.extend(group_tickers)
    return unique_in_order(names)


def parse_tickers(text: str) -> List[str]:
    normalized_text = text.replace(",", " ").replace(";", " ")
    return unique_in_order([t.strip().upper() for t in normalized_text.split() if t.strip()])


def format_ticker_text(tickers: List[str]) -> str:
    return "\n".join(tickers)


def calculate_price_levels(prices: pd.DataFrame) -> pd.DataFrame:
    if prices.empty:
        return pd.DataFrame()

    first_valid = prices.apply(
        lambda column: column.dropna().iloc[0] if not column.dropna().empty else np.nan
    )
    return prices.divide(first_valid).mul(100)


def select_line_data(
    change_data: pd.DataFrame,
    price_data: pd.DataFrame,
    level_data: pd.DataFrame,
    chart_mode: str,
) -> pd.DataFrame:
    if chart_mode == CHART_MODE_PRICE:
        data = price_data
    elif chart_mode == CHART_MODE_LEVEL:
        data = level_data
    else:
        data = change_data
    return data.dropna(how="all") if not data.empty else data


def mode_subtitle(base_subtitle: str, chart_mode: str) -> str:
    return f"{base_subtitle} {chart_mode_note(chart_mode)}"


def chart_mode_note(chart_mode: str) -> str:
    if chart_mode == CHART_MODE_PRICE:
        return "Adjusted close prices."
    if chart_mode == CHART_MODE_LEVEL:
        return "Indexed to 100 at first close."
    return "Cumulative change from window start."


def two_line_chart_subtitle(base_subtitle: str, chart_mode: str) -> str:
    return f"{base_subtitle}\n{chart_mode_note(chart_mode)}"


def wrap_chart_subtitle(text: str, max_chars: int) -> str:
    return "\n".join(
        textwrap.wrap(
            text,
            width=max_chars,
            break_long_words=False,
            break_on_hyphens=False,
        )
    )


def extract_close_prices(data: pd.DataFrame, requested_tickers: List[str]) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame()

    if isinstance(data.columns, pd.MultiIndex):
        if "Close" in data.columns.get_level_values(0):
            prices = data["Close"].copy()
        elif "Close" in data.columns.get_level_values(1):
            prices = data.xs("Close", level=1, axis=1).copy()
        else:
            return pd.DataFrame()
    elif "Close" in data.columns:
        prices = data[["Close"]].copy()
    else:
        return pd.DataFrame()

    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    if len(requested_tickers) == 1 and len(prices.columns) == 1:
        prices.columns = requested_tickers
    else:
        prices.columns = [str(column).upper() for column in prices.columns]

    ordered_columns = [ticker for ticker in requested_tickers if ticker in prices.columns]
    return prices[ordered_columns] if ordered_columns else pd.DataFrame()


@st.cache_data(ttl=60 * 60)
def download_prices(tickers: List[str], period: str) -> pd.DataFrame:
    """
    Download adjusted close prices from yfinance in small sequential batches.
    """
    import time

    if not tickers:
        return pd.DataFrame()

    requested_tickers = unique_in_order([ticker.strip().upper() for ticker in tickers if ticker.strip()])
    max_retries = 4
    price_chunks = []

    for chunk_start in range(0, len(requested_tickers), YFINANCE_CHUNK_SIZE):
        chunk = requested_tickers[chunk_start : chunk_start + YFINANCE_CHUNK_SIZE]
        chunk_prices = pd.DataFrame()

        for attempt in range(max_retries):
            try:
                data = yf.download(
                    tickers=chunk if len(chunk) > 1 else chunk[0],
                    period=period,
                    interval="1d",
                    auto_adjust=True,
                    progress=False,
                    group_by="column",
                    threads=False,
                )
            except Exception:
                data = pd.DataFrame()

            chunk_prices = extract_close_prices(data, chunk)
            if not chunk_prices.empty:
                break

            if attempt < max_retries - 1:
                wait = 2 ** attempt * 5  # 5s, 10s, 20s, 40s
                st.toast(
                    f"Yahoo Finance throttled or returned no data for {', '.join(chunk)}. "
                    f"Retrying in {wait}s ({attempt + 1}/{max_retries})..."
                )
                time.sleep(wait)

        if not chunk_prices.empty:
            price_chunks.append(chunk_prices)

        if chunk_start + YFINANCE_CHUNK_SIZE < len(requested_tickers):
            time.sleep(YFINANCE_CHUNK_PAUSE_SECONDS)

    if not price_chunks:
        return pd.DataFrame()

    prices = pd.concat(price_chunks, axis=1)
    prices = prices.loc[:, ~prices.columns.duplicated()]
    prices = prices[[ticker for ticker in requested_tickers if ticker in prices.columns]]
    prices = prices.dropna(axis=1, how="all")
    prices = prices.ffill().dropna(how="all")
    return prices


def calculate_returns(prices: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Return daily returns and cumulative returns.
    """
    daily_returns = prices.pct_change().dropna(how="all")
    cumulative_returns = (1 + daily_returns).cumprod() - 1
    return daily_returns, cumulative_returns


def calculate_industry_indexes(
    daily_returns: pd.DataFrame,
    groups: Dict[str, List[str]],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build equal-weight industry indexes from daily returns.

    The index return is the simple average of available member returns.
    This is intentionally transparent and easy to explain.
    """
    index_returns = {}

    for group_name, tickers in groups.items():
        available = [t for t in tickers if t in daily_returns.columns]
        if not available:
            continue
        index_returns[group_name] = daily_returns[available].mean(axis=1)

    index_returns_df = pd.DataFrame(index_returns, index=daily_returns.index)
    index_cumulative_df = (1 + index_returns_df).cumprod() - 1

    return index_returns_df, index_cumulative_df


def calculate_correlation_table(
    daily_returns: pd.DataFrame,
    target_tickers: List[str],
    benchmark_tickers: List[str],
) -> pd.DataFrame:
    available_targets = [t for t in target_tickers if t in daily_returns.columns]
    available_benchmarks = [b for b in benchmark_tickers if b in daily_returns.columns]

    if not available_targets or not available_benchmarks:
        return pd.DataFrame()

    corr = daily_returns.corr()
    output = corr.loc[available_targets, available_benchmarks].copy()

    rename_map = {ticker: label for label, ticker in BENCHMARKS.items()}
    output = output.rename(columns=rename_map)

    sort_col = "Nvidia" if "Nvidia" in output.columns else output.columns[0]
    return output.sort_values(sort_col, ascending=False)


def echarts_line_options(
    data: pd.DataFrame,
    title: str,
    subtitle: str,
    chart_mode: str,
    highlight_tickers: List[str] | None = None,
    height_focus: bool = False,
) -> dict:
    """
    Build dark ECharts line chart options.
    Change mode expects cumulative returns in decimal format; price mode expects
    adjusted close prices; price-level mode expects indexed price levels where
    100 is the first available close.
    """
    if data.empty:
        return {}

    highlight_tickers = set(highlight_tickers or [])
    is_change_mode = chart_mode == CHART_MODE_CHANGE
    is_price_mode = chart_mode == CHART_MODE_PRICE
    chart_data = data * 100 if is_change_mode else data
    dates = [d.strftime("%Y-%m-%d") for d in chart_data.index]
    if is_change_mode:
        value_formatter = JsCode(
            "function(value) { return value == null ? '-' : Number(value).toFixed(2) + '%'; }"
        )
        axis_formatter = "{value}%"
        y_axis_name = "Change %"
    elif is_price_mode:
        value_formatter = JsCode(
            "function(value) { return value == null ? '-' : '$' + Number(value).toFixed(2); }"
        )
        axis_formatter = "${value}"
        y_axis_name = "Adjusted Close Price"
    else:
        value_formatter = JsCode(
            "function(value) { return value == null ? '-' : Number(value).toFixed(2); }"
        )
        axis_formatter = "{value}"
        y_axis_name = "Indexed Price Level"

    wrapped_subtitle = subtitle if height_focus else wrap_chart_subtitle(subtitle, 40)
    subtitle_line_count = max(1, wrapped_subtitle.count("\n") + 1)
    subtitle_extra_top = (subtitle_line_count - 1) * 16
    legend_top = 52 + subtitle_extra_top
    grid_top = 100 + subtitle_extra_top

    series = []
    for ticker in chart_data.columns:
        is_highlight = ticker in highlight_tickers
        series.append(
            {
                "name": ticker,
                "type": "line",
                "showSymbol": False,
                "smooth": True,
                "connectNulls": True,
                "data": [
                    None if pd.isna(x) else round(float(x), 2)
                    for x in chart_data[ticker].values
                ],
                "lineStyle": {
                    "width": 3.1 if is_highlight else 1.8,
                    "opacity": 1.0 if is_highlight else 0.72,
                },
                "emphasis": {
                    "focus": "series",
                    "lineStyle": {"width": 4.2},
                },
            }
        )

    return {
        "backgroundColor": "transparent",
        "title": {
            "text": title,
            "left": 4,
            "top": 0,
            "textStyle": {
                "color": "#f8fafc",
                "fontSize": 18 if height_focus else 15,
                "fontWeight": 700,
            },
            "subtext": wrapped_subtitle,
            "subtextStyle": {
                "color": "#94a3b8",
                "fontSize": 12,
                "lineHeight": 16,
            },
        },
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": "rgba(15,23,42,.94)",
            "borderColor": "rgba(148,163,184,.25)",
            "textStyle": {"color": "#e5e7eb"},
            "valueFormatter": value_formatter,
        },
        "legend": {
            "type": "scroll",
            "top": legend_top,
            "left": 4,
            "right": 20,
            "textStyle": {"color": "#cbd5e1"},
            "pageTextStyle": {"color": "#cbd5e1"},
        },
        "grid": {
            "left": 52,
            "right": 32,
            "top": grid_top,
            "bottom": 92,
        },
        "xAxis": {
            "type": "category",
            "boundaryGap": False,
            "data": dates,
            "axisLine": {"lineStyle": {"color": "rgba(148,163,184,.24)"}},
            "axisLabel": {"color": "#94a3b8"},
        },
        "yAxis": {
            "type": "value",
            "name": y_axis_name,
            "nameTextStyle": {"color": "#94a3b8", "padding": [0, 0, 0, 8]},
            "axisLabel": {
                "color": "#94a3b8",
                "formatter": axis_formatter,
            },
            "splitLine": {"lineStyle": {"color": "rgba(148,163,184,.12)"}},
        },
        "dataZoom": [
            {
                "type": "inside",
                "xAxisIndex": 0,
                "start": 0,
                "end": 100,
                "filterMode": "none",
            },
            {
                "type": "slider",
                "xAxisIndex": 0,
                "start": 0,
                "end": 100,
                "bottom": 30,
                "height": 30,
                "borderColor": "rgba(148,163,184,.2)",
                "fillerColor": "rgba(96,165,250,.24)",
                "handleSize": "120%",
                "moveHandleSize": 10,
                "brushSelect": False,
                "filterMode": "none",
                "realtime": True,
                "handleStyle": {
                    "color": "#dbeafe",
                    "borderColor": "#60a5fa",
                    "borderWidth": 1,
                },
                "emphasis": {
                    "handleStyle": {
                        "color": "#f8fafc",
                        "borderColor": "#38bdf8",
                    }
                },
                "textStyle": {"color": "#94a3b8"},
            },
        ],
        "toolbox": {
            "right": 12,
            "top": 4,
            "feature": {
                "saveAsImage": {"backgroundColor": "#0b1020"},
                "restore": {},
                "dataZoom": {},
            },
            "iconStyle": {"borderColor": "#94a3b8"},
        },
        "series": series,
    }


def echarts_heatmap_options(corr_df: pd.DataFrame) -> dict:
    if corr_df.empty:
        return {}

    sort_col = "Nvidia" if "Nvidia" in corr_df.columns else corr_df.columns[0]
    heatmap_df = corr_df.sort_values(sort_col, ascending=False)

    x_labels = list(heatmap_df.columns)
    y_labels = list(heatmap_df.index)

    data = []
    for y_idx, ticker in enumerate(y_labels):
        for x_idx, col in enumerate(x_labels):
            value = heatmap_df.loc[ticker, col]
            data.append([x_idx, y_idx, None if pd.isna(value) else round(float(value), 3)])

    return {
        "backgroundColor": "transparent",
        "title": {
            "text": "Correlation Heatmap",
            "left": 4,
            "top": 0,
            "textStyle": {
                "color": "#f8fafc",
                "fontSize": 18,
                "fontWeight": 700,
            },
            "subtext": f"Daily return correlation, sorted by {sort_col}",
            "subtextStyle": {
                "color": "#94a3b8",
                "fontSize": 12,
            },
        },
        "tooltip": {
            "position": "top",
            "backgroundColor": "rgba(15,23,42,.94)",
            "borderColor": "rgba(148,163,184,.25)",
            "textStyle": {"color": "#e5e7eb"},
            "formatter": JsCode(
                """
                function(params) {
                    var value = params.value[2];
                    return params.name + ': ' + (value == null ? '-' : Number(value).toFixed(3));
                }
                """
            ),
        },
        "grid": {
            "left": 86,
            "right": 28,
            "top": 76,
            "bottom": 92,
        },
        "xAxis": {
            "type": "category",
            "data": x_labels,
            "axisLabel": {"color": "#cbd5e1", "fontWeight": 700},
            "axisLine": {"lineStyle": {"color": "rgba(148,163,184,.20)"}},
            "splitArea": {"show": True},
        },
        "yAxis": {
            "type": "category",
            "data": y_labels,
            "axisLabel": {"color": "#cbd5e1"},
            "axisLine": {"lineStyle": {"color": "rgba(148,163,184,.20)"}},
            "splitArea": {"show": True},
        },
        "visualMap": {
            "min": -1,
            "max": 1,
            "calculable": True,
            "orient": "horizontal",
            "left": "center",
            "bottom": 24,
            "textStyle": {"color": "#cbd5e1"},
            "inRange": {"color": ["#be123c", "#1f2937", "#059669"]},
        },
        "series": [
            {
                "name": "Correlation",
                "type": "heatmap",
                "data": data,
                "label": {
                    "show": True,
                    "color": "#f8fafc",
                    "formatter": JsCode(
                        "function(params) { return params.value[2] == null ? '-' : Number(params.value[2]).toFixed(2); }"
                    ),
                },
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 12,
                        "shadowColor": "rgba(0, 0, 0, 0.55)",
                    }
                },
            }
        ],
    }


def render_metric_card(label: str, value: str, note: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# Sidebar Controls
# =========================================================

st.sidebar.header("Control Panel")

selected_chart_mode = st.sidebar.radio(
    "Chart display mode",
    options=[CHART_MODE_CHANGE, CHART_MODE_PRICE, CHART_MODE_LEVEL],
    index=0,
)

with st.sidebar.form("control_panel"):
    selected_window = st.radio(
        "Tracking window",
        options=list(PERIOD_MAP.keys()),
        index=list(PERIOD_MAP.keys()).index(DEFAULT_TRACKING_WINDOW),
        horizontal=True,
    )

    selected_groups = st.multiselect(
        "Industry groups",
        options=list(DEFAULT_GROUPS.keys()),
        default=[
            "AI Chips / Semis",
            "Networking / Optical",
            "Power / Cooling / Electrical",
            "Servers / Hardware",
            "Engineering / Construction",
            "Software / Security",
        ],
    )

    selected_benchmarks_labels = st.multiselect(
        "Benchmark targets",
        options=list(BENCHMARKS.keys()),
        default=list(BENCHMARKS.keys()),
    )

    default_selected_tickers = flatten_groups(
        {group: DEFAULT_GROUPS[group] for group in selected_groups}
    )

    manual_ticker_text = st.text_area(
        "Additional / custom tickers",
        value=format_ticker_text(default_selected_tickers),
        height=180,
    )

    show_peer_panels = st.checkbox("Show industry peer comparison panels", value=True)
    show_index_vs_bench_panels = st.checkbox("Show industry index vs benchmark panels", value=True)

    refresh = st.form_submit_button("Apply controls / refresh data")

if refresh:
    download_prices.clear()

benchmark_tickers = [BENCHMARKS[label] for label in selected_benchmarks_labels]
custom_tickers = parse_tickers(manual_ticker_text)


# =========================================================
# Header
# =========================================================

st.markdown('<div class="dashboard-eyebrow">AI Infrastructure Equity Monitor</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-title">AI Shovel Stocks Tracker</div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="dashboard-subtitle">
    Track AI infrastructure stocks by industry group. The dashboard compares benchmark performance,
    equal-weight industry indexes, peer-level cumulative returns, and return correlations versus
    NVDA, AMD, SPY, and QQQ.
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Data Pipeline
# =========================================================

active_groups = {group: DEFAULT_GROUPS[group] for group in selected_groups}
all_group_tickers = flatten_groups(active_groups)
all_tickers = unique_in_order(custom_tickers + benchmark_tickers)

if not all_tickers:
    st.warning("Please select at least one ticker.")
    st.stop()

with st.spinner("Downloading price data and calculating dashboard outputs..."):
    prices = download_prices(all_tickers, PERIOD_MAP[selected_window])

if prices.empty:
    st.error("No price data was returned. Please check ticker symbols or yfinance availability.")
    st.stop()

daily_returns, cumulative_returns = calculate_returns(prices)
price_levels = calculate_price_levels(prices)

active_groups_available = {
    group: [ticker for ticker in tickers if ticker in daily_returns.columns]
    for group, tickers in active_groups.items()
}
active_groups_available = {
    group: tickers
    for group, tickers in active_groups_available.items()
    if tickers
}

industry_index_returns, industry_index_cumulative = calculate_industry_indexes(
    daily_returns=daily_returns,
    groups=active_groups_available,
)
industry_index_levels = (1 + industry_index_cumulative) * 100

available_benchmarks = [ticker for ticker in benchmark_tickers if ticker in cumulative_returns.columns]
available_custom_tickers = [ticker for ticker in custom_tickers if ticker in cumulative_returns.columns]

correlation_table = calculate_correlation_table(
    daily_returns=daily_returns,
    target_tickers=available_custom_tickers,
    benchmark_tickers=available_benchmarks,
)

latest_cumulative = cumulative_returns.iloc[-1].sort_values(ascending=False)
latest_industry_index = (
    industry_index_cumulative.iloc[-1].sort_values(ascending=False)
    if not industry_index_cumulative.empty
    else pd.Series(dtype=float)
)


# =========================================================
# KPI Cards
# =========================================================

best_ticker = latest_cumulative.index[0]
best_return = latest_cumulative.iloc[0] * 100
worst_ticker = latest_cumulative.index[-1]
worst_return = latest_cumulative.iloc[-1] * 100

best_industry = latest_industry_index.index[0] if not latest_industry_index.empty else "N/A"
best_industry_return = latest_industry_index.iloc[0] * 100 if not latest_industry_index.empty else np.nan

c1, c2, c3, c4 = st.columns(4)

with c1:
    render_metric_card(
        "Tracking Window",
        selected_window,
        f"{prices.index.min().date()} → {prices.index.max().date()}",
    )

with c2:
    render_metric_card(
        "Best Stock Return",
        f"{best_ticker} {best_return:.1f}%",
        "Ending cumulative return",
    )

with c3:
    render_metric_card(
        "Worst Stock Return",
        f"{worst_ticker} {worst_return:.1f}%",
        "Ending cumulative return",
    )

with c4:
    render_metric_card(
        "Best Industry Index",
        f"{best_industry} {best_industry_return:.1f}%" if best_industry != "N/A" else "N/A",
        "Equal-weight basket return",
    )


# =========================================================
# Dashboard Sections
# =========================================================

benchmark_df = cumulative_returns[[b for b in available_benchmarks if b in cumulative_returns.columns]]
benchmark_price_df = prices[[b for b in available_benchmarks if b in prices.columns]]
benchmark_level_df = price_levels[[b for b in available_benchmarks if b in price_levels.columns]]
benchmark_chart_df = select_line_data(
    benchmark_df,
    benchmark_price_df,
    benchmark_level_df,
    selected_chart_mode,
)

st.markdown('<div class="module-label">1. Benchmark Overview</div>', unsafe_allow_html=True)

if benchmark_chart_df.empty:
    st.warning("Benchmark data is not available.")
else:
    st_echarts(
        options=echarts_line_options(
            data=benchmark_chart_df,
            title=f"Benchmark Overview — {selected_window} ({selected_chart_mode})",
            subtitle=mode_subtitle(
                "NVDA, AMD, SPY, and QQQ provide the market / AI backdrop.",
                selected_chart_mode,
            ),
            chart_mode=selected_chart_mode,
            highlight_tickers=available_benchmarks,
            height_focus=True,
        ),
        height="560px",
    )


st.markdown('<div class="module-label">2. Industry Index Overview vs Four Benchmarks</div>', unsafe_allow_html=True)

industry_overview_parts = []
industry_overview_price_parts = []
industry_overview_level_parts = []
if not industry_index_cumulative.empty:
    industry_overview_parts.append(industry_index_cumulative)
if not industry_index_levels.empty:
    industry_overview_level_parts.append(industry_index_levels)
if not benchmark_df.empty:
    industry_overview_parts.append(benchmark_df)
if not benchmark_price_df.empty:
    industry_overview_price_parts.append(benchmark_price_df)
if not benchmark_level_df.empty:
    industry_overview_level_parts.append(benchmark_level_df)

if industry_overview_parts:
    industry_overview_change_df = pd.concat(industry_overview_parts, axis=1)
    industry_overview_price_df = (
        pd.concat(industry_overview_price_parts, axis=1)
        if industry_overview_price_parts
        else pd.DataFrame(index=industry_overview_change_df.index)
    )
    industry_overview_level_df = pd.concat(industry_overview_level_parts, axis=1)
    industry_overview_df = select_line_data(
        industry_overview_change_df,
        industry_overview_price_df,
        industry_overview_level_df,
        selected_chart_mode,
    )
    industry_overview_title = (
        "Benchmark Stock/ETF Prices"
        if selected_chart_mode == CHART_MODE_PRICE
        else "Industry Index Overview vs Benchmarks"
    )
    industry_overview_subtitle = (
        "Industry indexes are synthetic baskets and do not have literal dollar prices."
        if selected_chart_mode == CHART_MODE_PRICE
        else "Each industry index is an equal-weight basket of its available constituents."
    )
    if industry_overview_df.empty:
        st.warning("No data is available for this chart mode.")
    else:
        st_echarts(
            options=echarts_line_options(
                data=industry_overview_df,
                title=f"{industry_overview_title} — {selected_window} ({selected_chart_mode})",
                subtitle=mode_subtitle(
                    industry_overview_subtitle,
                    selected_chart_mode,
                ),
                chart_mode=selected_chart_mode,
                highlight_tickers=available_benchmarks,
                height_focus=True,
            ),
            height="620px",
        )
else:
    st.warning("No industry index or benchmark data is available.")


if show_index_vs_bench_panels:
    st.markdown('<div class="module-label">3. Industry Index vs Four Benchmarks</div>', unsafe_allow_html=True)

    group_names = list(industry_index_cumulative.columns)

    if selected_chart_mode == CHART_MODE_PRICE:
        st.info(
            "Industry indexes are synthetic baskets, so they do not have raw stock prices. "
            "Use Change % or Price Level to compare industry indexes against benchmarks."
        )
    else:
        for row_start in range(0, len(group_names), 2):
            cols = st.columns(2)
            for col, group_name in zip(cols, group_names[row_start : row_start + 2]):
                with col:
                    panel_change_df = pd.concat(
                        [
                            industry_index_cumulative[[group_name]],
                            benchmark_df,
                        ],
                        axis=1,
                    ).dropna(how="all")
                    panel_level_df = pd.concat(
                        [
                            industry_index_levels[[group_name]],
                            benchmark_level_df,
                        ],
                        axis=1,
                    ).dropna(how="all")
                    panel_df = select_line_data(
                        panel_change_df,
                        pd.DataFrame(index=panel_change_df.index),
                        panel_level_df,
                        selected_chart_mode,
                    )

                    st_echarts(
                        options=echarts_line_options(
                            data=panel_df,
                            title=f"{group_name} Index vs Benchmarks ({selected_chart_mode})",
                            subtitle=two_line_chart_subtitle(
                                "Industry basket vs benchmarks.",
                                selected_chart_mode,
                            ),
                            chart_mode=selected_chart_mode,
                            highlight_tickers=[group_name],
                        ),
                        height="430px",
                    )


if show_peer_panels:
    st.markdown('<div class="module-label">4. Industry Peer Comparison</div>', unsafe_allow_html=True)

    group_items = list(active_groups_available.items())

    for row_start in range(0, len(group_items), 2):
        cols = st.columns(2)
        for col, (group_name, tickers) in zip(cols, group_items[row_start : row_start + 2]):
            with col:
                panel_tickers = [ticker for ticker in tickers if ticker in cumulative_returns.columns]
                if not panel_tickers:
                    continue

                panel_change_df = cumulative_returns[panel_tickers].dropna(how="all")
                panel_price_df = prices[panel_tickers].dropna(how="all")
                panel_level_df = price_levels[panel_tickers].dropna(how="all")
                if selected_chart_mode == CHART_MODE_LEVEL and group_name in industry_index_levels.columns:
                    panel_level_df = pd.concat(
                        [
                            industry_index_levels[[group_name]],
                            panel_level_df,
                        ],
                        axis=1,
                    ).dropna(how="all")
                panel_df = select_line_data(
                    panel_change_df,
                    panel_price_df,
                    panel_level_df,
                    selected_chart_mode,
                )
                peer_subtitle = (
                    "Peers vs industry basket."
                    if selected_chart_mode == CHART_MODE_LEVEL
                    else "Peer comparison within industry."
                )
                st_echarts(
                    options=echarts_line_options(
                        data=panel_df,
                        title=f"{group_name} ({selected_chart_mode})",
                        subtitle=two_line_chart_subtitle(
                            peer_subtitle,
                            selected_chart_mode,
                        ),
                        chart_mode=selected_chart_mode,
                        highlight_tickers=[group_name] if group_name in panel_df.columns else [],
                    ),
                    height="430px",
                )


st.markdown('<div class="module-label">5. Correlation Heatmap and Data Tables</div>', unsafe_allow_html=True)

tab_heatmap, tab_corr_table, tab_prices, tab_industry_returns = st.tabs(
    ["🔥 Correlation Heatmap", "🔗 Correlation Table", "🧾 Price Data", "🏭 Industry Index Data"]
)

with tab_heatmap:
    if correlation_table.empty:
        st.warning("Correlation table is empty.")
    else:
        st_echarts(
            options=echarts_heatmap_options(correlation_table),
            height="820px",
        )

with tab_corr_table:
    if correlation_table.empty:
        st.warning("Correlation table is empty.")
    else:
        display = correlation_table.copy()
        ending_returns = (latest_cumulative * 100).rename("Cumulative Return %")
        display = display.join(ending_returns, how="left")
        display = display[["Cumulative Return %"] + [c for c in display.columns if c != "Cumulative Return %"]]

        st.dataframe(
            display.style.format("{:.3f}").background_gradient(
                subset=[c for c in display.columns if c != "Cumulative Return %"],
                cmap="RdYlGn",
                axis=None,
            ),
            width="stretch",
            height=680,
        )

        st.download_button(
            label="Download correlation table CSV",
            data=display.to_csv().encode("utf-8"),
            file_name=f"ai_shovel_correlation_{selected_window}.csv",
            mime="text/csv",
        )

with tab_prices:
    st.dataframe(prices, width="stretch", height=680)

    st.download_button(
        label="Download adjusted close prices CSV",
        data=prices.to_csv().encode("utf-8"),
        file_name=f"ai_shovel_prices_{selected_window}.csv",
        mime="text/csv",
    )

with tab_industry_returns:
    if industry_index_cumulative.empty:
        st.warning("Industry index data is empty.")
    else:
        display = industry_index_cumulative * 100
        st.dataframe(display, width="stretch", height=680)

        st.download_button(
            label="Download industry index cumulative returns CSV",
            data=display.to_csv().encode("utf-8"),
            file_name=f"ai_shovel_industry_indexes_{selected_window}.csv",
            mime="text/csv",
        )


# =========================================================
# Methodology Footer
# =========================================================

st.divider()

st.markdown(
    """
    ### Methodology

    - **Data source:** `yfinance`
    - **Price field:** adjusted close via `auto_adjust=True`
    - **Daily return:** percentage change of adjusted close
    - **Cumulative return:** `(1 + daily return).cumprod() - 1`
    - **Industry index:** equal-weight average of available member daily returns
    - **Correlation:** Pearson correlation of daily returns
    - **Benchmark proxies:** `NVDA`, `AMD`, `SPY`, `QQQ`

    This dashboard is for research and monitoring only. It is not investment advice.
    """
)
