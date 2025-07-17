from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import threading
import time
import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from patterns.detector import PatternDetector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'trading-tool-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

class TradingDataManager:
    def __init__(self):
        self.current_data = {}
        self.pattern_detector = PatternDetector()
        self.active_streams = {}
        
    def get_crypto_data(self, symbol='BTCUSDT', interval='1m', limit=100):
        """Get crypto data from Binance"""
        try:
            url = f"https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            formatted_data = []
            for kline in data:
                formatted_data.append({
                    'time': kline[0] / 1000,
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                })
            return formatted_data
        except Exception as e:
            print(f"Error fetching crypto data: {e}")
            return []
    
    def get_forex_data(self, symbol='EURUSD=X', period='1d', interval='1m'):
        """Get forex data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            formatted_data = []
            for index, row in data.iterrows():
                formatted_data.append({
                    'time': int(index.timestamp()),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': float(row['Volume'])
                })
            return formatted_data
        except Exception as e:
            print(f"Error fetching forex data: {e}")
            return []
    
    def start_live_updates(self, symbol, market_type, interval):
        """Start live data updates"""
        def update_data():
            while True:
                try:
                    if market_type == 'crypto':
                        data = self.get_crypto_data(symbol, interval, 50)
                    else:
                        data = self.get_forex_data(symbol, '1d', interval)
                    
                    if data:
                        patterns = self.pattern_detector.detect_patterns(data)
                        latest_candle = data[-1]
                        socketio.emit('candlestick_update', {
                            'candle': latest_candle,
                            'patterns': patterns
                        })
                    
                    time.sleep(5)
                except Exception as e:
                    print(f"Error in live updates: {e}")
                    time.sleep(10)
        
        update_thread = threading.Thread(target=update_data)
        update_thread.daemon = True
        update_thread.start()

data_manager = TradingDataManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/historical/<market>/<symbol>/<interval>')
def get_historical_data(market, symbol, interval):
    """Get historical data for chart initialization"""
    if market == 'crypto':
        data = data_manager.get_crypto_data(symbol, interval, 100)
    else:
        data = data_manager.get_forex_data(symbol, '5d', interval)
    
    return jsonify(data)

@app.route('/api/patterns/<market>/<symbol>/<interval>')
def get_patterns(market, symbol, interval):
    """Get pattern analysis"""
    if market == 'crypto':
        data = data_manager.get_crypto_data(symbol, interval, 100)
    else:
        data = data_manager.get_forex_data(symbol, '5d', interval)
    
    patterns = data_manager.pattern_detector.detect_patterns(data)
    return jsonify(patterns)

@socketio.on('start_live_feed')
def handle_start_live_feed(data):
    """Start live data feed"""
    symbol = data.get('symbol', 'BTCUSDT')
    market_type = data.get('market', 'crypto')
    interval = data.get('interval', '1m')
    
    data_manager.start_live_updates(symbol, market_type, interval)
    emit('feed_started', {'status': 'Live feed started'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
