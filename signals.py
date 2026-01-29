"""
Stock Signal Generator - Core Engine
====================================
Generates buy/sell/hold signals using technical analysis and market regime detection.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import yaml
import warnings
warnings.filterwarnings('ignore')


class MarketRegime:
    """Detects overall market conditions to contextualize individual stock signals."""
    
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"
    CRASH = "CRASH"
    
    def __init__(self, spy_data: pd.DataFrame, qqq_data: pd.DataFrame, vix_level: float):
        self.spy = spy_data
        self.qqq = qqq_data
        self.vix = vix_level
        
        # Handle multi-level columns from yfinance
        if isinstance(self.spy.columns, pd.MultiIndex):
            self.spy.columns = self.spy.columns.get_level_values(0)
        if isinstance(self.qqq.columns, pd.MultiIndex):
            self.qqq.columns = self.qqq.columns.get_level_values(0)
        
        self.regime = self._detect_regime()
        self.details = self._get_details()
    
    def _detect_regime(self) -> str:
        """Determine market regime based on SPY trend, QQQ trend, and VIX levels."""
        
        # Calculate moving averages
        spy_close = self.spy['Close'].iloc[-1]
        spy_ma50 = self.spy['Close'].rolling(50).mean().iloc[-1]
        spy_ma200 = self.spy['Close'].rolling(200).mean().iloc[-1]
        
        qqq_close = self.qqq['Close'].iloc[-1]
        qqq_ma50 = self.qqq['Close'].rolling(50).mean().iloc[-1]
        
        # SPY trend
        spy_above_50 = spy_close > spy_ma50
        spy_above_200 = spy_close > spy_ma200
        spy_50_above_200 = spy_ma50 > spy_ma200
        
        # QQQ trend
        qqq_above_50 = qqq_close > qqq_ma50
        
        # VIX levels
        vix_low = self.vix < 15
        vix_normal = 15 <= self.vix < 25
        vix_elevated = 25 <= self.vix < 35
        vix_extreme = self.vix >= 35
        
        # Regime logic
        if vix_extreme:
            return self.CRASH
        elif not spy_above_200 and not spy_above_50 and vix_elevated:
            return self.BEARISH
        elif spy_above_200 and spy_above_50 and spy_50_above_200 and (vix_low or vix_normal):
            if qqq_above_50:
                return self.BULLISH
            else:
                return self.NEUTRAL
        elif spy_above_200 or spy_above_50:
            return self.NEUTRAL
        else:
            return self.BEARISH
    
    def _get_details(self) -> Dict:
        """Get detailed market metrics."""
        spy_close = self.spy['Close'].iloc[-1]
        spy_ma50 = self.spy['Close'].rolling(50).mean().iloc[-1]
        spy_ma200 = self.spy['Close'].rolling(200).mean().iloc[-1]
        
        qqq_close = self.qqq['Close'].iloc[-1]
        qqq_ma50 = self.qqq['Close'].rolling(50).mean().iloc[-1]
        
        return {
            'spy_price': round(spy_close, 2),
            'spy_vs_50ma': round((spy_close / spy_ma50 - 1) * 100, 2),
            'spy_vs_200ma': round((spy_close / spy_ma200 - 1) * 100, 2),
            'qqq_price': round(qqq_close, 2),
            'qqq_vs_50ma': round((qqq_close / qqq_ma50 - 1) * 100, 2),
            'vix': round(self.vix, 2)
        }
    
    def get_signal_modifier(self) -> float:
        """Returns a multiplier to adjust signal strength based on market regime."""
        modifiers = {
            self.BULLISH: 1.0,
            self.NEUTRAL: 0.7,
            self.BEARISH: 0.4,
            self.CRASH: 0.1
        }
        return modifiers.get(self.regime, 0.5)


class TechnicalIndicators:
    """Calculate technical indicators for a stock."""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.close = data['Close']
        self.high = data['High']
        self.low = data['Low']
        self.volume = data['Volume']
        
    def rsi(self, period: int = 14) -> pd.Series:
        """Relative Strength Index."""
        delta = self.close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD, Signal line, and Histogram."""
        exp1 = self.close.ewm(span=fast, adjust=False).mean()
        exp2 = self.close.ewm(span=slow, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    def bollinger_bands(self, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands: upper, middle, lower."""
        middle = self.close.rolling(window=period).mean()
        std = self.close.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    def sma(self, period: int) -> pd.Series:
        """Simple Moving Average."""
        return self.close.rolling(window=period).mean()
    
    def ema(self, period: int) -> pd.Series:
        """Exponential Moving Average."""
        return self.close.ewm(span=period, adjust=False).mean()
    
    def atr(self, period: int = 14) -> pd.Series:
        """Average True Range for volatility."""
        high_low = self.high - self.low
        high_close = abs(self.high - self.close.shift())
        low_close = abs(self.low - self.close.shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(window=period).mean()
    
    def volume_sma(self, period: int = 20) -> pd.Series:
        """Volume Simple Moving Average."""
        return self.volume.rolling(window=period).mean()
    
    def stochastic(self, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """Stochastic Oscillator %K and %D."""
        lowest_low = self.low.rolling(window=k_period).min()
        highest_high = self.high.rolling(window=k_period).max()
        k = 100 * (self.close - lowest_low) / (highest_high - lowest_low)
        d = k.rolling(window=d_period).mean()
        return k, d
    
    def support_resistance(self, lookback: int = 20) -> Tuple[float, float]:
        """Simple support/resistance based on recent highs/lows."""
        recent_high = self.high.tail(lookback).max()
        recent_low = self.low.tail(lookback).min()
        return recent_low, recent_high


class StockSignal:
    """Generate trading signals for a single stock."""
    
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG BUY"
    STRONG_SELL = "STRONG SELL"
    
    def __init__(self, ticker: str, data: pd.DataFrame, sector: str, config: Dict):
        self.ticker = ticker
        self.data = data
        self.sector = sector
        self.config = config
        self.indicators = TechnicalIndicators(data)
        self.thresholds = config.get('thresholds', {})
        
        # Current values
        self.current_price = data['Close'].iloc[-1]
        self.prev_close = data['Close'].iloc[-2] if len(data) > 1 else self.current_price
        
        # Calculate all indicators
        self._calculate_indicators()
        
    def _calculate_indicators(self):
        """Pre-calculate all technical indicators."""
        # RSI
        rsi_series = self.indicators.rsi()
        self.rsi = rsi_series.iloc[-1]
        self.rsi_prev = rsi_series.iloc[-2] if len(rsi_series) > 1 else self.rsi
        
        # MACD
        macd, signal, hist = self.indicators.macd()
        self.macd = macd.iloc[-1]
        self.macd_signal = signal.iloc[-1]
        self.macd_hist = hist.iloc[-1]
        self.macd_hist_prev = hist.iloc[-2] if len(hist) > 1 else self.macd_hist
        
        # Bollinger Bands
        upper, middle, lower = self.indicators.bollinger_bands()
        self.bb_upper = upper.iloc[-1]
        self.bb_middle = middle.iloc[-1]
        self.bb_lower = lower.iloc[-1]
        self.bb_width = (self.bb_upper - self.bb_lower) / self.bb_middle
        
        # Moving Averages
        self.sma_20 = self.indicators.sma(20).iloc[-1]
        self.sma_50 = self.indicators.sma(50).iloc[-1]
        self.sma_200 = self.indicators.sma(200).iloc[-1] if len(self.data) >= 200 else None
        self.ema_9 = self.indicators.ema(9).iloc[-1]
        self.ema_21 = self.indicators.ema(21).iloc[-1]
        
        # Volume
        self.current_volume = self.data['Volume'].iloc[-1]
        self.avg_volume = self.indicators.volume_sma(20).iloc[-1]
        self.volume_ratio = self.current_volume / self.avg_volume if self.avg_volume > 0 else 1
        
        # ATR for price targets
        self.atr = self.indicators.atr().iloc[-1]
        
        # Stochastic
        k, d = self.indicators.stochastic()
        self.stoch_k = k.iloc[-1]
        self.stoch_d = d.iloc[-1]
        
        # Support/Resistance
        self.support, self.resistance = self.indicators.support_resistance()
        
    def _score_rsi(self) -> float:
        """Score based on RSI. Returns -1 to 1."""
        oversold = self.thresholds.get('rsi_oversold', 30)
        overbought = self.thresholds.get('rsi_overbought', 70)
        
        if self.rsi < oversold:
            # Oversold - bullish signal
            return min(1.0, (oversold - self.rsi) / 15)
        elif self.rsi > overbought:
            # Overbought - bearish signal
            return max(-1.0, (overbought - self.rsi) / 15)
        else:
            # Neutral zone
            return 0.0
    
    def _score_macd(self) -> float:
        """Score based on MACD crossover and histogram. Returns -1 to 1."""
        # Histogram momentum
        hist_momentum = 0.0
        if self.macd_hist > 0 and self.macd_hist > self.macd_hist_prev:
            hist_momentum = 0.5  # Bullish momentum increasing
        elif self.macd_hist < 0 and self.macd_hist < self.macd_hist_prev:
            hist_momentum = -0.5  # Bearish momentum increasing
            
        # Crossover signal
        crossover = 0.0
        if self.macd > self.macd_signal and self.macd_hist > 0:
            crossover = 0.5  # Bullish crossover
        elif self.macd < self.macd_signal and self.macd_hist < 0:
            crossover = -0.5  # Bearish crossover
            
        return hist_momentum + crossover
    
    def _score_bollinger(self) -> float:
        """Score based on Bollinger Band position. Returns -1 to 1."""
        position = (self.current_price - self.bb_lower) / (self.bb_upper - self.bb_lower)
        
        if position < 0.1:
            return 0.8  # Near lower band - bullish
        elif position > 0.9:
            return -0.8  # Near upper band - bearish
        elif position < 0.3:
            return 0.3
        elif position > 0.7:
            return -0.3
        else:
            return 0.0
    
    def _score_moving_averages(self) -> float:
        """Score based on moving average alignment. Returns -1 to 1."""
        score = 0.0
        
        # Price vs MAs
        if self.current_price > self.sma_20:
            score += 0.2
        else:
            score -= 0.2
            
        if self.current_price > self.sma_50:
            score += 0.3
        else:
            score -= 0.3
            
        if self.sma_200 is not None:
            if self.current_price > self.sma_200:
                score += 0.3
            else:
                score -= 0.3
                
        # EMA crossover
        if self.ema_9 > self.ema_21:
            score += 0.2
        else:
            score -= 0.2
            
        return max(-1.0, min(1.0, score))
    
    def _score_volume(self) -> float:
        """Score based on volume confirmation. Returns 0 to 0.5."""
        surge_threshold = self.thresholds.get('volume_surge', 1.5)
        
        if self.volume_ratio > surge_threshold:
            # High volume - amplifies other signals
            return 0.3
        elif self.volume_ratio > 1.0:
            return 0.1
        else:
            return -0.1  # Below average volume - less conviction
    
    def _score_stochastic(self) -> float:
        """Score based on Stochastic oscillator. Returns -0.5 to 0.5."""
        if self.stoch_k < 20 and self.stoch_d < 20:
            return 0.5  # Oversold
        elif self.stoch_k > 80 and self.stoch_d > 80:
            return -0.5  # Overbought
        elif self.stoch_k > self.stoch_d and self.stoch_k < 50:
            return 0.2  # Bullish crossover in lower half
        elif self.stoch_k < self.stoch_d and self.stoch_k > 50:
            return -0.2  # Bearish crossover in upper half
        return 0.0
    
    def calculate_composite_score(self, market_modifier: float = 1.0) -> float:
        """Calculate weighted composite score from all indicators."""
        
        # Weights for each indicator
        weights = {
            'rsi': 0.20,
            'macd': 0.25,
            'bollinger': 0.15,
            'ma': 0.25,
            'volume': 0.10,
            'stochastic': 0.05
        }
        
        # Calculate individual scores
        scores = {
            'rsi': self._score_rsi(),
            'macd': self._score_macd(),
            'bollinger': self._score_bollinger(),
            'ma': self._score_moving_averages(),
            'volume': self._score_volume(),
            'stochastic': self._score_stochastic()
        }
        
        # Weighted sum
        raw_score = sum(scores[k] * weights[k] for k in weights)
        
        # Apply market regime modifier
        adjusted_score = raw_score * market_modifier
        
        return adjusted_score, scores
    
    def generate_signal(self, market_regime: MarketRegime) -> Dict:
        """Generate the final trading signal with price targets."""
        
        modifier = market_regime.get_signal_modifier()
        composite_score, individual_scores = self.calculate_composite_score(modifier)
        
        # Determine signal
        if composite_score >= 0.5:
            signal = self.STRONG_BUY
        elif composite_score >= 0.2:
            signal = self.BUY
        elif composite_score <= -0.5:
            signal = self.STRONG_SELL
        elif composite_score <= -0.2:
            signal = self.SELL
        else:
            signal = self.HOLD
        
        # Adjust for market regime
        if market_regime.regime == MarketRegime.CRASH:
            if signal in [self.BUY, self.STRONG_BUY]:
                signal = self.HOLD
        elif market_regime.regime == MarketRegime.BEARISH:
            if signal == self.STRONG_BUY:
                signal = self.BUY
        
        # Calculate price targets
        buy_target_low = round(self.current_price - (self.atr * 1.5), 2)
        buy_target_high = round(self.current_price - (self.atr * 0.5), 2)
        sell_target_low = round(self.current_price + (self.atr * 0.5), 2)
        sell_target_high = round(self.current_price + (self.atr * 2.0), 2)
        
        # Confidence level (0-100)
        confidence = int(min(100, abs(composite_score) * 100 + 20))
        
        # Daily change
        daily_change = ((self.current_price - self.prev_close) / self.prev_close) * 100
        
        return {
            'ticker': self.ticker,
            'sector': self.sector,
            'signal': signal,
            'confidence': confidence,
            'composite_score': round(composite_score, 3),
            'current_price': round(self.current_price, 2),
            'daily_change': round(daily_change, 2),
            'buy_range': f"${buy_target_low} - ${buy_target_high}",
            'sell_range': f"${sell_target_low} - ${sell_target_high}",
            'support': round(self.support, 2),
            'resistance': round(self.resistance, 2),
            'indicators': {
                'rsi': round(self.rsi, 1),
                'macd_hist': round(self.macd_hist, 4),
                'bb_position': round((self.current_price - self.bb_lower) / (self.bb_upper - self.bb_lower) * 100, 1),
                'vs_sma50': round((self.current_price / self.sma_50 - 1) * 100, 2),
                'volume_ratio': round(self.volume_ratio, 2),
                'stoch_k': round(self.stoch_k, 1)
            },
            'individual_scores': {k: round(v, 3) for k, v in individual_scores.items()},
            'timestamp': datetime.now().isoformat()
        }


class SignalEngine:
    """Main engine to generate signals for all stocks."""
    
    def __init__(self, config_path: str = 'config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.watchlist = self.config.get('watchlist', {})
        self.all_tickers = self._flatten_watchlist()
        self.lookback_days = self.config.get('data', {}).get('lookback_days', 100)
        
    def _flatten_watchlist(self) -> List[Tuple[str, str]]:
        """Flatten watchlist to list of (ticker, sector) tuples."""
        tickers = []
        for sector, stocks in self.watchlist.items():
            for stock in stocks:
                tickers.append((stock, sector))
        return tickers
    
    def fetch_market_data(self) -> MarketRegime:
        """Fetch market index data and determine regime."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # Need 200 days for MA
        
        spy = yf.download('SPY', start=start_date, end=end_date, progress=False)
        qqq = yf.download('QQQ', start=start_date, end=end_date, progress=False)
        vix = yf.download('^VIX', start=start_date, end=end_date, progress=False)
        
        # Handle both single and multi-level column formats from yfinance
        if isinstance(spy.columns, pd.MultiIndex):
            spy.columns = spy.columns.get_level_values(0)
            qqq.columns = qqq.columns.get_level_values(0)
            vix.columns = vix.columns.get_level_values(0)
        
        # Extract scalar value for VIX
        vix_level = float(vix['Close'].iloc[-1])
        
        return MarketRegime(spy, qqq, vix_level)
    
    def fetch_stock_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """Fetch historical data for a single stock."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        try:
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if len(data) < 50:
                print(f"Warning: Insufficient data for {ticker}")
                return None
            
            # Handle both single and multi-level column formats from yfinance
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            return data
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None
    
    def generate_all_signals(self) -> Dict:
        """Generate signals for all stocks in watchlist."""
        print("Fetching market data...")
        market_regime = self.fetch_market_data()
        
        print(f"Market Regime: {market_regime.regime}")
        print(f"VIX: {market_regime.details['vix']}")
        print(f"SPY vs 50MA: {market_regime.details['spy_vs_50ma']}%")
        print()
        
        results = {
            'market_regime': {
                'regime': market_regime.regime,
                'details': market_regime.details,
                'modifier': market_regime.get_signal_modifier()
            },
            'signals': [],
            'summary': {
                'strong_buy': [],
                'buy': [],
                'hold': [],
                'sell': [],
                'strong_sell': []
            },
            'generated_at': datetime.now().isoformat()
        }
        
        print(f"Analyzing {len(self.all_tickers)} stocks...")
        
        for ticker, sector in self.all_tickers:
            data = self.fetch_stock_data(ticker)
            if data is None:
                continue
                
            try:
                signal_gen = StockSignal(ticker, data, sector, self.config)
                signal = signal_gen.generate_signal(market_regime)
                results['signals'].append(signal)
                
                # Categorize
                signal_type = signal['signal'].lower().replace(' ', '_')
                if signal_type in results['summary']:
                    results['summary'][signal_type].append(ticker)
                    
                print(f"  {ticker}: {signal['signal']} (confidence: {signal['confidence']}%)")
                
            except Exception as e:
                print(f"  Error analyzing {ticker}: {e}")
        
        return results
    
    def get_actionable_signals(self, results: Dict) -> List[Dict]:
        """Filter to only actionable signals (not HOLD)."""
        return [s for s in results['signals'] if s['signal'] != 'HOLD']
