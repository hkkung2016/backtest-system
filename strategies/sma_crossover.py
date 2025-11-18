"""
Simple Moving Average Crossover Strategy

This strategy uses two simple moving averages (fast and slow) to generate buy and sell signals.
When the fast SMA crosses above the slow SMA, it generates a buy signal.
When the fast SMA crosses below the slow SMA, it generates a sell signal.
"""

import backtrader as bt
import sys
import os

# Add parent directory to path to access logging config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.logging_config import get_logger


class SMACrossover(bt.Strategy):
    """
    Simple Moving Average Crossover Strategy
    
    Buy when fast SMA crosses above slow SMA
    Sell when fast SMA crosses below slow SMA
    """
    
    params = (
        ('fast_period', 10),   # Fast moving average period
        ('slow_period', 30),   # Slow moving average period
        ('stake', 100),        # Number of shares to trade
    )
    
    def __init__(self):
        """Initialize the strategy with indicators."""
        self.logger = get_logger('strategies')
        
        # Calculate moving averages
        self.fast_sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.fast_period
        )
        self.slow_sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.slow_period
        )
        
        # Create crossover signal
        self.crossover = bt.indicators.CrossOver(self.fast_sma, self.slow_sma)
        
        # Track orders
        self.order = None
    
    def next(self):
        """Define the trading logic for each bar."""
        # Check if an order is pending
        if self.order:
            return
        
        # Check if we are in the market
        if not self.position:
            # Not in the market - look for buy signal
            if self.crossover > 0:  # Fast SMA crosses above slow SMA
                self.order = self.buy(size=self.params.stake)
        else:
            # In the market - look for sell signal
            if self.crossover < 0:  # Fast SMA crosses below slow SMA
                self.order = self.sell(size=self.params.stake)
    
    def notify_order(self, order):
        """Handle order notifications - only reset order tracking."""
        self.order = None


class SMACrossoverWithStopLoss(bt.Strategy):
    """
    SMA Crossover Strategy with Stop Loss
    
    Enhanced version with stop loss protection
    """
    
    params = (
        ('fast_period', 10),     # Fast moving average period
        ('slow_period', 30),     # Slow moving average period
        ('stop_loss', 0.05),     # Stop loss percentage (5%)
        ('stake', 100),          # Number of shares to trade
    )
    
    def __init__(self):
        """Initialize the strategy with indicators."""
        self.logger = get_logger('strategies')
        
        # Calculate moving averages
        self.fast_sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.fast_period
        )
        self.slow_sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.slow_period
        )
        
        # Create crossover signal
        self.crossover = bt.indicators.CrossOver(self.fast_sma, self.slow_sma)
        
        # Track orders and entry price
        self.order = None
        self.entry_price = None
    
    def next(self):
        """Define the trading logic for each bar."""
        # Check if an order is pending
        if self.order:
            return
        
        # Check if we are in the market
        if not self.position:
            # Not in the market - look for buy signal
            if self.crossover > 0:  # Fast SMA crosses above slow SMA
                self.order = self.buy(size=self.params.stake)
                self.entry_price = self.data.close[0]
        else:
            # In the market - check for exit conditions
            current_price = self.data.close[0]
            
            # Check stop loss
            if self.entry_price and current_price <= self.entry_price * (1 - self.params.stop_loss):
                self.order = self.sell(size=self.params.stake)
                self.logger.debug(f'STOP LOSS TRIGGERED at ${current_price:.2f}')
            
            # Check crossover exit signal
            elif self.crossover < 0:  # Fast SMA crosses below slow SMA
                self.order = self.sell(size=self.params.stake)
    
    def notify_order(self, order):
        """Handle order notifications - reset order tracking and manage entry price."""
        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
            else:
                self.entry_price = None
        
        self.order = None
