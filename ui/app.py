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
from auth.middleware import get_current_user, show_login_page
from database.db_manager import DBManager
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
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "AAPL"  # Дефолтный тикер


# Проверка авторизации
user = get_current_user()

if not user:
    # Показываем страницу логина
    show_login_page()
    st.stop()
else:
    # Пользователь авторизован
    st.session_state.authenticated = True
    st.session_state.user_id = user['user_id']
    st.session_state.username = user['username']


def init_coordinator(ticker: str, initial_balance: float, force_reinit: bool = False):
    """Инициализирует координатор агентов"""
    user_id = st.session_state.user_id
    
    # Автоматически инициализируем, если coordinator не существует или тикер изменился
    if (st.session_state.coordinator is None or 
        st.session_state.coordinator.ticker != ticker or 
        force_reinit):
        st.session_state.coordinator = AgentCoordinator(
            ticker=ticker, 
            initial_balance=initial_balance,
            user_id=user_id,
            use_db=True
        )
        st.session_state.cycle_results = []
        st.session_state.current_ticker = ticker


# Автоматическая инициализация при входе пользователя
if st.session_state.user_id and st.session_state.coordinator is None:
    from database.db_manager import DBManager
    db_manager = DBManager()
    portfolio = db_manager.get_portfolio(st.session_state.user_id)
    current_balance = portfolio['balance'] if portfolio else 10000.0
    
    # Автоматически инициализируем с дефолтным тикером
    init_coordinator(st.session_state.current_ticker, current_balance)
    
    # Принудительная проверка и создание акций, если их нет
    if st.session_state.coordinator:
        try:
            holdings = db_manager.get_holdings(st.session_state.user_id)
            trade_history = db_manager.get_trade_history(st.session_state.user_id)
            
            # Если нет акций и нет истории - создаем 10 акций Apple
            if len(holdings) == 0 and trade_history.empty:
                # Получаем текущую цену
                market_data = st.session_state.coordinator.market_agent.get_market_data(period="1d", interval="1d")
                if market_data.get("type") == "market_update":
                    current_price = market_data.get("current_price", 0)
                    if current_price > 0:
                        # Покупаем 10 акций
                        shares = 10
                        cost = shares * current_price
                        new_balance = current_balance - cost
                        
                        if new_balance >= 0:
                            # Сохраняем в БД
                            db_manager.add_trade(
                                st.session_state.user_id, st.session_state.current_ticker, "BUY", 
                                shares, current_price, cost, new_balance, 0.8
                            )
                            db_manager.update_holding(
                                st.session_state.user_id, st.session_state.current_ticker, 
                                shares, current_price, cost
                            )
                            db_manager.update_portfolio_balance(st.session_state.user_id, new_balance)
                            
                            # Перезагружаем координатор чтобы он подхватил новые акции
                            init_coordinator(st.session_state.current_ticker, new_balance, force_reinit=True)
                            st.rerun()
        except Exception as e:
            # Если ошибка - просто продолжаем
            pass


