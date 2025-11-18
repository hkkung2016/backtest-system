"""
Bollinger Bands Strategy

This strategy uses Bollinger Bands to identify potential reversal points.
- Buy when price touches the lower band (oversold)
- Sell when price touches the upper band (overbought)
- Can also be used for breakout strategies
"""

import backtrader as bt
import sys
import os

# Add parent directory to path to access logging config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.logging_config import get_logger

class BollingerBandsReversal(bt.Strategy):
    """
    Bollinger Bands Mean Reversion Strategy
    
    Buy when price touches lower band, sell when price touches upper band
    """
    
    params = (
        ('bb_period', 20),      # Bollinger Bands period
        ('bb_std', 2.0),        # Standard deviation multiplier
        ('stake', 100),         # Number of shares to trade
        ('stop_loss', 0.02),    # Stop loss percentage
    )
    
    def __init__(self):
        """Initialize the strategy with indicators."""
        self.logger = get_logger('strategies')
        
        # Calculate Bollinger Bands
        self.bb = bt.indicators.BollingerBands(
            self.datas[0], period=self.params.bb_period, devfactor=self.params.bb_std
        )
        
        # Get individual bands
        self.bb_top = self.bb.lines.top
        self.bb_mid = self.bb.lines.mid
        self.bb_bot = self.bb.lines.bot
        
        # Track orders and entry price for stop loss
        self.order = None
        self.entry_price = 0
    
    def next(self):
        """Define the trading logic for each bar."""
        # Check if an order is pending
        if self.order:
            return
        
        current_price = self.data.close[0]
        
        # Check if we are in the market
        if not self.position:
            # Not in the market - look for buy signal (price at lower band)
            if current_price <= self.bb_bot[0]:
                self.order = self.buy(size=self.params.stake)
                self.entry_price = current_price
                self.logger.info(f'REVERSAL BUY - Price: ${current_price:.2f}, Lower Band: ${self.bb_bot[0]:.2f}')
        else:
            # In the market - look for sell signals
            
            # Check stop loss first (most important)
            stop_loss_price = self.entry_price * (1 - self.params.stop_loss)
            if current_price <= stop_loss_price:
                self.order = self.sell(size=self.params.stake)
                self.logger.info(f'STOP LOSS - Price: ${current_price:.2f}, Stop: ${stop_loss_price:.2f}')
            
            # Sell at upper band (profit target)
            elif current_price >= self.bb_top[0]:
                self.order = self.sell(size=self.params.stake)
                self.logger.info(f'REVERSAL SELL - Price: ${current_price:.2f}, Upper Band: ${self.bb_top[0]:.2f}')
    
    def notify_order(self, order):
        """Handle order notifications - only reset order tracking."""
        self.order = None


class BollingerBandsBreakout(bt.Strategy):
    """
    Bollinger Bands Breakout Strategy
    
    Buy when price breaks above upper band, sell when it comes back inside
    """
    
    params = (
        ('bb_period', 20),        # Bollinger Bands period
        ('bb_std', 2.0),          # Standard deviation multiplier
        ('volume_factor', 1.5),   # Volume confirmation factor
        ('stake', 100),           # Number of shares to trade
        ('stop_loss', 0.02),      # Stop loss percentage
    )
    
    def __init__(self):
        """Initialize the strategy with indicators."""
        self.logger = get_logger('strategies')
        
        # Calculate Bollinger Bands
        self.bb = bt.indicators.BollingerBands(
            self.datas[0], period=self.params.bb_period, devfactor=self.params.bb_std
        )
        
        # Get individual bands
        self.bb_top = self.bb.lines.top
        self.bb_mid = self.bb.lines.mid
        self.bb_bot = self.bb.lines.bot
        
        # Volume moving average for confirmation
        self.volume_sma = bt.indicators.SimpleMovingAverage(
            self.datas[0].volume, period=20
        )
        
        # Track orders, breakout status, and entry price for stop loss
        self.order = None
        self.breakout_confirmed = False
        self.entry_price = 0
    
    def next(self):
        """Define the trading logic for each bar."""
        # Check if an order is pending
        if self.order:
            return
        
        current_price = self.data.close[0]
        current_volume = self.data.volume[0]
        
        # Check if we are in the market
        if not self.position:
            # Not in the market - look for breakout signal
            
            # Upper band breakout with volume confirmation
            if (current_price > self.bb_top[0] and 
                current_volume > self.volume_sma[0] * self.params.volume_factor):
                self.order = self.buy(size=self.params.stake)
                self.breakout_confirmed = True
                self.entry_price = current_price
                self.logger.info(f'BREAKOUT BUY - Price: ${current_price:.2f}, '
                      f'Upper Band: ${self.bb_top[0]:.2f}')
        else:
            # In the market - look for exit signals
            
            # Check stop loss first (most important)
            stop_loss_price = self.entry_price * (1 - self.params.stop_loss)
            if current_price <= stop_loss_price:
                # Use stop order instead of market sell for better execution
                self.order = self.sell(size=self.params.stake, exectype=bt.Order.Stop, price=stop_loss_price)
                self.breakout_confirmed = False
                self.logger.info(f'STOP LOSS - Price: ${current_price:.2f}, Stop: ${stop_loss_price:.2f}')
            
            # Exit when price comes back inside the bands
            elif current_price < self.bb_top[0]:
                self.order = self.sell(size=self.params.stake)
                self.breakout_confirmed = False
                self.logger.info(f'BREAKOUT EXIT - Price back inside bands')
    
    def notify_order(self, order):
        """Handle order notifications - only reset order tracking."""
        self.order = None


