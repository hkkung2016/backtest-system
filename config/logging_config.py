"""
Logging configuration for the Backtest System
"""
import logging
import logging.config
import os
import glob
from datetime import datetime

def clear_log_files():
    """Clear all existing log files when system restarts."""
    try:
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        log_files = glob.glob(os.path.join(logs_dir, 'backtest_system_*.log'))
        for log_file in log_files:
            try:
                os.remove(log_file)
                print(f"🗑️  Cleared previous log file: {os.path.basename(log_file)}")
            except OSError as e:
                print(f"⚠️  Could not remove log file {log_file}: {e}")
    except Exception as e:
        print(f"❌ Error clearing log files: {e}")

def setup_logging():
    """Set up logging configuration for the application."""
    
    # Clear previous log files on system restart
    clear_log_files()
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Generate log filename with timestamp
    log_filename = os.path.join(logs_dir, f"backtest_system_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s:%(filename)s:%(funcName)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s:%(filename)s:%(funcName)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'simple',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': log_filename,
                'mode': 'a'
            }
        },
        'loggers': {
            'backtest_system': {
                'level': 'DEBUG',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'backtest_system.backtesting': {
                'level': 'DEBUG',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'backtest_system.routes': {
                'level': 'DEBUG',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'backtest_system.strategies': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console', 'file']
        }
    }
    
    logging.config.dictConfig(logging_config)
    
    # Log startup message
    logger = logging.getLogger('backtest_system')
    logger.info("Logging system initialized")
    logger.info(f"Log file: {log_filename}")
    
    return logger

def get_logger(name: str):
    """Get a logger instance for a specific module."""
    return logging.getLogger(f'backtest_system.{name}')
