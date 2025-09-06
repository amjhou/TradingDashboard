# trading_dashboard/strategy.py

import pandas as pd
import numpy as np


def get_vwap_status(price, vwap, vwap_series):
    """
    Analyzes the price relative to VWAP and the VWAP's trend.
    RETURNS: A tuple of (status_text, status_emoji, raw_slope_string).
    """
    if vwap is None or pd.isna(vwap):
        return "Not Available", "⚪", "N/A"  # Return 3 items

    if len(vwap_series) < 5:
        slope = "Flat"
    else:
        slope_val = np.polyfit(range(5), vwap_series.tail(5), 1)[0]
        if slope_val > 0.001:
            slope = "Rising"
        elif slope_val < -0.001:
            slope = "Falling"
        else:
            slope = "Flat"

    if price > vwap and slope == "Rising":
        return "Bullish Bias", "🟢", slope
    elif price < vwap and slope == "Falling":
        return "Bearish Bias", "🔴", slope
    elif abs(price - vwap) / price < 0.001:
        return f"Near VWAP ({slope})", "🟡", slope
    else:
        text = f"Price > VWAP ({slope})" if price > vwap else f"Price < VWAP ({slope})"
        return text, "⚪", slope


# The get_macd_status and get_rsi_status functions remain unchanged
def get_macd_status(macd, signal, hist):
    if macd is None or pd.isna(macd): return "Not Available", "⚪"
    if macd > signal and hist > 0:
        return "Bullish Trend", "🟢"
    elif macd < signal and hist < 0:
        return "Bearish Trend", "🔴"
    else:
        return "No Clear Trend", "🟡"


def get_rsi_status(rsi):
    if rsi is None or pd.isna(rsi): return "Not Available", "⚪"
    if rsi > 70:
        return f"Overbought ({rsi:.1f})", "🔴"
    elif rsi < 30:
        return f"Oversold ({rsi:.1f})", "🟢"
    elif rsi > 50:
        return f"Bullish Momentum ({rsi:.1f})", "🟢"
    else:
        return f"Bearish Momentum ({rsi:.1f})", "🔴"


def run_strategy_analysis(df_1m, df_5m, df_15m):
    """Runs the full multi-timeframe analysis and returns a results dictionary."""
    results = {
        '15m': {'bias': ('', '', '')},
        '5m': {'confirm': ('', '', '')},
        '1m': {'entry': ('', ''), 'vwap': ('', '', '')},
        'checklist': {},
        'overall': ('Hold', '⚪', 'Waiting for alignment...')
    }

    if df_1m.empty or df_5m.empty or df_15m.empty:
        results['overall'] = ('Error', '❌', 'Not enough data for all timeframes.')
        return results

    latest_1m, latest_5m, latest_15m = df_1m.iloc[-1], df_5m.iloc[-1], df_15m.iloc[-1]

    # Unpack 3 items from get_vwap_status
    vwap1_status, vwap1_emoji, vwap1_slope = get_vwap_status(latest_1m['Close'], latest_1m['VWAP'], df_1m['VWAP'])
    results['1m']['vwap'] = (vwap1_status, vwap1_emoji, vwap1_slope)

    vwap15_status, vwap15_emoji, vwap15_slope = get_vwap_status(latest_15m['Close'], latest_15m['VWAP'], df_15m['VWAP'])
    macd15_status, macd15_emoji = get_macd_status(latest_15m['MACD_12_26_9'], latest_15m['MACDs_12_26_9'],
                                                  latest_15m['MACDh_12_26_9'])
    results['15m']['bias'] = (f"{vwap15_status}", vwap15_emoji if vwap15_emoji != '⚪' else macd15_emoji)

    vwap5_status, vwap5_emoji, vwap5_slope = get_vwap_status(latest_5m['Close'], latest_5m['VWAP'], df_5m['VWAP'])
    macd5_status, macd5_emoji = get_macd_status(latest_5m['MACD_12_26_9'], latest_5m['MACDs_12_26_9'],
                                                latest_5m['MACDh_12_26_9'])
    results['5m']['confirm'] = (f"{vwap5_status}", vwap5_emoji if vwap5_emoji != '⚪' else macd5_emoji)

    rsi1_status, rsi1_emoji = get_rsi_status(latest_1m['RSI'])
    macd1_status, macd1_emoji = get_macd_status(latest_1m['MACD_12_26_9'], latest_1m['MACDs_12_26_9'],
                                                latest_1m['MACDh_12_26_9'])
    results['1m']['entry'] = (f"{macd1_status} & {rsi1_status}", macd1_emoji if macd1_emoji != '⚪' else rsi1_emoji)

    # The rest of the function logic remains the same
    bias_emoji, confirm_emoji, entry_emoji = results['15m']['bias'][1], results['5m']['confirm'][1], \
    results['1m']['entry'][1]
    if bias_emoji == '🟢' and confirm_emoji == '🟢' and entry_emoji == '🟢':
        results['overall'] = ('BULLISH', '🟢', 'All timeframes aligned for a bullish entry signal.')
    elif bias_emoji == '🔴' and confirm_emoji == '🔴' and entry_emoji == '🔴':
        results['overall'] = ('BEARISH', '🔴', 'All timeframes aligned for a bearish entry signal.')
    else:
        results['overall'] = ('HOLD', '🟡', 'Timeframes are not in full alignment. Wait for a clearer signal.')

    return results


