# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

The main application is a Streamlit dashboard. Run it using:
```bash
streamlit run app.py
```

Note: This project uses a virtual environment (`.venv`) with Python packages. If streamlit is not found globally, ensure the virtual environment is activated or use the venv python directly.

## Architecture Overview

This is a multi-timeframe trading dashboard built with a clear separation of concerns:

### Core Data Flow
1. **Data Ingestion** (`indicators.py`): Fetches market data from Yahoo Finance for three timeframes (1m, 5m, 15m) and computes technical indicators (VWAP, MACD, RSI, EMA)
2. **Strategy Analysis** (`strategy.py`): Implements multi-timeframe signal logic - 15m defines bias, 5m confirms, 1m provides entry signals
3. **Visualization** (`app.py`): Streamlit dashboard with real-time charts, replay functionality, and strategy results
4. **Utilities** (`utils.py`): Market calendar integration and custom UI components

### Key Technical Components

**Multi-Timeframe Strategy Pattern**: The strategy engine (`run_strategy_analysis`) requires alignment across all three timeframes before generating signals. This prevents trading on mixed signals and reduces false positives.

**Replay System**: The dashboard includes a day replay feature that simulates trading by advancing through historical data with configurable speed and window sizes. This is controlled via `st.session_state.replay_time` and auto-refresh mechanisms.

**Signal Detection**: The `find_entry_signals()` function uses vectorized pandas operations to identify all historical entry points where the multi-timeframe conditions aligned, enabling backtesting visualization.

**Data Alignment**: Each timeframe (1m, 5m, 15m) is reindexed to the 1-minute grid using forward-fill for consistent signal evaluation across different time intervals.

## Development Notes

- The app uses custom CSS styling embedded in `app.py` for dark theme and floating cards
- Session state management handles replay mode, timing, and data refresh cycles
- Market calendar integration ensures only valid trading days are processed
- Auto-refresh intervals: 60s for live mode, 1s for replay mode
- Chart height is configurable via sidebar to prevent page scrolling issues

## Data Dependencies

- **Yahoo Finance API**: Used for all market data via `yfinance` package
- **Market Calendar**: NYSE trading calendar via `pandas_market_calendars`
- **Technical Indicators**: Computed using `pandas_ta` library
- **Timezone Handling**: All data normalized to America/New_York timezone

The application gracefully handles API failures and missing data by displaying appropriate warnings and stopping execution rather than continuing with incomplete datasets.