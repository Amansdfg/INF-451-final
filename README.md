# Multi-Agent Financial AI Trading System

## 📋 What the project is about

**Multi-Agent Financial AI Trading System** is an automated trading system based on a multi-agent architecture that uses AI to make trading decisions. The project demonstrates coordination and communication between three specialized agents for market monitoring, decision-making, and trade execution.

### Key Features:
- ✅ **Real market data** via Yahoo Finance API
- ✅ **AI-powered predictions** using ML models (Random Forest / Linear Regression)
- ✅ **Automated decision-making** for buying/selling stocks
- ✅ **Trading simulation** with portfolio management
- ✅ **Web interface** for monitoring and control
- ✅ **User authentication** with JWT tokens
- ✅ **Personal portfolios** for each user (SQLite database)
- ✅ **Multi-agent coordination** with communication logging

### Project Goal:
Demonstrate coordination and communication between specialized agents for automated trading decisions based on real market data and AI predictions.

---

## 🤖 What each agent does

### Agent 1: Market Monitoring Agent (`agents/market_monitor.py`)

**Role:** Fetch and process market data

**Responsibilities:**
- Retrieves real-time market data via Yahoo Finance API (`yfinance`)
- Calculates technical indicators:
  - MA5, MA20 (moving averages)
  - Volatility (standard deviation of returns)
  - Returns (price changes)
  - Volume ratios
  - High-Low spread
- Formats structured message for Decision-Making Agent
- Maintains data update history

**Input:** Stock ticker (e.g., "AAPL")
**Output:** Dictionary with market data and technical indicators

**Key Methods:**
- `get_market_data()`: Fetches and processes market data
- `get_dataframe()`: Returns data as pandas DataFrame for visualization
- `get_latest_price()`: Gets current stock price

---

### Agent 2: Decision-Making Agent (`agents/decision_agent.py`)

**Role:** Make trading decisions based on AI model predictions

**Responsibilities:**
- Extracts 16 features from market data:
  - Technical indicators (MA5, MA20, Volatility)
  - Returns (current and historical)
  - Ratios (MA5/MA20, Price/MA20)
  - Volume and High-Low spread
  - Lag features (last 5 return values)
- Loads trained ML model (`models/model.pkl`)
- Predicts future stock price using ML model
- Makes trading decision based on prediction:
  - **BUY**: if predicted price > current price + 2%
  - **SELL**: if predicted price < current price - 2%
  - **HOLD**: otherwise
- Maintains decision history

**Input:** Market data from Market Monitoring Agent
**Output:** Trading decision (BUY/SELL/HOLD) with confidence

**Key Methods:**
- `extract_features()`: Extracts 16 features from market data
- `predict()`: Predicts future price using ML model
- `decide()`: Makes BUY/SELL/HOLD decision
- `process_market_update()`: Main processing method

**Important:** If model is not trained, agent uses random predictions for demonstration.

---

### Agent 3: Execution Agent (`agents/execution_agent.py`)

**Role:** Execute trades and manage portfolio

**Responsibilities:**
- Executes trades based on Decision Agent's decisions:
  - **BUY**: Purchases stocks using 10% of current balance
  - **SELL**: Sells 50% of existing holdings
  - **HOLD**: No action taken
- Manages user portfolio:
  - Tracks balance
  - Manages holdings (stocks in portfolio)
  - Calculates average purchase price
- Saves all trades to SQLite database
- Provides portfolio summary (balance, value, P&L)

**Input:** Trading decision from Decision-Making Agent
**Output:** Execution result and updated portfolio state

**Key Methods:**
- `execute_trade()`: Executes trade based on decision
- `get_portfolio_summary()`: Returns portfolio statistics
- `get_trade_history()`: Returns all trades

---

### Agent Coordinator (`agents/coordinator.py`)

**Role:** Coordinate all agents' work

**Responsibilities:**
- Manages lifecycle of all agents
- Coordinates task execution sequence
- Logs all inter-agent communications
- Provides unified interface for web UI
- Handles errors and exceptions

**Key Methods:**
- `run_cycle()`: Executes one complete system cycle
- `get_communication_log()`: Returns all communication logs
- `get_trade_history()`: Returns trade history
- `get_market_dataframe()`: Gets market data for visualization

---

## 💬 How they communicate

### Communication Architecture

The system uses **sequential communication** through the coordinator:

```
Market Agent → Coordinator → Decision Agent → Coordinator → Execution Agent → Coordinator → UI
```

### Communication Flow

