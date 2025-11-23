"""
Execution Agent
Получает решение и "выполняет" сделку, записывает результат
"""
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import os


class ExecutionAgent:
    """Агент для выполнения торговых операций"""
    
    def __init__(self, initial_balance: float = 10000.0, data_dir: str = "data"):
        """
        Инициализация агента
        
        Args:
            initial_balance: Начальный баланс портфеля
            data_dir: Директория для сохранения данных
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.portfolio = {}  # {ticker: {"shares": int, "avg_price": float}}
        self.trade_history = []
        self.data_dir = data_dir
        self.history_file = os.path.join(data_dir, "history.csv")
        
        # Создаем директорию если не существует
        os.makedirs(data_dir, exist_ok=True)
        
        # Загружаем историю если существует
        self.load_history()
    
    def load_history(self):
        """Загружает историю торгов из файла"""
        if os.path.exists(self.history_file):
            try:
                df = pd.read_csv(self.history_file)
                self.trade_history = df.to_dict('records')
                # Восстанавливаем баланс и портфель
                self._reconstruct_portfolio()
            except Exception as e:
                print(f"Error loading history: {e}")
    
    def _reconstruct_portfolio(self):
        """Восстанавливает состояние портфеля из истории"""
        self.balance = self.initial_balance
        self.portfolio = {}
        
        for trade in self.trade_history:
            ticker = trade.get("ticker")
            action = trade.get("action")
            shares = trade.get("shares", 0)
            price = trade.get("price", 0)
            
            if action == "BUY":
                cost = shares * price
                if self.balance >= cost:
                    self.balance -= cost
                    if ticker not in self.portfolio:
                        self.portfolio[ticker] = {"shares": 0, "avg_price": 0, "total_cost": 0}
                    
                    old_shares = self.portfolio[ticker]["shares"]
                    old_cost = self.portfolio[ticker]["total_cost"]
                    new_shares = old_shares + shares
                    new_cost = old_cost + cost
                    
                    self.portfolio[ticker]["shares"] = new_shares
                    self.portfolio[ticker]["total_cost"] = new_cost
                    self.portfolio[ticker]["avg_price"] = new_cost / new_shares if new_shares > 0 else 0
                    
            elif action == "SELL":
                if ticker in self.portfolio and self.portfolio[ticker]["shares"] >= shares:
                    revenue = shares * price
                    self.balance += revenue
                    self.portfolio[ticker]["shares"] -= shares
                    if self.portfolio[ticker]["shares"] == 0:
                        del self.portfolio[ticker]
    
    def execute_trade(self, decision_data: Dict) -> Dict:
        """
        Выполняет торговую операцию
        
        Args:
            decision_data: Данные от Decision-Making Agent
        
        Returns:
            Результат выполнения операции
        """
        try:
            if decision_data.get("type") != "trading_decision":
                return {
                    "type": "error",
                    "message": "Invalid decision data",
                    "timestamp": datetime.now().isoformat()
                }
            
            decision = decision_data.get("decision")
            ticker = decision_data.get("ticker")
            current_price = decision_data.get("current_price", 0)
            
            if decision == "HOLD":
                return {
                    "type": "execution_result",
                    "status": "hold",
                    "ticker": ticker,
                    "message": "No action taken - HOLD decision",
                    "timestamp": datetime.now().isoformat(),
                    "portfolio_value": self.get_portfolio_value(current_price),
                    "balance": self.balance
                }
            
            # Определяем количество акций для покупки/продажи
            # Используем 10% баланса для каждой сделки
            trade_percentage = 0.1
            
            if decision == "BUY":
                available_cash = self.balance * trade_percentage
                shares = int(available_cash / current_price) if current_price > 0 else 0
                
                if shares > 0 and self.balance >= shares * current_price:
                    cost = shares * current_price
                    self.balance -= cost
                    
                    if ticker not in self.portfolio:
                        self.portfolio[ticker] = {"shares": 0, "avg_price": 0, "total_cost": 0}
                    
                    old_shares = self.portfolio[ticker]["shares"]
                    old_cost = self.portfolio[ticker]["total_cost"]
                    new_shares = old_shares + shares
                    new_cost = old_cost + cost
                    
                    self.portfolio[ticker]["shares"] = new_shares
                    self.portfolio[ticker]["total_cost"] = new_cost
                    self.portfolio[ticker]["avg_price"] = new_cost / new_shares
                    
                    # Записываем в историю
                    trade_record = {
                        "timestamp": datetime.now().isoformat(),
                        "ticker": ticker,
                        "action": "BUY",
                        "shares": shares,
                        "price": current_price,
                        "total": cost,
                        "balance_after": self.balance,
                        "confidence": decision_data.get("confidence", 0)
                    }
                    self.trade_history.append(trade_record)
                    self.save_history()
                    
                    return {
                        "type": "execution_result",
                        "status": "success",
                        "ticker": ticker,
                        "action": "BUY",
                        "shares": shares,
                        "price": current_price,
                        "total": cost,
                        "message": f"Bought {shares} shares of {ticker} at ${current_price:.2f}",
                        "timestamp": datetime.now().isoformat(),
                        "portfolio_value": self.get_portfolio_value(current_price),
                        "balance": self.balance
                    }
                else:
                    return {
                        "type": "execution_result",
                        "status": "insufficient_funds",
                        "ticker": ticker,
                        "message": "Insufficient funds for BUY order",
                        "timestamp": datetime.now().isoformat(),
                        "balance": self.balance
                    }
            
            elif decision == "SELL":
                if ticker in self.portfolio and self.portfolio[ticker]["shares"] > 0:
                    available_shares = self.portfolio[ticker]["shares"]
                    # Продаем 50% имеющихся акций
                    shares_to_sell = max(1, int(available_shares * 0.5))
                    shares_to_sell = min(shares_to_sell, available_shares)
                    
                    revenue = shares_to_sell * current_price
                    self.balance += revenue
                    
                    self.portfolio[ticker]["shares"] -= shares_to_sell
                    if self.portfolio[ticker]["shares"] == 0:
                        del self.portfolio[ticker]
                    
                    # Записываем в историю
                    trade_record = {
                        "timestamp": datetime.now().isoformat(),
                        "ticker": ticker,
                        "action": "SELL",
                        "shares": shares_to_sell,
                        "price": current_price,
                        "total": revenue,
                        "balance_after": self.balance,
                        "confidence": decision_data.get("confidence", 0)
                    }
                    self.trade_history.append(trade_record)
                    self.save_history()
                    
                    return {
                        "type": "execution_result",
                        "status": "success",
                        "ticker": ticker,
                        "action": "SELL",
                        "shares": shares_to_sell,
                        "price": current_price,
                        "total": revenue,
                        "message": f"Sold {shares_to_sell} shares of {ticker} at ${current_price:.2f}",
                        "timestamp": datetime.now().isoformat(),
                        "portfolio_value": self.get_portfolio_value(current_price),
                        "balance": self.balance
                    }
                else:
                    return {
                        "type": "execution_result",
                        "status": "no_shares",
                        "ticker": ticker,
                        "message": f"No shares of {ticker} to sell",
                        "timestamp": datetime.now().isoformat(),
                        "balance": self.balance
                    }
            
            return {
                "type": "execution_result",
                "status": "unknown_decision",
                "message": f"Unknown decision: {decision}",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "type": "error",
                "message": f"Error executing trade: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_portfolio_value(self, current_price: float) -> float:
        """
        Вычисляет текущую стоимость портфеля
        
        Args:
            current_price: Текущая цена акции
        
        Returns:
            Общая стоимость портфеля
        """
        portfolio_value = self.balance
        for ticker, holdings in self.portfolio.items():
            # Используем текущую цену для оценки
            portfolio_value += holdings["shares"] * current_price
        return portfolio_value
    
    def get_portfolio_summary(self, current_price: float) -> Dict:
        """
        Возвращает сводку портфеля
        
        Args:
            current_price: Текущая цена акции
        
        Returns:
            Словарь с информацией о портфеле
        """
        portfolio_value = self.get_portfolio_value(current_price)
        total_invested = sum(holdings["total_cost"] for holdings in self.portfolio.values())
        
        return {
            "balance": self.balance,
            "portfolio_value": portfolio_value,
            "total_invested": total_invested,
            "pnl": portfolio_value - self.initial_balance,
            "pnl_pct": ((portfolio_value - self.initial_balance) / self.initial_balance * 100) if self.initial_balance > 0 else 0,
            "holdings": {ticker: {
                "shares": holdings["shares"],
                "avg_price": holdings["avg_price"],
                "current_value": holdings["shares"] * current_price,
                "unrealized_pnl": (current_price - holdings["avg_price"]) * holdings["shares"]
            } for ticker, holdings in self.portfolio.items()}
        }
    
    def save_history(self):
        """Сохраняет историю торгов в CSV файл"""
        if self.trade_history:
            df = pd.DataFrame(self.trade_history)
            df.to_csv(self.history_file, index=False)
    
    def get_trade_history(self) -> pd.DataFrame:
        """Возвращает историю торгов в виде DataFrame"""
        if not self.trade_history:
            return pd.DataFrame()
        return pd.DataFrame(self.trade_history)
    
    def reset_portfolio(self):
        """Сбрасывает портфель к начальному состоянию"""
        self.balance = self.initial_balance
        self.portfolio = {}
        self.trade_history = []
        if os.path.exists(self.history_file):
            os.remove(self.history_file)

