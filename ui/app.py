"""
Streamlit UI для Multi-Agent Trading System
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
import os

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.coordinator import AgentCoordinator
from models.train_model import train_model, prepare_training_data
import numpy as np


# Настройка страницы
st.set_page_config(
    page_title="Multi-Agent Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация session state
if 'coordinator' not in st.session_state:
    st.session_state.coordinator = None
if 'cycle_results' not in st.session_state:
    st.session_state.cycle_results = []
if 'model_metrics' not in st.session_state:
    st.session_state.model_metrics = None


def init_coordinator(ticker: str, initial_balance: float):
    """Инициализирует координатор агентов"""
    if st.session_state.coordinator is None or st.session_state.coordinator.ticker != ticker:
        st.session_state.coordinator = AgentCoordinator(ticker=ticker, initial_balance=initial_balance)
        st.session_state.cycle_results = []


# Sidebar
with st.sidebar:
    st.title("⚙️ Настройки")
    
    ticker = st.text_input("Тикер акции", value="AAPL", help="Например: AAPL, TSLA, MSFT")
    initial_balance = st.number_input("Начальный баланс ($)", min_value=1000, value=10000, step=1000)
    
    if st.button("🔄 Инициализировать систему"):
        init_coordinator(ticker, initial_balance)
        st.success(f"Система инициализирована для {ticker}")
    
    st.divider()
    
    st.subheader("📊 Навигация")
    page = st.radio(
        "Выберите страницу",
        ["Overview", "Real-time Simulation", "ML Model", "Trade History"]
    )


# Главная страница - Overview
if page == "Overview":
    st.title("📈 Multi-Agent Trading System")
    st.markdown("### Обзор системы и портфеля")
    
    if st.session_state.coordinator is None:
        st.warning("⚠️ Пожалуйста, инициализируйте систему в боковой панели")
    else:
        coordinator = st.session_state.coordinator
        
        # Получаем данные рынка
        df = coordinator.get_market_dataframe(period="3mo", interval="1d")
        
        if not df.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            current_price = df['Close'].iloc[-1]
            price_change = df['Close'].iloc[-1] - df['Close'].iloc[-2]
            price_change_pct = (price_change / df['Close'].iloc[-2]) * 100
            
            with col1:
                st.metric("Текущая цена", f"${current_price:.2f}", 
                         f"{price_change_pct:+.2f}%")
            
            portfolio_summary = coordinator.execution_agent.get_portfolio_summary(current_price)
            
            with col2:
                st.metric("Баланс", f"${portfolio_summary['balance']:.2f}")
            
            with col3:
                st.metric("Стоимость портфеля", f"${portfolio_summary['portfolio_value']:.2f}")
            
            with col4:
                pnl_color = "normal" if portfolio_summary['pnl'] >= 0 else "inverse"
                st.metric("P&L", f"${portfolio_summary['pnl']:.2f}", 
                         f"{portfolio_summary['pnl_pct']:+.2f}%")
            
            st.divider()
            
            # График цен
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 График цен")
                fig_price = go.Figure()
                
                fig_price.add_trace(go.Scatter(
                    x=df.index,
                    y=df['Close'],
                    mode='lines',
                    name='Цена закрытия',
                    line=dict(color='#1f77b4', width=2)
                ))
                
                if 'MA5' in df.columns:
                    fig_price.add_trace(go.Scatter(
                        x=df.index,
                        y=df['MA5'],
                        mode='lines',
                        name='MA5',
                        line=dict(color='orange', width=1, dash='dash')
                    ))
                
                if 'MA20' in df.columns:
                    fig_price.add_trace(go.Scatter(
                        x=df.index,
                        y=df['MA20'],
                        mode='lines',
                        name='MA20',
                        line=dict(color='red', width=1, dash='dash')
                    ))
                
                fig_price.update_layout(
                    title=f"Цена акции {coordinator.ticker}",
                    xaxis_title="Дата",
                    yaxis_title="Цена ($)",
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig_price, use_container_width=True)
            
            with col2:
                st.subheader("📊 Объем торгов")
                fig_volume = go.Figure()
                
                fig_volume.add_trace(go.Bar(
                    x=df.index,
                    y=df['Volume'],
                    name='Объем',
                    marker_color='lightblue'
                ))
                
                fig_volume.update_layout(
                    title="Объем торгов",
                    xaxis_title="Дата",
                    yaxis_title="Объем",
                    height=400
                )
                
                st.plotly_chart(fig_volume, use_container_width=True)
            
            # Информация о портфеле
            st.subheader("💼 Портфель")
            if portfolio_summary['holdings']:
                holdings_df = pd.DataFrame([
                    {
                        "Тикер": ticker,
                        "Акций": info["shares"],
                        "Средняя цена": f"${info['avg_price']:.2f}",
                        "Текущая стоимость": f"${info['current_value']:.2f}",
                        "Нереализованный P&L": f"${info['unrealized_pnl']:.2f}"
                    }
                    for ticker, info in portfolio_summary['holdings'].items()
                ])
                st.dataframe(holdings_df, use_container_width=True)
            else:
                st.info("Портфель пуст. Запустите симуляцию для начала торговли.")


# Страница Real-time Simulation
elif page == "Real-time Simulation":
    st.title("🔄 Real-time Simulation")
    st.markdown("### Запуск агентов и мониторинг коммуникации")
    
    if st.session_state.coordinator is None:
        st.warning("⚠️ Пожалуйста, инициализируйте систему в боковой панели")
    else:
        coordinator = st.session_state.coordinator
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("▶️ Запустить цикл агентов", type="primary"):
                with st.spinner("Выполняется цикл агентов..."):
                    result = coordinator.run_cycle()
                    st.session_state.cycle_results.append(result)
                    st.rerun()
            
            if st.button("🔄 Сбросить систему"):
                coordinator.reset_system()
                st.session_state.cycle_results = []
                st.success("Система сброшена")
                st.rerun()
        
        st.divider()
        
        # Логи агентов
        if st.session_state.cycle_results:
            st.subheader("📋 Результаты последнего цикла")
            latest_result = st.session_state.cycle_results[-1]
            
            if latest_result.get("status") == "success":
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### 📊 Market Agent")
                    st.json({
                        "Тикер": latest_result["market_data"]["ticker"],
                        "Цена": f"${latest_result['market_data']['current_price']:.2f}",
                        "Время": latest_result["market_data"]["timestamp"]
                    })
                
                with col2:
                    st.markdown("#### 🤖 Decision Agent")
                    decision = latest_result["decision"]
                    decision_color = {
                        "BUY": "🟢",
                        "SELL": "🔴",
                        "HOLD": "🟡"
                    }
                    st.markdown(f"**Решение:** {decision_color.get(decision['action'], '⚪')} {decision['action']}")
                    st.json({
                        "Текущая цена": f"${decision['current_price']:.2f}",
                        "Предсказанная цена": f"${decision['predicted_price']:.2f}",
                        "Уверенность": f"{decision['confidence']*100:.2f}%"
                    })
                
                with col3:
                    st.markdown("#### ⚡ Execution Agent")
                    execution = latest_result["execution"]
                    st.json({
                        "Статус": execution["status"],
                        "Действие": execution.get("action", "N/A"),
                        "Сообщение": execution.get("message", "N/A")
                    })
                
                st.divider()
                
                # История циклов
                st.subheader("📜 История циклов")
                cycles_df = pd.DataFrame([
                    {
                        "Время": r["timestamp"],
                        "Цена": f"${r['market_data']['current_price']:.2f}",
                        "Решение": r["decision"]["action"],
                        "Предсказание": f"${r['decision']['predicted_price']:.2f}",
                        "Статус": r["execution"]["status"],
                        "P&L": f"${r['portfolio']['pnl']:.2f}"
                    }
                    for r in st.session_state.cycle_results[-10:]
                ])
                st.dataframe(cycles_df, use_container_width=True)
            else:
                st.error(f"Ошибка: {latest_result.get('message', 'Unknown error')}")
        
        # Лог коммуникации
        st.divider()
        st.subheader("💬 Лог коммуникации агентов")
        
        comm_log = coordinator.get_communication_log()
        if comm_log:
            comm_df = pd.DataFrame([
                {
                    "Время": log["timestamp"],
                    "От": log["from"],
                    "К": log["to"],
                    "Тип сообщения": log["message_type"]
                }
                for log in comm_log[-20:]
            ])
            st.dataframe(comm_df, use_container_width=True)
        else:
            st.info("Лог коммуникации пуст. Запустите цикл агентов.")


# Страница ML Model
elif page == "ML Model":
    st.title("🤖 ML Model")
    st.markdown("### Обучение и метрики модели")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        model_ticker = st.text_input("Тикер для обучения", value="AAPL")
        model_type = st.selectbox("Тип модели", ["random_forest", "linear"])
        period = st.selectbox("Период данных", ["1y", "2y", "5y"], index=1)
    
    with col2:
        st.markdown("### Инструкции")
        st.info("""
        1. Выберите параметры модели
        2. Нажмите "Обучить модель"
        3. Просмотрите метрики и графики
        """)
    
    if st.button("🎓 Обучить модель", type="primary"):
        with st.spinner("Обучение модели..."):
            try:
                model, metrics, test_data = train_model(
                    ticker=model_ticker,
                    model_type=model_type,
                    period=period
                )
                st.session_state.model_metrics = metrics
                st.session_state.test_data = test_data
                st.success("Модель успешно обучена!")
                
                # Перезагружаем координатор для использования новой модели
                if st.session_state.coordinator:
                    st.session_state.coordinator.decision_agent.load_model()
                
            except Exception as e:
                st.error(f"Ошибка при обучении: {str(e)}")
    
    if st.session_state.model_metrics:
        metrics = st.session_state.model_metrics
        
        st.divider()
        st.subheader("📊 Метрики модели")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Test MAE", f"${metrics['test_mae']:.2f}")
            st.metric("Train MAE", f"${metrics['train_mae']:.2f}")
        
        with col2:
            st.metric("Test RMSE", f"${metrics['test_rmse']:.2f}")
            st.metric("Train RMSE", f"${metrics['train_rmse']:.2f}")
        
        with col3:
            st.metric("Test R²", f"{metrics['test_r2']:.4f}")
            st.metric("Train R²", f"{metrics['train_r2']:.4f}")
        
        # График сравнения
        if 'test_data' in st.session_state:
            X_test, y_test, y_pred = st.session_state.test_data
            
            st.divider()
            st.subheader("📈 Сравнение реальных и предсказанных цен")
            
            # Берем последние 100 точек для визуализации
            n_points = min(100, len(y_test))
            indices = np.arange(len(y_test))[-n_points:]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=indices,
                y=y_test[-n_points:],
                mode='lines',
                name='Реальная цена',
                line=dict(color='blue', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=indices,
                y=y_pred[-n_points:],
                mode='lines',
                name='Предсказанная цена',
                line=dict(color='red', width=2, dash='dash')
            ))
            
            fig.update_layout(
                title="Реальные vs Предсказанные цены",
                xaxis_title="Индекс тестового примера",
                yaxis_title="Цена ($)",
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # График ошибок
            errors = y_test[-n_points:] - y_pred[-n_points:]
            
            fig_errors = go.Figure()
            fig_errors.add_trace(go.Scatter(
                x=indices,
                y=errors,
                mode='lines+markers',
                name='Ошибка предсказания',
                line=dict(color='orange', width=1),
                marker=dict(size=4)
            ))
            
            fig_errors.add_hline(y=0, line_dash="dash", line_color="gray")
            
            fig_errors.update_layout(
                title="Ошибки предсказания",
                xaxis_title="Индекс тестового примера",
                yaxis_title="Ошибка ($)",
                height=400
            )
            
            st.plotly_chart(fig_errors, use_container_width=True)


# Страница Trade History
elif page == "Trade History":
    st.title("📜 Trade History")
    st.markdown("### История торгов и P&L")
    
    if st.session_state.coordinator is None:
        st.warning("⚠️ Пожалуйста, инициализируйте систему в боковой панели")
    else:
        coordinator = st.session_state.coordinator
        
        # История торгов
        trade_history = coordinator.get_trade_history()
        
        if not trade_history.empty:
            st.subheader("📋 Таблица сделок")
            
            # Форматируем данные для отображения
            display_df = trade_history.copy()
            if 'timestamp' in display_df.columns:
                display_df['timestamp'] = pd.to_datetime(display_df['timestamp'])
            
            # Переименовываем колонки для удобства
            display_df = display_df.rename(columns={
                'timestamp': 'Время',
                'ticker': 'Тикер',
                'action': 'Действие',
                'shares': 'Акций',
                'price': 'Цена',
                'total': 'Сумма',
                'balance_after': 'Баланс после',
                'confidence': 'Уверенность'
            })
            
            # Форматируем числовые значения
            if 'Цена' in display_df.columns:
                display_df['Цена'] = display_df['Цена'].apply(lambda x: f"${x:.2f}")
            if 'Сумма' in display_df.columns:
                display_df['Сумма'] = display_df['Сумма'].apply(lambda x: f"${x:.2f}")
            if 'Баланс после' in display_df.columns:
                display_df['Баланс после'] = display_df['Баланс после'].apply(lambda x: f"${x:.2f}")
            if 'Уверенность' in display_df.columns:
                display_df['Уверенность'] = display_df['Уверенность'].apply(lambda x: f"{x*100:.2f}%")
            
            st.dataframe(display_df, use_container_width=True)
            
            st.divider()
            
            # График P&L
            st.subheader("💰 P&L График")
            
            # Вычисляем кумулятивный P&L
            if 'timestamp' in trade_history.columns and 'action' in trade_history.columns:
                trade_history['timestamp'] = pd.to_datetime(trade_history['timestamp'])
                trade_history = trade_history.sort_values('timestamp')
                
                # Вычисляем P&L для каждой сделки
                initial_balance = coordinator.execution_agent.initial_balance
                cumulative_pnl = [0]
                cumulative_balance = [initial_balance]
                
                for idx, row in trade_history.iterrows():
                    if row['action'] == 'BUY':
                        # При покупке P&L не меняется сразу
                        cumulative_pnl.append(cumulative_pnl[-1])
                        cumulative_balance.append(row['balance_after'])
                    elif row['action'] == 'SELL':
                        # При продаже вычисляем прибыль
                        # Упрощенный расчет
                        cumulative_balance.append(row['balance_after'])
                        cumulative_pnl.append(cumulative_balance[-1] - initial_balance)
                
                # Создаем график
                if len(cumulative_pnl) > 1:
                    fig_pnl = go.Figure()
                    
                    timestamps = trade_history['timestamp'].tolist()
                    if len(timestamps) == len(cumulative_pnl) - 1:
                        timestamps = [timestamps[0] - pd.Timedelta(days=1)] + timestamps
                    
                    fig_pnl.add_trace(go.Scatter(
                        x=timestamps[:len(cumulative_pnl)],
                        y=cumulative_pnl,
                        mode='lines+markers',
                        name='Cumulative P&L',
                        line=dict(color='green' if cumulative_pnl[-1] >= 0 else 'red', width=2),
                        marker=dict(size=8)
                    ))
                    
                    fig_pnl.add_hline(y=0, line_dash="dash", line_color="gray", 
                                     annotation_text="Break-even")
                    
                    fig_pnl.update_layout(
                        title="Кумулятивный P&L",
                        xaxis_title="Дата",
                        yaxis_title="P&L ($)",
                        hovermode='x unified',
                        height=500
                    )
                    
                    st.plotly_chart(fig_pnl, use_container_width=True)
            
            # Статистика
            st.divider()
            st.subheader("📊 Статистика торгов")
            
            col1, col2, col3, col4 = st.columns(4)
            
            buy_count = len(trade_history[trade_history['action'] == 'BUY']) if 'action' in trade_history.columns else 0
            sell_count = len(trade_history[trade_history['action'] == 'SELL']) if 'action' in trade_history.columns else 0
            
            with col1:
                st.metric("Всего сделок", len(trade_history))
            with col2:
                st.metric("Покупок", buy_count)
            with col3:
                st.metric("Продаж", sell_count)
            with col4:
                current_price = coordinator.market_agent.get_latest_price() or 0
                portfolio_summary = coordinator.execution_agent.get_portfolio_summary(current_price)
                st.metric("Текущий P&L", f"${portfolio_summary['pnl']:.2f}")
        else:
            st.info("История торгов пуста. Запустите симуляцию для начала торговли.")


# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Multi-Agent Financial AI Trading System | Final Project</p>
</div>
""", unsafe_allow_html=True)

