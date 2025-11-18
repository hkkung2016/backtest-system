"""
Core backtesting engine using Backtrader
"""

import backtrader as bt
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
import importlib.util
import inspect

from .models import BacktestResult, StrategyConfig, BacktestConfig, TradeRecord
from config.logging_config import get_logger



class TradeAnalyzer(bt.Analyzer):
    """System-level trade analyzer that automatically captures all trades and handles order notifications."""
    
    def __init__(self, stake_size=100):
        super(TradeAnalyzer, self).__init__()
        self.trades = []
        self.trade_counter = 0
        self.current_stake = stake_size  # Store the stake size for this strategy
        self.logger = get_logger('strategies')  # Use same logger as strategies for consistency
    
    def notify_order(self, order):
        """Handle order notifications for all strategies."""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            # Get symbol name
            symbol = getattr(order.data, '_name', 'Unknown')
            
            # Get current date/time
            current_datetime = bt.num2date(order.data.datetime[0])
            current_date = current_datetime.strftime('%Y-%m-%d')
            
            # Determine if this is opening or closing a position
            position_action = "OPEN" if order.isbuy() else "CLOSE"
            order_type = "BUY" if order.isbuy() else "SELL"
            
            self.logger.info(f'TRADE {position_action} - order_type={order_type} | '
                  f'symbol={symbol} | date={current_date} | price=${order.executed.price:.2f} | '
                  f'size={order.executed.size} | value=${order.executed.value:.2f} | commission=${order.executed.comm:.2f}')
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            symbol = getattr(order.data, '_name', 'Unknown') if hasattr(order, 'data') else 'Unknown'
            self.logger.warning(f'Order {order.status} - symbol={symbol} | '
                  f'price=${getattr(order, "price", 0):.2f} | size={getattr(order, "size", 0)}')
    
    def notify_trade(self, trade):
        """Called when a trade is closed."""
        if not trade.isclosed:
            return
        
        self.trade_counter += 1
        
        # Get trade details
        data_name = getattr(trade.data, '_name', 'Unknown')
        
        # Convert dates with time precision
        entry_date = bt.num2date(trade.dtopen).strftime('%Y-%m-%d %H:%M:%S')
        exit_date = bt.num2date(trade.dtclose).strftime('%Y-%m-%d %H:%M:%S')
        
        # Get trade info from Backtrader's trade object
        entry_price = trade.price
        gross_pnl = trade.pnl  # This is GROSS P&L (before commissions)
        commission = trade.commission
        net_pnl = gross_pnl - commission  # Calculate actual net P&L
        side = 'long' if trade.long else 'short'
        
        # Get the actual stake size from the analyzer
        size = self.current_stake
        
        # Calculate exit price from gross P&L and size
        if side == 'long':
            exit_price = entry_price + (gross_pnl / size)
        else:
            exit_price = entry_price - (gross_pnl / size)
        
        # Calculate duration
        try:
            from datetime import datetime
            entry_dt = datetime.strptime(entry_date, '%Y-%m-%d %H:%M:%S')
            exit_dt = datetime.strptime(exit_date, '%Y-%m-%d %H:%M:%S')
            duration_seconds = (exit_dt - entry_dt).total_seconds()
            duration_days = max(1, int(duration_seconds / 86400))  # Convert to days
        except:
            duration_days = 1
        
        # Calculate percentage return
        position_value = entry_price * size
        pnl_percent = (net_pnl / position_value * 100) if position_value != 0 else 0
        
        # Log structured trade closure information in one line (aligned with frontend display)
        trade_value = size * entry_price if entry_price != 0 else 1
        return_pct = (net_pnl / trade_value * 100) if trade_value != 0 else 0
        price_change_pct = ((exit_price/entry_price - 1)*100) if entry_price != 0 else 0
        profit_loss_indicator = "✅" if net_pnl > 0 else "❌"
        
        self.logger.info(f'TRADE COMPLETE - trade_id={self.trade_counter} | '
              f'symbol={data_name} | side={side.upper()} | entry_date={entry_date} | exit_date={exit_date} | '
              f'entry_price=${entry_price:.2f} | exit_price=${exit_price:.2f} | size={size} | '
              f'duration_days={duration_days} | pnl=${net_pnl:.2f} | return_pct={return_pct:.2f}% | '
              f'commission=${commission:.2f} | result={profit_loss_indicator}')
        
        # Create trade record
        trade_record = TradeRecord(
            trade_id=self.trade_counter,
            symbol=data_name,
            entry_date=entry_date,
            exit_date=exit_date,
            entry_price=entry_price,
            exit_price=exit_price,
            size=size,
            side=side,
            pnl=net_pnl,
            pnl_percent=pnl_percent,
            commission=commission,
            duration_days=duration_days,
            entry_reason="Strategy Signal",
            exit_reason="Strategy Signal"
        )
        
        self.trades.append(trade_record)
    
    def get_trades(self):
        """Get all recorded trades."""
        return self.trades.copy()
    
    def get_analysis(self):
        """Required method for Analyzer."""
        return {'trades': self.trades}

