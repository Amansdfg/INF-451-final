#!/usr/bin/env python3
"""
Простой тест для проверки работоспособности системы
"""
import sys
import os

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Проверяет, что все модули импортируются"""
    print("=" * 50)
    print("Тест 1: Проверка импортов")
    print("=" * 50)
    
    try:
        print("Импорт agents...")
        from agents.market_monitor import MarketMonitoringAgent
        from agents.decision_agent import DecisionMakingAgent
        from agents.execution_agent import ExecutionAgent
        from agents.coordinator import AgentCoordinator
        print("✅ Все агенты импортированы успешно")
        
        print("\nИмпорт моделей...")
        from models.train_model import train_model
        print("✅ Модели импортированы успешно")
        
        print("\nИмпорт библиотек...")
        import yfinance as yf
        import pandas as pd
        import numpy as np
        import streamlit
        print("✅ Все библиотеки импортированы успешно")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_market_agent():
    """Тестирует Market Monitoring Agent"""
    print("\n" + "=" * 50)
    print("Тест 2: Market Monitoring Agent")
    print("=" * 50)
    
    try:
        from agents.market_monitor import MarketMonitoringAgent
        
        print("Создание агента для AAPL...")
        agent = MarketMonitoringAgent("AAPL")
        
        print("Получение данных рынка...")
        data = agent.get_market_data(period="5d", interval="1d")
        
        if data.get("type") == "market_update":
            print(f"✅ Данные получены успешно!")
            print(f"   Тикер: {data.get('ticker')}")
            print(f"   Текущая цена: ${data.get('current_price', 0):.2f}")
            print(f"   Время обновления: {data.get('timestamp')}")
            return True
        else:
            print(f"❌ Ошибка получения данных: {data.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_decision_agent():
    """Тестирует Decision-Making Agent"""
    print("\n" + "=" * 50)
    print("Тест 3: Decision-Making Agent")
    print("=" * 50)
    
    try:
        from agents.market_monitor import MarketMonitoringAgent
        from agents.decision_agent import DecisionMakingAgent
        
        print("Получение данных рынка...")
        market_agent = MarketMonitoringAgent("AAPL")
        market_data = market_agent.get_market_data(period="5d", interval="1d")
        
        if market_data.get("type") != "market_update":
            print("❌ Не удалось получить данные рынка")
            return False
        
        print("Создание Decision Agent...")
        decision_agent = DecisionMakingAgent()
        
        print("Обработка данных и принятие решения...")
        decision = decision_agent.process_market_update(market_data)
        
        if decision.get("type") == "trading_decision":
            print(f"✅ Решение принято успешно!")
            print(f"   Решение: {decision.get('decision')}")
            print(f"   Текущая цена: ${decision.get('current_price', 0):.2f}")
            print(f"   Предсказанная цена: ${decision.get('predicted_price', 0):.2f}")
            return True
        else:
            print(f"❌ Ошибка принятия решения: {decision.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_execution_agent():
    """Тестирует Execution Agent"""
    print("\n" + "=" * 50)
    print("Тест 4: Execution Agent")
    print("=" * 50)
    
    try:
        from agents.execution_agent import ExecutionAgent
        
        print("Создание Execution Agent с балансом $10000...")
        exec_agent = ExecutionAgent(initial_balance=10000.0)
        
        print(f"Начальный баланс: ${exec_agent.balance:.2f}")
        
        # Создаем тестовое решение
        test_decision = {
            "type": "trading_decision",
            "ticker": "AAPL",
            "decision": "BUY",
            "current_price": 150.0,
            "predicted_price": 155.0,
            "confidence": 0.03
        }
        
        print("Выполнение тестовой сделки BUY...")
        result = exec_agent.execute_trade(test_decision)
        
        if result.get("type") == "execution_result":
            print(f"✅ Сделка выполнена!")
            print(f"   Статус: {result.get('status')}")
            print(f"   Действие: {result.get('action', 'N/A')}")
            print(f"   Баланс после: ${result.get('balance', 0):.2f}")
            return True
        else:
            print(f"❌ Ошибка выполнения сделки: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_coordinator():
    """Тестирует полный цикл координатора"""
    print("\n" + "=" * 50)
    print("Тест 5: Agent Coordinator (полный цикл)")
    print("=" * 50)
    
    try:
        from agents.coordinator import AgentCoordinator
        
        print("Создание координатора...")
        coordinator = AgentCoordinator(ticker="AAPL", initial_balance=10000.0)
        
        print("Запуск полного цикла агентов...")
        result = coordinator.run_cycle()
        
        if result.get("status") == "success":
            print("✅ Цикл выполнен успешно!")
            print(f"   Тикер: {result['market_data']['ticker']}")
            print(f"   Цена: ${result['market_data']['current_price']:.2f}")
            print(f"   Решение: {result['decision']['action']}")
            print(f"   P&L: ${result['portfolio']['pnl']:.2f}")
            return True
        else:
            print(f"❌ Ошибка в цикле: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Запускает все тесты"""
    print("\n" + "🚀" * 25)
    print("ТЕСТИРОВАНИЕ MULTI-AGENT TRADING SYSTEM")
    print("🚀" * 25 + "\n")
    
    results = []
    
    # Запускаем тесты
    results.append(("Импорты", test_imports()))
    results.append(("Market Agent", test_market_agent()))
    results.append(("Decision Agent", test_decision_agent()))
    results.append(("Execution Agent", test_execution_agent()))
    results.append(("Coordinator", test_coordinator()))
    
    # Итоги
    print("\n" + "=" * 50)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nПройдено тестов: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к работе!")
        print("\nДля запуска веб-интерфейса выполните:")
        print("  streamlit run ui/app.py")
        print("\nИли:")
        print("  python run.py")
    else:
        print("\n⚠️  Некоторые тесты не прошли. Проверьте ошибки выше.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

