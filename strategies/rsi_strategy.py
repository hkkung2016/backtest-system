"""
RSI (Relative Strength Index) Strategy

This strategy uses the RSI indicator to identify overbought and oversold conditions.
- Buy when RSI < oversold_level (typically 30)
- Sell when RSI > overbought_level (typically 70)
"""

import backtrader as bt
import sys
import os

# Add parent directory to path to access logging config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.logging_config import get_logger


class RSIStrategy(bt.Strategy):
    """
    RSI-based trading strategy
    
    Uses RSI to identify overbought/oversold conditions
    """
    
    params = (
        ('rsi_period', 14),        # RSI calculation period
        ('oversold_level', 30),    # RSI oversold threshold
        ('overbought_level', 70),  # RSI overbought threshold
        ('stake', 100),            # Number of shares to trade
    )
    
    def __init__(self):
        """Initialize the strategy with indicators."""
        self.logger = get_logger('strategies')
        
        # Calculate RSI
        self.rsi = bt.indicators.RelativeStrengthIndex(
            self.datas[0], period=self.params.rsi_period
        )
        
        # Track orders
        self.order = None
    
    def next(self):
        """Define the trading logic for each bar."""
        # Check if an order is pending
        if self.order:
            return
        
        # Check if we are in the market
        if not self.position:
            # Not in the market - look for buy signal (oversold)
            if self.rsi < self.params.oversold_level:
                self.order = self.buy(size=self.params.stake)
        else:
            # In the market - look for sell signal (overbought)
            if self.rsi > self.params.overbought_level:
                self.order = self.sell(size=self.params.stake)
    
    def notify_order(self, order):
        """Handle order notifications - only reset order tracking."""
        self.order = None


class RSIMeanReversion(bt.Strategy):
    """
    RSI Mean Reversion Strategy
    
    More sophisticated RSI strategy with multiple levels
    """
    
    params = (
        ('rsi_period', 14),           # RSI calculation period
        ('extreme_oversold', 20),     # Extreme oversold level
        ('oversold_level', 30),       # Normal oversold level
        ('overbought_level', 70),     # Normal overbought level
        ('extreme_overbought', 80),   # Extreme overbought level
        ('stake_normal', 50),         # Normal position size
        ('stake_extreme', 100),       # Extreme condition position size
    )
    
    def __init__(self):
        """Initialize the strategy with indicators."""
        self.logger = get_logger('strategies')
        
        # Calculate RSI
        self.rsi = bt.indicators.RelativeStrengthIndex(
            self.datas[0], period=self.params.rsi_period
        )
        
        # Add SMA for trend filter
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=50
        )
        
        # Track orders
        self.order = None
    
    def next(self):
        """Define the trading logic for each bar."""
        # Check if an order is pending
        if self.order:
            return
        
        current_price = self.data.close[0]
        
        # Check if we are in the market
        if not self.position:
            # Not in the market - look for buy signals
            
            # Extreme oversold condition
            if self.rsi < self.params.extreme_oversold:
                self.order = self.buy(size=self.params.stake_extreme)
                self.logger.info(f'EXTREME OVERSOLD BUY - RSI: {self.rsi[0]:.2f}')
            
            # Normal oversold condition (but only if above long-term trend)
            elif (self.rsi < self.params.oversold_level and 
                  current_price > self.sma):
                self.order = self.buy(size=self.params.stake_normal)
                self.logger.info(f'OVERSOLD BUY - RSI: {self.rsi[0]:.2f}')
        
        else:
            # In the market - look for sell signals
            
            # Extreme overbought condition
            if self.rsi > self.params.extreme_overbought:
                self.order = self.sell(size=self.position.size)
                self.logger.info(f'EXTREME OVERBOUGHT SELL - RSI: {self.rsi[0]:.2f}')
            
            # Normal overbought condition
            elif self.rsi > self.params.overbought_level:
                # Sell half the position
                sell_size = min(self.params.stake_normal, self.position.size)
                self.order = self.sell(size=sell_size)
                self.logger.info(f'OVERBOUGHT PARTIAL SELL - RSI: {self.rsi[0]:.2f}')
    
    def notify_order(self, order):
        """Handle order notifications - only reset order tracking."""
        self.order = None
