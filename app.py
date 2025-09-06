# trading_dashboard/app.py

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from indicators import process_all_timeframes
from utils import display_summary_cards, get_valid_trading_dates
from strategy import run_strategy_analysis, find_entry_signals
from datetime import datetime, date, time, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh

# ─── Streamlit Page Config & Custom CSS ──────────────────────────────────────
st.set_page_config(
    page_title="Pro Trading Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📈"
)


def load_css():
    """Simple CSS for custom floating cards only."""
    st.markdown("""
        <style>
            .floating-card-container {
                display: flex; 
                flex-wrap: wrap; 
                justify-content: space-around;
                padding: 1rem 0; 
                margin-bottom: 1rem;
                gap: 1rem;
            }
            
            .floating-card {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                padding: 1.5rem; 
                text-align: center;
                flex: 1; 
                min-width: 200px; 
                transition: all 0.3s ease;
            }
            
            .floating-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            
            .card-title { 
                font-size: 0.9rem; 
                color: #666; 
                margin-bottom: 0.5rem; 
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .card-value { 
                font-size: 2rem; 
                font-weight: 700; 
                color: #333; 
                line-height: 1.2;
                margin-bottom: 0.5rem;
            }
            
            .card-delta { 
                font-size: 0.9rem; 
                font-weight: 600;
                padding: 4px 8px;
                border-radius: 4px;
                display: inline-block;
            }
            
            .green-text { 
                color: #28a745;
                background-color: rgba(40, 167, 69, 0.1);
            }
            
            .red-text { 
                color: #dc3545;
                background-color: rgba(220, 53, 69, 0.1);
            }
        </style>
    """, unsafe_allow_html=True)


load_css()

# ─── Initialize Session State for Replay ─────────────────────────────────────
if 'replay_time' not in st.session_state:
    st.session_state.replay_time = None
if 'is_playing' not in st.session_state:
    st.session_state.is_playing = False

# ─── Sidebar Controls ──────────────────────────────────────────────────────────
st.sidebar.header("Dashboard Controls")
ticker = st.sidebar.text_input("Ticker Symbol", "SPY").upper()
ny_tz = pytz.timezone("America/New_York")
today_ny = datetime.now(ny_tz).date()

year_start = date(today_ny.year - 1, today_ny.month, today_ny.day)
valid_dates = get_valid_trading_dates(start_date=year_start, end_date=today_ny)
if len(valid_dates) == 0:
    st.error("Could not retrieve market calendar.");
    st.stop()

selected_date = st.sidebar.date_input("Select Trading Day", value=valid_dates[-1], min_value=valid_dates[0],
                                      max_value=valid_dates[-1])
if selected_date not in valid_dates:
    st.error(f"{selected_date} is not a valid trading day.");
    st.stop()

# MODIFICATION: Add Chart Height slider to prevent page scrolling
chart_height = st.sidebar.slider(
    "Chart Height",
    min_value=400, max_value=1000, value=600, step=50,
    help="Adjust chart height to fit your screen and avoid scrolling."
)

chart_type = st.sidebar.radio("Select Chart Type", ('Candlestick', 'Line'))

market_open_time, market_close_time = time(9, 30), time(16, 0)
market_open_dt = ny_tz.localize(datetime.combine(selected_date, market_open_time))
market_close_dt = ny_tz.localize(datetime.combine(selected_date, market_close_time))

is_replay_mode = st.session_state.is_playing
selected_time_range = st.sidebar.slider(
    "Manual Time Range",
    min_value=market_open_dt, max_value=market_close_dt,
    value=(market_open_dt, market_close_dt),
    step=timedelta(minutes=1), format="HH:mm",
    disabled=is_replay_mode
)

# ─── Day Replay Controls ─────────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.header("📅 Day Replay Controls")
st.sidebar.caption("Simulate the trading day.")

is_playing_toggle = st.sidebar.toggle("▶️ Play Replay", value=st.session_state.is_playing)
if is_playing_toggle != st.session_state.is_playing:
    st.session_state.is_playing = is_playing_toggle
    if st.session_state.is_playing and st.session_state.replay_time is None:
        st.session_state.replay_time = selected_time_range[0] + timedelta(minutes=60)
    st.rerun()

replay_speed_mins = st.sidebar.select_slider(
    "Replay Speed (minutes per refresh)",
    options=[1, 2, 5, 10, 15, 30], value=5, disabled=is_replay_mode
)

