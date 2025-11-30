"""
Agent Coordinator
Координирует коммуникацию между агентами
"""
from typing import Dict, List, Optional
from datetime import datetime
from .market_monitor import MarketMonitoringAgent
from .decision_agent import DecisionMakingAgent
from .execution_agent import ExecutionAgent


class AgentCoordinator:
    """Координатор для управления взаимодействием агентов"""
    
    def __init__(self, ticker: str = "AAPL", initial_balance: float = 10000.0, 
                 user_id: Optional[int] = None, use_db: bool = True):
        """
        Инициализация координатора
        
        Args:
            ticker: Тикер акции
            initial_balance: Начальный баланс портфеля
            user_id: ID пользователя (обязательно если use_db=True)
            use_db: Использовать ли БД вместо CSV
        """
        self.ticker = ticker
        self.user_id = user_id
        self.market_agent = MarketMonitoringAgent(ticker)
        self.decision_agent = DecisionMakingAgent()
        
        # Если user_id не указан, используем старый способ (CSV)
        if user_id is None:
            use_db = False
        
        self.execution_agent = ExecutionAgent(
            user_id=user_id if user_id else 0,
            initial_balance=initial_balance,
            use_db=use_db
        )
        self.communication_log = []
    
    def log_communication(self, from_agent: str, to_agent: str, message: Dict):
        """Логирует коммуникацию между агентами"""
        log_entry = {
            "timestamp": datetime.now(),
            "from": from_agent,
            "to": to_agent,
            "message_type": message.get("type", "unknown"),
            "message": message
        }
        self.communication_log.append(log_entry)
    
    def run_cycle(self) -> Dict:
        """
        Выполняет один цикл работы системы:
        1. Market Agent получает данные
        2. Decision Agent принимает решение
        3. Execution Agent выполняет сделку
        
        Returns:
            Результат выполнения цикла
        """
        try:
            # Шаг 1: Market Monitoring Agent получает данные
            market_data = self.market_agent.get_market_data(period="1mo", interval="1d")
            self.log_communication("MarketAgent", "DecisionAgent", market_data)
            
            if market_data.get("type") == "error":
                return {
                    "status": "error",
                    "step": "market_data",
                    "message": market_data.get("message"),
                    "timestamp": datetime.now().isoformat()
                }
            
            # Шаг 2: Decision-Making Agent обрабатывает данные и принимает решение
            decision = self.decision_agent.process_market_update(market_data)
            self.log_communication("DecisionAgent", "ExecutionAgent", decision)
            
            if decision.get("type") == "error":
                return {
                    "status": "error",
                    "step": "decision",
                    "message": decision.get("message"),
                    "timestamp": datetime.now().isoformat()
                }
            
            # Шаг 3: Execution Agent выполняет сделку
            execution_result = self.execution_agent.execute_trade(decision)
            self.log_communication("ExecutionAgent", "UI", execution_result)
            
            # Формируем итоговый результат
            current_price = market_data.get("current_price", 0)
            portfolio_summary = self.execution_agent.get_portfolio_summary(current_price)
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "market_data": {
                    "ticker": market_data.get("ticker"),
                    "current_price": market_data.get("current_price"),
                    "timestamp": market_data.get("timestamp")
                },
                "decision": {
                    "action": decision.get("decision"),
                    "current_price": decision.get("current_price"),
                    "predicted_price": decision.get("predicted_price"),
                    "confidence": decision.get("confidence")
                },
                "execution": {
                    "status": execution_result.get("status"),
                    "action": execution_result.get("action"),
                    "message": execution_result.get("message")
                },
                "portfolio": portfolio_summary
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error in cycle execution: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_market_dataframe(self, period: str = "1mo", interval: str = "1d", force_refresh: bool = False):
        """Получает данные рынка в виде DataFrame"""
        return self.market_agent.get_dataframe(period, interval, force_refresh=force_refresh)
    
    def get_communication_log(self) -> List[Dict]:
        """Возвращает лог коммуникации"""
        return self.communication_log
    
    def get_decision_history(self):
        """Возвращает историю решений"""
        return self.decision_agent.get_decision_history()
    
    def get_trade_history(self):
        """Возвращает историю торгов"""
        return self.execution_agent.get_trade_history()
    
    def reset_system(self):
        """Сбрасывает систему к начальному состоянию"""
        self.execution_agent.reset_portfolio()
        self.communication_log = []
        self.decision_agent.decision_history = []

