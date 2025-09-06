# trading_dashboard/indicators.py

import pandas as pd
import numpy as np
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
        # Calculate VWAP manually (Volume Weighted Average Price)
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        df['VWAP'] = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        
        # Calculate EMA manually
        def calculate_ema(prices, period):
            alpha = 2 / (period + 1)
            ema = prices.ewm(alpha=alpha, adjust=False).mean()
            return ema
        
        df['EMA_50'] = calculate_ema(df['close'], 50)
        
        # Calculate MACD manually
        ema_12 = calculate_ema(df['close'], 12)
        ema_26 = calculate_ema(df['close'], 26)
        df['MACD_12_26_9'] = ema_12 - ema_26
        df['MACDs_12_26_9'] = calculate_ema(df['MACD_12_26_9'], 9)
        df['MACDh_12_26_9'] = df['MACD_12_26_9'] - df['MACDs_12_26_9']
        
        # Calculate RSI manually
        def calculate_rsi(prices, period=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        df['RSI'] = calculate_rsi(df['close'])

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