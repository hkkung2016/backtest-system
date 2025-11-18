// Main JavaScript functionality for the Backtest System

// Global variables
let currentResults = [];
let currentComparison = {};

// Utility functions
function formatCurrency(value, decimals = 2) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value);
}

function formatPercentage(value, decimals = 2) {
    return `${value.toFixed(decimals)}%`;
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(dateTimeString) {
    const date = new Date(dateTimeString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }) + ' ' + date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

// Trade history utilities
function createTradeHistoryTable(containerId, trades, strategyName) {
    const container = document.getElementById(containerId);
    
    if (!trades || trades.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-chart-line fa-2x text-muted mb-3"></i>
                <h6 class="text-muted">No Trades Available</h6>
                <p class="text-muted small">This strategy didn't execute any trades during the backtest period.</p>
            </div>
        `;
        return;
    }
    
    // Group trades by strategy if needed
    const groupedTrades = trades;
    
    // Calculate summary statistics
    const totalPnL = trades.reduce((sum, trade) => sum + trade.pnl, 0);
    const winningTrades = trades.filter(trade => trade.pnl > 0);
    const losingTrades = trades.filter(trade => trade.pnl < 0);
    const winRate = trades.length > 0 ? (winningTrades.length / trades.length) * 100 : 0;
    
    let tableHTML = `
        <div class="trade-history-container">
            <!-- Trade Summary -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card border-0 bg-light">
                        <div class="card-body py-3">
                            <div class="row">
                                <div class="col-md-3 col-6 text-center">
                                    <div class="small text-muted mb-1">Total Trades</div>
                                    <div class="h5 mb-0 text-primary">${trades.length}</div>
                                </div>
                                <div class="col-md-3 col-6 text-center">
                                    <div class="small text-muted mb-1">Win Rate</div>
                                    <div class="h5 mb-0 ${winRate >= 50 ? 'text-success' : 'text-warning'}">${winRate.toFixed(1)}%</div>
                                </div>
                                <div class="col-md-3 col-6 text-center">
                                    <div class="small text-muted mb-1">Net PnL</div>
                                    <div class="h5 mb-0 ${totalPnL >= 0 ? 'text-success' : 'text-danger'}">${formatCurrency(totalPnL)}</div>
                                </div>
                                <div class="col-md-3 col-6 text-center">
                                    <div class="small text-muted mb-1">Avg Trade</div>
                                    <div class="h5 mb-0">${formatCurrency(totalPnL / trades.length)}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
                            <!-- Trade Table -->
                <div class="mb-2">
                    <small class="text-muted">
                        <i class="fas fa-info-circle me-1"></i>
                        Net PnL is profit/loss after commissions. Final Value = Initial Capital + Net PnL.
                    </small>
                </div>
                <div class="table-responsive">
                    <table class="table table-hover align-middle">
                    <thead class="table-dark">
                        <tr>
                            <th scope="col">Trade #</th>
                            <th scope="col">Action</th>
                            <th scope="col">Symbol</th>
                            <th scope="col">Date</th>
                            <th scope="col">Price</th>
                            <th scope="col">Size</th>
                            <th scope="col">Value</th>
                            <th scope="col">Commission</th>
                            <th scope="col">Net PnL</th>
                            <th scope="col">Return %</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    trades.forEach((trade, index) => {
        const pnlClass = trade.pnl >= 0 ? 'text-success' : 'text-danger';
        const pnlIcon = trade.pnl >= 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down';
        
        // OPEN row
        tableHTML += `
            <tr class="table-light border-bottom-0">
                <td rowspan="2" class="align-middle">
                    <span class="badge bg-secondary">${trade.trade_id}</span>
                </td>
                <td>
                    <span class="badge bg-success">
                        <i class="fas fa-arrow-up me-1"></i>OPEN
                    </span>
                </td>
                <td><strong>${trade.symbol}</strong></td>
                <td><small>${formatDateTime(trade.entry_date)}</small></td>
                <td>${formatCurrency(trade.entry_price)}</td>
                <td>+${trade.size.toLocaleString()}</td>
                <td>${formatCurrency(trade.entry_price * trade.size)}</td>
                <td>${formatCurrency(trade.commission / 2)}</td>
                <td class="text-muted">-</td>
                <td class="text-muted">-</td>
            </tr>
            <tr class="table-light border-top-0">
                <td>
                    <span class="badge bg-danger">
                        <i class="fas fa-arrow-down me-1"></i>CLOSE
                    </span>
                </td>
                <td><strong>${trade.symbol}</strong></td>
                <td><small>${formatDateTime(trade.exit_date)}</small></td>
                <td>${formatCurrency(trade.exit_price)}</td>
                <td>-${trade.size.toLocaleString()}</td>
                <td>${formatCurrency(trade.exit_price * trade.size)}</td>
                <td>${formatCurrency(trade.commission / 2)}</td>
                <td class="${pnlClass}">
                    <i class="${pnlIcon} me-1"></i>
                    ${formatCurrency(trade.pnl)}
                </td>
                <td class="${pnlClass}">
                    ${formatPercentage(trade.pnl_percent)}
                </td>
            </tr>
            <tr><td colspan="10" class="border-0" style="height: 8px;"></td></tr>
        `;
    });
    
    tableHTML += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    container.innerHTML = tableHTML;
}

// Helper function to get portfolio value at specific date
function getPortfolioValueAtDate(equityCurve, targetDate, initialCash = 100000) {
    if (!equityCurve || equityCurve.length === 0) return initialCash; // fallback to initial cash
    
    // Find exact match first
    for (let point of equityCurve) {
        if (point.date === targetDate) {
            return point.value;
        }
    }
    
    // If no exact match, find closest date
    const target = new Date(targetDate);
    let closest = equityCurve[0];
    let minDiff = Math.abs(new Date(closest.date) - target);
    
    for (let point of equityCurve) {
        const diff = Math.abs(new Date(point.date) - target);
        if (diff < minDiff) {
            minDiff = diff;
            closest = point;
        }
    }
    
    return closest.value;
}

// Chart creation utilities
function createEquityCurveChart(containerId, data, title = 'Equity Curve', tradesData = null, initialCash = 100000) {
    const traces = [];
    
    // Add equity curve lines
    Object.entries(data).forEach(([strategyName, equityCurve]) => {
        const dates = equityCurve.map(point => point.date);
        const values = equityCurve.map(point => point.value);
        
        traces.push({
            x: dates,
            y: values,
            type: 'scatter',
            mode: 'lines',
            name: strategyName,
            line: { width: 2 },
            hovertemplate: '<b>%{fullData.name}</b><br>' +
                          'Date: %{x}<br>' +
                          'Total Capital: $%{y:,.2f}<br>' +
                          '<extra></extra>'
        });
    });
    
    // Add trade markers if trade data is provided
    if (tradesData && Array.isArray(tradesData)) {
        tradesData.forEach(result => {
            if (result.trades && result.trades.length > 0) {
                const equityCurve = data[result.strategy_name];
                
                const entryTrades = [];
                const exitTrades = [];
                
                result.trades.forEach(trade => {
                    const entryValue = getPortfolioValueAtDate(equityCurve, trade.entry_date, initialCash);
                    const exitValue = getPortfolioValueAtDate(equityCurve, trade.exit_date, initialCash);
                    
                    entryTrades.push({
                        x: trade.entry_date,
                        y: entryValue,
                        text: `BUY ${trade.symbol}<br>Price: $${trade.entry_price.toFixed(2)}<br>Size: ${trade.size}`
                    });
                    
                    exitTrades.push({
                        x: trade.exit_date,
                        y: exitValue,
                        text: `SELL ${trade.symbol}<br>Price: $${trade.exit_price.toFixed(2)}<br>P&L: $${trade.pnl.toFixed(2)} (${trade.pnl_percent.toFixed(2)}%)`
                    });
                });
                
                // Add entry markers
                if (entryTrades.length > 0) {
                    traces.push({
                        x: entryTrades.map(t => t.x),
                        y: entryTrades.map(t => t.y),
                        type: 'scatter',
                        mode: 'markers',
                        name: `${result.strategy_name} - Buy Orders`,
                        marker: {
                            symbol: 'triangle-up',
                            size: 12,
                            color: 'green',
                            line: { width: 2, color: 'darkgreen' }
                        },
                        text: entryTrades.map(t => t.text),
                        hovertemplate: '%{text}<extra></extra>'
                    });
                }
                
                // Add exit markers
                if (exitTrades.length > 0) {
                    traces.push({
                        x: exitTrades.map(t => t.x),
                        y: exitTrades.map(t => t.y),
                        type: 'scatter',
                        mode: 'markers',
                        name: `${result.strategy_name} - Sell Orders`,
                        marker: {
                            symbol: 'triangle-down',
                            size: 12,
                            color: 'red',
                            line: { width: 2, color: 'darkred' }
                        },
                        text: exitTrades.map(t => t.text),
                        hovertemplate: '%{text}<extra></extra>'
                    });
                }
            }
        });
    }
    
    const layout = {
        title: {
            text: title,
            font: { size: 16, weight: 'bold' }
        },
        xaxis: { 
            title: 'Date',
            showgrid: true,
            gridcolor: '#e9ecef'
        },
        yaxis: { 
            title: 'Total Capital ($)',
            tickformat: ',.0f',
            showgrid: true,
            gridcolor: '#e9ecef'
        },
        hovermode: 'closest',
        showlegend: true,
        legend: {
            orientation: 'h',
            yanchor: 'bottom',
            y: 1.02,
            xanchor: 'right',
            x: 1
        },
        margin: { t: 60, r: 40, b: 60, l: 80 },
        plot_bgcolor: 'white',
        paper_bgcolor: 'white'
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d', 'autoScale2d'],
        displaylogo: false
    };
    
    Plotly.newPlot(containerId, traces, layout, config);
}

function createDrawdownChart(containerId, data, title = 'Drawdown Analysis') {
    // This would need actual drawdown data from the backend
    // For now, we'll create a placeholder
    console.log('Drawdown chart placeholder for:', containerId);
}

function createReturnsDistribution(containerId, data, title = 'Returns Distribution') {
    // This would create a histogram of returns
    console.log('Returns distribution placeholder for:', containerId);
}

// Data management
function saveResultsToLocalStorage(results, comparison) {
    try {
        const existingResults = JSON.parse(localStorage.getItem('backtestResults') || '[]');
        
        // Add new results
        results.forEach(result => {
            existingResults.push(result);
        });
        
        // Keep only the last 50 results to avoid storage limits
        if (existingResults.length > 50) {
            existingResults.splice(0, existingResults.length - 50);
        }
        
        localStorage.setItem('backtestResults', JSON.stringify(existingResults));
        
        // Also save the latest comparison
        localStorage.setItem('latestComparison', JSON.stringify(comparison));
        
        // Trigger storage event for other tabs
        window.dispatchEvent(new Event('storage'));
        
    } catch (error) {
        console.error('Error saving results to localStorage:', error);
    }
}

function loadResultsFromLocalStorage() {
    try {
        const results = JSON.parse(localStorage.getItem('backtestResults') || '[]');
        const comparison = JSON.parse(localStorage.getItem('latestComparison') || '{}');
        
        return { results, comparison };
    } catch (error) {
        console.error('Error loading results from localStorage:', error);
        return { results: [], comparison: {} };
    }
}

// Performance calculations
function calculateMetrics(results) {
    if (!results || results.length === 0) {
        return {};
    }
    
    const totalReturns = results.map(r => r.total_return);
    const sharpeRatios = results.map(r => r.sharpe_ratio);
    const maxDrawdowns = results.map(r => r.max_drawdown);
    
    return {
        bestReturn: Math.max(...totalReturns),
        worstReturn: Math.min(...totalReturns),
        avgReturn: totalReturns.reduce((a, b) => a + b, 0) / totalReturns.length,
        bestSharpe: Math.max(...sharpeRatios),
        worstSharpe: Math.min(...sharpeRatios),
        avgSharpe: sharpeRatios.reduce((a, b) => a + b, 0) / sharpeRatios.length,
        bestDrawdown: Math.min(...maxDrawdowns),
        worstDrawdown: Math.max(...maxDrawdowns),
        avgDrawdown: maxDrawdowns.reduce((a, b) => a + b, 0) / maxDrawdowns.length
    };
}

// UI helpers
function showLoading(elementId, message = 'Loading...') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2 text-muted">${message}</p>
            </div>
        `;
    }
}

function showError(elementId, message = 'An error occurred') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
    }
}

function showSuccess(elementId, message = 'Operation completed successfully') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="alert alert-success" role="alert">
                <i class="fas fa-check-circle me-2"></i>
                ${message}
            </div>
        `;
    }
}

