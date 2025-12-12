# Multi-Agent Financial AI Trading System
## Final Project Report

---

**Course:** INF 451  
**Project:** Multi-Agent Financial AI Trading System  
**Date:** December 2025  
**Author:** Aman Kalabay

---

# Table of Contents

1. [Cover Page](#cover-page)
2. [Abstract](#abstract)
3. [Introduction & Problem](#introduction--problem)
4. [Background / Related Work](#background--related-work)
5. [System Design & Diagrams](#system-design--diagrams)
6. [How I Built It](#how-i-built-it)
7. [Results / What Happened](#results--what-happened)
8. [What Worked & What Didn't](#what-worked--what-didnt)
9. [Conclusion & Future Ideas](#conclusion--future-ideas)
10. [References](#references)
11. [Extra Materials](#extra-materials)

---

## Cover Page

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         Multi-Agent Financial AI Trading System              ║
║                                                              ║
║                    Final Project Report                      ║
║                                                              ║
║                        INF 451                               ║
║                                                              ║
║                      November 2024                           ║
║                                                              ║
║  Author: Aman Kalabay                                        ║
║  Student ID: 230103375                                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Abstract

This report presents a **Multi-Agent Financial AI Trading System** that demonstrates coordination and communication between three specialized software agents for automated stock trading decisions. The system integrates real-time market data from Yahoo Finance API, machine learning models for price prediction, and a web-based interface for user interaction.

The system consists of three autonomous agents: a **Market Monitoring Agent** that fetches and processes market data, a **Decision-Making Agent** that uses AI to predict stock prices and make trading decisions, and an **Execution Agent** that manages portfolio and executes trades. An **Agent Coordinator** manages the lifecycle and communication between all agents.

Key achievements include successful implementation of inter-agent communication, real-time data integration, ML-based price prediction, user authentication with JWT tokens, and persistent data storage using SQLite. The system demonstrates practical application of multi-agent systems in financial trading scenarios.

**Keywords:** Multi-Agent Systems, Financial Trading, Machine Learning, Stock Prediction, Agent Communication, Automated Trading

---

## Introduction & Problem

### Introduction

Financial markets generate vast amounts of data daily, making it challenging for individual traders to analyze and make informed decisions in real-time. Automated trading systems have emerged as a solution, leveraging computational power and artificial intelligence to process market data and execute trades.

Multi-agent systems provide an elegant architecture for such complex systems, where specialized agents can handle different aspects of trading: data collection, analysis, decision-making, and execution. This project implements a multi-agent trading system that demonstrates coordination, communication, and autonomous decision-making.

### Problem Statement

The primary problem addressed by this project is:

1. **How to coordinate multiple specialized agents** to work together for automated trading decisions
2. **How to integrate real-time market data** with AI-powered predictions
3. **How to implement effective communication protocols** between agents
4. **How to manage user portfolios** and trading history in a scalable way
5. **How to provide an intuitive interface** for users to interact with the system

### Objectives

The project aims to:

- Demonstrate multi-agent system architecture with three specialized agents
- Implement real-time market data integration via Yahoo Finance API
- Develop an AI-powered decision-making system using machine learning
- Create a user-friendly web interface for system interaction
- Implement user authentication and personal portfolio management
- Showcase agent communication and coordination mechanisms

### Scope

The system focuses on:
- **Simulation-based trading** (no real money transactions)
- **Single stock trading** per user session
- **Historical and real-time data** from Yahoo Finance
- **ML-based price prediction** using scikit-learn
- **Web-based interface** using Streamlit

---

## Background / Related Work

### Multi-Agent Systems

Multi-agent systems (MAS) are computational systems composed of multiple interacting intelligent agents. In financial trading, MAS have been used for:

- **Distributed decision-making**: Different agents handle different aspects of trading
- **Specialization**: Each agent focuses on a specific task (data collection, analysis, execution)
- **Scalability**: Easy to add new agents or modify existing ones
- **Fault tolerance**: System continues working if one agent fails

### Related Work

**1. Algorithmic Trading Systems**
- High-frequency trading systems use multiple agents for order execution
- Market-making algorithms coordinate multiple strategies
- Risk management systems use agent-based architectures

**2. Machine Learning in Trading**
- Random Forest and ensemble methods for price prediction
- Deep learning models (LSTM, GRU) for time series forecasting
- Reinforcement learning for trading strategy optimization

**3. Agent Communication Protocols**
- FIPA (Foundation for Intelligent Physical Agents) standards
- Message-passing architectures
- Event-driven communication patterns

### Our Contribution

This project combines:
- **Multi-agent architecture** with specialized roles
- **Real-time data integration** via public APIs
- **ML-based predictions** using traditional machine learning
- **User-centric design** with authentication and personalization
- **Practical implementation** ready for deployment

---

## System Design & Diagrams

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│                    (Streamlit Web App)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Overview │  │Simulation│  │ML Model  │  │  History │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              Agent Coordinator                              │
│  - Manages agent lifecycle                                  │
│  - Coordinates communication                                │
│  - Logs all interactions                                    │
└──────┬───────────────┬───────────────┬─────────────────────┘
       │               │               │
       ↓               ↓               ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Market       │ │ Decision     │ │ Execution    │
│ Monitoring   │ │ Making       │ │ Agent         │
│ Agent        │ │ Agent        │ │              │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       ↓                ↓                ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Yahoo Finance│ │ ML Model     │ │ SQLite DB    │
│ API          │ │ (model.pkl)  │ │ (Portfolio)  │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Agent Communication Flow

```
┌─────────────────┐
│ Market Agent    │
│                 │
│ 1. Fetch data   │
│ 2. Calculate    │
│    indicators   │
│ 3. Format msg   │
└────────┬────────┘
         │
         │ market_update
         ↓
┌─────────────────┐
│ Coordinator     │ ← Logs communication
│                 │
│ Routes message  │
└────────┬────────┘
         │
         │ market_update
         ↓
┌─────────────────┐
│ Decision Agent  │
│                 │
│ 1. Extract      │
│    features     │
│ 2. Predict      │
│    price        │
│ 3. Make         │
│    decision     │
└────────┬────────┘
         │
         │ trading_decision
         ↓
┌─────────────────┐
│ Coordinator     │ ← Logs communication
│                 │
│ Routes message  │
└────────┬────────┘
         │
         │ trading_decision
         ↓
┌─────────────────┐
│ Execution Agent │
│                 │
│ 1. Execute      │
│    trade        │
│ 2. Update DB    │
│ 3. Return result│
└────────┬────────┘
         │
         │ execution_result
         ↓
┌─────────────────┐
│ Coordinator     │ ← Logs communication
│                 │
│ Returns to UI   │
└─────────────────┘
```

### Data Flow Diagram

```
User Input (Ticker: "AAPL")
    ↓
Market Agent
    ├─→ Yahoo Finance API
    ├─→ Historical Data (OHLCV)
    ├─→ Technical Indicators
    └─→ Market Update Message
         ↓
Decision Agent
    ├─→ Feature Extraction (16 features)
    ├─→ ML Model (model.pkl)
    ├─→ Price Prediction
    ├─→ Decision Logic
    └─→ Trading Decision (BUY/SELL/HOLD)
         ↓
Execution Agent
    ├─→ Trade Execution
    ├─→ Portfolio Update
    ├─→ SQLite Database
    └─→ Execution Result
         ↓
User Interface
    ├─→ Display Results
    ├─→ Update Charts
    └─→ Show Portfolio
```

### Database Schema

```
┌─────────────┐
│   users     │
├─────────────┤
│ id (PK)     │
│ username    │
│ email       │
│ password    │
│ created_at  │
└──────┬──────┘
       │
       │ 1:N
       ↓
┌─────────────┐      ┌─────────────┐
│ portfolios  │      │  holdings   │
├─────────────┤      ├─────────────┤
│ id (PK)     │      │ id (PK)     │
│ user_id (FK)│◄─────┤ user_id (FK)│
│ balance     │      │ ticker      │
│ created_at  │      │ shares      │
│ updated_at  │      │ avg_price   │
└──────┬──────┘      │ total_cost  │
       │             └─────────────┘
       │ 1:N
       ↓
┌─────────────┐
│trade_history│
├─────────────┤
│ id (PK)     │
│ user_id (FK)│
│ timestamp   │
│ ticker      │
│ action      │
│ shares      │
│ price       │
│ total       │
│ balance_after│
│ confidence  │
└─────────────┘
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Streamlit UI (ui/app.py)            │  │
│  │  - Overview Page                                  │  │
│  │  - Real-time Simulation                          │  │
│  │  - ML Model Training                             │  │
│  │  - Trade History                                 │  │
│  │  - Database Status                               │  │
│  └──────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────┐
│                  Business Logic Layer                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Market     │  │   Decision   │  │  Execution   │ │
│  │   Agent      │  │   Agent      │  │   Agent      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         │                 │                 │          │
│         └─────────────────┼─────────────────┘          │
│                           │                             │
│                  ┌────────┴────────┐                    │
│                  │   Coordinator  │                    │
│                  └─────────────────┘                    │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────┐
│                    Data Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Yahoo      │  │   SQLite     │  │   ML Model   │ │
│  │   Finance    │  │   Database   │  │   (model.pkl)│ │
│  │   API        │  │              │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## How I Built It

### Development Process

**Phase 1: Core Agent Implementation**
1. Created Market Monitoring Agent with yfinance integration
2. Implemented Decision-Making Agent with ML model support
3. Built Execution Agent with portfolio management
4. Developed Agent Coordinator for orchestration

**Phase 2: ML Model Integration**
1. Created feature extraction pipeline (16 features)
2. Implemented model training script
3. Integrated model loading and prediction
4. Added model metrics visualization

**Phase 3: Web Interface**
1. Built Streamlit application with multiple pages
2. Implemented real-time data visualization
3. Added agent cycle execution interface
4. Created trade history and portfolio views

**Phase 4: User Authentication & Database**
1. Implemented JWT authentication system
2. Created SQLite database schema
3. Integrated user-specific portfolio management
4. Added database status monitoring page

**Phase 5: Enhancements**
1. Added automatic system initialization
2. Implemented customizable data periods
3. Enhanced error handling and logging
4. Improved user experience

### Technology Stack

**Backend:**
- **Python 3.8+**: Core programming language
- **yfinance**: Real-time market data
- **scikit-learn**: Machine learning models
- **pandas/numpy**: Data processing
- **SQLite**: Database storage
- **PyJWT/bcrypt**: Authentication

**Frontend:**
- **Streamlit**: Web framework
- **Plotly**: Interactive charts
- **Matplotlib**: Additional visualizations

### Key Implementation Details

#### 1. Agent Communication

```python
# Coordinator logs all communications
def log_communication(self, from_agent, to_agent, message):
    log_entry = {
        "timestamp": datetime.now(),
        "from": from_agent,
        "to": to_agent,
        "message_type": message.get("type"),
        "message": message
    }
    self.communication_log.append(log_entry)
```

#### 2. ML Model Integration

```python
# Decision Agent loads and uses ML model
def predict(self, features):
    if self.model is None:
        return random_prediction()
    return self.model.predict(features)[0]
```

#### 3. Database Integration

```python
# Execution Agent saves to SQLite
def execute_trade(self, decision):
    # Execute trade logic
    self.db_manager.add_trade(
        user_id, ticker, action, shares, price, total, balance, confidence
    )
```

#### 4. Real-time Data Fetching

```python
# Market Agent gets live data
stock = yf.Ticker(self.ticker)
df = stock.history(period=period, interval=interval)
current_price = df['Close'].iloc[-1]
```

### File Structure

```
project/
├── agents/
│   ├── market_monitor.py      # Market data fetching
│   ├── decision_agent.py      # AI decision making
│   ├── execution_agent.py     # Trade execution
│   └── coordinator.py         # Agent coordination
├── auth/
│   ├── auth_manager.py        # JWT & authentication
│   └── middleware.py         # Auth middleware
├── database/
│   └── db_manager.py          # SQLite operations
├── models/
│   ├── train_model.py         # ML training
│   └── model.pkl              # Trained model
├── ui/
│   └── app.py                 # Streamlit interface
├── data/
│   └── trading_system.db      # SQLite database
└── requirements.txt           # Dependencies
```

### Development Challenges

1. **Agent Synchronization**: Implemented coordinator pattern for sequential execution
2. **Data Consistency**: Used SQLite transactions for portfolio updates
3. **Model Loading**: Implemented lazy loading with fallback to random predictions
4. **User Isolation**: Database queries filtered by user_id for security
5. **Real-time Updates**: Streamlit rerun mechanism for live updates

---

## Results / What Happened

### System Functionality

**✅ Successfully Implemented:**

1. **Multi-Agent Architecture**
   - Three specialized agents working independently
   - Coordinator managing communication
   - Sequential message passing working correctly

2. **Real-time Data Integration**
   - Successfully fetching data from Yahoo Finance
   - Technical indicators calculated accurately
   - Data updates in real-time

3. **ML Model Integration**
   - Model training functional
   - Price predictions generated
   - Decision logic working (BUY/SELL/HOLD)

4. **User Authentication**
   - JWT tokens working
   - User registration and login functional
   - Session management implemented

5. **Database Operations**
   - SQLite database created automatically
   - User portfolios isolated
   - Trade history persisted

6. **Web Interface**
   - All pages functional
   - Real-time updates working
   - Charts and visualizations displaying correctly

### Test Results

**ML Model Performance (AAPL, Random Forest, 2 years data):**
- Train R²: ~0.95-0.98
- Test R²: ~0.85-0.92
- MAE: ~$1-3
- RMSE: ~$2-5

**System Performance:**
- Agent cycle execution: < 5 seconds
- Data fetching: < 2 seconds
- Model prediction: < 0.1 seconds
- Database operations: < 0.1 seconds

**User Experience:**
- Automatic system initialization working
- Real-time data updates functional
- Portfolio tracking accurate
- Trade history complete

### Example Execution

**Cycle 1:**
- Ticker: AAPL
- Current Price: $175.50
- Predicted Price: $178.00 (+1.4%)
- Decision: BUY
- Action: Purchased 5 shares at $175.50
- Balance: $9,122.50

**Cycle 2:**
- Ticker: AAPL
- Current Price: $177.20
- Predicted Price: $176.50 (-0.4%)
- Decision: HOLD
- Action: No trade executed

**Cycle 3:**
- Ticker: AAPL
- Current Price: $179.00
- Predicted Price: $175.00 (-2.2%)
- Decision: SELL
- Action: Sold 2 shares at $179.00
- Balance: $9,480.50

### Metrics Collected

- **Total Trades**: Varies by user activity
- **Success Rate**: Depends on model accuracy
- **Portfolio Performance**: Tracked via P&L
- **Agent Communication**: All logged successfully
- **System Uptime**: Stable during testing

---

## What Worked & What Didn't

### ✅ What Worked Well

1. **Multi-Agent Architecture**
   - Clean separation of concerns
   - Easy to extend with new agents
   - Coordinator pattern effective

2. **Real-time Data Integration**
   - Yahoo Finance API reliable
   - Data fetching fast and accurate
   - Technical indicators calculated correctly

3. **ML Model Integration**
   - Model training straightforward
   - Predictions generated successfully
   - Decision logic working as expected

4. **User Authentication**
   - JWT tokens secure and functional
   - User isolation working
   - Session management stable

5. **Database Design**
   - SQLite simple and effective
   - Schema supports all requirements
   - Queries performant

6. **Web Interface**
   - Streamlit easy to use
   - Real-time updates working
   - Visualizations clear and informative

7. **Automatic Initialization**
   - System initializes automatically
   - No manual intervention needed
   - User experience improved

### ❌ What Didn't Work / Challenges

1. **Model Accuracy**
   - **Issue**: Model predictions sometimes inaccurate
   - **Reason**: Market is inherently unpredictable
   - **Impact**: Some trading decisions suboptimal
   - **Solution**: Used threshold-based decisions (2%) to reduce false signals

2. **Data Delays**
   - **Issue**: Yahoo Finance data has 15-20 minute delay
   - **Reason**: Free API limitations
   - **Impact**: Not truly "real-time"
   - **Solution**: Acceptable for simulation purposes

3. **Model Training Time**
   - **Issue**: Training takes 1-2 minutes for 2 years of data
   - **Reason**: Feature calculation and model training
   - **Impact**: User must wait for training
   - **Solution**: Training happens once, model saved

4. **Limited to Single Stock**
   - **Issue**: System handles one ticker at a time
   - **Reason**: Design decision for simplicity
   - **Impact**: Cannot trade multiple stocks simultaneously
   - **Solution**: Can be extended in future

5. **No Risk Management**
   - **Issue**: No stop-loss or position sizing logic
   - **Reason**: Focus on agent communication
   - **Impact**: Portfolio can lose significant value
   - **Solution**: Can add risk management agent

6. **Streamlit Limitations**
   - **Issue**: Some UI limitations (e.g., complex layouts)
   - **Reason**: Streamlit framework constraints
   - **Impact**: Some features harder to implement
   - **Solution**: Acceptable for prototype

### Lessons Learned

1. **Agent Communication**: Coordinator pattern essential for managing complex interactions
2. **Data Quality**: Real-time data quality affects all downstream decisions
3. **Model Selection**: Random Forest better than Linear Regression for this use case
4. **User Experience**: Automatic initialization significantly improves UX
5. **Database Design**: Proper schema design crucial for scalability

---

## Conclusion & Future Ideas

### Conclusion

This project successfully demonstrates a **Multi-Agent Financial AI Trading System** with three specialized agents working together to make automated trading decisions. The system integrates real-time market data, machine learning predictions, and user-friendly interfaces.

**Key Achievements:**
- ✅ Implemented multi-agent architecture with clear separation of concerns
- ✅ Integrated real-time market data via Yahoo Finance API
- ✅ Developed ML-based price prediction system
- ✅ Created user authentication and personal portfolio management
- ✅ Built comprehensive web interface for system interaction
- ✅ Demonstrated effective agent communication and coordination

The system proves that multi-agent architectures are well-suited for financial trading applications, where different agents can specialize in data collection, analysis, and execution. The coordinator pattern effectively manages complex interactions between agents.

### Future Ideas & Improvements

**1. Enhanced ML Models**
- Implement deep learning models (LSTM, GRU) for time series prediction
- Add ensemble methods combining multiple models
- Implement reinforcement learning for strategy optimization
- Add sentiment analysis from news and social media

**2. Advanced Trading Strategies**
- Implement multiple trading strategies (momentum, mean reversion, etc.)
- Add risk management agent with stop-loss and position sizing
- Support for multiple stocks simultaneously
- Portfolio optimization algorithms

**3. Real-time Features**
- WebSocket connections for live price updates
- Real-time order execution (paper trading)
- Live market data feeds (paid APIs)
- Real-time notifications and alerts

**4. Enhanced User Features**
- Backtesting interface for strategy testing
- Performance analytics and reporting
- Social features (share strategies, leaderboards)
- Mobile app version

**5. System Improvements**
- Add more agents (Risk Management Agent, News Analysis Agent)
- Implement parallel agent execution
- Add agent learning capabilities
- Implement distributed architecture

**6. Advanced Analytics**
- Portfolio optimization algorithms
- Risk metrics (Sharpe ratio, maximum drawdown)
- Performance attribution analysis
- Strategy comparison tools

**7. Security & Scalability**
- Implement rate limiting
- Add API key management
- Support for multiple databases (PostgreSQL)
- Implement caching for performance

**8. Integration**
- Connect to real broker APIs (paper trading)
- Integrate with news APIs for sentiment
- Add economic calendar integration
- Support for cryptocurrency trading

---

## References

### Academic Papers

1. Wooldridge, M. (2009). *An Introduction to MultiAgent Systems*. John Wiley & Sons.

2. Russell, S., & Norvig, P. (2020). *Artificial Intelligence: A Modern Approach*. Pearson.

3. Murphy, K. P. (2012). *Machine Learning: A Probabilistic Perspective*. MIT Press.

4. Sutton, R. S., & Barto, A. G. (2018). *Reinforcement Learning: An Introduction*. MIT Press.

### Technical Documentation

5. Streamlit Documentation. (2024). *Streamlit - The fastest way to build and share data apps*. https://docs.streamlit.io/

6. yfinance Documentation. (2024). *yfinance - Yahoo Finance market data downloader*. https://github.com/ranaroussi/yfinance

7. scikit-learn Documentation. (2024). *Machine Learning in Python*. https://scikit-learn.org/stable/

8. SQLite Documentation. (2024). *SQLite - A self-contained, serverless database*. https://www.sqlite.org/docs.html

### Related Work

9. FIPA. (2002). *Foundation for Intelligent Physical Agents*. http://www.fipa.org/

10. Yahoo Finance. (2024). *Yahoo Finance - Stock Market Live, Quotes, Business & Finance News*. https://finance.yahoo.com/

11. JWT.io. (2024). *JSON Web Tokens - Introduction*. https://jwt.io/introduction

12. Plotly. (2024). *Plotly Python Graphing Library*. https://plotly.com/python/

### Tools & Libraries

13. pandas Development Team. (2024). *pandas - Python Data Analysis Library*. https://pandas.pydata.org/

14. NumPy Developers. (2024). *NumPy - The fundamental package for scientific computing*. https://numpy.org/

15. PyJWT. (2024). *PyJWT - Python implementation of JSON Web Token*. https://pyjwt.readthedocs.io/

---

## Extra Materials

### Screenshots

#### 1. System Overview Page
```
[Description: Screenshot showing Overview page with stock price chart, 
portfolio metrics, and technical indicators]
```

**Features visible:**
- Current stock price with change percentage
- Portfolio balance and value
- P&L metrics
- Price chart with MA5 and MA20
- Volume chart
- Holdings table

#### 2. Real-time Simulation Page
```
[Description: Screenshot showing agent cycle execution with logs from 
each agent and communication history]
```

**Features visible:**
- Market Agent data (ticker, price, timestamp)
- Decision Agent output (action, predicted price, confidence)
- Execution Agent result (status, action, message)
- Cycle history table
- Communication log

#### 3. ML Model Training Page
```
[Description: Screenshot showing model training interface with metrics 
and prediction comparison charts]
```

**Features visible:**
- Model training controls (ticker, model type, period)
- Performance metrics (MAE, RMSE, R²)
- Real vs predicted price comparison chart
- Prediction error chart

#### 4. Trade History Page
```
[Description: Screenshot showing trade history table and cumulative P&L chart]
```

**Features visible:**
- All trades table with details
- Cumulative P&L chart
- Trading statistics (total trades, buys, sells, current P&L)

#### 5. Database Status Page
```
[Description: Screenshot showing database connection info, table statistics, 
and user data]
```

**Features visible:**
- Database path and connection status
- SQLite version
- Table statistics
- User list
- SQL query interface

### Code Snippets

#### Agent Coordinator - Run Cycle
```python
def run_cycle(self) -> Dict:
    """Executes one complete system cycle"""
    try:
        # Step 1: Market Agent gets data
        market_data = self.market_agent.get_market_data(period="1mo", interval="1d")
        self.log_communication("MarketAgent", "DecisionAgent", market_data)
        
        # Step 2: Decision Agent makes decision
        decision = self.decision_agent.process_market_update(market_data)
        self.log_communication("DecisionAgent", "ExecutionAgent", decision)
        
        # Step 3: Execution Agent executes trade
        execution_result = self.execution_agent.execute_trade(decision)
        self.log_communication("ExecutionAgent", "UI", execution_result)
        
        return {
            "status": "success",
            "market_data": {...},
            "decision": {...},
            "execution": {...}
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

#### Decision Agent - Feature Extraction
```python
def extract_features(self, market_data: Dict) -> np.ndarray:
    """Extracts 16 features from market data"""
    features = []
    indicators = market_data.get("data", {}).get("indicators", {})
    
    # Technical indicators
    features.append(indicators.get("MA5", 0))
    features.append(indicators.get("MA20", 0))
    features.append(indicators.get("volatility", 0))
    
    # Returns
    features.append(indicators.get("returns", 0))
    features.append(indicators.get("returns_5", 0))
    features.append(indicators.get("returns_20", 0))
    
    # Ratios
    ma5 = indicators.get("MA5", 0) or 0
    ma20 = indicators.get("MA20", 0) or 0
    features.append(ma5 / ma20 if ma20 != 0 else 1.0)
    
    # ... (additional features)
    
    return np.array(features).reshape(1, -1)
```

#### Execution Agent - Trade Execution
```python
def execute_trade(self, decision_data: Dict) -> Dict:
    """Executes trade based on decision"""
    decision = decision_data.get("decision")
    ticker = decision_data.get("ticker")
    current_price = decision_data.get("current_price", 0)
    
    if decision == "BUY":
        available_cash = self.balance * 0.1  # 10% of balance
        shares = int(available_cash / current_price)
        
        if shares > 0:
            cost = shares * current_price
            self.balance -= cost
            # Update portfolio in database
            self.db_manager.add_trade(...)
            return {"status": "success", "action": "BUY", ...}
    
    elif decision == "SELL":
        # Sell 50% of holdings
        # Update database
        return {"status": "success", "action": "SELL", ...}
    
    return {"status": "hold"}
```

### System Architecture Diagram (ASCII)

```
                    ┌─────────────────┐
                    │   Streamlit UI   │
                    │   (ui/app.py)    │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │   Coordinator  │
                    │  (Orchestrator)│
                    └───┬──────┬──────┘
                        │      │      │
            ┌────────────┘      │      └────────────┐
            │                  │                  │
    ┌───────▼──────┐  ┌───────▼──────┐  ┌───────▼──────┐
    │   Market     │  │   Decision   │  │  Execution   │
    │   Agent      │  │   Agent      │  │   Agent      │
    └───────┬──────┘  └───────┬──────┘  └───────┬──────┘
            │                  │                  │
    ┌───────▼──────┐  ┌───────▼──────┐  ┌───────▼──────┐
    │ Yahoo Finance│  │  ML Model    │  │  SQLite DB   │
    │     API      │  │ (model.pkl)  │  │  (Portfolio) │
    └──────────────┘  └──────────────┘  └──────────────┘
```

### Database Schema (SQL)

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Portfolios table
CREATE TABLE portfolios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    balance REAL DEFAULT 10000.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id)
);

-- Holdings table
CREATE TABLE holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    shares INTEGER NOT NULL,
    avg_price REAL NOT NULL,
    total_cost REAL NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, ticker)
);

-- Trade history table
CREATE TABLE trade_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    ticker TEXT NOT NULL,
    action TEXT NOT NULL,
    shares INTEGER NOT NULL,
    price REAL NOT NULL,
    total REAL NOT NULL,
    balance_after REAL NOT NULL,
    confidence REAL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Message Flow Example

```
Cycle Execution Log:

[10:00:00] Market Agent → Decision Agent
  Type: market_update
  Ticker: AAPL
  Current Price: $175.50
  Indicators: MA5=$174.20, MA20=$172.50

[10:00:01] Decision Agent → Execution Agent
  Type: trading_decision
  Decision: BUY
  Current Price: $175.50
  Predicted Price: $178.00
  Confidence: 1.4%

[10:00:02] Execution Agent → UI
  Type: execution_result
  Status: success
  Action: BUY
  Shares: 5
  Price: $175.50
  Message: "Bought 5 shares of AAPL at $175.50"
```

### Performance Metrics Example

```
Model Performance (AAPL, Random Forest, 2 years):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Train MAE:    $1.23
Test MAE:     $2.45
Train RMSE:   $1.67
Test RMSE:    $3.12
Train R²:     0.9678
Test R²:      0.8923
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Installation Commands

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Train model (optional)
python models/train_model.py

# 4. Run application
streamlit run ui/app.py
```

---

## Appendix

### A. Complete File List

```
Inf 451 final/
├── agents/
│   ├── __init__.py
│   ├── coordinator.py         (147 lines)
│   ├── decision_agent.py      (224 lines)
│   ├── execution_agent.py     (415 lines)
│   └── market_monitor.py      (151 lines)
├── auth/
│   ├── __init__.py
│   ├── auth_manager.py        (181 lines)
│   └── middleware.py           (111 lines)
├── database/
│   ├── __init__.py
│   └── db_manager.py          (315 lines)
├── models/
│   ├── __init__.py
│   ├── train_model.py         (205 lines)
│   └── model.pkl              (binary)
├── ui/
│   └── app.py                 (987 lines)
├── data/
│   ├── history.csv
│   └── trading_system.db
├── requirements.txt
├── README.md
├── REPORT.md                  (this file)
└── run.py
```

### B. Dependencies

```
streamlit>=1.28.0
yfinance>=0.2.28
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
plotly>=5.15.0
joblib>=1.3.0
PyJWT>=2.8.0
bcrypt>=4.0.0
python-dotenv>=1.0.0
```

### C. System Requirements

- **Python**: 3.8 or higher
- **RAM**: Minimum 2GB
- **Storage**: 100MB for application + data
- **Internet**: Required for market data
- **Browser**: Modern browser for Streamlit

---

**End of Report**

---

*This report documents the complete implementation and analysis of the Multi-Agent Financial AI Trading System, demonstrating practical application of multi-agent systems, machine learning, and web technologies in financial trading scenarios.*


