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
    
    def __init__(self, user_id: int, initial_balance: float = 10000.0, 
                 data_dir: str = "data", use_db: bool = True):
        """
        Инициализация агента
        
        Args:
            user_id: ID пользователя
            initial_balance: Начальный баланс портфеля
            data_dir: Директория для сохранения данных (если не используется БД)
            use_db: Использовать ли БД вместо CSV файлов
        """
        # КРИТИЧЕСКИ ВАЖНО: Устанавливаем ticker ПЕРВЫМ, до любых других операций
        # Это защита от ошибок в старых версиях кода
        self.ticker = "AAPL"  # Значение по умолчанию
        
        self.user_id = user_id
        self.initial_balance = initial_balance
        self.use_db = use_db
        
        if use_db:
            # Используем БД
            from database.db_manager import DBManager
            self.db_manager = DBManager()
            self._load_from_db()
        else:
            # Используем CSV (старый способ для обратной совместимости)
            self.balance = initial_balance
            self.portfolio = {}  # {ticker: {"shares": int, "avg_price": float}}
            self.trade_history = []
            self.data_dir = data_dir
            self.history_file = os.path.join(data_dir, f"history_{user_id}.csv")
            
            # Создаем директорию если не существует
            os.makedirs(data_dir, exist_ok=True)
            
            # Загружаем историю если существует
            self.load_history()
    
    def _load_from_db(self):
        """Загружает портфель из БД"""
        # КРИТИЧЕСКАЯ ЗАЩИТА: Гарантируем, что ticker всегда установлен
        # Это должно быть ПЕРВОЙ строкой в методе
        if not hasattr(self, 'ticker') or self.ticker is None or self.ticker == "":
            self.ticker = "AAPL"
        
        portfolio_data = self.db_manager.get_portfolio(self.user_id)
        
        if portfolio_data:
            self.balance = portfolio_data['balance']
            # Сохраняем начальный баланс только при первом создании
            # Если портфель уже существует, не меняем initial_balance
            if not hasattr(self, 'initial_balance_set'):
                # Пытаемся вычислить начальный баланс из истории
                trade_history = self.db_manager.get_trade_history(self.user_id)
                if not trade_history.empty:
                    # Если есть история, вычисляем начальный баланс
                    first_trade = trade_history.iloc[-1]  # Первая сделка (последняя в отсортированном списке)
                    if first_trade['action'] == 'BUY':
                        self.initial_balance = first_trade['balance_after'] + first_trade['total']
                    else:
                        self.initial_balance = first_trade['balance_after'] - first_trade['total']
                else:
                    # Если истории нет, используем текущий баланс
                    self.initial_balance = self.balance
                self.initial_balance_set = True
        else:
            # Создаем портфель если не существует
            self.db_manager.create_portfolio(self.user_id, self.initial_balance)
            self.balance = self.initial_balance
            self.initial_balance_set = True
        
        # Загружаем холдинги
        holdings = self.db_manager.get_holdings(self.user_id)
        self.portfolio = {}
        for holding in holdings:
            self.portfolio[holding['ticker']] = {
                "shares": holding['shares'],
                "avg_price": holding['avg_price'],
                "total_cost": holding['total_cost']
            }
    
    def load_history(self):
        """Загружает историю торгов из файла (только если use_db=False)"""
        if self.use_db:
            return  # Используем БД
        
        if os.path.exists(self.history_file):
            try:
                df = pd.read_csv(self.history_file)
                self.trade_history = df.to_dict('records')
                # Восстанавливаем баланс и портфель
                self._reconstruct_portfolio()
            except Exception as e:
                print(f"Error loading history: {e}")
    
    def _reconstruct_portfolio(self):
        """Восстанавливает состояние портфеля из истории (только если use_db=False)"""
        if self.use_db:
            return  # Используем БД
        
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
                    confidence = decision_data.get("confidence", 0)
                    
                    if self.use_db:
                        # Сохраняем в БД
                        self.db_manager.add_trade(
                            self.user_id, ticker, "BUY", shares, current_price,
                            cost, self.balance, confidence
                        )
                        # Обновляем холдинг в БД
                        self.db_manager.update_holding(
                            self.user_id, ticker, new_shares, 
                            self.portfolio[ticker]["avg_price"], new_cost
                        )
                        # Обновляем баланс в БД
                        self.db_manager.update_portfolio_balance(self.user_id, self.balance)
                    else:
                        # Сохраняем в CSV
                        trade_record = {
                            "timestamp": datetime.now().isoformat(),
                            "ticker": ticker,
                            "action": "BUY",
                            "shares": shares,
                            "price": current_price,
                            "total": cost,
                            "balance_after": self.balance,
                            "confidence": confidence
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
                    confidence = decision_data.get("confidence", 0)
                    
                    if self.use_db:
                        # Сохраняем в БД
                        self.db_manager.add_trade(
                            self.user_id, ticker, "SELL", shares_to_sell, current_price,
                            revenue, self.balance, confidence
                        )
                        # Обновляем или удаляем холдинг в БД
                        remaining_shares = self.portfolio[ticker]["shares"]
                        if remaining_shares > 0:
                            remaining_cost = self.portfolio[ticker]["total_cost"] * (remaining_shares / (remaining_shares + shares_to_sell))
                            self.db_manager.update_holding(
                                self.user_id, ticker, remaining_shares,
                                self.portfolio[ticker]["avg_price"], remaining_cost
                            )
                        else:
                            self.db_manager.delete_holding(self.user_id, ticker)
                        # Обновляем баланс в БД
                        self.db_manager.update_portfolio_balance(self.user_id, self.balance)
                    else:
                        # Сохраняем в CSV
                        trade_record = {
                            "timestamp": datetime.now().isoformat(),
                            "ticker": ticker,
                            "action": "SELL",
                            "shares": shares_to_sell,
                            "price": current_price,
                            "total": revenue,
                            "balance_after": self.balance,
                            "confidence": confidence
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
        """Сохраняет историю торгов в CSV файл (только если use_db=False)"""
        if self.use_db:
            return  # Используем БД
        
        if self.trade_history:
            df = pd.DataFrame(self.trade_history)
            df.to_csv(self.history_file, index=False)
    
    def get_trade_history(self) -> pd.DataFrame:
        """Возвращает историю торгов в виде DataFrame"""
        if self.use_db:
            return self.db_manager.get_trade_history(self.user_id)
        else:
            if not self.trade_history:
                return pd.DataFrame()
            return pd.DataFrame(self.trade_history)
    
    def reset_portfolio(self):
        """Сбрасывает портфель к начальному состоянию"""
        if self.use_db:
            # Сбрасываем в БД
            self.db_manager.update_portfolio_balance(self.user_id, self.initial_balance)
            # Удаляем все холдинги
            holdings = self.db_manager.get_holdings(self.user_id)
            for holding in holdings:
                self.db_manager.delete_holding(self.user_id, holding['ticker'])
            # Перезагружаем из БД
            self._load_from_db()
        else:
            self.balance = self.initial_balance
            self.portfolio = {}
            self.trade_history = []
            if os.path.exists(self.history_file):
                os.remove(self.history_file)