// Form validation
function validateBacktestForm() {
    const startDate = document.getElementById('start-date')?.value;
    const endDate = document.getElementById('end-date')?.value;
    const initialCash = document.getElementById('initial-cash')?.value;
    const symbols = document.getElementById('symbols')?.value;
    
    const errors = [];
    
    if (!startDate) {
        errors.push('Start date is required');
    }
    
    if (!endDate) {
        errors.push('End date is required');
    }
    
    if (startDate && endDate && new Date(startDate) >= new Date(endDate)) {
        errors.push('End date must be after start date');
    }
    
    if (!initialCash || parseFloat(initialCash) <= 0) {
        errors.push('Initial cash must be greater than 0');
    }
    
    if (!symbols || symbols.trim().length === 0) {
        errors.push('At least one symbol is required');
    }
    
    return errors;
}

// Strategy management
function getSelectedStrategies() {
    const strategies = [];
    
    document.querySelectorAll('.strategy-config').forEach(strategyElement => {
        const moduleSelect = strategyElement.querySelector('.strategy-module');
        const classSelect = strategyElement.querySelector('.strategy-class');
        const parameterInputs = strategyElement.querySelectorAll('.parameter-input');
        
        if (moduleSelect?.value && classSelect?.value) {
            const parameters = {};
            parameterInputs.forEach(input => {
                const paramName = input.dataset.param;
                let value = input.value;
                
                // Try to parse as number if it looks like one
                if (!isNaN(value) && value !== '') {
                    value = parseFloat(value);
                }
                
                parameters[paramName] = value;
            });
            
            strategies.push({
                name: `${moduleSelect.value}_${classSelect.value}`,
                module_name: moduleSelect.value,
                class_name: classSelect.value,
                parameters: parameters,
                description: ''
            });
        }
    });
    
    return strategies;
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(() => {
        document.querySelectorAll('.alert-dismissible').forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Export functions for global use
window.BacktestSystem = {
    formatCurrency,
    formatPercentage,
    formatDate,
    formatDateTime,
    createEquityCurveChart,
    createTradeHistoryTable
};
