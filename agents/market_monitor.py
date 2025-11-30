"""
Market Monitoring Agent
Получает реальные данные рынка и отправляет их другим агентам
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional


class MarketMonitoringAgent:
    """Агент для мониторинга рынка и получения данных"""
    
    def __init__(self, ticker: str = "AAPL"):
        """
        Инициализация агента
        
        Args:
            ticker: Тикер акции (по умолчанию AAPL)
        """
        self.ticker = ticker
        self.last_update = None
        self.data_history = []
        
    def get_market_data(self, period: str = "1mo", interval: str = "1d") -> Dict:
        """
        Получает данные рынка по тикеру
        
        Args:
            period: Период данных (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Интервал (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        
        Returns:
            Словарь с данными рынка
        """
        try:
            stock = yf.Ticker(self.ticker)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                return {
                    "type": "error",
                    "message": f"No data available for {self.ticker}",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Получаем дополнительную информацию
            info = stock.info
            current_price = df['Close'].iloc[-1]
            
            # Вычисляем технические индикаторы (как в train_model.py)
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA50'] = df['Close'].rolling(window=50).mean()
            df['Returns'] = df['Close'].pct_change()
            df['Returns_5'] = df['Returns'].rolling(window=5).mean()
            df['Returns_20'] = df['Returns'].rolling(window=20).mean()
            df['Volatility'] = df['Returns'].rolling(window=20).std()
            
            # Тренд и импульс (важно для предсказания роста)
            df['Trend'] = (df['Close'] - df['Close'].shift(5)) / df['Close'].shift(5)  # 5-дневный тренд
            df['Momentum'] = df['Close'] / df['Close'].shift(10) - 1  # 10-дневный импульс
            
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_ratio'] = df['Volume'] / df['Volume_MA']
            df['HL_spread'] = (df['High'] - df['Low']) / df['Close']
            
            # RSI (Relative Strength Index)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            self.last_update = datetime.now()
            
            # Получаем последние значения для признаков
            last_row = df.iloc[-1]
            
            # Формируем сообщение для других агентов
            message = {
                "type": "market_update",
                "ticker": self.ticker,
                "timestamp": self.last_update.isoformat(),
                "current_price": float(current_price),
                "data": {
                    "prices": df[['Open', 'High', 'Low', 'Close', 'Volume']].to_dict('records'),
                    "indicators": {
                        "MA5": float(last_row['MA5']) if not pd.isna(last_row['MA5']) else None,
                        "MA20": float(last_row['MA20']) if not pd.isna(last_row['MA20']) else None,
                        "MA50": float(last_row['MA50']) if not pd.isna(last_row['MA50']) else None,
                        "volatility": float(last_row['Volatility']) if not pd.isna(last_row['Volatility']) else None,
                        "returns": float(last_row['Returns']) if not pd.isna(last_row['Returns']) else None,
                        "returns_5": float(last_row['Returns_5']) if not pd.isna(last_row['Returns_5']) else None,
                        "returns_20": float(last_row['Returns_20']) if not pd.isna(last_row['Returns_20']) else None,
                        "trend": float(last_row['Trend']) if not pd.isna(last_row['Trend']) else None,
                        "momentum": float(last_row['Momentum']) if not pd.isna(last_row['Momentum']) else None,
                        "volume_ratio": float(last_row['Volume_ratio']) if not pd.isna(last_row['Volume_ratio']) else None,
                        "hl_spread": float(last_row['HL_spread']) if not pd.isna(last_row['HL_spread']) else None,
                        "RSI": float(last_row['RSI']) if not pd.isna(last_row['RSI']) else None,
                    },
                    "returns": df['Returns'].tolist()[-20:]  # Последние 20 значений для lag features
                },
                "info": {
                    "company_name": info.get('longName', 'N/A'),
                    "sector": info.get('sector', 'N/A'),
                    "market_cap": info.get('marketCap', 0)
                }
            }
            
            # Сохраняем в историю
            self.data_history.append({
                "timestamp": self.last_update,
                "price": current_price,
                "volume": df['Volume'].iloc[-1]
            })
            
            return message
            
        except Exception as e:
            return {
                "type": "error",
                "message": f"Error fetching data: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_latest_price(self) -> Optional[float]:
        """Получает последнюю цену"""
        try:
            stock = yf.Ticker(self.ticker)
            data = stock.history(period="1d", interval="1m")
            if not data.empty:
                return float(data['Close'].iloc[-1])
            return None
        except:
            return None
    
    def get_dataframe(self, period: str = "1mo", interval: str = "1d", force_refresh: bool = False) -> pd.DataFrame:
        """
        Получает данные в виде DataFrame для визуализации
        
        Args:
            period: Период данных
            interval: Интервал
            force_refresh: Принудительно обновить данные (игнорировать кэш)
        
        Returns:
            DataFrame с данными
        """
        try:
            stock = yf.Ticker(self.ticker)
            # Всегда получаем свежие данные
            # Используем более длинный период для получения последних данных
            if force_refresh or period == "1d" or period == "5d":
                # Для коротких периодов используем более свежие данные
                df = stock.history(period=period, interval=interval, prepost=True)
            else:
                df = stock.history(period=period, interval=interval)
            
            if not df.empty:
                df['MA5'] = df['Close'].rolling(window=5).mean()
                df['MA20'] = df['Close'].rolling(window=20).mean()
                df['MA50'] = df['Close'].rolling(window=50).mean()
                df['Returns'] = df['Close'].pct_change()
                df['Returns_5'] = df['Returns'].rolling(window=5).mean()
                df['Returns_20'] = df['Returns'].rolling(window=20).mean()
                df['Volatility'] = df['Returns'].rolling(window=20).std()
                df['Trend'] = (df['Close'] - df['Close'].shift(5)) / df['Close'].shift(5)
                df['Momentum'] = df['Close'] / df['Close'].shift(10) - 1
                df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
                df['Volume_ratio'] = df['Volume'] / df['Volume_MA']
                df['HL_spread'] = (df['High'] - df['Low']) / df['Close']
                # RSI
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))
            
            return df
        except Exception as e:
            return pd.DataFrame()