def find_entry_signals(df_1m, df_5m, df_15m):
    """
    Analyzes historical data to find all points where a trade entry signal occurred.
    Uses a vectorized approach for efficiency.
    Returns two dataframes: one for buy signals, one for sell signals.
    """
    if df_1m.empty or df_5m.empty or df_15m.empty:
        return pd.DataFrame(), pd.DataFrame()

    # 1. Align all timeframes to the 1-minute index for row-by-row comparison
    df_5m_aligned = df_5m.reindex(df_1m.index, method='ffill')
    df_15m_aligned = df_15m.reindex(df_1m.index, method='ffill')

    # 2. Define conditions for each timeframe based on the strategy
    # 15-Minute Bullish Bias
    is_15m_bullish = (df_15m_aligned['Close'] > df_15m_aligned['VWAP']) & (
                df_15m_aligned['MACD_12_26_9'] > df_15m_aligned['MACDs_12_26_9'])
    is_15m_bearish = (df_15m_aligned['Close'] < df_15m_aligned['VWAP']) & (
                df_15m_aligned['MACD_12_26_9'] < df_15m_aligned['MACDs_12_26_9'])

    # 5-Minute Bullish Confirmation
    is_5m_bullish = (df_5m_aligned['Close'] > df_5m_aligned['VWAP']) & (
                df_5m_aligned['MACD_12_26_9'] > df_5m_aligned['MACDs_12_26_9'])
    is_5m_bearish = (df_5m_aligned['Close'] < df_5m_aligned['VWAP']) & (
                df_5m_aligned['MACD_12_26_9'] < df_5m_aligned['MACDs_12_26_9'])

    # 1-Minute Entry Trigger: A MACD crossover event
    macd_cross_up = (df_1m['MACD_12_26_9'] > df_1m['MACDs_12_26_9']) & (
                df_1m['MACD_12_26_9'].shift(1) < df_1m['MACDs_12_26_9'].shift(1))
    macd_cross_down = (df_1m['MACD_12_26_9'] < df_1m['MACDs_12_26_9']) & (
                df_1m['MACD_12_26_9'].shift(1) > df_1m['MACDs_12_26_9'].shift(1))

    # --- UPDATED RSI FILTER ---
    # Require RSI > 50 for buys and RSI < 50 for sells to confirm momentum.
    is_rsi_ok_for_buy = (df_1m['RSI'] > 50) & (df_1m['RSI']<70)
    is_rsi_ok_for_sell = (df_1m['RSI'] < 50) & (df_1m['RSI']>30)

    # 3. Combine all conditions for the final signal
    is_buy_signal = is_15m_bullish & is_5m_bullish & macd_cross_up & is_rsi_ok_for_buy
    is_sell_signal = is_15m_bearish & is_5m_bearish & macd_cross_down & is_rsi_ok_for_sell

    # 4. Extract the exact points in time where signals occurred
    buy_points = df_1m[is_buy_signal]
    sell_points = df_1m[is_sell_signal]

    # 5. Prepare dataframes for plotting markers on the chart
    buy_signals = pd.DataFrame({'Price': buy_points['Low'] * 0.998}, index=buy_points.index)
    sell_signals = pd.DataFrame({'Price': sell_points['High'] * 1.002}, index=sell_points.index)

    return buy_signals, sell_signals