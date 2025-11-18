# Backtest System Documentation

## Overview

The Backtest System is a comprehensive web-based platform for backtesting trading strategies using the Backtrader library. It provides an intuitive interface for strategy management, execution, and performance analysis.

## Features

### 🌐 Web Interface
- **Dashboard**: Overview of strategies and recent results
- **Strategy Management**: Upload, view, and organize trading strategies
- **Backtest Configuration**: Easy setup of backtest parameters
- **Results Visualization**: Interactive charts and performance metrics

### 📊 Multi-Strategy Comparison
- Run multiple strategies simultaneously
- Side-by-side performance comparison
- Overlaid equity curves for visual analysis
- Comprehensive metrics comparison table

### 🧠 Strategy Support
- Support for any Backtrader-compatible strategy
- Parameter customization through web interface
- Sample strategies included (SMA Crossover, RSI, Bollinger Bands)
- Easy strategy upload and validation

### 📈 Analytics & Visualization
- **Performance Metrics**: Sharpe ratio, maximum drawdown, total return
- **Interactive Charts**: Plotly-powered charts with zoom and pan
- **Trade Analysis**: Number of trades, win rate, profit factor
- **Equity Curves**: Visual representation of strategy performance

## Quick Start

### Installation

1. **Clone or download the project**
```bash
cd /path/to/your/project/backtest-system
```

2. **Create virtual environment** (recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
python run.py
```

5. **Open your browser** to `http://localhost:5000`

### First Steps

1. **Explore Sample Strategies**: The system comes with three pre-built strategies
2. **Run a Backtest**: Use the "Run Backtest" page to test strategies
3. **Compare Results**: Add multiple strategies to compare performance
4. **Upload Custom Strategies**: Use the strategy management page to add your own

## Strategy Development

### Basic Strategy Structure

```python
import backtrader as bt

class MyStrategy(bt.Strategy):
    params = (
        ('period', 20),  # Strategy parameters
        ('stake', 100),
    )
    
    def __init__(self):
        # Initialize indicators
        self.sma = bt.indicators.SMA(period=self.params.period)
    
    def next(self):
        # Trading logic
        if not self.position:
            if self.data.close > self.sma:
                self.buy(size=self.params.stake)
        else:
            if self.data.close < self.sma:
                self.sell(size=self.params.stake)
```

### Strategy Requirements

1. **Inherit from bt.Strategy**
2. **Define parameters** using the `params` tuple
3. **Implement `__init__`** method for indicators
4. **Implement `next`** method for trading logic
5. **Use proper file naming** (no spaces, valid Python identifier)

### Parameter Definition

Parameters allow customization through the web interface:

```python
params = (
    ('fast_period', 10),    # Fast SMA period
    ('slow_period', 30),    # Slow SMA period
    ('stop_loss', 0.05),    # 5% stop loss
    ('stake', 100),         # Position size
)
```

## Web Interface Guide

### Dashboard
- **Quick Stats**: Overview of strategies and performance
- **Recent Results**: Latest backtest results
- **Quick Actions**: Navigate to key functions

### Strategy Management
- **View Strategies**: Browse available strategies
- **Upload New**: Add custom strategy files
- **Strategy Details**: View parameters and descriptions
- **Download Templates**: Get started with example code

### Backtest Configuration
- **Date Range**: Set start and end dates
- **Capital Settings**: Initial cash and commission
- **Symbol Selection**: Choose stocks to test
- **Strategy Selection**: Add multiple strategies with custom parameters

### Results Analysis
- **Performance Table**: Compare key metrics across strategies
- **Equity Curves**: Visual performance comparison
- **Detailed Analysis**: In-depth look at individual results
- **Export Options**: Save results for further analysis

## API Endpoints

### Strategy Management
- `GET /api/strategies/<name>` - Get strategy information

### Backtesting
- `POST /api/run-backtest` - Execute backtest with configuration

### Results
- Results are returned in JSON format with comprehensive metrics

## Configuration

### Environment Variables
Create a `.env` file based on `.env.example`:

```bash
SECRET_KEY=your-secret-key
DEBUG=True
HOST=127.0.0.1
PORT=5000
```

### Application Settings
Modify `config/settings.py` for advanced configuration:

- Default cash amounts
- Commission rates
- Data sources
- Performance limits

## Sample Strategies

### 1. SMA Crossover (`sma_crossover.py`)
- **Basic**: Simple moving average crossover
- **With Stop Loss**: Enhanced version with risk management
- **Parameters**: Fast/slow periods, position size, stop loss

### 2. RSI Strategy (`rsi_strategy.py`)
- **Basic RSI**: Overbought/oversold signals
- **Mean Reversion**: Multi-level RSI with trend filter
- **Parameters**: RSI period, thresholds, position sizes

### 3. Bollinger Bands (`bollinger_bands.py`)
- **Reversal**: Mean reversion at band touches
- **Breakout**: Momentum strategy on band breaks
- **Squeeze**: Low volatility breakout strategy
- **Parameters**: Band period, standard deviation, confirmation factors

## Performance Metrics

### Core Metrics
- **Total Return**: Overall percentage gain/loss
- **Sharpe Ratio**: Risk-adjusted return measure
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss

### Risk Metrics
- **Volatility**: Standard deviation of returns
- **Calmar Ratio**: Return vs. maximum drawdown
- **Sortino Ratio**: Downside deviation adjusted return

## Troubleshooting

### Common Issues

1. **Strategy Upload Fails**
   - Check Python syntax
   - Ensure class inherits from bt.Strategy
   - Verify file extension is .py

2. **Backtest Errors**
   - Check date ranges (weekends/holidays)
   - Verify symbol exists and has data
   - Ensure sufficient lookback period for indicators

3. **No Data Retrieved**
   - Check internet connection
   - Verify symbol spelling
   - Try different date ranges

### Debug Mode
Enable debug mode in `run.py` or set `DEBUG=True` in environment for detailed error messages.

## Advanced Features

### Custom Data Sources
Extend the system to support additional data sources by modifying `app/backtesting.py`.

### Additional Analyzers
Add more Backtrader analyzers in the backtesting engine for enhanced metrics.

### Custom Indicators
Create custom indicators following the Backtrader indicator framework.

## Best Practices

### Strategy Development
1. **Test Thoroughly**: Validate strategies with different market conditions
2. **Parameter Sensitivity**: Test how parameter changes affect performance
3. **Risk Management**: Always include position sizing and risk controls
4. **Documentation**: Add clear docstrings explaining strategy logic

### Backtesting
1. **Realistic Assumptions**: Use appropriate commission and slippage
2. **Sufficient Data**: Ensure enough historical data for reliable results
3. **Out-of-Sample Testing**: Reserve data for validation
4. **Multiple Timeframes**: Test across different market periods

### Performance Analysis
1. **Risk-Adjusted Returns**: Focus on Sharpe ratio, not just returns
2. **Drawdown Analysis**: Understand maximum potential losses
3. **Trade Analysis**: Examine individual trade characteristics
4. **Robustness**: Test sensitivity to parameter changes

## Support and Resources

### Backtrader Documentation
- Official Docs: https://www.backtrader.com/docu/
- Indicators Reference: Built-in technical indicators
- Strategy Examples: Community examples and tutorials

### Python Libraries
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Matplotlib/Plotly**: Charting and visualization
- **YFinance**: Market data retrieval

## Contributing

To contribute to the project:

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. See LICENSE file for details.
