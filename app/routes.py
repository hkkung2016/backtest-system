"""
Flask routes for the web interface
"""

from flask import Blueprint, render_template, request, jsonify
import json
import os
import traceback

from .backtesting import BacktestEngine
from .models import BacktestConfig, StrategyConfig
from config.logging_config import get_logger

main_bp = Blueprint('main', __name__)
engine = BacktestEngine()
logger = get_logger('routes')

@main_bp.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')

@main_bp.route('/strategies')
def strategies():
    """Strategy management page."""
    # Load available strategies
    strategy_files = []
    strategies_dir = 'strategies'
    
    if os.path.exists(strategies_dir):
        for file in os.listdir(strategies_dir):
            if file.endswith('.py') and not file.startswith('__'):
                strategy_files.append(file[:-3])  # Remove .py extension
    
    return render_template('strategies.html', strategies=strategy_files)

@main_bp.route('/backtest')
def backtest_page():
    """Backtesting configuration page."""
    # Load available strategies
    strategy_files = []
    strategies_dir = 'strategies'
    
    if os.path.exists(strategies_dir):
        for file in os.listdir(strategies_dir):
            if file.endswith('.py') and not file.startswith('__'):
                strategy_files.append(file[:-3])
    
    return render_template('backtest.html', strategies=strategy_files)

@main_bp.route('/results')
def results():
    """Results visualization page."""
    return render_template('results.html')

@main_bp.route('/api/run-backtest', methods=['POST'])
def run_backtest():
    """API endpoint to run backtests."""
    try:
        data = request.get_json()
        
        # Parse configuration
        config = BacktestConfig.from_dict(data['config'])
        
        # Parse strategy configurations
        strategy_configs = []
        for strategy_data in data['strategies']:
            strategy_config = StrategyConfig.from_dict(strategy_data)
            strategy_configs.append(strategy_config)
        
        # Run backtests - always returns a list, handles both single and multiple cases
        results = engine.run_backtest(config, strategy_configs)
        
        # Generate comparison data
        comparison = engine.compare_strategies(results)
        
        # Convert results to JSON-serializable format
        results_data = [result.to_dict() for result in results]
        
        return jsonify({
            'success': True,
            'results': results_data,
            'comparison': comparison
        })
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Backtest error: {error_msg}")
        logger.error("Full traceback:", exc_info=True)
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@main_bp.route('/api/strategies/<strategy_name>')
def get_strategy_info(strategy_name):
    """Get information about a specific strategy."""
    try:
        strategy_path = os.path.join('strategies', f'{strategy_name}.py')
        
        if not os.path.exists(strategy_path):
            return jsonify({'error': 'Strategy not found'}), 404
        
        # Load strategy and get class information
        strategy_classes = engine.load_strategy(strategy_path)
        
        strategy_info = {}
        for class_name, strategy_class in strategy_classes.items():
            # Get parameters if defined
            params = {}
            if hasattr(strategy_class, 'params'):
                try:
                    if hasattr(strategy_class.params, '_getpairs'):
                        # This is a Backtrader params object
                        param_names = strategy_class.params._getpairs()
                        for param_name in param_names:
                            if not param_name.startswith('_') and param_name not in ['isdefault', 'notdefault']:
                                param_value = getattr(strategy_class.params, param_name)
                                if isinstance(param_value, (str, int, float, bool, type(None))):
                                    params[param_name] = param_value
                    elif isinstance(strategy_class.params, tuple):
                        # Direct tuple format
                        for param_item in strategy_class.params:
                            if isinstance(param_item, tuple) and len(param_item) >= 2:
                                param_name = param_item[0]
                                param_value = param_item[1]
                                if isinstance(param_value, (str, int, float, bool, type(None))):
                                    params[param_name] = param_value
                except Exception as e:
                    # Fallback: empty params
                    logger.warning(f"Could not extract parameters for {class_name}: {e}")
                    params = {}
            
            # Get docstring
            doc = strategy_class.__doc__ or "No description available"
            
            strategy_info[class_name] = {
                'name': class_name,
                'description': doc.strip(),
                'parameters': params
            }
        
        return jsonify(strategy_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/upload-strategy', methods=['POST'])
def upload_strategy():
    """Upload a new strategy file."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.py'):
            return jsonify({'error': 'File must be a Python file (.py)'}), 400
        
        # Save file to strategies directory
        filename = file.filename
        filepath = os.path.join('strategies', filename)
        file.save(filepath)
        
        # Validate the strategy file
        try:
            strategy_classes = engine.load_strategy(filepath)
            if not strategy_classes:
                os.remove(filepath)  # Remove invalid file
                return jsonify({'error': 'No valid strategy classes found in file'}), 400
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)  # Remove invalid file
            return jsonify({'error': f'Invalid strategy file: {str(e)}'}), 400
        
        return jsonify({
            'success': True,
            'message': f'Strategy {filename} uploaded successfully',
            'strategies': list(strategy_classes.keys())
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/symbols')
def get_symbols():
    """Get simple list of available symbols from JSON file."""
    try:
        symbols_file = os.path.join('config', 'symbols.json')
        with open(symbols_file, 'r') as f:
            data = json.load(f)
        
        return jsonify({
            'success': True,
            'symbols': data['symbols']
        })
    except Exception as e:
        logger.error(f"Error loading symbols: {str(e)}")
        # Fallback to basic symbols if file is missing
        fallback_symbols = ['AAPL', 'MSFT', 'ETH-USD', 'BTC-USD']
        return jsonify({
            'success': True,
            'symbols': fallback_symbols
        })