# MODIFICATION: Add Replay Window Size slider for the panning window
window_size_mins = st.sidebar.select_slider(
    "Replay Window Size (minutes)",
    options=[15, 30, 60, 90, 120], value=60,
    help="Controls the duration of the visible chart window during replay.",
    disabled=is_replay_mode
)
window_delta = timedelta(minutes=window_size_mins)

if st.sidebar.button("🔄 Reset Replay", use_container_width=True):
    st.session_state.is_playing = False
    st.session_state.replay_time = None
    st.rerun()

# ─── App Status & Manual Refresh ─────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.header("⚙️ App Status")
if is_replay_mode and st.session_state.replay_time:
    st.sidebar.info(f"Replay Time: **{st.session_state.replay_time.strftime('%H:%M')}**")

is_live_mode = (selected_date == today_ny and not st.session_state.is_playing)
if is_replay_mode:
    st.sidebar.info(f"Replay is ON (refreshing every 1s).")
elif is_live_mode:
    st.sidebar.success(f"Live Mode is ON (refreshing every 60s).")
else:
    st.sidebar.warning("Live Mode is OFF (viewing historical data).")

if st.sidebar.button("🔄 Refresh Data Now", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ─── Auto-Refresh & Replay Logic ─────────────────────────────────────────────
refresh_interval = 1000 if st.session_state.is_playing else 60000
if st.session_state.is_playing or is_live_mode:
    st_autorefresh(interval=refresh_interval, key="main_refresh")

if st.session_state.is_playing and st.session_state.replay_time is not None:
    replay_increment = timedelta(minutes=replay_speed_mins)
    new_time = st.session_state.replay_time + replay_increment
    if new_time >= market_close_dt:
        st.session_state.replay_time = market_close_dt
        st.session_state.is_playing = False
    else:
        st.session_state.replay_time = new_time

# ─── Main App Body ───────────────────────────────────────────────────────────
st.title(f"📈 Pro Trading Dashboard – {ticker}")


@st.cache_data(ttl=55)
def load_data(ticker_symbol):
    return process_all_timeframes(ticker_symbol)


with st.spinner(f"Fetching market data for {ticker}..."):
    df_1m, df_5m, df_15m = load_data(ticker)

if df_1m.empty or df_5m.empty or df_15m.empty:
    st.error(f"Failed to fetch complete data for {ticker}.");
    st.stop()

df_1m_day = df_1m[df_1m.index.date == selected_date]
df_5m_day = df_5m[df_5m.index.date == selected_date]
df_15m_day = df_15m[df_15m.index.date == selected_date]

# MODIFICATION: Logic for panning window during replay
if is_replay_mode and st.session_state.replay_time is not None:
    analysis_end_time = st.session_state.replay_time
    chart_start_time = st.session_state.replay_time - window_delta
    if chart_start_time < market_open_dt: chart_start_time = market_open_dt
    df_chart = df_1m_day.loc[chart_start_time:analysis_end_time]
else:
    analysis_end_time = selected_time_range[1]
    df_chart = df_1m_day.loc[selected_time_range[0]:selected_time_range[1]]

analysis_df_1m = df_1m_day.loc[:analysis_end_time]
analysis_df_5m = df_5m_day.loc[:analysis_end_time]
analysis_df_15m = df_15m_day.loc[:analysis_end_time]

if df_chart.empty:
    st.warning("No data available for the selected time range.");
    st.stop()

latest_in_view = df_chart.iloc[-1]
analysis = run_strategy_analysis(analysis_df_1m, analysis_df_5m, analysis_df_15m)
buy_signals, sell_signals = find_entry_signals(analysis_df_1m, analysis_df_5m, analysis_df_15m)

tab1, tab2 = st.tabs(["📊 Chart & Analysis", "📘 Strategy Guide"])

with tab1:
    display_summary_cards(latest_in_view, analysis)

    with st.container(border=True):
        overall_signal, overall_emoji, overall_text = analysis['overall']
        st.header(f"Live Signal: {overall_signal} {overall_emoji}")
        st.caption(overall_text)
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1: st.metric(label="1️⃣ 15-min Bias", value=analysis['15m']['bias'][0],
                             delta=analysis['15m']['bias'][1])
        with col2: st.metric(label="2️⃣ 5-min Confirmation", value=analysis['5m']['confirm'][0],
                             delta=analysis['5m']['confirm'][1])
        with col3: st.metric(label="3️⃣ 1-min Entry", value=analysis['1m']['entry'][0],
                             delta=analysis['1m']['entry'][1])

    st.markdown("---")

    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.6, 0.1, 0.15, 0.15])

    if chart_type == 'Line':
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Close'], name='Close', line=dict(color='#00A0B0')),
                      row=1, col=1)
    else:
        fig.add_trace(
            go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'],
                           close=df_chart['Close'], name='Price'), row=1, col=1)

    fig.add_trace(
        go.Scatter(x=df_chart.index, y=df_chart['VWAP'], name='VWAP', line=dict(color='#F0A800', dash='dash')), row=1,
        col=1)
    fig.add_trace(
        go.Scatter(x=df_chart.index, y=df_chart['EMA_50'], name='EMA 50', line=dict(color='#C71585', width=1)), row=1,
        col=1)
    fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['Price'], mode='markers', marker_symbol='triangle-up',
                             marker_color='#00FE35', marker_size=12, name='Buy Signal'), row=1, col=1)
    fig.add_trace(
        go.Scatter(x=sell_signals.index, y=sell_signals['Price'], mode='markers', marker_symbol='triangle-down',
                   marker_color='#FF3333', marker_size=12, name='Sell Signal'), row=1, col=1)

    volume_colors = ['#26A69A' if row['Close'] >= row['Open'] else '#EF5350' for index, row in df_chart.iterrows()]
    fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['Volume'], name='Volume', marker_color=volume_colors), row=2,
                  col=1)

    fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['RSI'], name='RSI', line=dict(color='#FFD700')), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)

    macd_colors = ['#26A69A' if val >= 0 else '#EF5350' for val in df_chart['MACDh_12_26_9']]
    fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['MACDh_12_26_9'], name='Histogram', marker_color=macd_colors),
                  row=4, col=1)
    fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MACD_12_26_9'], name='MACD', line=dict(color='#4472C4')),
                  row=4, col=1)
    fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MACDs_12_26_9'], name='Signal',
                             line=dict(color='#ED7D31', dash='dot')), row=4, col=1)

    config = {'scrollZoom': True, 'displaylogo': False, 'responsive': True}
    fig.update_layout(
        height=chart_height,
        showlegend=True, template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_rangeslider_visible=False, margin=dict(l=30, r=30, t=30, b=30)
    )
    st.plotly_chart(fig, use_container_width=True, config=config)

