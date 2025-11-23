"""
Decision-Making Agent
AI-модель предсказывает движение цены и принимает решение BUY/SELL/HOLD
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
import joblib
import os
from datetime import datetime


class DecisionMakingAgent:
    """Агент для принятия торговых решений на основе ML-модели"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Инициализация агента
        
        Args:
            model_path: Путь к обученной модели (если None, создаст новую)
        """
        self.model = None
        self.model_path = model_path or "models/model.pkl"
        self.decision_history = []
        self.load_model()
    
    def load_model(self):
        """Загружает обученную модель"""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print(f"Model loaded from {self.model_path}")
            except Exception as e:
                print(f"Error loading model: {e}")
                self.model = None
        else:
            print(f"Model not found at {self.model_path}. Please train the model first.")
            self.model = None
    
    def extract_features(self, market_data: Dict) -> Optional[np.ndarray]:
        """
        Извлекает признаки из данных рынка для ML-модели
        
        Args:
            market_data: Данные от Market Monitoring Agent
        
        Returns:
            Массив признаков или None
        """
        try:
            if market_data.get("type") != "market_update":
                return None
            
            data = market_data.get("data", {})
            indicators = data.get("indicators", {})
            returns_list = data.get("returns", [])
            current_price = market_data.get("current_price", 0)
            
            # Извлекаем признаки (в том же порядке, что и в train_model.py)
            features = []
            
            # 1. MA5
            features.append(indicators.get("MA5", 0) or 0)
            # 2. MA20
            features.append(indicators.get("MA20", 0) or 0)
            # 3. Volatility
            features.append(indicators.get("volatility", 0) or 0)
            # 4. Returns (текущее значение)
            features.append(indicators.get("returns", 0) or 0)
            # 5. Returns_5
            features.append(indicators.get("returns_5", 0) or 0)
            # 6. Returns_20
            features.append(indicators.get("returns_20", 0) or 0)
            # 7. MA5_MA20_ratio
            ma5 = indicators.get("MA5", 0) or 0
            ma20 = indicators.get("MA20", 0) or 0
            features.append(ma5 / ma20 if ma20 != 0 else 1.0)
            # 8. Price_MA20_ratio
            features.append(current_price / ma20 if ma20 != 0 else 1.0)
            # 9. Volume_ratio
            features.append(indicators.get("volume_ratio", 0) or 0)
            # 10. HL_spread
            features.append(indicators.get("hl_spread", 0) or 0)
            # 11. Close (текущая цена)
            features.append(current_price)
            
            # 12-16. Return_lag_1 through Return_lag_5
            if returns_list:
                # Берем последние 5 значений (lag features)
                lag_returns = returns_list[-5:] if len(returns_list) >= 5 else returns_list
                # Дополняем нулями если недостаточно данных
                while len(lag_returns) < 5:
                    lag_returns.insert(0, 0.0)
                features.extend(lag_returns[:5])
            else:
                features.extend([0.0] * 5)
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            return None
    
    def predict(self, features: np.ndarray) -> float:
        """
        Предсказывает будущую цену
        
        Args:
            features: Признаки для модели
        
        Returns:
            Предсказанная цена
        """
        if self.model is None:
            # Если модель не загружена, возвращаем случайное предсказание
            # (для демонстрации, когда модель еще не обучена)
            return features[0, -2] * (1 + np.random.uniform(-0.02, 0.02))
        
        try:
            prediction = self.model.predict(features)[0]
            return float(prediction)
        except Exception as e:
            print(f"Error in prediction: {e}")
            return features[0, -2]  # Возвращаем текущую цену как fallback
    
    def decide(self, current_price: float, predicted_price: float, 
               threshold: float = 0.02) -> str:
        """
        Принимает решение на основе предсказания
        
        Args:
            current_price: Текущая цена
            predicted_price: Предсказанная цена
            threshold: Порог для принятия решения (2% по умолчанию)
        
        Returns:
            "BUY", "SELL" или "HOLD"
        """
        if current_price == 0:
            return "HOLD"
        
        price_change_pct = (predicted_price - current_price) / current_price
        
        if price_change_pct > threshold:
            return "BUY"
        elif price_change_pct < -threshold:
            return "SELL"
        else:
            return "HOLD"
    
    def process_market_update(self, market_data: Dict) -> Dict:
        """
        Обрабатывает обновление рынка и принимает решение
        
        Args:
            market_data: Данные от Market Monitoring Agent
        
        Returns:
            Сообщение для Execution Agent
        """
        try:
            if market_data.get("type") != "market_update":
                return {
                    "type": "error",
                    "message": "Invalid market data",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Извлекаем признаки
            features = self.extract_features(market_data)
            if features is None:
                return {
                    "type": "error",
                    "message": "Failed to extract features",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Делаем предсказание
            current_price = market_data.get("current_price", 0)
            predicted_price = self.predict(features)
            
            # Принимаем решение
            decision = self.decide(current_price, predicted_price)
            
            # Сохраняем в историю
            decision_record = {
                "timestamp": datetime.now(),
                "ticker": market_data.get("ticker"),
                "current_price": current_price,
                "predicted_price": predicted_price,
                "decision": decision,
                "confidence": abs((predicted_price - current_price) / current_price) if current_price > 0 else 0
            }
            self.decision_history.append(decision_record)
            
            # Формируем сообщение для Execution Agent
            message = {
                "type": "trading_decision",
                "ticker": market_data.get("ticker"),
                "timestamp": datetime.now().isoformat(),
                "decision": decision,
                "current_price": current_price,
                "predicted_price": predicted_price,
                "confidence": decision_record["confidence"],
                "features": features.tolist()[0] if features is not None else []
            }
            
            return message
            
        except Exception as e:
            return {
                "type": "error",
                "message": f"Error processing decision: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_decision_history(self) -> pd.DataFrame:
        """Возвращает историю решений в виде DataFrame"""
        if not self.decision_history:
            return pd.DataFrame()
        return pd.DataFrame(self.decision_history)

