"""
Strategy Template for Backtest System

This is a comprehensive template for creating new trading strategies.
Copy this file and modify it to implement your own trading logic.

Key Components:
1. Strategy class with parameters
2. Indicators initialization
3. Trading logic in next() method
4. Order and trade notifications (optional)
5. Logging integration

Guidelines:
- Keep the strategy focused on a single concept
- Use clear parameter names with good defaults
- Add comprehensive logging for debugging
- Handle edge cases (no position, pending orders)
- Use consistent naming conventions
"""

import backtrader as bt
import sys
import os

# Add parent directory to path to access logging config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.logging_config import get_logger


class TemplateStrategy(bt.Strategy):
    """
    Template Strategy
    
    Description: [Describe your strategy logic here]
    
    Entry Conditions:
    - [List your buy/entry conditions]
    
    Exit Conditions:
    - [List your sell/exit conditions]
    
    Risk Management:
    - [Describe any risk management rules]
    """
    
    # ===== PARAMETERS =====
    # Define all configurable parameters with good defaults
    params = (
        # Trading parameters
        ('stake', 100),                    # Number of shares to trade
        
        # Strategy-specific parameters (customize these)
        ('fast_period', 10),               # Fast moving average period
        ('slow_period', 30),               # Slow moving average period
        ('rsi_period', 14),                # RSI period
        ('rsi_oversold', 30),              # RSI oversold threshold
        ('rsi_overbought', 70),            # RSI overbought threshold
        
        # Risk management parameters
        ('stop_loss_pct', 0.05),           # Stop loss percentage (5%)
        ('take_profit_pct', 0.10),         # Take profit percentage (10%)
        ('max_position_size', 1000),       # Maximum position size
        
        # Optional parameters
        ('debug_mode', False),             # Enable extra logging
        ('min_volume', 0),                 # Minimum volume requirement
    )
    
    def __init__(self):
        """
        Initialize the strategy with indicators and variables.
        
        This method is called once when the strategy is created.
        Define all indicators and instance variables here.
        """
        # Initialize logging
        self.logger = get_logger('strategies')
        
        # ===== INDICATORS =====
        # Define all technical indicators you'll use
        
        # Moving averages
        self.fast_ma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.fast_period
        )
        self.slow_ma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.slow_period
        )
        
        # RSI indicator
        self.rsi = bt.indicators.RelativeStrengthIndex(
            self.datas[0], period=self.params.rsi_period
        )
        
        # Volume indicator
        self.volume_sma = bt.indicators.SimpleMovingAverage(
            self.datas[0].volume, period=20
        )
        
        # Price indicators
        self.high_20 = bt.indicators.Highest(self.datas[0].high, period=20)
        self.low_20 = bt.indicators.Lowest(self.datas[0].low, period=20)
        
        # ===== INSTANCE VARIABLES =====
        # Track orders and positions
        self.order = None                  # Track pending orders
        self.entry_price = 0               # Track entry price for risk management
        self.stop_loss_price = 0           # Stop loss price
        self.take_profit_price = 0         # Take profit price
        
        # Strategy state variables
        self.signal_strength = 0           # Custom signal strength indicator
        self.bars_in_position = 0          # Count bars since entry
        
        # Logging
        if self.params.debug_mode:
            self.logger.info("Template Strategy initialized with parameters:")
            for param_name, param_value in self.params._getpairs():
                self.logger.info(f"  {param_name}: {param_value}")
    
    def next(self):
        """
        Main trading logic - called for each new bar.
        
        This is where you implement your strategy's decision-making logic.
        It's called once for each bar in your data.
        """
        # Skip if we have a pending order
        if self.order:
            return
        
        # Get current market data
        current_price = self.data.close[0]
        current_volume = self.data.volume[0]
        current_date = self.data.datetime.date(0)
        
        # ===== ENTRY LOGIC =====
        if not self.position:
            # Not in market - look for entry signals
            
            # Example entry conditions (customize these)
            buy_signal = self._check_buy_conditions(current_price, current_volume)
            
            if buy_signal:
                # Calculate position size
                position_size = self._calculate_position_size(current_price)
                
                # Place buy order
                self.order = self.buy(size=position_size)
                self.entry_price = current_price
                
                # Set risk management levels
                self.stop_loss_price = current_price * (1 - self.params.stop_loss_pct)
                self.take_profit_price = current_price * (1 + self.params.take_profit_pct)
                
                if self.params.debug_mode:
                    self.logger.info(f'BUY SIGNAL - Price: ${current_price:.2f}, '
                          f'Size: {position_size}, Stop: ${self.stop_loss_price:.2f}, '
                          f'Target: ${self.take_profit_price:.2f}')
        
        else:
            # In market - look for exit signals
            self.bars_in_position += 1
            
            # Check exit conditions
            exit_signal = self._check_exit_conditions(current_price)
            
            if exit_signal:
                # Place sell order
                self.order = self.sell(size=self.position.size)
                
                # Calculate P&L
                pnl = (current_price - self.entry_price) * self.position.size
                pnl_pct = (current_price / self.entry_price - 1) * 100
                
                if self.params.debug_mode:
                    self.logger.info(f'SELL SIGNAL - Price: ${current_price:.2f}, '
                          f'P&L: ${pnl:.2f} ({pnl_pct:.2f}%), '
                          f'Bars held: {self.bars_in_position}')
                
                # Reset position tracking
                self.bars_in_position = 0
    
    def _check_buy_conditions(self, price, volume):
        """
        Check if buy conditions are met.
        
        Args:
            price: Current price
            volume: Current volume
            
        Returns:
            bool: True if should buy, False otherwise
        """
        # Example buy conditions - customize these
        conditions = [
            # Moving average crossover
            self.fast_ma[0] > self.slow_ma[0],
            self.fast_ma[-1] <= self.slow_ma[-1],  # Just crossed over
            
            # RSI not overbought
            self.rsi[0] < self.params.rsi_overbought,
            
            # Volume confirmation
            volume > self.volume_sma[0] * 1.2,
            
            # Price above minimum volume requirement
            volume >= self.params.min_volume,
            
            # Price trend confirmation
            price > self.data.close[-5],  # Higher than 5 bars ago
        ]
        
        # All conditions must be True
        return all(conditions)
    
    def _check_exit_conditions(self, price):
        """
        Check if exit conditions are met.
        
        Args:
            price: Current price
            
        Returns:
            bool: True if should exit, False otherwise
        """
        # Example exit conditions - customize these
        conditions = [
            # Stop loss
            price <= self.stop_loss_price,
            
            # Take profit
            price >= self.take_profit_price,
            
            # Moving average exit signal
            self.fast_ma[0] < self.slow_ma[0],
            
            # RSI overbought
            self.rsi[0] > self.params.rsi_overbought,
            
            # Maximum holding period (optional)
            self.bars_in_position >= 50,  # Exit after 50 bars
        ]
        
        # Any condition can trigger exit
        return any(conditions)
    
    def _calculate_position_size(self, price):
        """
        Calculate position size based on risk management rules.
        
        Args:
            price: Current entry price
            
        Returns:
            int: Number of shares to buy
        """
        # Simple position sizing - you can make this more sophisticated
        base_size = self.params.stake
        
        # Don't exceed maximum position size
        max_size = min(base_size, self.params.max_position_size)
        
        # Ensure we can afford the position
        cash = self.broker.getcash()
        affordable_size = int(cash / price)
        
        return min(max_size, affordable_size)
    
    def notify_order(self, order):
        """
        Handle order notifications.
        
        This method is called whenever an order status changes.
        The system-level TradeAnalyzer handles most logging, but you can
        add strategy-specific order handling here if needed.
        """
        # Reset order tracking when order is completed/cancelled
        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            self.order = None
        
        # Optional: Add custom order handling logic here
        if self.params.debug_mode and order.status == order.Completed:
            self.logger.info(f'Order completed: {order.tradeid}, '
                  f'Size: {order.executed.size}, Price: ${order.executed.price:.2f}')
    
    def notify_trade(self, trade):
        """
        Handle trade notifications.
        
        This method is called when a trade is closed.
        The system-level TradeAnalyzer handles most logging, but you can
        add strategy-specific trade analysis here if needed.
        """
        if not trade.isclosed:
            return
        
        # Optional: Add custom trade analysis here
        if self.params.debug_mode:
            self.logger.info(f'Trade closed: P&L=${trade.pnl:.2f}, '
                  f'Duration: {trade.barlen} bars')
    
    def stop(self):
        """
        Called when the strategy finishes.
        
        This method is called once at the end of the backtest.
        Use it for final calculations or cleanup.
        """
        if self.params.debug_mode:
            final_value = self.broker.getvalue()
            self.logger.info(f'Strategy finished. Final portfolio value: ${final_value:.2f}')