# Sidebar
with st.sidebar:
    st.title("⚙️ Настройки")
    
    # Информация о пользователе
    st.info(f"👤 Пользователь: **{st.session_state.username}**")
    
    if st.button("🚪 Выйти"):
        # Очищаем session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.divider()
    
    # Получаем текущий баланс из БД
    db_manager = DBManager()
    portfolio = db_manager.get_portfolio(st.session_state.user_id)
    current_balance = portfolio['balance'] if portfolio else 10000.0
    
    st.info(f"💰 Текущий баланс: **${current_balance:.2f}**")
    
    # Показываем текущий тикер
    current_ticker = st.session_state.current_ticker if st.session_state.coordinator else "AAPL"
    
    ticker = st.text_input(
        "Тикер акции", 
        value=current_ticker, 
        help="Например: AAPL, TSLA, MSFT. Система автоматически инициализируется при изменении."
    )
    
    # Автоматически инициализируем при изменении тикера
    if ticker != current_ticker:
        init_coordinator(ticker, current_balance, force_reinit=True)
        st.success(f"✅ Система автоматически инициализирована для {ticker}")
        st.rerun()
    
    # Показываем статус системы
    if st.session_state.coordinator:
        st.success(f"✅ Система активна для тикера: **{st.session_state.coordinator.ticker}**")
        
        # Опциональная кнопка для принудительной переинициализации
        if st.button("🔄 Переинициализировать систему", help="Принудительно перезапустить систему"):
            init_coordinator(ticker, current_balance, force_reinit=True)
            st.success(f"Система переинициализирована для {ticker}")
            st.rerun()
    else:
        st.warning("⚠️ Система не инициализирована")
    
    st.divider()
    
    st.subheader("📊 Навигация")
    page = st.radio(
        "Выберите страницу",
        ["Overview", "Real-time Simulation", "ML Model", "Trade History", "Database Status"]
    )


