"""
Bollinger Bands Crossover Strategy

This strategy uses Bollinger Bands to generate trading signals:
- BUY: When close price crosses above the lower Bollinger Band
- SELL: When close price crosses above the upper Bollinger Band

The strategy is designed to capture mean reversion moves within the bands.
"""

import backtrader as bt
import sys
import os

# Add parent directory to path to access logging config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.logging_config import get_logger


class BollingerBandsCrossover(bt.Strategy):
    """
    Bollinger Bands Crossover Strategy
    
    Description: Mean reversion strategy using Bollinger Bands crossovers
    
    Entry Conditions:
    - Buy when close price crosses above the lower Bollinger Band
    - This indicates a potential bounce from oversold conditions
    
    Exit Conditions:
    - Sell when close price crosses above the upper Bollinger Band
    - This indicates the price has reached overbought levels
    
    Risk Management:
    - Stop loss to limit downside risk
    - Position sizing based on stake parameter
    """
    
    # ===== PARAMETERS =====
    params = (
        # Bollinger Bands parameters
        ('bb_period', 20),           # Period for Bollinger Bands calculation
        ('bb_std', 2.0),             # Standard deviation multiplier
        
        # Trading parameters
        ('stake', 1),              # Number of shares to trade
        
        # Risk management
        ('stop_loss', 0.02),         # Stop loss percentage (2%)
    )
    
    def __init__(self):
        """Initialize the strategy with indicators and variables."""
        # Initialize logging
        self.logger = get_logger('strategies')
        
        # ===== INDICATORS =====
        # Bollinger Bands
        self.bb = bt.indicators.BollingerBands(
            self.datas[0], 
            period=self.params.bb_period, 
            devfactor=self.params.bb_std
        )
        
        # ===== CROSSOVER SIGNALS =====
        # Buy signal: when close price crosses above lower band
        self.buy_signal = bt.indicators.CrossOver(
            self.datas[0].close, 
            self.bb.lines.bot
        )
        
        # Sell signal: when close price crosses above upper band
        self.sell_signal = bt.indicators.CrossOver(
            self.datas[0].close, 
            self.bb.lines.top
        )
        
        # ===== INSTANCE VARIABLES =====
        # Track orders and positions
        self.order = None            # Track pending orders
        self.entry_price = 0         # Track entry price for stop loss
        
        # Strategy state variables
        self.bars_in_position = 0    # Count bars since entry
        

    
    def next(self):
        """
        Main trading logic - called for each new bar.
        
        This is where you implement your strategy's decision-making logic.
        """
        # Check if any order is pending
        if self.order or (hasattr(self, 'buy_order') and self.buy_order) or (hasattr(self, 'stop_loss_order') and self.stop_loss_order):
            return
        
        # Get current prices and indicator values
        close_price = self.data.close[0]
        bb_upper = self.bb.lines.top[0]
        bb_lower = self.bb.lines.bot[0]
        
        # Check if we are in the market
        if not self.position:
            # Not in the market - look for buy signal
            # Buy when close price crosses above the lower band
            if self.buy_signal > 0:
                self.logger.info(f'BUY SIGNAL - Price: ${close_price:.2f}, Lower Band: ${bb_lower:.2f} (CROSSOVER DETECTED)')
                
                # Place buy order with simultaneous stop loss order
                if self.params.stop_loss > 0:
                    stop_loss_price = close_price * (1 - self.params.stop_loss)
                    
                    # Place both orders simultaneously
                    self.buy_order = self.buy(size=self.params.stake)
                    self.stop_loss_order = self.sell(size=self.params.stake, exectype=bt.Order.Stop, price=stop_loss_price)
                    
                    self.logger.info(f'BUY + STOP LOSS ORDERS PLACED - Entry: ${close_price:.2f}, Stop: ${stop_loss_price:.2f}')
                else:
                    # Simple buy order without stop loss
                    self.buy_order = self.buy(size=self.params.stake)
                
                self.entry_price = close_price
                self.bars_in_position = 0
                
        else:
            # In the market - look for sell signal
            # Sell when close price crosses above the upper band
            if self.sell_signal > 0:
                self.logger.info(f'SELL SIGNAL - Price: ${close_price:.2f}, Upper Band: ${bb_upper:.2f} (CROSSOVER DETECTED)')
                
                # Cancel stop loss order before placing sell order
                if hasattr(self, 'stop_loss_order') and self.stop_loss_order:
                    self.broker.cancel(self.stop_loss_order)
                    self.logger.info(f'CANCELLED STOP LOSS ORDER - Normal exit condition met')
                    self.stop_loss_order = None
                
                # Place sell order
                self.order = self.sell(size=self.params.stake)
            
            # Stop loss is now handled automatically by stop orders - no manual checking needed
            
            # Update bars in position
            self.bars_in_position += 1
    
    def notify_order(self, order):
        """Handle order notifications."""
        if order.status in [order.Submitted, order.Accepted]:
            # Order submitted/accepted - no action needed
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.logger.info(f'BUY EXECUTED - Price: ${order.executed.price:.2f}, Cost: ${order.executed.value:.2f}, Commission: ${order.executed.comm:.2f}')
                
                # Reset buy order tracking
                if hasattr(self, 'buy_order') and self.buy_order and order.ref == self.buy_order.ref:
                    self.buy_order = None
                
            else:
                self.logger.info(f'SELL EXECUTED - Price: ${order.executed.price:.2f}, Cost: ${order.executed.value:.2f}, Commission: ${order.executed.comm:.2f}')
                
                # Reset sell order tracking
                if hasattr(self, 'order') and self.order and order.ref == self.order.ref:
                    self.order = None
                
                # If this was a stop loss order, log it specifically
                if hasattr(self, 'stop_loss_order') and self.stop_loss_order and order.ref == self.stop_loss_order.ref:
                    self.logger.info(f'STOP LOSS ORDER EXECUTED - Price: ${order.executed.price:.2f}')
                    self.stop_loss_order = None
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.logger.warning(f'Order Canceled/Margin/Rejected: {order.status}')
            
            # Reset appropriate order tracking
            if hasattr(self, 'buy_order') and self.buy_order and order.ref == self.buy_order.ref:
                self.buy_order = None
            elif hasattr(self, 'stop_loss_order') and self.stop_loss_order and order.ref == self.stop_loss_order.ref:
                self.stop_loss_order = None
            elif self.order and order.ref == self.order.ref:
                self.order = None
    
    def notify_trade(self, trade):
        """Handle trade notifications."""
        if trade.isclosed:
            self.logger.info(f'TRADE COMPLETE - Gross P&L: ${trade.pnl:.2f}, Net P&L: ${trade.pnlcomm:.2f}, Commission: ${trade.commission:.2f}')
            
            # Reset position tracking
            self.entry_price = 0
            self.bars_in_position = 0


