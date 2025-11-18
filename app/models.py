"""
Data models for the backtesting system
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

@dataclass
class TradeRecord:
    """Individual trade record with entry and exit details."""
    trade_id: int
    symbol: str
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    size: int
    side: str  # 'long' or 'short'
    pnl: float
    pnl_percent: float
    commission: float
    duration_days: int
    entry_reason: str = ""
    exit_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

@dataclass
class BacktestResult:
    """Results from a single backtest run."""
    strategy_name: str
    start_date: str
    end_date: str
    initial_cash: float
    final_value: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    num_trades: int
    win_rate: float
    profit_factor: float
    won_trades: int
    lost_trades: int
    trades: List[TradeRecord]
    equity_curve: List[Dict]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        result['trades'] = [trade.to_dict() for trade in self.trades]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestResult':
        """Create from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

@dataclass
class FilterConfig:
    """Configuration for data filters applied to strategy."""
    filter_type: str  # 'volume', 'price', 'technical', 'datetime', 'custom'
    operator: str     # '>', '<', '>=', '<=', '==', '!=', 'between', 'outside'
    value: Any        # Single value or list for 'between'/'outside'
    parameter: str = ""  # Additional parameter (e.g., indicator period)
    enabled: bool = True
    indicator: str = ""  # Technical indicator type (for technical filters)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FilterConfig':
        """Create from dictionary."""
        return cls(**data)

@dataclass
class StrategyConfig:
    """Configuration for a trading strategy."""
    name: str
    module_name: str
    class_name: str
    symbol: str
    parameters: Dict[str, Any]
    description: str = ""
    filters: List[FilterConfig] = field(default_factory=list)  # Optional list of filters
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyConfig':
        """Create from dictionary."""
        # Handle filters conversion
        if 'filters' in data and data['filters']:
            data['filters'] = [FilterConfig.from_dict(f) for f in data['filters']]
        return cls(**data)

@dataclass
class BacktestConfig:
    """Configuration for a backtest run."""
    start_date: str
    end_date: str
    initial_cash: float
    commission: float
    data_source: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestConfig':
        """Create from dictionary."""
        return cls(**data)