# Главная страница - Overview
if page == "Overview":
    st.title("📈 Multi-Agent Trading System")
    st.markdown("### Обзор системы и портфеля")
    
    # Автоматическая инициализация, если нужно
    if st.session_state.coordinator is None and st.session_state.user_id:
        from database.db_manager import DBManager
        db_manager = DBManager()
        portfolio = db_manager.get_portfolio(st.session_state.user_id)
        current_balance = portfolio['balance'] if portfolio else 10000.0
        init_coordinator(st.session_state.current_ticker, current_balance)
        st.info(f"✅ Система автоматически инициализирована для {st.session_state.current_ticker}")
        st.rerun()
    
    if st.session_state.coordinator is None:
        st.warning("⚠️ Система не инициализирована. Пожалуйста, подождите...")
    else:
        coordinator = st.session_state.coordinator
        
        # Выбор периода данных
        col_period, col_info = st.columns([1, 2])
        
        with col_period:
            st.subheader("⚙️ Настройки графика")
            period_options = {
                "1 неделя": "5d",
                "1 месяц": "1mo",
                "3 месяца": "3mo",
                "6 месяцев": "6mo",
                "1 год": "1y",
                "2 года": "2y",
                "5 лет": "5y",
                "Максимум": "max"
            }
            
            selected_period_label = st.selectbox(
                "Период данных",
                options=list(period_options.keys()),
                index=2,  # По умолчанию 3 месяца
                help="Выберите период для отображения графика"
            )
            
            selected_period = period_options[selected_period_label]
            
            # Выбор интервала
            interval_options = {
                "1 день": "1d",
                "1 неделя": "1wk",
                "1 месяц": "1mo"
            }
            
            selected_interval_label = st.selectbox(
                "Интервал",
                options=list(interval_options.keys()),
                index=0,  # По умолчанию 1 день
                help="Интервал между точками данных"
            )
            
            selected_interval = interval_options[selected_interval_label]
        
        with col_info:
            st.info(f"""
            **Выбранный период:** {selected_period_label}  
            **Интервал:** {selected_interval_label}  
            **Тикер:** {coordinator.ticker}
            """)
        
        # Кнопка обновления данных
        col_refresh1, col_refresh2 = st.columns([1, 10])
        with col_refresh1:
            if st.button("🔄 Обновить данные", help="Обновить данные с Yahoo Finance", type="primary"):
                # Устанавливаем флаг для принудительного обновления
                st.session_state.force_refresh = True
                st.rerun()
        
        # Получаем данные рынка с выбранными параметрами
        with st.spinner(f"Загрузка свежих данных за {selected_period_label}..."):
            # Всегда получаем свежие данные (без кэширования)
            # Проверяем, была ли нажата кнопка обновления
            force_refresh = st.session_state.get('force_refresh', False)
            try:
                # Пробуем вызвать с force_refresh (новая версия)
                df = coordinator.get_market_dataframe(period=selected_period, interval=selected_interval, force_refresh=force_refresh)
            except TypeError:
                # Если метод не поддерживает force_refresh (старая версия), вызываем без него
                df = coordinator.get_market_dataframe(period=selected_period, interval=selected_interval)
            st.session_state.force_refresh = False  # Сбрасываем флаг
        
        if not df.empty:
            # Показываем время последнего обновления
            last_update_time = datetime.now().strftime("%H:%M:%S")
            st.caption(f"🕐 Последнее обновление: {last_update_time}")
            
            col1, col2, col3, col4 = st.columns(4)
            
            current_price = df['Close'].iloc[-1]
            # Безопасное вычисление изменения цены
            if len(df) > 1:
                price_change = df['Close'].iloc[-1] - df['Close'].iloc[-2]
                price_change_pct = (price_change / df['Close'].iloc[-2]) * 100
            else:
                price_change = 0
                price_change_pct = 0
            
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
                
                # Показываем информацию о данных
                data_info = f"Данных: {len(df)} точек | Период: {df.index[0].strftime('%Y-%m-%d')} - {df.index[-1].strftime('%Y-%m-%d')}"
                st.caption(data_info)
                
                fig_price = go.Figure()
                
                # Основная линия цены
                fig_price.add_trace(go.Scatter(
                    x=df.index,
                    y=df['Close'],
                    mode='lines+markers',
                    name='Цена закрытия',
                    line=dict(color='#1f77b4', width=2),
                    marker=dict(size=4),
                    hovertemplate='<b>%{y:.2f}</b><br>%{x}<extra></extra>'
                ))
                
                # Добавляем последнюю цену как отдельную точку
                if len(df) > 0:
                    last_price = df['Close'].iloc[-1]
                    fig_price.add_trace(go.Scatter(
                        x=[df.index[-1]],
                        y=[last_price],
                        mode='markers',
                        name='Текущая цена',
                        marker=dict(size=12, color='green', symbol='circle'),
                        hovertemplate=f'<b>Текущая: ${last_price:.2f}</b><br>%{{x}}<extra></extra>'
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
                    title=f"Цена акции {coordinator.ticker} (обновлено: {datetime.now().strftime('%H:%M:%S')})",
                    xaxis_title="Дата",
                    yaxis_title="Цена ($)",
                    hovermode='x unified',
                    height=400,
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                # Добавляем аннотацию с текущей ценой
                if len(df) > 0:
                    fig_price.add_annotation(
                        x=df.index[-1],
                        y=df['Close'].iloc[-1],
                        text=f"${df['Close'].iloc[-1]:.2f}",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=2,
                        arrowcolor="green",
                        ax=0,
                        ay=-40,
                        bgcolor="rgba(0,0,0,0.8)",
                        bordercolor="green",
                        borderwidth=2,
                        font=dict(color="white", size=12)
                    )
                
                st.plotly_chart(fig_price, width='stretch')
            
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
                
                st.plotly_chart(fig_volume, width='stretch')
            
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
                st.dataframe(holdings_df, width='stretch')
            else:
                st.info("Портфель пуст. Запустите симуляцию для начала торговли.")


# Страница Real-time Simulation
elif page == "Real-time Simulation":
    st.title("🔄 Real-time Simulation")
    st.markdown("### Запуск агентов и мониторинг коммуникации")
    
    # Автоматическая инициализация, если нужно
    if st.session_state.coordinator is None and st.session_state.user_id:
        from database.db_manager import DBManager
        db_manager = DBManager()
        portfolio = db_manager.get_portfolio(st.session_state.user_id)
        current_balance = portfolio['balance'] if portfolio else 10000.0
        init_coordinator(st.session_state.current_ticker, current_balance)
        st.info(f"✅ Система автоматически инициализирована для {st.session_state.current_ticker}")
        st.rerun()
    
    if st.session_state.coordinator is None:
        st.warning("⚠️ Система не инициализирована. Пожалуйста, подождите...")
    else:
        coordinator = st.session_state.coordinator
        
        # Автоматическая торговля
        st.subheader("🤖 Автоматическая торговля")
        auto_trade_col1, auto_trade_col2, auto_trade_col3 = st.columns(3)
        
        with auto_trade_col1:
            auto_trade_enabled = st.checkbox("🔄 Автоматическая торговля", 
                                            value=st.session_state.get('auto_trade', False),
                                            help="AI будет автоматически делать сделки каждые несколько секунд")
        
        with auto_trade_col2:
            if auto_trade_enabled:
                auto_interval = st.number_input("Интервал (секунды)", min_value=5, max_value=300, 
                                               value=st.session_state.get('auto_interval', 10),
                                               step=5)
                st.session_state.auto_interval = auto_interval
            else:
                auto_interval = 10
        
        with auto_trade_col3:
            if auto_trade_enabled:
                max_cycles = st.number_input("Макс. циклов", min_value=1, max_value=1000, 
                                           value=st.session_state.get('max_cycles', 100),
                                           step=10)
                st.session_state.max_cycles = max_cycles
            else:
                max_cycles = 100
        
        st.session_state.auto_trade = auto_trade_enabled
        
        # Ручное управление
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if not auto_trade_enabled:
                if st.button("▶️ Запустить цикл агентов", type="primary"):
                    with st.spinner("Выполняется цикл агентов..."):
                        result = coordinator.run_cycle()
                        st.session_state.cycle_results.append(result)
                        st.rerun()
            else:
                st.info("🤖 Автоматическая торговля активна")
                if st.button("⏸️ Остановить автоматическую торговлю"):
                    st.session_state.auto_trade = False
                    st.rerun()
            
            if st.button("🔄 Сбросить систему"):
                coordinator.reset_system()
                st.session_state.cycle_results = []
                st.session_state.auto_trade = False
                st.success("Система сброшена")
                st.rerun()
        
        # Автоматический запуск циклов
        if auto_trade_enabled:
            if 'auto_cycle_count' not in st.session_state:
                st.session_state.auto_cycle_count = 0
            if 'last_auto_cycle_time' not in st.session_state:
                st.session_state.last_auto_cycle_time = datetime.now()
            
            current_time = datetime.now()
            time_since_last = (current_time - st.session_state.last_auto_cycle_time).total_seconds()
            
            if st.session_state.auto_cycle_count < max_cycles:
                if time_since_last >= auto_interval:
                    # Время для следующего цикла
                    with st.spinner(f"🤖 Автоматический цикл {st.session_state.auto_cycle_count + 1}/{max_cycles}..."):
                        result = coordinator.run_cycle()
                        st.session_state.cycle_results.append(result)
                        st.session_state.auto_cycle_count += 1
                        st.session_state.last_auto_cycle_time = datetime.now()
                    st.rerun()
                else:
                    # Показываем обратный отсчет
                    remaining = auto_interval - time_since_last
                    st.info(f"⏳ Следующий цикл через {remaining:.1f} секунд... "
                           f"(Цикл {st.session_state.auto_cycle_count + 1}/{max_cycles})")
                    # Автоматически обновляем страницу через оставшееся время
                    import time
                    time.sleep(min(1.0, remaining))
                    st.rerun()
            else:
                st.success(f"✅ Выполнено {max_cycles} автоматических циклов")
                st.session_state.auto_trade = False
                st.session_state.auto_cycle_count = 0
                st.session_state.last_auto_cycle_time = None
        
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
                    
                    # Проверяем, загружена ли модель
                    model_status = "✅ Модель загружена" if coordinator.decision_agent.model is not None else "⚠️ Модель не загружена"
                    st.caption(model_status)
                    
                    action = decision['action']
                    price_diff = decision['predicted_price'] - decision['current_price']
                    price_diff_pct = (price_diff / decision['current_price']) * 100 if decision['current_price'] > 0 else 0
                    
                    st.markdown(f"**Решение:** {decision_color.get(action, '⚪')} {action}")
                    
                    # Показываем разницу в цене с цветом
                    if price_diff_pct > 0:
                        diff_color = "🟢"
                        diff_text = f"+{price_diff_pct:.2f}%"
                    else:
                        diff_color = "🔴"
                        diff_text = f"{price_diff_pct:.2f}%"
                    
                    st.json({
                        "Текущая цена": f"${decision['current_price']:.2f}",
                        "Предсказанная цена": f"${decision['predicted_price']:.2f}",
                        "Изменение": f"{diff_color} {diff_text}",
                        "Уверенность": f"{decision['confidence']*100:.1f}%"
                    })
                    
                    # Показываем качество предсказания
                    if abs(price_diff_pct) < 1:
                        st.info("💡 Предсказание близко к текущей цене - консервативное решение")
                    elif abs(price_diff_pct) > 5:
                        st.warning("⚠️ Большое изменение цены - проверьте предсказание")
                
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
                st.dataframe(cycles_df, width='stretch')
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
            st.dataframe(comm_df, width='stretch')
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
            test_data = st.session_state.test_data
            if len(test_data) == 4:
                X_test, y_test, y_pred, dates_test = test_data
            else:
                # Обратная совместимость со старым форматом
                X_test, y_test, y_pred = test_data
                dates_test = None
            
            st.divider()
            st.subheader("📈 Сравнение реальных и предсказанных цен")
            
            # Настройки отображения
            col_period1, col_period2 = st.columns(2)
            with col_period1:
                # Выбор количества точек для отображения
                max_points = len(y_test)
                display_points = st.slider(
                    "Количество точек для отображения",
                    min_value=min(20, max_points),
                    max_value=max_points,
                    value=min(100, max_points),
                    step=10,
                    help="Выберите, сколько точек показать на графике"
                )
            
            with col_period2:
                # Выбор части данных (начало/конец/все)
                display_mode = st.radio(
                    "Показать",
                    options=["Все данные", "Начало", "Конец"],
                    horizontal=True,
                    help="Выберите, какую часть данных показать"
                )
            
            # Определяем, какие данные показывать
            if display_mode == "Все данные":
                start_idx = 0
                end_idx = display_points
            elif display_mode == "Начало":
                start_idx = 0
                end_idx = display_points
            else:  # Конец
                start_idx = max(0, len(y_test) - display_points)
                end_idx = len(y_test)
            
            # Берем нужные данные
            y_test_display = y_test[start_idx:end_idx]
            y_pred_display = y_pred[start_idx:end_idx]
            
            # Используем даты, если они есть
            if dates_test is not None:
                dates_display = pd.to_datetime(dates_test[start_idx:end_idx])
                x_data = dates_display
                x_title = "Дата"
                hover_template = '<b>Дата:</b> %{x|%Y-%m-%d}<br><b>Цена:</b> $%{y:.2f}<extra></extra>'
            else:
                # Fallback на индексы, если дат нет
                x_data = np.arange(start_idx, end_idx)
                x_title = "Индекс тестового примера"
                hover_template = '<b>Индекс:</b> %{x}<br><b>Цена:</b> $%{y:.2f}<extra></extra>'
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=x_data,
                y=y_test_display,
                mode='lines+markers',
                name='Реальная цена',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=5),
                hovertemplate=hover_template.replace('Цена', 'Реальная цена')
            ))
            
            fig.add_trace(go.Scatter(
                x=x_data,
                y=y_pred_display,
                mode='lines+markers',
                name='Предсказанная цена',
                line=dict(color='red', width=2, dash='dash'),
                marker=dict(size=5, symbol='circle'),
                hovertemplate=hover_template.replace('Цена', 'Предсказанная цена')
            ))
            
            # Добавляем информацию о периоде
            if dates_test is not None and len(dates_display) > 0:
                period_info = f"Период: {dates_display[0].strftime('%Y-%m-%d')} - {dates_display[-1].strftime('%Y-%m-%d')}"
            else:
                period_info = f"Показано {len(y_test_display)} точек"
            
            fig.update_layout(
                title=f"Реальные vs Предсказанные цены | {period_info}",
                xaxis_title=x_title,
                yaxis_title="Цена ($)",
                hovermode='x unified',
                height=500,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='lightgray'
                ),
                yaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='lightgray'
                )
            )
            
            st.plotly_chart(fig, width='stretch')
            
            # График ошибок
            errors = y_test_display - y_pred_display
            
            fig_errors = go.Figure()
            fig_errors.add_trace(go.Scatter(
                x=x_data,
                y=errors,
                mode='lines+markers',
                name='Ошибка предсказания',
                line=dict(color='orange', width=2),
                marker=dict(size=5),
                hovertemplate=hover_template.replace('Цена', 'Ошибка').replace('$', '')
            ))
            
            fig_errors.add_hline(y=0, line_dash="dash", line_color="gray", 
                                annotation_text="Нулевая ошибка")
            
            # Вычисляем среднюю ошибку
            mean_error = np.mean(np.abs(errors))
            fig_errors.add_hline(y=mean_error, line_dash="dot", line_color="blue",
                                annotation_text=f"Средняя ошибка: ${mean_error:.2f}")
            fig_errors.add_hline(y=-mean_error, line_dash="dot", line_color="blue")
            
            fig_errors.update_layout(
                title=f"Ошибки предсказания | {period_info}",
                xaxis_title=x_title,
                yaxis_title="Ошибка ($)",
                height=400,
                hovermode='x unified',
                showlegend=True,
                xaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='lightgray'
                ),
                yaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='lightgray'
                )
            )
            
            st.plotly_chart(fig_errors, width='stretch')
            
            # Статистика ошибок
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            with col_stat1:
                st.metric("Средняя ошибка", f"${np.mean(np.abs(errors)):.2f}")
            with col_stat2:
                st.metric("Макс. ошибка", f"${np.max(np.abs(errors)):.2f}")
            with col_stat3:
                st.metric("Мин. ошибка", f"${np.min(np.abs(errors)):.2f}")
            with col_stat4:
                st.metric("Среднекв. ошибка", f"${np.sqrt(np.mean(errors**2)):.2f}")


