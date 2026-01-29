"""
Stock Signal Generator - Options Module
=======================================
Analyzes LEAPS (Long-Term Options) for stocks with actionable signals.
Recommends optimal strike, expiry, and price targets.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class OptionsAnalyzer:
    """Analyzes options chains and recommends optimal LEAPS."""
    
    def __init__(self, ticker: str, current_price: float, signal: str, sell_target: float, buy_target: float):
        self.ticker = ticker
        self.current_price = current_price
        self.signal = signal
        self.sell_target = sell_target  # Upper price target
        self.buy_target = buy_target    # Lower price target (for entry)
        self.stock = yf.Ticker(ticker)
        
    def get_leaps_expiries(self, min_days: int = 180, max_days: int = 1100) -> List[str]:
        """Get expiration dates for LEAPS (6 months to 3 years out)."""
        try:
            all_expiries = self.stock.options
            leaps = []
            today = datetime.now()
            
            for exp in all_expiries:
                exp_date = datetime.strptime(exp, '%Y-%m-%d')
                days_to_exp = (exp_date - today).days
                
                if min_days <= days_to_exp <= max_days:
                    leaps.append(exp)
            
            return leaps
        except Exception as e:
            print(f"Error getting expiries for {self.ticker}: {e}")
            return []
    
    def get_options_chain(self, expiry: str) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Get calls and puts for a specific expiry."""
        try:
            chain = self.stock.option_chain(expiry)
            return chain.calls, chain.puts
        except Exception as e:
            print(f"Error getting chain for {self.ticker} {expiry}: {e}")
            return None, None
    
    def calculate_option_metrics(self, option_row: pd.Series, is_call: bool, target_price: float, days_to_expiry: int) -> Dict:
        """Calculate key metrics for an option."""
        
        strike = option_row['strike']
        bid = option_row.get('bid', 0) or 0
        ask = option_row.get('ask', 0) or 0
        last_price = option_row.get('lastPrice', 0) or 0
        implied_vol = option_row.get('impliedVolatility', 0) or 0
        
        # Handle NaN values for volume and open interest
        volume = option_row.get('volume', 0)
        open_interest = option_row.get('openInterest', 0)
        
        # Convert NaN to 0
        if pd.isna(volume):
            volume = 0
        if pd.isna(open_interest):
            open_interest = 0
        if pd.isna(bid):
            bid = 0
        if pd.isna(ask):
            ask = 0
        if pd.isna(last_price):
            last_price = 0
        if pd.isna(implied_vol):
            implied_vol = 0
        
        volume = int(volume)
        open_interest = int(open_interest)
        
        # Use mid price if available, otherwise last price
        if bid > 0 and ask > 0:
            mid_price = (bid + ask) / 2
        else:
            mid_price = last_price
        
        if mid_price <= 0:
            return None
        
        # Calculate intrinsic and extrinsic value
        if is_call:
            intrinsic = max(0, self.current_price - strike)
            value_at_target = max(0, target_price - strike)
        else:
            intrinsic = max(0, strike - self.current_price)
            value_at_target = max(0, strike - target_price)
        
        extrinsic = mid_price - intrinsic
        
        # Calculate returns
        if mid_price > 0:
            return_at_target = ((value_at_target - mid_price) / mid_price) * 100
            max_loss = -100  # Can lose entire premium
        else:
            return_at_target = 0
            max_loss = 0
        
        # Break-even price
        if is_call:
            break_even = strike + mid_price
        else:
            break_even = strike - mid_price
        
        # Moneyness
        if is_call:
            moneyness = (self.current_price - strike) / self.current_price * 100
        else:
            moneyness = (strike - self.current_price) / self.current_price * 100
        
        # Leverage (delta approximation for ATM)
        delta = option_row.get('delta', None)
        if delta is None:
            # Rough delta estimate
            if is_call:
                if moneyness > 10:
                    delta = 0.8
                elif moneyness > 0:
                    delta = 0.55
                elif moneyness > -10:
                    delta = 0.45
                else:
                    delta = 0.2
            else:
                if moneyness > 10:
                    delta = -0.8
                elif moneyness > 0:
                    delta = -0.55
                elif moneyness > -10:
                    delta = -0.45
                else:
                    delta = -0.2
        
        # Leverage ratio (how much option moves vs stock)
        leverage = (abs(delta) * self.current_price) / mid_price if mid_price > 0 else 0
        
        # Theta decay (rough estimate - higher for OTM, shorter expiry)
        daily_theta_pct = (extrinsic / days_to_expiry / mid_price * 100) if days_to_expiry > 0 and mid_price > 0 else 0
        
        # Liquidity score (0-100)
        liquidity_score = min(100, (volume or 0) / 10 + (open_interest or 0) / 100)
        
        # Risk/Reward score (higher is better)
        if return_at_target > 0:
            risk_reward = return_at_target / 100  # Simplified: potential return vs 100% loss
        else:
            risk_reward = 0
        
        return {
            'strike': strike,
            'bid': round(bid, 2),
            'ask': round(ask, 2),
            'mid_price': round(mid_price, 2),
            'last_price': round(last_price, 2),
            'volume': volume,
            'open_interest': open_interest,
            'implied_volatility': round(implied_vol * 100, 1),
            'delta': round(delta, 2) if delta else None,
            'intrinsic': round(intrinsic, 2),
            'extrinsic': round(extrinsic, 2),
            'moneyness': round(moneyness, 1),
            'moneyness_label': 'ITM' if moneyness > 2 else ('ATM' if moneyness > -2 else 'OTM'),
            'break_even': round(break_even, 2),
            'target_price': round(target_price, 2),
            'return_at_target': round(return_at_target, 1),
            'max_loss': -100,
            'leverage': round(leverage, 1),
            'daily_theta_pct': round(daily_theta_pct, 3),
            'liquidity_score': round(liquidity_score, 1),
            'risk_reward': round(risk_reward, 2)
        }
    
    def find_optimal_options(self, num_recommendations: int = 1) -> Dict:
        """Find the best CALL option based on potential gain and value."""
        
        # Always look for CALLS (user believes all stocks will go up)
        is_call = True
        target = self.sell_target  # Upper price target
        
        # Get LEAPS expiries
        expiries = self.get_leaps_expiries()
        
        if not expiries:
            return {
                'ticker': self.ticker,
                'current_price': round(self.current_price, 2),
                'signal': self.signal,
                'recommendation': 'No LEAPS available (options may not be listed)',
                'options': []
            }
        
        all_options = []
        
        for expiry in expiries:
            calls, puts = self.get_options_chain(expiry)
            
            exp_date = datetime.strptime(expiry, '%Y-%m-%d')
            days_to_exp = (exp_date - datetime.now()).days
            
            if calls is not None:
                for _, row in calls.iterrows():
                    metrics = self.calculate_option_metrics(row, True, target, days_to_exp)
                    if metrics and metrics['mid_price'] > 0:
                        metrics['expiry'] = expiry
                        metrics['days_to_expiry'] = days_to_exp
                        metrics['option_type'] = 'CALL'
                        all_options.append(metrics)
        
        if not all_options:
            return {
                'ticker': self.ticker,
                'current_price': round(self.current_price, 2),
                'signal': self.signal,
                'recommendation': 'No suitable options found',
                'options': []
            }
        
        # Score and rank options - optimized for best value and potential gain
        for opt in all_options:
            score = 0
            
            # HIGHEST WEIGHT: Potential return at target (50% weight)
            # We want options with the best upside potential
            if opt['return_at_target'] > 0:
                score += min(50, opt['return_at_target'] / 4)  # Cap at 50 points for 200%+ return
            
            # VALUE: Prefer reasonable leverage 3-10x (15% weight)
            # Sweet spot for risk/reward
            if 4 <= opt['leverage'] <= 8:
                score += 15
            elif 3 <= opt['leverage'] <= 12:
                score += 10
            elif opt['leverage'] > 1:
                score += 5
            
            # MONEYNESS: Prefer slightly OTM to ATM for best value (15% weight)
            # Slightly OTM gives better leverage, ATM gives better probability
            if -10 <= opt['moneyness'] <= 5:
                score += 15  # Slightly OTM to ATM - best value zone
            elif -15 <= opt['moneyness'] <= 10:
                score += 10
            elif -20 <= opt['moneyness'] <= 15:
                score += 5
            
            # TIME: Prefer 9-18 months for LEAPS sweet spot (10% weight)
            if 270 <= opt['days_to_expiry'] <= 540:
                score += 10  # 9-18 months - ideal LEAPS range
            elif 365 <= opt['days_to_expiry'] <= 730:
                score += 8   # 1-2 years
            elif opt['days_to_expiry'] >= 180:
                score += 5
            
            # VALUE: Lower IV means cheaper options (5% weight)
            if opt['implied_volatility'] < 35:
                score += 5
            elif opt['implied_volatility'] < 50:
                score += 3
            elif opt['implied_volatility'] < 70:
                score += 1
            
            # LIQUIDITY: Prefer liquid options (5% weight)
            if opt['liquidity_score'] > 50:
                score += 5
            elif opt['liquidity_score'] > 20:
                score += 3
            elif opt['liquidity_score'] > 5:
                score += 1
            
            opt['score'] = round(score, 1)
        
        # Sort by score and get THE BEST option only
        all_options.sort(key=lambda x: x['score'], reverse=True)
        best_option = all_options[:1]  # Only 1 option
        
        # Generate recommendation text
        if best_option:
            opt = best_option[0]
            rec_text = f"${opt['strike']} CALL exp {opt['expiry']} → Target ${self.sell_target:.2f}"
        else:
            rec_text = "No suitable CALL found"
        
        return {
            'ticker': self.ticker,
            'current_price': round(self.current_price, 2),
            'signal': self.signal,
            'target_price': round(self.sell_target, 2),
            'recommendation': rec_text,
            'options': best_option
        }


