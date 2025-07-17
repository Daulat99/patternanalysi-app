import numpy as np
import pandas as pd
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

class PatternDetector:
    def __init__(self):
        self.min_periods = 20
        
    def detect_patterns(self, data):
        """Main pattern detection function"""
        if len(data) < self.min_periods:
            return []
        
        df = pd.DataFrame(data)
        patterns = []
        
        # Technical indicators
        df['sma_20'] = SMAIndicator(df['close'], window=20).sma_indicator()
        df['ema_12'] = EMAIndicator(df['close'], window=12).ema_indicator()
        df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
        
        # Bollinger Bands
        bb = BollingerBands(df['close'], window=20, window_dev=2)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()
        
        # Pattern detection
        patterns.extend(self.detect_double_top(df))
        patterns.extend(self.detect_double_bottom(df))
        patterns.extend(self.detect_head_shoulders(df))
        patterns.extend(self.detect_triangle(df))
        patterns.extend(self.detect_flag(df))
        patterns.extend(self.detect_support_resistance(df))
        
        return patterns
    
    def detect_double_top(self, df):
        """Detect Double Top pattern"""
        patterns = []
        highs = df['high'].values
        closes = df['close'].values
        
        if len(highs) < 20:
            return patterns
        
        # Find peaks
        peaks = []
        for i in range(2, len(highs)-2):
            if (highs[i] > highs[i-1] and highs[i] > highs[i+1] and 
                highs[i] > highs[i-2] and highs[i] > highs[i+2]):
                peaks.append({'index': i, 'price': highs[i]})
        
        # Check for double top
        if len(peaks) >= 2:
            for i in range(len(peaks)-1):
                peak1 = peaks[i]
                peak2 = peaks[i+1]
                
                price_diff = abs(peak1['price'] - peak2['price'])
                avg_price = (peak1['price'] + peak2['price']) / 2
                
                if price_diff / avg_price < 0.02:  # Within 2%
                    current_price = closes[-1]
                    resistance = max(peak1['price'], peak2['price'])
                    
                    if current_price < resistance * 0.98:
                        patterns.append({
                            'pattern': 'Double Top',
                            'type': 'BEARISH',
                            'confidence': 75,
                            'entry': current_price,
                            'stop_loss': resistance * 1.01,
                            'target': current_price * 0.94,
                            'risk_reward': 2.5,
                            'description': 'Bearish reversal pattern detected'
                        })
        
        return patterns
    
    def detect_double_bottom(self, df):
        """Detect Double Bottom pattern"""
        patterns = []
        lows = df['low'].values
        closes = df['close'].values
        
        if len(lows) < 20:
            return patterns
        
        # Find troughs
        troughs = []
        for i in range(2, len(lows)-2):
            if (lows[i] < lows[i-1] and lows[i] < lows[i+1] and 
                lows[i] < lows[i-2] and lows[i] < lows[i+2]):
                troughs.append({'index': i, 'price': lows[i]})
        
        # Check for double bottom
        if len(troughs) >= 2:
            for i in range(len(troughs)-1):
                trough1 = troughs[i]
                trough2 = troughs[i+1]
                
                price_diff = abs(trough1['price'] - trough2['price'])
                avg_price = (trough1['price'] + trough2['price']) / 2
                
                if price_diff / avg_price < 0.02:  # Within 2%
                    current_price = closes[-1]
                    support = min(trough1['price'], trough2['price'])
                    
                    if current_price > support * 1.02:
                        patterns.append({
                            'pattern': 'Double Bottom',
                            'type': 'BULLISH',
                            'confidence': 75,
                            'entry': current_price,
                            'stop_loss': support * 0.99,
                            'target': current_price * 1.06,
                            'risk_reward': 2.5,
                            'description': 'Bullish reversal pattern detected'
                        })
        
        return patterns
    
    def detect_head_shoulders(self, df):
        """Detect Head and Shoulders pattern"""
        patterns = []
        highs = df['high'].values
        closes = df['close'].values
        
        if len(highs) < 30:
            return patterns
        
        # Find three consecutive peaks
        peaks = []
        for i in range(2, len(highs)-2):
            if (highs[i] > highs[i-1] and highs[i] > highs[i+1] and 
                highs[i] > highs[i-2] and highs[i] > highs[i+2]):
                peaks.append({'index': i, 'price': highs[i]})
        
        if len(peaks) >= 3:
            for i in range(len(peaks)-2):
                left_shoulder = peaks[i]
                head = peaks[i+1]
                right_shoulder = peaks[i+2]
                
                # Check if middle peak is highest (head)
                if (head['price'] > left_shoulder['price'] and 
                    head['price'] > right_shoulder['price']):
                    
                    # Check if shoulders are roughly equal
                    shoulder_diff = abs(left_shoulder['price'] - right_shoulder['price'])
                    avg_shoulder = (left_shoulder['price'] + right_shoulder['price']) / 2
                    
                    if shoulder_diff / avg_shoulder < 0.03:  # Within 3%
                        current_price = closes[-1]
                        neckline = avg_shoulder * 0.98
                        
                        if current_price < neckline:
                            patterns.append({
                                'pattern': 'Head and Shoulders',
                                'type': 'BEARISH',
                                'confidence': 80,
                                'entry': current_price,
                                'stop_loss': head['price'] * 1.01,
                                'target': neckline - (head['price'] - neckline),
                                'risk_reward': 2.0,
                                'description': 'Strong bearish reversal pattern'
                            })
        
        return patterns
    
    def detect_triangle(self, df):
        """Detect Triangle patterns"""
        patterns = []
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        if len(highs) < 20:
            return patterns
        
        # Get recent highs and lows
        recent_highs = highs[-20:]
        recent_lows = lows[-20:]
        
        # Check for ascending triangle
        high_trend = np.polyfit(range(len(recent_highs)), recent_highs, 1)[0]
        low_trend = np.polyfit(range(len(recent_lows)), recent_lows, 1)[0]
        
        current_price = closes[-1]
        
        if abs(high_trend) < 0.001 and low_trend > 0:  # Flat resistance, rising support
            patterns.append({
                'pattern': 'Ascending Triangle',
                'type': 'BULLISH',
                'confidence': 65,
                'entry': current_price,
                'stop_loss': recent_lows[-1] * 0.98,
                'target': current_price * 1.05,
                'risk_reward': 2.0,
                'description': 'Bullish continuation pattern'
            })
        
        elif abs(low_trend) < 0.001 and high_trend < 0:  # Flat support, falling resistance
            patterns.append({
                'pattern': 'Descending Triangle',
                'type': 'BEARISH',
                'confidence': 65,
                'entry': current_price,
                'stop_loss': recent_highs[-1] * 1.02,
                'target': current_price * 0.95,
                'risk_reward': 2.0,
                'description': 'Bearish continuation pattern'
            })
        
        return patterns
    
    def detect_flag(self, df):
        """Detect Flag patterns"""
        patterns = []
        closes = df['close'].values
        
        if len(closes) < 15:
            return patterns
        
        # Check for strong move followed by consolidation
        recent_closes = closes[-15:]
        price_change = (recent_closes[-1] - recent_closes[0]) / recent_closes[0]
        
        if abs(price_change) > 0.05:  # Strong move of 5%+
            # Check for consolidation (low volatility)
            consolidation_period = recent_closes[-8:]
            volatility = np.std(consolidation_period) / np.mean(consolidation_period)
            
            if volatility < 0.02:  # Low volatility consolidation
                current_price = closes[-1]
                
                if price_change > 0:  # Bullish flag
                    patterns.append({
                        'pattern': 'Bull Flag',
                        'type': 'BULLISH',
                        'confidence': 70,
                        'entry': current_price,
                        'stop_loss': min(consolidation_period) * 0.98,
                        'target': current_price * 1.06,
                        'risk_reward': 2.5,
                        'description': 'Bullish continuation pattern'
                    })
                else:  # Bearish flag
                    patterns.append({
                        'pattern': 'Bear Flag',
                        'type': 'BEARISH',
                        'confidence': 70,
                        'entry': current_price,
                        'stop_loss': max(consolidation_period) * 1.02,
                        'target': current_price * 0.94,
                        'risk_reward': 2.5,
                        'description': 'Bearish continuation pattern'
                    })
        
        return patterns
    
    def detect_support_resistance(self, df):
        """Detect Support and Resistance levels"""
        patterns = []
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        
        if len(closes) < 20:
            return patterns
        
        current_price = closes[-1]
        
        # Find support levels
        recent_lows = lows[-20:]
        support_level = np.percentile(recent_lows, 25)
        
        # Find resistance levels
        recent_highs = highs[-20:]
        resistance_level = np.percentile(recent_highs, 75)
        
        # Check if price is near support
        if abs(current_price - support_level) / support_level < 0.02:
            patterns.append({
                'pattern': 'Support Level',
                'type': 'BULLISH',
                'confidence': 60,
                'entry': current_price,
                'stop_loss': support_level * 0.98,
                'target': current_price * 1.04,
                'risk_reward': 2.0,
                'description': f'Price bouncing off support at {support_level:.2f}'
            })
        
        # Check if price is near resistance
        if abs(current_price - resistance_level) / resistance_level < 0.02:
            patterns.append({
                'pattern': 'Resistance Level',
                'type': 'BEARISH',
                'confidence': 60,
                'entry': current_price,
                'stop_loss': resistance_level * 1.02,
                'target': current_price * 0.96,
                'risk_reward': 2.0,
                'description': f'Price rejecting resistance at {resistance_level:.2f}'
            })
        
        return patterns