# Страница Trade History
elif page == "Trade History":
    st.title("📜 Trade History")
    st.markdown("### История торгов и P&L")
    
    # Автоматическая инициализация, если нужно
    if st.session_state.coordinator is None and st.session_state.user_id:
        from database.db_manager import DBManager
        db_manager = DBManager()
        portfolio = db_manager.get_portfolio(st.session_state.user_id)
        current_balance = portfolio['balance'] if portfolio else 10000.0
        init_coordinator(st.session_state.current_ticker, current_balance)
        st.info(f"✅ Система автоматически инициализирована для {st.session_state.current_ticker}")
        st.rerun()
    
    if st.session_state.coordinator is None:
        st.warning("⚠️ Система не инициализирована. Пожалуйста, подождите...")
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
                # Получаем начальный баланс из БД
                db_manager = DBManager()
                portfolio = db_manager.get_portfolio(st.session_state.user_id)
                initial_balance = portfolio['balance'] if portfolio else 10000.0
                
                # Вычисляем начальный баланс из истории (первая сделка)
                if len(trade_history) > 0:
                    first_trade = trade_history.iloc[0]
                    if first_trade['action'] == 'BUY':
                        # Если первая сделка - покупка, начальный баланс = balance_after + total
                        initial_balance = first_trade['balance_after'] + first_trade['total']
                    else:
                        # Если первая сделка - продажа, начальный баланс = balance_after - total
                        initial_balance = first_trade['balance_after'] - first_trade['total']
                
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
                    
                    st.plotly_chart(fig_pnl, width='stretch')
            
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
                # Получаем начальный баланс из БД
                db_manager = DBManager()
                portfolio = db_manager.get_portfolio(st.session_state.user_id)
                initial_balance = portfolio['balance'] if portfolio else 10000.0
                current_pnl = portfolio_summary['portfolio_value'] - initial_balance
                st.metric("Текущий P&L", f"${current_pnl:.2f}")
        else:
            st.info("История торгов пуста. Запустите симуляцию для начала торговли.")