# ===== ADDITIONAL STRATEGY EXAMPLES =====

class SimpleMovingAverageCrossover(bt.Strategy):
    """
    Simple example strategy: Buy when fast MA crosses above slow MA.
    """
    
    params = (
        ('fast_period', 10),
        ('slow_period', 30),
        ('stake', 100),
    )
    
    def __init__(self):
        self.logger = get_logger('strategies')
        self.fast_ma = bt.indicators.SMA(self.datas[0], period=self.params.fast_period)
        self.slow_ma = bt.indicators.SMA(self.datas[0], period=self.params.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        self.order = None
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            if self.crossover[0] > 0:  # Fast MA crossed above slow MA
                self.order = self.buy(size=self.params.stake)
                self.logger.info(f'MA Crossover BUY - Fast: {self.fast_ma[0]:.2f}, Slow: {self.slow_ma[0]:.2f}')
        else:
            if self.crossover[0] < 0:  # Fast MA crossed below slow MA
                self.order = self.sell(size=self.params.stake)
                self.logger.info(f'MA Crossover SELL - Fast: {self.fast_ma[0]:.2f}, Slow: {self.slow_ma[0]:.2f}')
    
    def notify_order(self, order):
        self.order = None


class RSIMeanReversion(bt.Strategy):
    """
    Simple example strategy: Buy when RSI oversold, sell when overbought.
    """
    
    params = (
        ('rsi_period', 14),
        ('oversold', 30),
        ('overbought', 70),
        ('stake', 100),
    )
    
    def __init__(self):
        self.logger = get_logger('strategies')
        self.rsi = bt.indicators.RSI(self.datas[0], period=self.params.rsi_period)
        self.order = None
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            if self.rsi[0] < self.params.oversold:
                self.order = self.buy(size=self.params.stake)
                self.logger.info(f'RSI Oversold BUY - RSI: {self.rsi[0]:.2f}')
        else:
            if self.rsi[0] > self.params.overbought:
                self.order = self.sell(size=self.params.stake)
                self.logger.info(f'RSI Overbought SELL - RSI: {self.rsi[0]:.2f}')
    
    def notify_order(self, order):
        self.order = None
