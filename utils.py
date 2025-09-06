# trading_dashboard/utils.py

import streamlit as st
import pandas as pd
import pandas_market_calendars as mcal
from datetime import date
from time import time

# utils.py (add this function)
def get_market_hours(trading_date):
    """Get market open/close times for a given date"""
    # Implement logic to get actual market hours from calendar
    # This is a placeholder implementation
    return time(9, 30), time(16, 0)

# get_valid_trading_dates function remains unchanged
def get_valid_trading_dates(start_date: date, end_date: date) -> pd.DatetimeIndex:
    nyse = mcal.get_calendar('NYSE')
    schedule = nyse.schedule(start_date=start_date, end_date=end_date)
    return schedule.index.date


def display_summary_cards(latest_data: pd.Series, analysis_results: dict):
    """Displays key metrics in custom-styled "floating" cards."""
    st.subheader("Live Market Snapshot")

    if latest_data.empty:
        st.warning("No data available to display summary cards.")
        return

    # Extract latest values
    price = latest_data.get('Close', 0)
    vwap = latest_data.get('VWAP', 0)
    rsi = latest_data.get('RSI', 0)
    macd_hist = latest_data.get('MACDh_12_26_9', 0)

    # --- VWAP Slope Analysis (UPDATED) ---
    # Get the raw slope string directly from the 3rd item in the analysis tuple
    slope_text = analysis_results.get('1m', {}).get('vwap', ('', '', 'N/A'))[2]

    slope_emoji = '⚪ N/A'  # Default value
    if slope_text == 'Rising':
        slope_emoji = '↗️ Rising'
    elif slope_text == 'Falling':
        slope_emoji = '↘️ Falling'
    elif slope_text == 'Flat':
        slope_emoji = '↔️ Flat'

    # The rest of the function remains the same
    price_vwap_delta = price - vwap
    price_vwap_color = 'green-text' if price_vwap_delta >= 0 else 'red-text'
    macd_hist_color = 'green-text' if macd_hist >= 0 else 'red-text'
    rsi_color = ''
    if rsi > 70:
        rsi_color = 'red-text'
    elif rsi < 30:
        rsi_color = 'green-text'

    # HTML for the floating cards
    cards_html = f"""
    <div class="floating-card-container">
        <div class="floating-card">
            <p class="card-title">PRICE</p>
            <p class="card-value">${price:.2f}</p>
        </div>
        <div class="floating-card">
            <p class="card-title">VWAP</p>
            <p class="card-value">${vwap:.2f}</p>
            <p class="card-delta">SLOPE: {slope_emoji}</p>
        </div>
        <div class="floating-card">
            <p class="card-title">RSI</p>
            <p class="card-value {rsi_color}">{rsi:.1f}</p>
        </div>
        <div class="floating-card">
            <p class="card-title">MACD HISTOGRAM</p>
            <p class="card-value {macd_hist_color}">{macd_hist:+.3f}</p>
        </div>
    </div>
    """
    st.markdown(cards_html, unsafe_allow_html=True)