# Страница Database Status
elif page == "Database Status":
    st.title("🗄️ Database Status")
    st.markdown("### Информация о подключении к базе данных")
    
    from database.db_manager import DBManager
    import sqlite3
    import os
    
    db = DBManager()
    
    # Информация о подключении
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📁 Информация о БД")
        st.info(f"**Путь к БД:** `{db.db_path}`")
        file_exists = os.path.exists(db.db_path)
        st.info(f"**Файл существует:** {'✅ Да' if file_exists else '❌ Нет'}")
        
        if file_exists:
            try:
                file_size = os.path.getsize(db.db_path)
                st.info(f"**Размер файла:** {file_size / 1024:.2f} KB")
            except Exception as e:
                st.warning(f"Не удалось получить размер: {e}")
    
    with col2:
        st.subheader("🔌 Статус подключения")
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Проверяем версию SQLite
            cursor.execute("SELECT sqlite_version()")
            sqlite_version = cursor.fetchone()[0]
            st.success("✅ Подключение активно")
            st.info(f"**SQLite версия:** {sqlite_version}")
            
            # Проверяем, можем ли мы выполнять запросы
            cursor.execute("SELECT 1")
            test_result = cursor.fetchone()
            if test_result:
                st.success("✅ Запросы выполняются успешно")
            
            conn.close()
        except Exception as e:
            st.error(f"❌ Ошибка подключения: {str(e)}")
            st.code(str(e), language="text")
    
    st.divider()
    
    # Список таблиц и статистика
    st.subheader("📊 Таблицы в базе данных")
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Получаем список таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        if tables:
            # Создаем DataFrame со статистикой
            table_stats = []
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                
                # Получаем структуру таблицы
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                table_stats.append({
                    "Таблица": table_name,
                    "Записей": count,
                    "Колонок": len(columns)
                })
            
            stats_df = pd.DataFrame(table_stats)
            st.dataframe(stats_df, use_container_width=True)
            
            st.divider()
            
            # Детальная информация по таблицам
            for table in tables:
                table_name = table[0]
                with st.expander(f"📋 Детали таблицы: {table_name}"):
                    # Показываем структуру
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    st.write("**Структура:**")
                    cols_df = pd.DataFrame([
                        {
                            "Колонка": col[1],
                            "Тип": col[2],
                            "NOT NULL": "Да" if col[3] else "Нет",
                            "По умолчанию": col[4] or "-"
                        }
                        for col in columns
                    ])
                    st.dataframe(cols_df, use_container_width=True)
                    
                    # Показываем примеры данных (первые 5 записей)
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                    rows = cursor.fetchall()
                    
                    if rows:
                        st.write("**Примеры данных (первые 5 записей):**")
                        # Преобразуем в DataFrame
                        data = [dict(row) for row in rows]
                        # Скрываем пароли для безопасности
                        if data and 'password_hash' in data[0]:
                            for d in data:
                                d['password_hash'] = '***скрыто***'
                        st.dataframe(pd.DataFrame(data), width='stretch')
                    else:
                        st.info("Таблица пуста")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Ошибка при получении информации: {str(e)}")
        st.code(str(e), language="text")
    
    st.divider()
    
    # Статистика по пользователям
    st.subheader("👥 Статистика")
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Количество пользователей
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # Количество портфелей
        cursor.execute("SELECT COUNT(*) FROM portfolios")
        portfolio_count = cursor.fetchone()[0]
        
        # Общий баланс всех портфелей
        cursor.execute("SELECT SUM(balance) FROM portfolios")
        total_balance = cursor.fetchone()[0] or 0
        
        # Количество сделок
        cursor.execute("SELECT COUNT(*) FROM trade_history")
        trade_count = cursor.fetchone()[0]
        
        # Количество холдингов
        cursor.execute("SELECT COUNT(*) FROM holdings")
        holdings_count = cursor.fetchone()[0]
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("👥 Пользователей", user_count)
        with col2:
            st.metric("💰 Портфелей", portfolio_count)
        with col3:
            st.metric("💵 Общий баланс", f"${total_balance:,.2f}")
        with col4:
            st.metric("📈 Сделок", trade_count)
        with col5:
            st.metric("📊 Холдингов", holdings_count)
        
        # Показываем пользователей (без паролей)
        if user_count > 0:
            st.subheader("📋 Список пользователей")
            cursor.execute("SELECT id, username, email, created_at FROM users ORDER BY created_at DESC")
            users = cursor.fetchall()
            users_df = pd.DataFrame([dict(u) for u in users])
            st.dataframe(users_df, use_container_width=True)
        
        conn.close()
        
    except Exception as e:
        st.error(f"Ошибка при получении статистики: {str(e)}")
        st.code(str(e), language="text")
    
    st.divider()
    
    # SQL запросы (опционально, для отладки)
    st.subheader("🔍 SQL Запросы (для отладки)")
    st.warning("⚠️ Используйте с осторожностью! Только SELECT запросы для безопасности.")
    
    sql_query = st.text_area(
        "Введите SQL запрос:",
        value="SELECT * FROM users LIMIT 5;",
        height=100
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Выполнить SELECT запрос"):
            try:
                if not sql_query.strip().upper().startswith('SELECT'):
                    st.error("Разрешены только SELECT запросы для безопасности")
                else:
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute(sql_query)
                    results = cursor.fetchall()
                    
                    if results:
                        df = pd.DataFrame([dict(row) for row in results])
                        # Скрываем пароли
                        if 'password_hash' in df.columns:
                            df['password_hash'] = '***скрыто***'
                        st.dataframe(df, width='stretch')
                        st.success(f"✅ Найдено записей: {len(results)}")
                    else:
                        st.info("Запрос выполнен, но результатов нет")
                    conn.close()
            except Exception as e:
                st.error(f"Ошибка выполнения запроса: {str(e)}")
                st.code(str(e), language="text")
    
    with col2:
        if st.button("🔄 Обновить страницу"):
            st.rerun()
    
    # Информация о текущем пользователе
    st.divider()
    st.subheader("👤 Текущая сессия")
    st.info(f"**Ваш User ID:** {st.session_state.user_id}")
    st.info(f"**Ваш Username:** {st.session_state.username}")
    
    # Показываем портфель текущего пользователя
    try:
        db_manager = DBManager()
        portfolio = db_manager.get_portfolio(st.session_state.user_id)
        if portfolio:
            st.success(f"✅ Ваш портфель найден. Баланс: ${portfolio['balance']:.2f}")
            
            # Показываем холдинги
            holdings = db_manager.get_holdings(st.session_state.user_id)
            if holdings:
                st.write("**Ваши холдинги:**")
                holdings_df = pd.DataFrame([
                    {
                        "Тикер": h['ticker'],
                        "Акций": h['shares'],
                        "Средняя цена": f"${h['avg_price']:.2f}",
                        "Общая стоимость": f"${h['total_cost']:.2f}"
                    }
                    for h in holdings
                ])
                st.dataframe(holdings_df, width='stretch')
        else:
            st.warning("⚠️ Портфель не найден")
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")
        st.code(str(e), language="text")


# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Multi-Agent Financial AI Trading System | Final Project</p>
</div>
""", unsafe_allow_html=True)

