#!/usr/bin/env python3
"""
Main application runner for the Backtest System

Run this file to start the Flask web application.
"""

import os
import sys
from app import create_app
from config.logging_config import setup_logging

def main():
    """Main entry point for the application."""
    
    # Initialize logging
    logger = setup_logging()
    
    # Add the parent directory to the Python path to access backtrader
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Create the Flask application
    app = create_app()
    
    # Configuration
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    logger.info("=" * 60)
    logger.info("🚀 Starting Backtest System")
    logger.info("=" * 60)
    logger.info(f"📊 Web Interface: http://{host}:{port}")
    logger.info(f"🔧 Debug Mode: {'Enabled' if debug else 'Disabled'}")
    logger.info(f"📁 Strategies Directory: ./strategies/")
    logger.info(f"💾 Data Directory: ./data/")
    logger.info("=" * 60)
    logger.info("\n💡 Tips:")
    logger.info("   • Upload strategies via the web interface")
    logger.info("   • Use the backtest page to compare multiple strategies")
    logger.info("   • View results with interactive charts")
    logger.info("   • Press Ctrl+C to stop the server")
    logger.info("\n" + "=" * 60)
    
    try:
        # Run the Flask development server
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=False  # Disable reloader to avoid watchdog issues
        )
    except KeyboardInterrupt:
        logger.info("\n\n👋 Shutting down Backtest System...")
        logger.info("Thanks for using the system!")

if __name__ == '__main__':
    main()
