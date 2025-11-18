"""
Configuration settings for the Backtest System
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Application settings
    APP_NAME = "Backtest System"
    APP_VERSION = "1.0.0"
    
    # Directories
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    STRATEGIES_DIR = os.path.join(BASE_DIR, 'strategies')
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    STATIC_DIR = os.path.join(BASE_DIR, 'static')
    TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
    
    # Backtest settings
    DEFAULT_INITIAL_CASH = 100000.0
    DEFAULT_COMMISSION = 0.001  # 0.1%
    DEFAULT_SLIPPAGE = 0.0001   # 0.01%
    
    # Data settings
    DEFAULT_DATA_SOURCE = 'yahoo'
    SUPPORTED_DATA_SOURCES = ['yahoo', 'csv', 'pandas']
    
    # Performance settings
    MAX_CONCURRENT_BACKTESTS = 3
    BACKTEST_TIMEOUT = 300  # 5 minutes
    
    # Chart settings
    DEFAULT_CHART_HEIGHT = 600
    DEFAULT_CHART_WIDTH = 1000
    
    # Cache settings
    CACHE_TIMEOUT = timedelta(hours=1)
    MAX_CACHED_RESULTS = 50

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in production")

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    SECRET_KEY = 'test-secret-key'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