1. **Market Agent → Decision Agent**
   - Message type: `market_update`
   - Contains: ticker, current price, technical indicators, timestamp
   - Logged by Coordinator

2. **Decision Agent → Execution Agent**
   - Message type: `trading_decision`
   - Contains: decision (BUY/SELL/HOLD), current price, predicted price, confidence
   - Logged by Coordinator

3. **Execution Agent → UI**
   - Message type: `execution_result`
   - Contains: execution status, action taken, shares, price, message
   - Logged by Coordinator

### Message Format Examples

**Market Update:**
```python
{
    "type": "market_update",
    "ticker": "AAPL",
    "timestamp": "2024-11-29T10:00:00",
    "current_price": 175.50,
    "data": {
        "indicators": {
            "MA5": 174.20,
            "MA20": 172.50,
            "volatility": 0.02
        }
    }
}
```

**Trading Decision:**
```python
{
    "type": "trading_decision",
    "ticker": "AAPL",
    "decision": "BUY",
    "current_price": 175.50,
    "predicted_price": 178.00,
    "confidence": 0.014
}
```

**Execution Result:**
```python
{
    "type": "execution_result",
    "status": "success",
    "action": "BUY",
    "shares": 5,
    "price": 175.50,
    "message": "Bought 5 shares of AAPL at $175.50"
}
```

### Communication Logging

The Coordinator logs all communications with:
- **From**: Source agent name
- **To**: Destination agent name
- **Message Type**: Type of message
- **Timestamp**: When communication occurred
- **Full Message**: Complete message content

Access logs via: `coordinator.get_communication_log()`

---

## ⚙️ How the system works

### Complete System Cycle

**Step 1: Initialization**
1. User logs in (JWT authentication)
2. Portfolio created with initial balance $10,000
3. System automatically initializes with default ticker (AAPL)

**Step 2: User Triggers Cycle**
User clicks "Run Agent Cycle" on "Real-time Simulation" page

**Step 3: Market Monitoring Agent**
1. Requests data via `yfinance` for selected ticker
2. Receives historical data (Open, High, Low, Close, Volume)
3. Calculates technical indicators
4. Formats `market_update` message
5. Sends message through Coordinator to Decision Agent

**Step 4: Decision-Making Agent**
1. Receives `market_update` from Market Agent
2. Extracts 16 features from data
3. Loads ML model (if trained)
4. Predicts future price:
   - If model trained → uses ML prediction
   - If model not trained → random prediction (±2%)
5. Compares predicted price with current:
   - Difference > 2% → BUY
   - Difference < -2% → SELL
   - Otherwise → HOLD
6. Formats `trading_decision` message
7. Sends through Coordinator to Execution Agent

**Step 5: Execution Agent**
1. Receives `trading_decision` from Decision Agent
2. Executes operation:
   - **BUY**: Purchases stocks using 10% of balance
   - **SELL**: Sells 50% of existing holdings
   - **HOLD**: No action
3. Updates portfolio in SQLite database
4. Saves trade to trade history
5. Formats `execution_result` message
6. Sends through Coordinator to UI

**Step 6: Display Results**
1. UI receives cycle execution result
2. Displays:
   - Current stock price
   - AI decision (BUY/SELL/HOLD)
   - Predicted price
   - Trade execution result
   - Updated portfolio state

### Data Flow Diagram

```
User Input (Ticker)
    ↓
Market Agent → Real-time Market Data (Yahoo Finance)
    ↓
Technical Indicators Calculation
    ↓
Decision Agent → Feature Extraction (16 features)
    ↓
ML Model → Price Prediction
    ↓
Decision Logic → BUY/SELL/HOLD
    ↓
Execution Agent → Trade Execution
    ↓
Database Update (SQLite)
    ↓
UI Display → Results to User
```

### Data Storage

- **Users**: SQLite table `users`
- **Portfolios**: SQLite table `portfolios`
- **Holdings**: SQLite table `holdings`
- **Trade History**: SQLite table `trade_history`
- **ML Model**: File `models/model.pkl`

---

## 🚀 Instructions to run it

### Prerequisites

- Python 3.8 or higher
- Internet connection (for market data)

### Step 1: Install Dependencies

```bash
# Navigate to project directory
cd "/path/to/Inf 451 final"

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configuration (Optional)

For JWT authentication, create `.streamlit/secrets.toml`:

```toml
JWT_SECRET_KEY = "your-secret-key-here"
```

Or configure secrets in Streamlit Cloud when deploying.

### Step 3: Train ML Model (Recommended)

**Option A: Via Web Interface**
1. Run the application (see Step 4)
2. Go to "ML Model" page
3. Select ticker, model type, and data period
4. Click "Train Model"

**Option B: Via Command Line**
```bash
python models/train_model.py
```

### Step 4: Run the Application

**Option A: Using run.py**
```bash
python run.py
```

**Option B: Directly via Streamlit**
```bash
streamlit run ui/app.py
```

The application will open in your browser at: `http://localhost:8501`

