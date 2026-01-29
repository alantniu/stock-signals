"""
Stock Signal Generator - Dashboard Module
=========================================
Generates a static HTML dashboard for viewing signals.
Features: Clickable tickers, auto-refresh, manual refresh button, CALL options only
"""

from typing import Dict
from datetime import datetime
import json


def generate_dashboard(results: Dict, output_path: str = 'dashboard.html', options_data: list = None) -> str:
    """Generate a static HTML dashboard with all signal data."""
    
    regime = results['market_regime']
    signals = results['signals']
    
    # Sort signals by composite score
    sorted_signals = sorted(signals, key=lambda x: x['composite_score'], reverse=True)
    
    # Prepare options data
    options_json = json.dumps(options_data if options_data else [])
    
    # Convert to JSON for JavaScript
    signals_json = json.dumps(sorted_signals)
    regime_json = json.dumps(regime)
    summary_json = json.dumps(results['summary'])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stock Signal Dashboard</title>
    <meta http-equiv="refresh" content="300">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
        }}
        
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            border-bottom: 1px solid #334155;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .header-left {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .header-right {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        h1 {{ font-size: 28px; font-weight: 600; }}
        .timestamp {{ color: #94a3b8; font-size: 14px; }}
        
        .refresh-btn {{
            background: #3b82f6;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: background 0.2s;
        }}
        
        .refresh-btn:hover {{
            background: #2563eb;
        }}
        
        .refresh-btn:active {{
            transform: scale(0.98);
        }}
        
        .refresh-btn.loading {{
            opacity: 0.7;
            cursor: not-allowed;
        }}
        
        .refresh-icon {{
            display: inline-block;
            transition: transform 0.3s;
        }}
        
        .refresh-btn.loading .refresh-icon {{
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        
        .auto-refresh-note {{
            font-size: 12px;
            color: #64748b;
        }}
        
        .market-banner {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }}
        
        .market-card {{
            background: #1e293b;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #334155;
        }}
        
        .market-card.regime {{
            border-left: 4px solid;
        }}
        
        .market-card.regime.BULLISH {{ border-left-color: #22c55e; background: linear-gradient(135deg, #1e293b 0%, #14532d33 100%); }}
        .market-card.regime.NEUTRAL {{ border-left-color: #eab308; background: linear-gradient(135deg, #1e293b 0%, #71380033 100%); }}
        .market-card.regime.BEARISH {{ border-left-color: #ef4444; background: linear-gradient(135deg, #1e293b 0%, #7f1d1d33 100%); }}
        .market-card.regime.CRASH {{ border-left-color: #dc2626; background: linear-gradient(135deg, #1e293b 0%, #450a0a33 100%); }}
        
        .market-label {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }}
        .market-value {{ font-size: 24px; font-weight: 600; margin-top: 5px; }}
        .market-change {{ font-size: 14px; margin-top: 5px; }}
        .market-change.positive {{ color: #22c55e; }}
        .market-change.negative {{ color: #ef4444; }}
        
        .summary-bar {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 25px;
            padding: 15px;
            background: #1e293b;
            border-radius: 12px;
            border: 1px solid #334155;
        }}
        
        .summary-group {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .summary-label {{
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 4px;
        }}
        
        .summary-label.strong-buy {{ background: #14532d; color: #86efac; }}
        .summary-label.buy {{ background: #166534; color: #bbf7d0; }}
        .summary-label.hold {{ background: #374151; color: #9ca3af; }}
        .summary-label.sell {{ background: #991b1b; color: #fecaca; }}
        .summary-label.strong-sell {{ background: #7f1d1d; color: #fca5a5; }}
        
        .summary-tickers {{ font-size: 14px; color: #cbd5e1; }}
        
        .filters {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        
        .filter-btn {{
            background: #1e293b;
            border: 1px solid #334155;
            color: #e2e8f0;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }}
        
        .filter-btn:hover {{ background: #334155; }}
        .filter-btn.active {{ background: #3b82f6; border-color: #3b82f6; }}
        
        .signals-table {{
            width: 100%;
            border-collapse: collapse;
            background: #1e293b;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #334155;
        }}
        
        .signals-table th {{
            background: #0f172a;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #94a3b8;
            border-bottom: 1px solid #334155;
        }}
        
        .signals-table td {{
            padding: 15px;
            border-bottom: 1px solid #1e293b;
        }}
        
        .signals-table tr:hover {{ background: #334155; }}
        
        .ticker-cell {{
            font-weight: 600;
            font-size: 16px;
        }}
        
        .ticker-link {{
            color: #60a5fa;
            cursor: pointer;
            text-decoration: none;
            transition: color 0.2s;
        }}
        
        .ticker-link:hover {{
            color: #93c5fd;
            text-decoration: underline;
        }}
        
        .sector-badge {{
            font-size: 11px;
            color: #94a3b8;
            background: #0f172a;
            padding: 2px 8px;
            border-radius: 4px;
            margin-left: 8px;
        }}
        
        .signal-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
        }}
        
        .signal-badge.strong-buy {{ background: #14532d; color: #86efac; }}
        .signal-badge.buy {{ background: #166534; color: #bbf7d0; }}
        .signal-badge.hold {{ background: #374151; color: #9ca3af; }}
        .signal-badge.sell {{ background: #991b1b; color: #fecaca; }}
        .signal-badge.strong-sell {{ background: #7f1d1d; color: #fca5a5; }}
        
        .price-cell {{ font-family: 'SF Mono', Monaco, monospace; }}
        
        .change-positive {{ color: #22c55e; }}
        .change-negative {{ color: #ef4444; }}
        
        .confidence-bar {{
            width: 60px;
            height: 6px;
            background: #334155;
            border-radius: 3px;
            overflow: hidden;
        }}
        
        .confidence-fill {{
            height: 100%;
            border-radius: 3px;
            transition: width 0.3s;
        }}
        
        .range-cell {{
            font-size: 13px;
            font-family: 'SF Mono', Monaco, monospace;
        }}
        
        .indicators-cell {{
            font-size: 12px;
            color: #94a3b8;
        }}
        
        .indicator {{ margin-right: 12px; white-space: nowrap; }}
        .indicator-label {{ color: #64748b; }}
        
        /* Options Section Styles */
        .options-section {{
            margin-top: 40px;
            padding-top: 30px;
            border-top: 1px solid #334155;
        }}
        
        .options-section h2 {{
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .options-subtitle {{
            color: #94a3b8;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        
        .options-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 15px;
        }}
        
        .option-card {{
            background: #1e293b;
            border-radius: 12px;
            border: 1px solid #334155;
            padding: 20px;
            transition: border-color 0.2s, transform 0.2s;
        }}
        
        .option-card:hover {{
            border-color: #3b82f6;
        }}
        
        .option-card.highlighted {{
            border-color: #3b82f6;
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
            transform: scale(1.02);
        }}
        
        .option-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #334155;
        }}
        
        .option-ticker {{
            font-size: 24px;
            font-weight: 700;
        }}
        
        .option-stock-price {{
            font-size: 14px;
            color: #94a3b8;
            margin-top: 4px;
        }}
        
        .option-signal {{
            text-align: right;
        }}
        
        .option-contract {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }}
        
        .option-field {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        
        .option-field-label {{
            font-size: 11px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .option-field-value {{
            font-size: 16px;
            font-weight: 600;
            font-family: 'SF Mono', Monaco, monospace;
        }}
        
        .option-field-value.highlight {{
            color: #22c55e;
            font-size: 18px;
        }}
        
        .option-field-value.negative {{
            color: #ef4444;
        }}
        
        .option-field-sub {{
            font-size: 12px;
            color: #94a3b8;
        }}
        
        .option-buy-range {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #334155;
            background: #14532d33;
            margin: 15px -20px -20px -20px;
            padding: 15px 20px;
            border-radius: 0 0 12px 12px;
        }}
        
        .option-buy-range-label {{
            font-size: 11px;
            color: #86efac;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}
        
        .option-buy-range-value {{
            font-size: 18px;
            font-weight: 700;
            color: #86efac;
            font-family: 'SF Mono', Monaco, monospace;
        }}
        
        .no-options {{
            color: #64748b;
            font-style: italic;
            padding: 20px;
            text-align: center;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            color: #64748b;
            font-size: 12px;
        }}
        
        .options-warning {{
            padding: 15px 20px;
            background: #451a03;
            color: #fcd34d;
            font-size: 12px;
            text-align: center;
            border-radius: 8px;
            margin-top: 20px;
        }}
        
        @media (max-width: 1200px) {{
            .signals-table {{ display: block; overflow-x: auto; }}
        }}
        
        @media (max-width: 768px) {{
            .market-banner {{ grid-template-columns: 1fr 1fr; }}
            header {{ flex-direction: column; gap: 10px; text-align: center; }}
            .options-grid {{ grid-template-columns: 1fr; }}
            .option-contract {{ grid-template-columns: 1fr 1fr; }}
        }}
        
        @media (max-width: 480px) {{
            .option-contract {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-left">
                <h1>📊 Stock Signal Dashboard</h1>
            </div>
            <div class="header-right">
                <div class="timestamp">
                    Last updated: <span id="update-time">{results['generated_at']}</span>
                    <div class="auto-refresh-note">Auto-refreshes every 5 minutes</div>
                </div>
                <button class="refresh-btn" onclick="refreshPage()">
                    <span class="refresh-icon">🔄</span>
                    Refresh Now
                </button>
            </div>
        </header>
        
        <div class="market-banner">
            <div class="market-card regime {regime['regime']}" id="regime-card">
                <div class="market-label">Market Regime</div>
                <div class="market-value" id="regime-value">{regime['regime']}</div>
                <div class="market-change">Signal modifier: {regime['modifier']:.1f}x</div>
            </div>
            <div class="market-card">
                <div class="market-label">S&P 500 (SPY)</div>
                <div class="market-value">${regime['details']['spy_price']}</div>
                <div class="market-change {'positive' if regime['details']['spy_vs_50ma'] >= 0 else 'negative'}">{regime['details']['spy_vs_50ma']:+.1f}% vs 50MA</div>
            </div>
            <div class="market-card">
                <div class="market-label">NASDAQ 100 (QQQ)</div>
                <div class="market-value">${regime['details']['qqq_price']}</div>
                <div class="market-change {'positive' if regime['details']['qqq_vs_50ma'] >= 0 else 'negative'}">{regime['details']['qqq_vs_50ma']:+.1f}% vs 50MA</div>
            </div>
            <div class="market-card">
                <div class="market-label">Volatility (VIX)</div>
                <div class="market-value">{regime['details']['vix']}</div>
                <div class="market-change">{'Low' if regime['details']['vix'] < 15 else 'Normal' if regime['details']['vix'] < 25 else 'Elevated' if regime['details']['vix'] < 35 else 'Extreme'}</div>
            </div>
        </div>
        
        <div class="summary-bar">
            <div class="summary-group">
                <span class="summary-label strong-buy">🟢🟢 STRONG BUY</span>
                <span class="summary-tickers">{', '.join(results['summary']['strong_buy']) or '—'}</span>
            </div>
            <div class="summary-group">
                <span class="summary-label buy">🟢 BUY</span>
                <span class="summary-tickers">{', '.join(results['summary']['buy']) or '—'}</span>
            </div>
            <div class="summary-group">
                <span class="summary-label sell">🔴 SELL</span>
                <span class="summary-tickers">{', '.join(results['summary']['sell']) or '—'}</span>
            </div>
            <div class="summary-group">
                <span class="summary-label strong-sell">🔴🔴 STRONG SELL</span>
                <span class="summary-tickers">{', '.join(results['summary']['strong_sell']) or '—'}</span>
            </div>
        </div>
        
        <div class="filters">
            <button class="filter-btn active" onclick="filterSignals('all')">All ({len(signals)})</button>
            <button class="filter-btn" onclick="filterSignals('actionable')">Actionable ({len([s for s in signals if s['signal'] != 'HOLD'])})</button>
            <button class="filter-btn" onclick="filterSignals('buy')">Buy Signals</button>
            <button class="filter-btn" onclick="filterSignals('sell')">Sell Signals</button>
        </div>
        
        <table class="signals-table">
            <thead>
                <tr>
                    <th>Ticker</th>
                    <th>Signal</th>
                    <th>Price</th>
                    <th>Change</th>
                    <th>Confidence</th>
                    <th>Buy Range</th>
                    <th>Sell Range</th>
                    <th>Key Indicators</th>
                </tr>
            </thead>
            <tbody id="signals-body">
            </tbody>
        </table>
        
        <div class="options-section" id="options-section">
            <h2>📈 LEAPS Call Options - Best Value Picks</h2>
            <p class="options-subtitle">One optimal CALL option per stock. Click any ticker above to jump to its option. Sorted by potential return.</p>
            <div class="options-grid" id="options-grid">
                <!-- Options rendered by JavaScript -->
            </div>
            <div class="options-warning">
                ⚠️ Options can result in 100% loss of premium. These suggestions are based on technical analysis, not financial advice. Always do your own research.
            </div>
        </div>
        
        <div class="footer">
            <p>Auto-refreshes every 5 minutes • Not financial advice • Always do your own research</p>
        </div>
    </div>
    
    <script>
        const signals = {signals_json};
        const regime = {regime_json};
        const summary = {summary_json};
        const optionsData = {options_json};
        
        function getSignalClass(signal) {{
            return signal.toLowerCase().replace(' ', '-');
        }}
        
        function getConfidenceColor(confidence) {{
            if (confidence >= 70) return '#22c55e';
            if (confidence >= 50) return '#eab308';
            return '#94a3b8';
        }}
        
        function scrollToOption(ticker) {{
            const optionCard = document.getElementById('option-' + ticker);
            if (optionCard) {{
                // Remove highlight from all cards
                document.querySelectorAll('.option-card').forEach(card => card.classList.remove('highlighted'));
                
                // Add highlight to target card
                optionCard.classList.add('highlighted');
                
                // Scroll to the card
                optionCard.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                
                // Remove highlight after 3 seconds
                setTimeout(() => {{
                    optionCard.classList.remove('highlighted');
                }}, 3000);
            }}
        }}
        
        function refreshPage() {{
            const btn = document.querySelector('.refresh-btn');
            btn.classList.add('loading');
            btn.disabled = true;
            
            // Reload the page
            location.reload();
        }}
        
        function renderSignals(filteredSignals) {{
            const tbody = document.getElementById('signals-body');
            tbody.innerHTML = '';
            
            filteredSignals.forEach(signal => {{
                const changeClass = signal.daily_change >= 0 ? 'change-positive' : 'change-negative';
                const changeSign = signal.daily_change >= 0 ? '+' : '';
                
                const row = document.createElement('tr');
                row.dataset.signal = signal.signal;
                row.innerHTML = `
                    <td class="ticker-cell">
                        <a class="ticker-link" onclick="scrollToOption('${{signal.ticker}}')">${{signal.ticker}}</a>
                        <span class="sector-badge">${{signal.sector}}</span>
                    </td>
                    <td>
                        <span class="signal-badge ${{getSignalClass(signal.signal)}}">${{signal.signal}}</span>
                    </td>
                    <td class="price-cell">$${{signal.current_price.toFixed(2)}}</td>
                    <td class="${{changeClass}}">${{changeSign}}${{signal.daily_change.toFixed(2)}}%</td>
                    <td>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: ${{signal.confidence}}%; background: ${{getConfidenceColor(signal.confidence)}};"></div>
                            </div>
                            <span>${{signal.confidence}}%</span>
                        </div>
                    </td>
                    <td class="range-cell">${{signal.buy_range}}</td>
                    <td class="range-cell">${{signal.sell_range}}</td>
                    <td class="indicators-cell">
                        <span class="indicator"><span class="indicator-label">RSI:</span> ${{signal.indicators.rsi.toFixed(0)}}</span>
                        <span class="indicator"><span class="indicator-label">Vol:</span> ${{signal.indicators.volume_ratio.toFixed(1)}}x</span>
                        <span class="indicator"><span class="indicator-label">vs50MA:</span> ${{signal.indicators.vs_sma50 >= 0 ? '+' : ''}}${{signal.indicators.vs_sma50.toFixed(1)}}%</span>
                    </td>
                `;
                tbody.appendChild(row);
            }});
        }}
        
        function renderOptions() {{
            const grid = document.getElementById('options-grid');
            grid.innerHTML = '';
            
            if (!optionsData || optionsData.length === 0) {{
                grid.innerHTML = '<p class="no-options">No options data available. Run with options analysis enabled.</p>';
                return;
            }}
            
            // Sort by return potential
            const sortedOptions = [...optionsData].filter(s => s.options && s.options.length > 0)
                .sort((a, b) => {{
                    const returnA = a.options[0]?.return_at_target || 0;
                    const returnB = b.options[0]?.return_at_target || 0;
                    return returnB - returnA;
                }});
            
            if (sortedOptions.length === 0) {{
                grid.innerHTML = '<p class="no-options">No suitable LEAPS options found for any stocks.</p>';
                return;
            }}
            
            sortedOptions.forEach(stock => {{
                const opt = stock.options[0];
                const returnClass = opt.return_at_target >= 0 ? 'highlight' : 'negative';
                
                // Calculate buy price range (bid to mid)
                const buyLow = opt.bid > 0 ? opt.bid.toFixed(2) : (opt.mid_price * 0.95).toFixed(2);
                const buyHigh = opt.mid_price.toFixed(2);
                
                const card = document.createElement('div');
                card.className = 'option-card';
                card.id = 'option-' + stock.ticker;
                
                card.innerHTML = `
                    <div class="option-header">
                        <div>
                            <div class="option-ticker">${{stock.ticker}}</div>
                            <div class="option-stock-price">Stock: $${{stock.current_price.toFixed(2)}} → Target: $${{stock.target_price?.toFixed(2) || opt.target_price.toFixed(2)}}</div>
                        </div>
                        <div class="option-signal">
                            <span class="signal-badge ${{getSignalClass(stock.signal)}}">${{stock.signal}}</span>
                        </div>
                    </div>
                    
                    <div class="option-contract">
                        <div class="option-field">
                            <span class="option-field-label">Strike Price</span>
                            <span class="option-field-value">$${{opt.strike.toFixed(2)}}</span>
                            <span class="option-field-sub">${{opt.moneyness_label}} (${{opt.moneyness > 0 ? '+' : ''}}${{opt.moneyness.toFixed(1)}}%)</span>
                        </div>
                        <div class="option-field">
                            <span class="option-field-label">Expiry</span>
                            <span class="option-field-value">${{opt.expiry}}</span>
                            <span class="option-field-sub">${{opt.days_to_expiry}} days</span>
                        </div>
                        <div class="option-field">
                            <span class="option-field-label">Potential Return</span>
                            <span class="option-field-value ${{returnClass}}">${{opt.return_at_target >= 0 ? '+' : ''}}${{opt.return_at_target.toFixed(0)}}%</span>
                            <span class="option-field-sub">at target price</span>
                        </div>
                        <div class="option-field">
                            <span class="option-field-label">Leverage</span>
                            <span class="option-field-value">${{opt.leverage.toFixed(1)}}x</span>
                            <span class="option-field-sub">IV: ${{opt.implied_volatility.toFixed(0)}}%</span>
                        </div>
                    </div>
                    
                    <div class="option-buy-range">
                        <div class="option-buy-range-label">💰 Recommended Buy Range</div>
                        <div class="option-buy-range-value">$${{buyLow}} - $${{buyHigh}} per share</div>
                    </div>
                `;
                
                grid.appendChild(card);
            }});
            
            // Add cards for stocks without options
            const noOptionsStocks = optionsData.filter(s => !s.options || s.options.length === 0);
            if (noOptionsStocks.length > 0) {{
                const noOptDiv = document.createElement('div');
                noOptDiv.className = 'option-card';
                noOptDiv.style.gridColumn = '1 / -1';
                noOptDiv.innerHTML = `
                    <p class="no-options">No LEAPS available for: ${{noOptionsStocks.map(s => s.ticker).join(', ')}}</p>
                `;
                grid.appendChild(noOptDiv);
            }}
        }}
        
        function filterSignals(filter) {{
            // Update button states
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            let filtered;
            switch(filter) {{
                case 'actionable':
                    filtered = signals.filter(s => s.signal !== 'HOLD');
                    break;
                case 'buy':
                    filtered = signals.filter(s => s.signal.includes('BUY'));
                    break;
                case 'sell':
                    filtered = signals.filter(s => s.signal.includes('SELL'));
                    break;
                default:
                    filtered = signals;
            }}
            
            renderSignals(filtered);
        }}
        
        // Initial render
        renderSignals(signals);
        renderOptions();
        
        // Check for hash in URL to auto-scroll to option
        if (window.location.hash) {{
            const ticker = window.location.hash.substring(1);
            setTimeout(() => scrollToOption(ticker), 500);
        }}
    </script>
</body>
</html>"""
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"✅ Dashboard generated: {output_path}")
    return output_path