class FilterProcessor:
    """Processes data filters for strategy backtesting."""
    
    def __init__(self):
        self.logger = get_logger('filter_processor')
    
    def apply_filters(self, data, filters):
        """Apply a list of filters to the data and return filtered data."""
        if not filters:
            return data
        
        filtered_data = data.copy()
        
        for filter_config in filters:
            if not filter_config.enabled:
                continue
                
            try:
                filtered_data = self._apply_single_filter(filtered_data, filter_config)
                self.logger.info(f"Applied filter: {filter_config.filter_type} {filter_config.operator} {filter_config.value}")
            except Exception as e:
                self.logger.warning(f"Failed to apply filter {filter_config.filter_type}: {str(e)}")
                continue
        
        self.logger.info(f"Filtered data from {len(data)} to {len(filtered_data)} rows")
        return filtered_data
    
    def _apply_single_filter(self, data, filter_config):
        """Apply a single filter to the data."""
        filter_type = filter_config.filter_type
        operator = filter_config.operator
        value = filter_config.value
        parameter = filter_config.parameter
        
        # Convert value to appropriate type
        try:
            if str(value).replace('.', '').replace('-', '').isdigit():
                value = float(value)
        except:
            pass
        
        if filter_type == 'volume':
            return self._filter_by_volume(data, operator, value)
        elif filter_type == 'price':
            return self._filter_by_price(data, operator, value, parameter)
        elif filter_type == 'technical':
            return self._filter_by_technical(data, operator, value, parameter, filter_config)
        elif filter_type == 'datetime':
            return self._filter_by_datetime(data, operator, value, parameter)
        else:
            self.logger.warning(f"Unknown filter type: {filter_type}")
            return data
    
    def _filter_by_volume(self, data, operator, value):
        """Filter by volume conditions."""
        if operator == '>':
            return data[data['volume'] > value]
        elif operator == '<':
            return data[data['volume'] < value]
        elif operator == '>=':
            return data[data['volume'] >= value]
        elif operator == '<=':
            return data[data['volume'] <= value]
        elif operator == '==':
            return data[data['volume'] == value]
        elif operator == '!=':
            return data[data['volume'] != value]
        else:
            return data
    
    def _filter_by_price(self, data, operator, value, parameter):
        """Filter by price conditions."""
        # Default to 'close' if no parameter specified
        price_type = parameter.lower() if parameter else 'close'
        
        if price_type not in ['open', 'high', 'low', 'close']:
            price_type = 'close'
        
        if operator == '>':
            return data[data[price_type] > value]
        elif operator == '<':
            return data[data[price_type] < value]
        elif operator == '>=':
            return data[data[price_type] >= value]
        elif operator == '<=':
            return data[data[price_type] <= value]
        elif operator == '==':
            return data[data[price_type] == value]
        elif operator == '!=':
            return data[data[price_type] != value]
        else:
            return data
    
    def _filter_by_technical(self, data, operator, value, parameter, filter_config):
        """Filter by technical indicators."""
        try:
            # Get the indicator type from the filter config
            indicator = getattr(filter_config, 'indicator', None)
            if not indicator:
                self.logger.warning("No indicator specified for technical filter")
                return data
            
            # Get period parameter
            period = int(parameter) if parameter and parameter.isdigit() else 14
            
            # Calculate the specified technical indicator
            if indicator == 'sma':
                indicator_values = data['close'].rolling(window=period).mean()
            elif indicator == 'ema':
                indicator_values = data['close'].ewm(span=period).mean()
            elif indicator == 'rsi':
                indicator_values = self._calculate_rsi(data['close'], period)
            elif indicator == 'macd':
                indicator_values = self._calculate_macd(data['close'])
            elif indicator == 'bb_upper':
                bb_data = self._calculate_bollinger_bands(data['close'], period)
                indicator_values = bb_data['upper']
            elif indicator == 'bb_lower':
                bb_data = self._calculate_bollinger_bands(data['close'], period)
                indicator_values = bb_data['lower']
            elif indicator == 'bb_middle':
                bb_data = self._calculate_bollinger_bands(data['close'], period)
                indicator_values = bb_data['middle']
            elif indicator == 'stoch_k':
                indicator_values = self._calculate_stochastic(data, period)
            elif indicator == 'stoch_d':
                stoch_k = self._calculate_stochastic(data, period)
                indicator_values = stoch_k.rolling(window=3).mean()  # %D is 3-period SMA of %K
            elif indicator == 'atr':
                indicator_values = self._calculate_atr(data, period)
            elif indicator == 'adx':
                indicator_values = self._calculate_adx(data, period)
            else:
                self.logger.warning(f"Unknown technical indicator: {indicator}")
                return data
            
            # Apply the filter based on indicator type
            # Moving averages and BB bands: compare close price vs indicator value (no threshold)
            # Oscillators: compare indicator value vs threshold value
            if indicator in ['sma', 'ema', 'bb_middle', 'bb_upper', 'bb_lower']:
                # For moving averages and BB bands, compare close price vs indicator
                # The 'value' parameter is ignored for these indicators
                if operator == '>':
                    return data[data['close'] > indicator_values]
                elif operator == '<':
                    return data[data['close'] < indicator_values]
                elif operator == '>=':
                    return data[data['close'] >= indicator_values]
                elif operator == '<=':
                    return data[data['close'] <= indicator_values]
                elif operator == '==':
                    return data[data['close'] == indicator_values]
                elif operator == '!=':
                    return data[data['close'] != indicator_values]
                else:
                    self.logger.warning(f"Unknown operator for moving average/BB filter: {operator}")
                    return data
            else:
                # For oscillators (RSI, Stochastic, MACD, ATR, ADX), compare indicator vs threshold
                # The 'value' parameter is the threshold
                if operator == '>':
                    return data[indicator_values > value]
                elif operator == '<':
                    return data[indicator_values < value]
                elif operator == '>=':
                    return data[indicator_values >= value]
                elif operator == '<=':
                    return data[indicator_values <= value]
                elif operator == '==':
                    return data[indicator_values == value]
                elif operator == '!=':
                    return data[indicator_values != value]
                else:
                    self.logger.warning(f"Unknown operator for oscillator filter: {operator}")
                    return data
                
        except Exception as e:
            self.logger.error(f"Error in technical filter {indicator}: {e}")
            return data
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD indicator."""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        return macd_line - signal_line  # MACD histogram
    
    def _calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Calculate Bollinger Bands."""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return {'upper': upper, 'lower': lower, 'middle': sma}
    
    def _calculate_stochastic(self, data, period=14):
        """Calculate Stochastic %K."""
        low_min = data['low'].rolling(window=period).min()
        high_max = data['high'].rolling(window=period).max()
        k_percent = 100 * ((data['close'] - low_min) / (high_max - low_min))
        return k_percent
    
    def _calculate_atr(self, data, period=14):
        """Calculate Average True Range."""
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift())
        low_close = abs(data['low'] - data['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def _calculate_adx(self, data, period=14):
        """Calculate Average Directional Index."""
        # Simplified ADX calculation
        high_diff = data['high'].diff()
        low_diff = data['low'].diff()
        
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = -low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
        
        tr = self._calculate_atr(data, period)
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / tr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / tr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        return adx
    
    def _filter_by_datetime(self, data, operator, value, parameter):
        """Filter by datetime conditions."""
        # Simple implementation for common datetime filters
        try:
            if parameter == 'weekdays_only':
                # Filter out weekends
                return data[data.index.dayofweek < 5]
            elif parameter == 'trading_hours':
                # This would need more sophisticated implementation
                return data
            else:
                return data
        except Exception as e:
            self.logger.error(f"Error in datetime filter: {e}")
            return data


class BacktestEngine:
    """Main backtesting engine that wraps Backtrader functionality."""
    
    def __init__(self):
        self.logger = get_logger('backtesting')
        self.strategies = {}
        self.results = []
        self.filter_processor = FilterProcessor()
        
    def load_strategy(self, strategy_path: str) -> Dict[str, Any]:
        """Load a strategy module and return available strategy classes."""
        try:
            # Use the filename as module name to avoid conflicts
            import os
            module_name = os.path.splitext(os.path.basename(strategy_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, strategy_path)
            module = importlib.util.module_from_spec(spec)
            
            # Add to sys.modules to avoid KeyError
            import sys
            sys.modules[module_name] = module
            
            spec.loader.exec_module(module)
            
            # Find strategy classes (inherit from bt.Strategy)
            strategy_classes = {}
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, bt.Strategy) and 
                    obj != bt.Strategy):
                    strategy_classes[name] = obj
            
            return strategy_classes
        except Exception as e:
            raise Exception(f"Failed to load strategy: {str(e)}")
    
    def get_data(self, symbol: str, start_date: str, end_date: str) -> bt.feeds.PandasData:
        """Download and prepare data for backtesting."""
        try:
            # Download data using yfinance
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                raise Exception(f"No data found for symbol {symbol}")
            
            # Prepare data for Backtrader
            df.index.name = 'datetime'
            df.columns = [col.lower() for col in df.columns]
            
            # Create Backtrader data feed
            data = bt.feeds.PandasData(
                dataname=df,
                datetime=None,
                open='open',
                high='high',
                low='low',
                close='close',
                volume='volume',
                openinterest=None
            )
            
            return data
        except Exception as e:
            raise Exception(f"Failed to get data for {symbol}: {str(e)}")
    
    def run_backtest(self, config: BacktestConfig, strategy_configs: List[StrategyConfig]) -> List[BacktestResult]:
        """
        Run single or multiple backtests. Always returns a list of results.
        
        For single backtest: Pass a list with one StrategyConfig.
        For multiple backtests: Pass a list with multiple StrategyConfigs.
        
        Returns: List[BacktestResult] (always a list, even for single strategy)
        """
        results = []
        
        # Track strategy names to ensure uniqueness
        strategy_name_counter = {}
        
        for strategy_config in strategy_configs:
            try:
                # Load strategy class
                strategy_path = os.path.join('strategies', f'{strategy_config.module_name}.py')
                strategy_classes = self.load_strategy(strategy_path)
                
                if strategy_config.class_name not in strategy_classes:
                    raise Exception(f"Strategy class {strategy_config.class_name} not found")
                
                strategy_class = strategy_classes[strategy_config.class_name]
                
                # Generate unique strategy name with counter
                base_name = f"{strategy_class.__name__}_{strategy_config.symbol}"
                if base_name in strategy_name_counter:
                    strategy_name_counter[base_name] += 1
                    counter = strategy_name_counter[base_name]
                else:
                    strategy_name_counter[base_name] = 1
                    counter = 1
                
                # Run backtest for strategy's symbol
                result = self._run_single_backtest(
                    strategy_class=strategy_class,
                    strategy_params=strategy_config.parameters,
                    symbol=strategy_config.symbol,
                    start_date=config.start_date,
                    end_date=config.end_date,
                    initial_cash=config.initial_cash,
                    commission=config.commission,
                    filters=strategy_config.filters,
                    counter=counter
                )
                results.append(result)
                    
            except Exception as e:
                self.logger.error(f"Error running backtest for {strategy_config.name}: {str(e)}")
                continue
        
        return results
    
    def _run_single_backtest(self, strategy_class, strategy_params: Dict, 
                           symbol: str, start_date: str, end_date: str,
                           initial_cash: float, commission: float, filters: List = None, 
                           counter: int = 1) -> BacktestResult:
        """Run a single backtest and return results."""
        
        try:
            # Create Cerebro engine
            cerebro = bt.Cerebro()
            
            # Add strategy
            cerebro.addstrategy(strategy_class, **strategy_params)
        
            # Add data with optional filtering
            data = self.get_data(symbol, start_date, end_date)
            
            # Apply filters if provided
            if filters:
                self.logger.info(f"Applying {len(filters)} filters to {symbol} data")
                # Convert Backtrader data to pandas for filtering
                data_df = data._dataname if hasattr(data, '_dataname') else None
                if data_df is not None:
                    filtered_df = self.filter_processor.apply_filters(data_df, filters)
                    # Create new Backtrader data feed from filtered dataframe
                    filtered_data = bt.feeds.PandasData(
                        dataname=filtered_df,
                        datetime=None,
                        open='open',
                        high='high',
                        low='low',
                        close='close',
                        volume='volume',
                        openinterest=None
                    )
                    cerebro.adddata(filtered_data, name=symbol)
                else:
                    self.logger.warning("Could not apply filters - using original data")
                    cerebro.adddata(data, name=symbol)
            else:
                cerebro.adddata(data, name=symbol)
            
            # Set broker parameters
            cerebro.broker.setcash(initial_cash)
            cerebro.broker.setcommission(commission=commission)
            
            # Add analyzers
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
            cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
            cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn')
            # Get stake size from strategy parameters
            stake_size = strategy_params.get('stake', 100)
            cerebro.addanalyzer(TradeAnalyzer, stake_size=stake_size, _name='custom_trades')
            
            # Add observers for equity curve
            cerebro.addobserver(bt.observers.Value)
            
            # Run backtest
            results = cerebro.run()
            strategy_result = results[0]
            
            # Extract trade data from the TradeAnalyzer
            trade_records = []
            try:
                custom_trades_analyzer = strategy_result.analyzers.custom_trades
                trade_records = custom_trades_analyzer.get_trades()
            except Exception as e:
                self.logger.warning(f"Could not access custom trade analyzer: {e}")
            
            # Extract results
            final_value = cerebro.broker.getvalue()
            total_return = (final_value / initial_cash - 1) * 100
            
            # Get analyzer results with error handling
            try:
                sharpe_analysis = strategy_result.analyzers.sharpe.get_analysis()
                sharpe = sharpe_analysis.get('sharperatio', 0) if sharpe_analysis else 0
                if sharpe is None:
                    sharpe = 0
            except Exception as e:
                self.logger.warning(f"Could not get Sharpe ratio: {e}")
                sharpe = 0
                
            try:
                drawdown_analysis = strategy_result.analyzers.drawdown.get_analysis()
                max_drawdown = drawdown_analysis.get('max', {}).get('drawdown', 0) if drawdown_analysis else 0
            except Exception as e:
                self.logger.warning(f"Could not get drawdown: {e}")
                max_drawdown = 0
            
            try:
                # Get trade counts from our custom trade analyzer
                custom_trades = strategy_result.analyzers.custom_trades.get_analysis()
                total_trades = len(custom_trades.get('trades', [])) if custom_trades else 0
                
                # Count won and lost trades from our custom analyzer
                won_trades = 0
                lost_trades = 0
                gross_profit = 0
                gross_loss = 0
                
                if custom_trades and 'trades' in custom_trades:
                    for trade in custom_trades['trades']:
                        if trade.pnl > 0:
                            won_trades += 1
                            gross_profit += trade.pnl
                        else:
                            lost_trades += 1
                            gross_loss += abs(trade.pnl)
                
                win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0
                
                # Calculate profit factor with proper handling of edge cases
                if gross_loss > 0:
                    profit_factor = gross_profit / gross_loss
                elif gross_profit > 0:
                    # When there are profits but no losses, use a high value for JSON compatibility
                    profit_factor = 999999.0
                else:
                    profit_factor = 0  # No trades or no profit
                    
            except Exception as e:
                self.logger.warning(f"Could not get trade analysis: {e}")
                total_trades = 0
                won_trades = 0
                lost_trades = 0
                win_rate = 0
                profit_factor = 0
            
            # Get equity curve data - portfolio value over time
            equity_curve = []
            try:
                timereturn_data = strategy_result.analyzers.timereturn.get_analysis()
                if timereturn_data:
                    portfolio_value = initial_cash  # Start with initial capital
                    # Add starting point
                    first_date = min(timereturn_data.keys()).strftime('%Y-%m-%d')
                    equity_curve.append({
                        'date': first_date,
                        'value': portfolio_value
                    })
                    
                    for date, daily_return in timereturn_data.items():
                        portfolio_value *= (1 + daily_return)  # Compound the returns to get absolute value
                        equity_curve.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'value': portfolio_value
                        })
                else:
                    # Generate simple equity curve from portfolio value
                    equity_curve = [
                        {'date': start_date, 'value': initial_cash}, 
                        {'date': end_date, 'value': final_value}
                    ]
            except Exception as e:
                self.logger.warning(f"Could not get time return data: {e}")
                # Generate simple equity curve from portfolio value
                equity_curve = [
                    {'date': start_date, 'value': initial_cash}, 
                    {'date': end_date, 'value': final_value}
                ]
        
            # Create result object with unique name including counter
            strategy_name = f"{strategy_class.__name__}_{symbol}_{counter}" if counter > 1 else f"{strategy_class.__name__}_{symbol}"
            
            result = BacktestResult(
                strategy_name=strategy_name,
                start_date=start_date,
                end_date=end_date,
                initial_cash=initial_cash,
                final_value=final_value,
                total_return=total_return,
                sharpe_ratio=sharpe,
                max_drawdown=max_drawdown,
                num_trades=total_trades,
                win_rate=win_rate,
                profit_factor=profit_factor,
                won_trades=won_trades,
                lost_trades=lost_trades,
                trades=trade_records,
                equity_curve=equity_curve,
                created_at=datetime.now()
            )
            
            return result
            
        except ZeroDivisionError as e:
            import traceback
            self.logger.error(f"Division by zero error in backtest: {e}")
            self.logger.error("Full traceback:", exc_info=True)
            # Return a default result with zero values
            return BacktestResult(
                strategy_name=strategy_name,
                start_date=start_date,
                end_date=end_date,
                initial_cash=initial_cash,
                final_value=initial_cash,
                total_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                num_trades=0,
                win_rate=0.0,
                profit_factor=0.0,
                won_trades=0,
                lost_trades=0,
                trades=[],
                equity_curve=[],
                created_at=datetime.now()
            )
        except Exception as e:
            import traceback
            self.logger.error(f"General error in backtest: {e}")
            self.logger.error("Full traceback:", exc_info=True)
            # Return a default result with zero values
            return BacktestResult(
                strategy_name=strategy_name,
                start_date=start_date,
                end_date=end_date,
                initial_cash=initial_cash,
                final_value=initial_cash,
                total_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                num_trades=0,
                win_rate=0.0,
                profit_factor=0.0,
                won_trades=0,
                lost_trades=0,
                trades=[],
                equity_curve=[],
                created_at=datetime.now()
            )
    
    def compare_strategies(self, results: List[BacktestResult]) -> Dict[str, Any]:
        """Generate comparison data for multiple strategy results."""
        if not results:
            return {}
        
        comparison = {
            'summary': [],
            'equity_curves': {},
            'metrics': {}
        }
        
        # Summary table data
        for result in results:
            comparison['summary'].append({
                'strategy': result.strategy_name,
                'total_return': f"{result.total_return:.2f}%",
                'sharpe_ratio': f"{result.sharpe_ratio:.3f}",
                'max_drawdown': f"{result.max_drawdown:.2f}%",
                'num_trades': result.num_trades,
                'win_rate': f"{result.win_rate:.1f}%",
                'profit_factor': f"{result.profit_factor:.2f}",
                'final_value': f"${result.final_value:,.2f}"
            })
        
        # Equity curves for plotting
        for result in results:
            comparison['equity_curves'][result.strategy_name] = result.equity_curve
        
        # Metrics for detailed analysis
        comparison['metrics'] = {
            'best_return': max(results, key=lambda x: x.total_return),
            'best_sharpe': max(results, key=lambda x: x.sharpe_ratio),
            'lowest_drawdown': min(results, key=lambda x: x.max_drawdown)
        }
        
        return comparison