class BollingerBandsCrossoverAggressive(bt.Strategy):
    """
    Aggressive version of Bollinger Bands Crossover Strategy
    
    This version uses more aggressive entry/exit conditions:
    - BUY: When close price is near or crosses above lower band
    - SELL: When close price is near or crosses below upper band
    - Also includes take profit functionality
    """
    
    params = (
        # Bollinger Bands parameters
        ('bb_period', 20),           # Period for Bollinger Bands calculation
        ('bb_std', 2.0),             # Standard deviation multiplier
        
        # Trading parameters
        ('stake', 100),              # Number of shares to trade
        
        # Risk management
        ('stop_loss', 0.03),         # Stop loss percentage (3%)
        ('take_profit', 0.08),      # Take profit percentage (8%)
        
        # Entry/exit sensitivity
        ('entry_threshold', 0.01),   # Entry threshold (1% above lower band)
        ('exit_threshold', 0.01),    # Exit threshold (1% below upper band)
    )
    
    def __init__(self):
        """Initialize the strategy with indicators and variables."""
        # Initialize logging
        self.logger = get_logger('strategies')
        
        # ===== INDICATORS =====
        # Bollinger Bands
        self.bb = bt.indicators.BollingerBands(
            self.datas[0], 
            period=self.params.bb_period, 
            devfactor=self.params.bb_std
        )
        
        # ===== INSTANCE VARIABLES =====
        # Track orders and positions
        self.order = None            # Track pending orders
        self.entry_price = 0         # Track entry price for risk management
        
        # Strategy state variables
        self.bars_in_position = 0    # Count bars since entry
    
    def next(self):
        """Main trading logic - called for each new bar."""
        # Check if an order is pending
        if self.order:
            return
        
        # Get current prices and indicator values
        close_price = self.data.close[0]
        bb_upper = self.bb.lines.top[0]
        bb_lower = self.bb.lines.bot[0]
        
        # Check if we are in the market
        if not self.position:
            # Not in the market - look for buy signal
            # Buy when close price is near or crosses above the lower band
            entry_trigger = bb_lower * (1 + self.params.entry_threshold)
            if close_price >= entry_trigger:
                self.logger.info(f'AGGRESSIVE BUY - Price: ${close_price:.2f}, Lower Band: ${bb_lower:.2f}, Trigger: ${entry_trigger:.2f}')
                
                # Place buy order
                self.order = self.buy(size=self.params.stake)
                self.entry_price = close_price
                self.bars_in_position = 0
                
        else:
            # In the market - look for sell signal
            # Sell when close price is near or crosses below the upper band
            exit_trigger = bb_upper * (1 - self.params.exit_threshold)
            if close_price <= exit_trigger:
                self.logger.info(f'AGGRESSIVE SELL - Price: ${close_price:.2f}, Upper Band: ${bb_upper:.2f}, Trigger: ${exit_trigger:.2f}')
                
                # Place sell order
                self.order = self.sell(size=self.params.stake)
            
            # Check stop loss
            elif self.params.stop_loss > 0:
                stop_loss_price = self.entry_price * (1 - self.params.stop_loss)
                if close_price <= stop_loss_price:
                    self.logger.info(f'STOP LOSS - Price: ${close_price:.2f}, Stop: ${stop_loss_price:.2f}')
                    # Use stop order instead of market sell for better execution
                    self.order = self.sell(size=self.params.stake, exectype=bt.Order.Stop, price=stop_loss_price)
            
            # Check take profit
            elif self.params.take_profit > 0:
                take_profit_price = self.entry_price * (1 + self.params.take_profit)
                if close_price >= take_profit_price:
                    self.logger.info(f'TAKE PROFIT - Price: ${close_price:.2f}, Target: ${take_profit_price:.2f}')
                    # Use limit order for take profit
                    self.order = self.sell(size=self.params.stake, exectype=bt.Order.Limit, price=take_profit_price)
            
            # Update bars in position
            self.bars_in_position += 1
    
    def notify_order(self, order):
        """Handle order notifications."""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.logger.info(f'BUY EXECUTED - Price: ${order.executed.price:.2f}, Cost: ${order.executed.value:.2f}, Commission: ${order.executed.comm:.2f}')
            else:
                self.logger.info(f'SELL EXECUTED - Price: ${order.executed.price:.2f}, Cost: ${order.executed.value:.2f}, Commission: ${order.executed.comm:.2f}')
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.logger.warning(f'Order Canceled/Margin/Rejected: {order.status}')
        
        # Reset order tracking
        self.order = None
    
    def notify_trade(self, trade):
        """Handle trade notifications."""
        if trade.isclosed:
            self.logger.info(f'TRADE COMPLETE - Gross P&L: ${trade.pnl:.2f}, Net P&L: ${trade.pnlcomm:.2f}, Commission: ${trade.commission:.2f}')
            
            # Reset position tracking
            self.entry_price = 0
            self.bars_in_position = 0
