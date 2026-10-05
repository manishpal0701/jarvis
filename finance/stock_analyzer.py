import yfinance as yf
import pandas as pd
import ta
import ollama
import numpy as np
import traceback
import requests
import time
import os
import json

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DEFAULT_TRADES_FILE = os.path.join(DATA_DIR, "completed_trades.json")

class StockAnalyzer:
    def __init__(self, trades_log_file=DEFAULT_TRADES_FILE):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.ollama_client = ollama.Client()
        self.cache = {}
        self.trades_log_file = trades_log_file
        self._init_learning_engine()

    def _init_learning_engine(self):
        if not os.path.exists(self.trades_log_file):
            with open(self.trades_log_file, "w") as f:
                json.dump([], f)

    def log_trade(self, symbol, entry_price, exit_price, trade_type, outcome, notes=""):
        """
        Future Learning Engine: Logs a completed trade to improve future recommendations.
        """
        try:
            trades = []
            if os.path.exists(self.trades_log_file):
                with open(self.trades_log_file, "r") as f:
                    trades = json.load(f)
            trades.append({
                "timestamp": time.time(),
                "symbol": symbol,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "trade_type": trade_type,
                "outcome": outcome, # 'win' or 'loss'
                "notes": notes
            })
            with open(self.trades_log_file, "w") as f:
                json.dump(trades, f, indent=4)
            print(f"Trade logged for {symbol}.")
            return True
        except Exception as e:
            print(f"Error logging trade: {e}")
            return False

    def get_multi_timeframe_data(self, symbol):
        timeframes = {
            "1D": {"period": "1d", "interval": "5m"},
            "5D": {"period": "5d", "interval": "15m"},
            "1M": {"period": "1mo", "interval": "1d"},
            "3M": {"period": "3mo", "interval": "1d"},
            "6M": {"period": "6mo", "interval": "1d"},
            "1Y": {"period": "1y", "interval": "1d"}
        }
        
        data = {}
        for tf, params in timeframes.items():
            try:
                df = yf.download(
                    symbol,
                    period=params["period"],
                    interval=params["interval"],
                    progress=False,
                    auto_adjust=True,
                    session=self.session
                )
                if df.empty and "." not in symbol:
                    alt_symbol = symbol + ".NS"
                    df = yf.download(alt_symbol, period=params["period"], interval=params["interval"], progress=False, auto_adjust=True, session=self.session)
                    if not df.empty:
                        symbol = alt_symbol
                
                if not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    data[tf] = df
            except Exception as e:
                print(f"Error fetching {tf} data for {symbol}: {e}")
        return data, symbol

    def calculate_indicators(self, df):
        try:
            if "Close" not in df.columns:
                return df

            close = df["Close"].astype(float)
            high = df["High"].astype(float)
            low = df["Low"].astype(float)
            volume = df["Volume"].astype(float)

            # MAs
            df["EMA20"] = ta.trend.EMAIndicator(close=close, window=20).ema_indicator()
            df["EMA50"] = ta.trend.EMAIndicator(close=close, window=50).ema_indicator()
            df["SMA200"] = ta.trend.SMAIndicator(close=close, window=200).sma_indicator()

            # Momentum
            df["RSI"] = ta.momentum.RSIIndicator(close=close, window=14).rsi()
            macd_indicator = ta.trend.MACD(close=close)
            df["MACD"] = macd_indicator.macd()
            df["MACD_SIGNAL"] = macd_indicator.macd_signal()

            # Volatility
            df["ATR"] = ta.volatility.AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
            bb = ta.volatility.BollingerBands(close=close)
            df["BB_HIGH"] = bb.bollinger_hband()
            df["BB_LOW"] = bb.bollinger_lband()

            # Trend Strength
            df["ADX"] = ta.trend.ADXIndicator(high=high, low=low, close=close, window=14).adx()

            # Volume
            df["OBV"] = ta.volume.OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume()

            # VWAP
            typical_price = (high + low + close) / 3
            df["VWAP"] = (typical_price * volume).cumsum() / volume.cumsum()

            # Fibonacci Retracement
            max_price = high.max()
            min_price = low.min()
            diff = max_price - min_price
            df["FIB_236"] = max_price - 0.236 * diff
            df["FIB_382"] = max_price - 0.382 * diff
            df["FIB_500"] = max_price - 0.5 * diff
            df["FIB_618"] = max_price - 0.618 * diff

            # Pivot Points
            df["PIVOT"] = (high + low + close) / 3
            df["R1"] = (2 * df["PIVOT"]) - low
            df["S1"] = (2 * df["PIVOT"]) - high
            df["R2"] = df["PIVOT"] + (high - low)
            df["S2"] = df["PIVOT"] - (high - low)

            return df
        except Exception as e:
            print(f"Error calculating indicators: {e}")
            return df

    def detect_candlestick_patterns(self, df):
        patterns = []
        if len(df) < 5:
            return patterns

        try:
            close = df["Close"].iloc[-1]
            open_p = df["Open"].iloc[-1]
            high = df["High"].iloc[-1]
            low = df["Low"].iloc[-1]
            
            prev_close = df["Close"].iloc[-2]
            prev_open = df["Open"].iloc[-2]

            body = abs(close - open_p)
            range_p = high - low if (high - low) > 0 else 0.001
            upper_shadow = high - max(open_p, close)
            lower_shadow = min(open_p, close) - low

            if body <= range_p * 0.1:
                patterns.append("Doji (Indecision in the market)")

            if lower_shadow >= 2 * body and upper_shadow <= range_p * 0.1:
                patterns.append("Hammer (Potential bullish reversal)")

            if upper_shadow >= 2 * body and lower_shadow <= range_p * 0.1:
                patterns.append("Shooting Star (Potential bearish reversal)")

            if close > open_p and prev_close < prev_open and close >= prev_open and open_p <= prev_close:
                patterns.append("Bullish Engulfing (Strong buying pressure)")

            if close < open_p and prev_close > prev_open and close <= prev_open and open_p >= prev_close:
                patterns.append("Bearish Engulfing (Strong selling pressure)")

            if abs(prev_close - prev_open) > 2 * body:
                if min(open_p, close) >= min(prev_open, prev_close) and max(open_p, close) <= max(prev_open, prev_close):
                    patterns.append("Harami (Inside bar, potential trend pause or reversal)")

        except Exception as e:
            print(f"Error detecting candlestick patterns: {e}")

        return patterns

    def detect_chart_patterns(self, df):
        patterns = []
        if len(df) < 20:
            return patterns

        try:
            close_prices = df["Close"].tail(20).values
            high_prices = df["High"].tail(20).values
            low_prices = df["Low"].tail(20).values

            peaks = []
            troughs = []
            for i in range(1, len(close_prices) - 1):
                if close_prices[i] > close_prices[i-1] and close_prices[i] > close_prices[i+1]:
                    peaks.append(close_prices[i])
                if close_prices[i] < close_prices[i-1] and close_prices[i] < close_prices[i+1]:
                    troughs.append(close_prices[i])

            if len(peaks) >= 2:
                if abs(peaks[-1] - peaks[-2]) / peaks[-1] < 0.02:
                    patterns.append("Double Top (Bearish reversal structure)")
            if len(troughs) >= 2:
                if abs(troughs[-1] - troughs[-2]) / troughs[-1] < 0.02:
                    patterns.append("Double Bottom (Bullish reversal structure)")

            resistance = high_prices[:-1].max()
            support = low_prices[:-1].min()
            latest_close = close_prices[-1]
            latest_volume = df["Volume"].iloc[-1]
            avg_volume = df["Volume"].tail(20).mean()

            if latest_close > resistance:
                if latest_volume > 1.5 * avg_volume:
                    patterns.append("Bullish Breakout (Price broke resistance with high volume)")
                else:
                    patterns.append("Fake Breakout (Price broke resistance but on weak volume)")
            elif latest_close < support:
                if latest_volume > 1.5 * avg_volume:
                    patterns.append("Bearish Breakout (Price broke support with high volume)")
                else:
                    patterns.append("Fake Breakout (Price broke support but on weak volume)")

        except Exception as e:
            print(f"Error detecting chart patterns: {e}")

        return patterns

    def analyze_volume(self, df):
        analysis = {}
        if len(df) < 20:
            return analysis

        try:
            latest_volume = df["Volume"].iloc[-1]
            avg_volume = df["Volume"].tail(20).mean()
            rvol = latest_volume / avg_volume if avg_volume > 0 else 1.0
            
            analysis["relative_volume"] = round(rvol, 2)
            analysis["volume_spike"] = rvol > 2.0
            
            price_change = df["Close"].iloc[-1] - df["Close"].iloc[-2]
            if price_change > 0 and rvol > 1.2:
                analysis["confirmation"] = "Volume confirms the upward move."
            elif price_change < 0 and rvol > 1.2:
                analysis["confirmation"] = "Volume confirms the downward move."
            else:
                analysis["confirmation"] = "Volume is weak, trend lacks confirmation."

        except Exception as e:
            print(f"Error analyzing volume: {e}")

        return analysis

    def get_sector_strength(self, symbol):
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            sector = info.get("sector", "Unknown")
            industry = info.get("industry", "Unknown")
            
            return {
                "sector": sector,
                "industry": industry,
                "sector_strength": "Neutral to Positive (compared to broader index)"
            }
        except:
            return {"sector": "Unknown", "industry": "Unknown", "sector_strength": "N/A"}

    def get_market_sentiment(self):
        sentiment = {}
        indices = {
            "NIFTY 50": "^NSEI",
            "BANKNIFTY": "^NSEBANK",
            "INDIA VIX": "^INDIAVIX",
            "S&P 500": "^GSPC"
        }
        for name, sym in indices.items():
            try:
                df = yf.download(sym, period="5d", interval="1d", progress=False)
                if not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    latest_close = df["Close"].iloc[-1]
                    prev_close = df["Close"].iloc[-2]
                    pct_change = ((latest_close - prev_close) / prev_close) * 100
                    sentiment[name] = {
                        "price": round(float(latest_close), 2),
                        "change": round(float(pct_change), 2)
                    }
            except:
                pass
        return sentiment

    def get_recent_news(self, symbol):
        news_list = []
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            if news:
                for item in news[:3]:
                    title = item.get("title", "")
                    publisher = item.get("publisher", "")
                    news_list.append({
                        "title": title,
                        "publisher": publisher,
                        "sentiment": "Neutral"
                    })
        except Exception as e:
            print(f"Error fetching news: {e}")
        return news_list

    def monitor_market(self, symbol, callback):
        try:
            df = yf.download(symbol, period="1d", interval="1m", progress=False)
            if df.empty:
                return
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            latest_volume = df["Volume"].iloc[-1]
            avg_volume = df["Volume"].tail(10).mean()
            if latest_volume > 3 * avg_volume:
                callback(f"Live Alert: Volume spike detected on {symbol}!")
        except Exception as e:
            print(f"Error in live monitoring: {e}")

    def ai_explanation(self, symbol, analysis_data):
        from conversation.conversation_manager import ConversationManager
        person = ConversationManager().get_person()
        speaker_name = person["name"]
        relation = person["relation"]

        system_content = f"You are a professional Wall Street Trading Analyst. You are currently speaking to {speaker_name} ({relation})."
        if relation == "owner":
            system_content += " Address the user as Boss."
        else:
            system_content += f" Address the user as {speaker_name}."

        prompt = f"""
        Act as a Professional Trading Analyst. Analyze this comprehensive stock data and generate a structured report:

        Symbol: {symbol}
        Sector: {analysis_data['sector']['sector']} (Industry: {analysis_data['sector']['industry']})
        
        TECHNICAL INDICATORS (1Y Timeframe):
        - Current Price: {analysis_data['price']}
        - EMA 20/50: {analysis_data['ema20']} / {analysis_data['ema50']}
        - SMA 200: {analysis_data['sma200']}
        - RSI: {analysis_data['rsi']}
        - MACD: {analysis_data['macd']} (Signal: {analysis_data['macd_signal']})
        - ATR: {analysis_data['atr']}
        - Bollinger Bands: High {analysis_data['bb_high']} / Low {analysis_data['bb_low']}
        - ADX (Trend Strength): {analysis_data['adx']}
        - OBV: {analysis_data['obv']}
        - VWAP: {analysis_data['vwap']}
        - Fibonacci Levels: 23.6% ({analysis_data['fib_236']}), 38.2% ({analysis_data['fib_382']}), 50.0% ({analysis_data['fib_500']}), 61.8% ({analysis_data['fib_618']})
        - Pivot Points: Pivot ({analysis_data['pivot']}), R1 ({analysis_data['r1']}), S1 ({analysis_data['s1']})

        PATTERNS & VOLUME:
        - Candlestick Patterns: {analysis_data['candlestick_patterns']}
        - Chart Patterns: {analysis_data['chart_patterns']}
        - Volume Analysis: Relative Volume {analysis_data['volume']['relative_volume']}, Confirmation: {analysis_data['volume']['confirmation']}

        MARKET SENTIMENT & NEWS:
        - Broader Market Sentiment: {analysis_data['market_sentiment']}
        - Recent News: {analysis_data['news']}

        Please generate a professional, structured report containing:
        1. Market Trend & Strength (Bullish/Bearish/Sideways with ADX explanation)
        2. Technical Analysis Summary (How indicators align)
        3. Pattern Recognition (Candlestick & Chart structures)
        4. Volume Analysis
        5. Sector & Market Sentiment Influence
        6. Risk Analysis (Suggested Stop-Loss, Target, Risk/Reward Ratio)
        7. Confidence Score (Bullish/Bearish/Neutral probabilities & overall confidence %)
        8. Final Analytical Assessment (Clear, logical reasoning)

        Keep it professional, logical, and easy to understand. Avoid guaranteed predictions.
        """

        try:
            response = self.ollama_client.chat(
                model="qwen3:8b",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ]
            )
            return response["message"]["content"]
        except Exception as e:
            return f"AI Analysis Error: {e}"

    def analyze(self, symbol):
        if symbol in self.cache:
            cached_time, cached_result = self.cache[symbol]
            if time.time() - cached_time < 3600:
                print(f"Using cached analysis for {symbol}")
                return cached_result

        print(f"Analyzing {symbol}...")
        data, resolved_symbol = self.get_multi_timeframe_data(symbol)

        if not data or "1Y" not in data:
            return f"Error: No data found for {symbol}. Please check the symbol and try again."

        df_1y = data["1Y"]
        if len(df_1y) < 15:
            return f"Insufficient data for analysis of {symbol}."

        df_1y = self.calculate_indicators(df_1y)
        df_1y = df_1y.dropna(subset=['Close', 'RSI', 'MACD', 'EMA20'])
        if df_1y.empty:
            return f"Error: Technical processing resulted in no valid data for {symbol}."

        latest = df_1y.iloc[-1]
        
        analysis_data = {
            'price': round(float(latest["Close"]), 2),
            'rsi': round(float(latest["RSI"]), 2),
            'macd': round(float(latest["MACD"]), 2),
            'macd_signal': round(float(latest["MACD_SIGNAL"]), 2),
            'ema20': round(float(latest["EMA20"]), 2),
            'ema50': round(float(latest["EMA50"]), 2),
            'sma200': round(float(latest["SMA200"]), 2) if not np.isnan(latest["SMA200"]) else "N/A",
            'atr': round(float(latest["ATR"]), 4) if not np.isnan(latest["ATR"]) else "N/A",
            'bb_high': round(float(latest["BB_HIGH"]), 2) if not np.isnan(latest["BB_HIGH"]) else "N/A",
            'bb_low': round(float(latest["BB_LOW"]), 2) if not np.isnan(latest["BB_LOW"]) else "N/A",
            'adx': round(float(latest["ADX"]), 2) if not np.isnan(latest["ADX"]) else "N/A",
            'obv': float(latest["OBV"]) if not np.isnan(latest["OBV"]) else "N/A",
            'vwap': round(float(latest["VWAP"]), 2) if not np.isnan(latest["VWAP"]) else "N/A",
            'fib_236': round(float(latest["FIB_236"]), 2),
            'fib_382': round(float(latest["FIB_382"]), 2),
            'fib_500': round(float(latest["FIB_500"]), 2),
            'fib_618': round(float(latest["FIB_618"]), 2),
            'pivot': round(float(latest["PIVOT"]), 2),
            'r1': round(float(latest["R1"]), 2),
            's1': round(float(latest["S1"]), 2),
            'candlestick_patterns': self.detect_candlestick_patterns(df_1y),
            'chart_patterns': self.detect_chart_patterns(df_1y),
            'volume': self.analyze_volume(df_1y),
            'sector': self.get_sector_strength(resolved_symbol),
            'market_sentiment': self.get_market_sentiment(),
            'news': self.get_recent_news(resolved_symbol)
        }

        result = self.ai_explanation(resolved_symbol, analysis_data)
        self.cache[symbol] = (time.time(), result)
        return result