with tab2:
    st.header("📘 Trading Strategy Guide")
    st.markdown("### Intraday Trading Strategy: VWAP + MACD + RSI with Multi-Timeframe Confirmation")
    with st.expander("🔧 Indicators Used", expanded=True):
        st.markdown(
            "- **VWAP (Volume-Weighted Average Price):** Acts as 'gravity' or the mean fair value for the session. \n- **MACD (Moving Average Convergence Divergence):** Detects trend direction and momentum. \n- **RSI (Relative Strength Index):** Confirms momentum and identifies potential exhaustion points.")
    with st.expander("📈 Core Trading Logic & Flow", expanded=True):
        st.markdown(
            "#### Multi-Timeframe Strategy Flow \n- **Step 1: 15-min (Define Bias):** Use VWAP slope and MACD to determine the main trend. \n- **Step 2: 5-min (Confirm Trend):** Check if the 5-min timeframe agrees with the 15-min bias. \n- **Step 3: 1-min (Execute Entry):** Use the 1-minute chart for a precise entry signal. \n\n**🔒 Only enter if all three timeframes point in the same direction.**")
    with st.expander("✅ Trade Entry Checklist"):
        st.markdown(
            "1. Is the price near VWAP? \n2. Are the 15-min MACD and VWAP slope aligned? \n3. Does the 5-min chart confirm this direction? \n4. Is a MACD crossover occurring on the 1-min chart? \n5. Is the RSI showing strength and not at an exhaustion level?")
    with st.expander("🛑 Exit Plan & Risk Management"):
        st.markdown(
            "- **Profit Target:** A key resistance/support level, or when momentum weakens. \n- **Stop Loss:** Below a recent swing low (for buys) or above a swing high (for sells). \n- **Warning Signs:** Exit on RSI divergence or a decisive break of VWAP.")
    with st.expander("⚠️ Common Pitfalls to Avoid"):
        st.markdown("- **Ignoring Higher Timeframes.** \n- **Trading in Chop.** \n- **Conflicting Indicators.**")