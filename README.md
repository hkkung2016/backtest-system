# Backtest System

A comprehensive Python-based backtesting system powered by Backtrader with a web-based frontend for strategy comparison and visualization.

## Features

- 📊 **Web-based Dashboard**: Interactive visualizations running on localhost
- 🔄 **Multi-Strategy Comparison**: Compare multiple strategies side-by-side
- 📈 **Advanced Analytics**: Sharpe ratio, drawdown, returns analysis
- ⚡ **Easy Strategy Addition**: Simple framework for adding new strategies
- 📊 **Interactive Charts**: Plotly-powered charts with zoom, pan, and analysis tools

## Project Structure

```
backtest-system/
├── app/                    # Core Flask application
│   ├── __init__.py        # App factory
│   ├── backtesting.py     # Backtrader integration engine
│   ├── models.py          # Data models
│   └── routes.py          # Web routes & API endpoints
├── strategies/            # Trading strategies (3 samples included)
│   ├── sma_crossover.py   # Moving average strategies
│   ├── rsi_strategy.py    # RSI-based strategies
│   └── bollinger_bands.py # Bollinger Bands strategies
├── templates/             # HTML templates
│   ├── base.html          # Base template
│   ├── index.html         # Dashboard
│   ├── backtest.html      # Backtest configuration
│   ├── strategies.html    # Strategy management
│   └── results.html       # Results visualization
├── static/               # CSS & JavaScript
│   ├── css/style.css     # Custom styling
│   └── js/main.js        # Interactive functionality
├── config/               # Configuration
│   └── settings.py       # App settings
├── data/                 # Data storage
├── tests/                # Unit tests
├── run.py               # Main application runner
├── requirements.txt     # Dependencies
├── README.md           # Quick start guide
└── DOCUMENTATION.md    # Complete documentation
```

## Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python run.py
```

4. Open your browser to `http://localhost:5000`

## Quick Start

1. Add your strategies to the `strategies/` folder
2. Upload or configure data sources
3. Run backtests through the web interface
4. Compare results with interactive charts and analytics

## Usage

See the examples in the `strategies/` folder for creating new trading strategies.
