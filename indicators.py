# trading_dashboard/indicators.py

import pandas as pd
import pandas_ta as ta
import yfinance as yf
import streamlit as st
import pytz


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Computes technical indicators for a given dataframe."""
    if df is None or df.empty:
        return pd.DataFrame()

    # Standardize column names for pandas_ta
    df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"},
              inplace=True, errors='ignore')

    try:
        df.ta.vwap(append=True)
        df.ta.macd(close='close', fast=12, slow=26, signal=9, append=True)
        df.ta.rsi(close='close', length=14, append=True)
        df.ta.ema(length=50, append=True)

        if 'VWAP_D' in df.columns:
            df.rename(columns={'VWAP_D': 'VWAP'}, inplace=True)
        if 'RSI_14' in df.columns:
            df.rename(columns={'RSI_14': 'RSI'}, inplace=True)

        df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"},
                  inplace=True, errors='ignore')
        df.dropna(inplace=True)
    except Exception as e:
        st.error(f"Error in indicator calculation: {e}")
        return pd.DataFrame()
    return df


def _fetch_and_process(ticker: yf.Ticker, period: str, interval: str, name: str) -> pd.DataFrame:
    """Helper function to fetch, process, and handle errors for one timeframe."""
    try:
        df = ticker.history(period=period, interval=interval, auto_adjust=True)
        if df.empty:
            st.warning(f"No data returned for {name} timeframe. The API may have limitations for the requested period.")
            return pd.DataFrame()

        if df.index.tz is None:
            df = df.tz_localize('America/New_York', ambiguous='infer')
        else:
            df = df.tz_convert('America/New_York')

        return compute_indicators(df)
    except Exception as e:
        st.error(f"Failed to get {name} data: {e}")
        return pd.DataFrame()


def process_all_timeframes(ticker_symbol: str):
    """
    Fetches and processes data for 1m, 5m, and 15m timeframes directly
    using optimized historical periods for each.
    """
    ticker = yf.Ticker(ticker_symbol)

    # 1. Fetch 1-minute data (limited to last 7 days by API)
    df_1m = _fetch_and_process(ticker, period="7d", interval="1m", name="1-minute")

    # 2. Fetch 5m & 15m data (can go back further, e.g., 60 days)
    # This provides a long, stable history for calculating slow indicators like EMA(50).
    df_5m = _fetch_and_process(ticker, period="60d", interval="5m", name="5-minute")
    df_15m = _fetch_and_process(ticker, period="60d", interval="15m", name="15-minute")

    return df_1m, df_5m, df_15m