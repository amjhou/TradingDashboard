# Trading Dashboard

A professional real-time trading dashboard built with Streamlit that provides multi-timeframe technical analysis and trading signals using VWAP, MACD, and RSI indicators.

## Features

- **Real-time Market Data**: Live price feeds via Yahoo Finance with auto-refresh
- **Multi-timeframe Analysis**: Synchronized 1-minute, 5-minute, and 15-minute charts
- **Technical Indicators**: VWAP, MACD, RSI, and EMA(50) with customizable parameters
- **Trading Signals**: Automated buy/sell signal generation with multi-timeframe confirmation
- **Day Replay Mode**: Simulate historical trading days with variable speed controls
- **Interactive Charts**: Candlestick and line charts with volume analysis
- **Professional UI**: Dark theme with responsive design and custom styling

## Strategy Overview

The dashboard implements a sophisticated multi-timeframe trading strategy:

1. **15-minute timeframe**: Defines overall market bias using VWAP slope and MACD trend
2. **5-minute timeframe**: Confirms the direction from the higher timeframe
3. **1-minute timeframe**: Provides precise entry signals with MACD crossovers and RSI momentum

Signals are only generated when all three timeframes align, reducing false positives and improving trade quality.

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd TradingDashboard
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/Scripts/activate  # On Windows
# source .venv/bin/activate    # On Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit application:
```bash
streamlit run app.py
```

The dashboard will open in your default web browser at `http://localhost:8501`.

### Dashboard Controls

- **Ticker Symbol**: Enter any valid stock symbol (default: SPY)
- **Trading Day**: Select from available trading days using market calendar
- **Chart Type**: Toggle between candlestick and line charts
- **Chart Height**: Adjust chart size to fit your screen
- **Time Range**: Manually select time window for analysis

### Replay Mode

- **Play Replay**: Activate day replay simulation
- **Replay Speed**: Control how fast time advances (1-30 minutes per refresh)
- **Window Size**: Set the visible time window during replay (15-120 minutes)

## Technical Requirements

- Python 3.8+
- Internet connection for market data
- Modern web browser

## Dependencies

Key libraries used:
- `streamlit`: Web application framework
- `yfinance`: Yahoo Finance market data
- `pandas`: Data manipulation and analysis
- `pandas-ta`: Technical analysis indicators
- `plotly`: Interactive charting
- `pytz`: Timezone handling
- `pandas-market-calendars`: Trading calendar integration

## Configuration

The application automatically handles:
- Market timezone conversion (America/New_York)
- Trading calendar validation
- Data caching with 55-second TTL
- Error handling and graceful degradation

## Disclaimer

This software is for educational and informational purposes only. It is not intended as financial advice or as a recommendation to buy or sell securities. Trading involves risk and may result in financial loss.

## License

This project is open source and available under the MIT License.