def analyze_options_for_signals(signals: List[Dict]) -> List[Dict]:
    """Analyze CALL options for ALL stocks (user believes all will go up)."""
    
    options_results = []
    
    for signal in signals:
        # Analyze ALL stocks, not just actionable ones
        try:
            # Parse price targets from ranges
            buy_range = signal['buy_range'].replace('$', '').split(' - ')
            sell_range = signal['sell_range'].replace('$', '').split(' - ')
            
            buy_target = float(buy_range[0])  # Lower target
            sell_target = float(sell_range[1])  # Upper target
            
            analyzer = OptionsAnalyzer(
                ticker=signal['ticker'],
                current_price=signal['current_price'],
                signal=signal['signal'],
                sell_target=sell_target,
                buy_target=buy_target
            )
            
            result = analyzer.find_optimal_options(num_recommendations=1)
            options_results.append(result)
            
            if result['options']:
                opt = result['options'][0]
                print(f"  {signal['ticker']}: ${opt['strike']} CALL exp {opt['expiry']} | +{opt['return_at_target']:.0f}% potential")
            else:
                print(f"  {signal['ticker']}: No options found")
            
        except Exception as e:
            print(f"  {signal['ticker']}: Error - {e}")
            options_results.append({
                'ticker': signal['ticker'],
                'signal': signal['signal'],
                'recommendation': f'Error analyzing options: {str(e)}',
                'options': []
            })
    
    return options_results


def format_option_for_display(opt: Dict) -> str:
    """Format a single option recommendation for display."""
    
    return (
        f"{opt['option_type']} ${opt['strike']} exp {opt['expiry']} | "
        f"Price: ${opt['mid_price']} | "
        f"Break-even: ${opt['break_even']} | "
        f"Return at target: {opt['return_at_target']:+.0f}% | "
        f"Leverage: {opt['leverage']}x | "
        f"IV: {opt['implied_volatility']}%"
    )