### Step 5: Using the System

1. **Registration/Login:**
   - On first launch, register a new account
   - Login to the system

2. **Select Ticker:**
   - In sidebar, enter stock ticker (e.g., AAPL, TSLA, MSFT)
   - System automatically initializes

3. **Train Model (if not already trained):**
   - Go to "ML Model" page
   - Train model for selected ticker

4. **Run Agent Cycle:**
   - Go to "Real-time Simulation" page
   - Click "Run Agent Cycle"
   - Observe agents working

5. **View Results:**
   - **Overview**: Price charts, portfolio status
   - **Trade History**: All trades, P&L chart
   - **Database Status**: Database information

### Project Structure

```
Inf 451 final/
├── agents/              # System agents
│   ├── market_monitor.py
│   ├── decision_agent.py
│   ├── execution_agent.py
│   └── coordinator.py
├── auth/                # JWT authentication
│   ├── auth_manager.py
│   └── middleware.py
├── database/            # SQLite database
│   └── db_manager.py
├── models/              # ML model
│   ├── train_model.py
│   └── model.pkl
├── ui/                  # Web interface
│   └── app.py
├── data/                # Data (DB, history)
│   └── trading_system.db
├── requirements.txt     # Dependencies
└── run.py              # Launch script
```

### Deploy to Streamlit Cloud

1. Upload project to GitHub repository
2. Connect repository to Streamlit Cloud
3. Configure Secrets:
   - Add `JWT_SECRET_KEY` in app settings
4. Set Main file path: `ui/app.py`
5. Deploy application

### Troubleshooting

**Error "Model not found":**
- Train model on "ML Model" page

**Yahoo Finance connection error:**
- Check internet connection
- Verify ticker is correct

**Database error:**
- Ensure `data/` directory exists
- Check file permissions

---

## 📊 Web Interface Pages

### 1. Overview
- Current stock price
- Portfolio status
- Price and volume charts
- Holdings information
- **NEW**: Customizable data period (1 week to max)

### 2. Real-time Simulation
- Run agent cycles
- View agent logs
- Cycle history
- Agent communication log

### 3. ML Model
- Train model
- Performance metrics (MAE, RMSE, R²)
- Real vs predicted price comparison
- Prediction error chart

### 4. Trade History
- All trades table
- Cumulative P&L chart
- Trading statistics

### 5. Database Status
- Database connection info
- Table statistics
- User data
- SQL query interface

---

## 🤖 ML Model Details

### Features (16 total)

1. MA5 (5-day moving average)
2. MA20 (20-day moving average)
3. Volatility
4. Returns (current)
5. Returns_5 (5-day average)
6. Returns_20 (20-day average)
7. MA5_MA20_ratio
8. Price_MA20_ratio
9. Volume_ratio
10. HL_spread
11. Close (current price)
12-16. Return_lag_1 through Return_lag_5

### Model Types

1. **Random Forest Regressor**
   - More accurate predictions
   - Better with non-linear relationships
   - Recommended for production

2. **Linear Regression**
   - Faster training
   - Easier to interpret
   - Good for basic experiments

### Metrics

- **MAE (Mean Absolute Error)**: Average absolute error in dollars
- **RMSE (Root Mean Squared Error)**: Root mean squared error
- **R² (Coefficient of Determination)**: 0-1, higher is better

---

## 🛠️ Technologies

- **Python 3.8+**
- **Streamlit** - Web interface
- **yfinance** - Market data (Yahoo Finance API)
- **scikit-learn** - ML models
- **pandas** - Data processing
- **numpy** - Numerical computations
- **plotly** - Interactive charts
- **matplotlib** - Additional charts
- **PyJWT** - JWT authentication
- **bcrypt** - Password hashing
- **SQLite** - Database

---

## 📝 Important Notes

- System uses **simulation** - no real trades are executed
- Data fetched in real-time via Yahoo Finance API
- Model trained on historical data
- All trades logged to SQLite database
- Model saved in `models/model.pkl`
- Each user has isolated portfolio data

---

## 📄 License

This project is created for educational purposes as a final course project.

## 👤 Author

Final Project - Multi-Agent Financial AI Trading System

---

**Good luck with your project presentation! 🚀**