class BollingerBandsSqueezeStrategy(bt.Strategy):
    """
    Bollinger Bands Squeeze Strategy
    
    Identifies periods of low volatility (squeeze) and trades the breakout
    """
    
    params = (
        ('bb_period', 20),        # Bollinger Bands period
        ('bb_std', 2.0),          # Standard deviation multiplier
        ('squeeze_periods', 5),   # Number of periods to confirm squeeze
        ('min_squeeze_ratio', 0.05),  # Minimum band width ratio for squeeze
        ('stake', 100),           # Number of shares to trade
        ('stop_loss', 0.02),      # Stop loss percentage
    )
    
    def __init__(self):
        """Initialize the strategy with indicators."""
        self.logger = get_logger('strategies')
        
        # Calculate Bollinger Bands
        self.bb = bt.indicators.BollingerBands(
            self.datas[0], period=self.params.bb_period, devfactor=self.params.bb_std
        )
        
        # Calculate band width (protect against division by zero)
        # Use a small epsilon to avoid division by zero
        self.band_width = (self.bb.lines.top - self.bb.lines.bot) / (self.bb.lines.mid + 0.0001)
        
        # Moving average of band width to identify squeezes
        self.band_width_sma = bt.indicators.SimpleMovingAverage(
            self.band_width, period=self.params.squeeze_periods
        )
        
        # Track orders, squeeze status, and entry price for stop loss
        self.order = None
        self.in_squeeze = False
        self.entry_price = 0
    
    def next(self):
        """Define the trading logic for each bar."""
        # Check if an order is pending
        if self.order:
            return
        
        current_price = self.data.close[0]
        current_band_width = self.band_width[0]
        
        # Determine if we're in a squeeze
        self.in_squeeze = current_band_width < self.params.min_squeeze_ratio
        
        # Check if we are in the market
        if not self.position:
            # Not in the market - look for breakout from squeeze
            
            if (not self.in_squeeze and 
                self.band_width[-1] < self.params.min_squeeze_ratio):  # Just exited squeeze
                
                # Determine breakout direction
                if current_price > self.bb.lines.mid[0]:
                    # Upward breakout
                    self.order = self.buy(size=self.params.stake)
                    self.entry_price = current_price
                    self.logger.info(f'SQUEEZE BREAKOUT BUY - Price: ${current_price:.2f}')
        else:
            # In the market - look for exit signals
            
            # Check stop loss first (most important)
            stop_loss_price = self.entry_price * (1 - self.params.stop_loss)
            if current_price <= stop_loss_price:
                # Use stop order instead of market sell for better execution
                self.order = self.sell(size=self.params.stake, exectype=bt.Order.Stop, price=stop_loss_price)
                self.logger.info(f'STOP LOSS - Price: ${current_price:.2f}, Stop: ${stop_loss_price:.2f}')
            
            # Exit when price comes back to middle band (protect against division by zero)
            elif self.bb.lines.mid[0] > 0 and abs(current_price - self.bb.lines.mid[0]) / self.bb.lines.mid[0] < 0.01:
                self.order = self.sell(size=self.params.stake)
                self.logger.info(f'SQUEEZE EXIT - Price back to middle band')
    
    def notify_order(self, order):
        """Handle order notifications - only reset order tracking."""
        self.order = None
