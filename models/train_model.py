"""
Training script for ML model
Создает и обучает модель для предсказания цен акций
"""
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Создает признаки для ML-модели
    
    Args:
        df: DataFrame с данными рынка
    
    Returns:
        DataFrame с признаками
    """
    # Копируем данные
    data = df.copy()
    
    # Технические индикаторы
    data['MA5'] = data['Close'].rolling(window=5).mean()
    data['MA20'] = data['Close'].rolling(window=20).mean()
    data['MA50'] = data['Close'].rolling(window=50).mean()
    
    # Returns
    data['Returns'] = data['Close'].pct_change()
    data['Returns_5'] = data['Returns'].rolling(window=5).mean()
    data['Returns_20'] = data['Returns'].rolling(window=20).mean()
    
    # Volatility
    data['Volatility'] = data['Returns'].rolling(window=20).std()
    
    # Price ratios
    data['MA5_MA20_ratio'] = data['MA5'] / data['MA20']
    data['Price_MA20_ratio'] = data['Close'] / data['MA20']
    data['Price_MA50_ratio'] = data['Close'] / data['MA50']
    
    # Тренд и импульс (важно для предсказания роста)
    data['Trend'] = (data['Close'] - data['Close'].shift(5)) / data['Close'].shift(5)  # 5-дневный тренд
    data['Momentum'] = data['Close'] / data['Close'].shift(10) - 1  # 10-дневный импульс
    
    # Volume indicators
    data['Volume_MA'] = data['Volume'].rolling(window=20).mean()
    data['Volume_ratio'] = data['Volume'] / data['Volume_MA']
    
    # High-Low spread
    data['HL_spread'] = (data['High'] - data['Low']) / data['Close']
    
    # RSI (Relative Strength Index) - индикатор силы тренда
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # Target: будущая цена (сдвигаем на 1 день вперед)
    data['Future_Price'] = data['Close'].shift(-1)
    
    return data


def prepare_training_data(ticker: str = "AAPL", period: str = "2y") -> tuple:
    """
    Подготавливает данные для обучения
    
    Args:
        ticker: Тикер акции
        period: Период данных
    
    Returns:
        Кортеж (X, y) - признаки и целевая переменная
    """
    print(f"Downloading data for {ticker}...")
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    
    if df.empty:
        raise ValueError(f"No data available for {ticker}")
    
    print(f"Data shape: {df.shape}")
    
    # Создаем признаки
    df = create_features(df)
    
    # Удаляем строки с NaN
    df = df.dropna()
    
    # Выбираем признаки для модели
    feature_columns = [
        'MA5', 'MA20', 'Volatility',
        'Returns', 'Returns_5', 'Returns_20',
        'MA5_MA20_ratio', 'Price_MA20_ratio', 'Price_MA50_ratio',
        'Trend', 'Momentum',  # Добавлены тренд и импульс
        'Volume_ratio', 'HL_spread',
        'RSI',  # Добавлен RSI
        'Close'
    ]
    
    # Добавляем последние 5 значений Returns как отдельные признаки
    for i in range(5):
        df[f'Return_lag_{i+1}'] = df['Returns'].shift(i+1)
        feature_columns.append(f'Return_lag_{i+1}')
    
    # Удаляем NaN после добавления lag features
    df = df.dropna()
    
    X = df[feature_columns].values
    y = df['Future_Price'].values
    dates = df.index.values  # Сохраняем даты
    
    print(f"Features shape: {X.shape}")
    print(f"Target shape: {y.shape}")
    
    return X, y, feature_columns, dates


def train_model(ticker: str = "AAPL", model_type: str = "random_forest", 
                period: str = "2y", test_size: float = 0.2):
    """
    Обучает модель
    
    Args:
        ticker: Тикер акции
        model_type: Тип модели ("random_forest" или "linear")
        period: Период данных для обучения
        test_size: Доля тестовых данных
    
    Returns:
        Обученная модель и метрики
    """
    # Подготавливаем данные
    X, y, feature_columns, dates = prepare_training_data(ticker, period)
    
    # Разделяем на train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, shuffle=False
    )
    
    # Разделяем даты соответственно
    dates_train, dates_test = train_test_split(
        dates, test_size=test_size, random_state=42, shuffle=False
    )
    
    print(f"Train size: {X_train.shape[0]}, Test size: {X_test.shape[0]}")
    
    # Выбираем модель
    if model_type == "random_forest":
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=5,  # Уменьшено с 10 до 5 для предотвращения переобучения
            min_samples_split=10,  # Минимум примеров для разделения узла
            min_samples_leaf=5,  # Минимум примеров в листе
            max_features='sqrt',  # Ограничение признаков для каждого дерева
            random_state=42,
            n_jobs=-1
        )
    elif model_type == "linear":
        model = LinearRegression()
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Обучаем модель
    print("Training model...")
    model.fit(X_train, y_train)
    
    # Предсказания
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # Метрики
    train_mae = mean_absolute_error(y_train, y_train_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    train_r2 = r2_score(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    
    metrics = {
        "train_mae": train_mae,
        "test_mae": test_mae,
        "train_rmse": train_rmse,
        "test_rmse": test_rmse,
        "train_r2": train_r2,
        "test_r2": test_r2,
        "feature_columns": feature_columns
    }
    
    print("\n=== Model Performance ===")
    print(f"Train MAE: ${train_mae:.2f}")
    print(f"Test MAE: ${test_mae:.2f}")
    print(f"Train RMSE: ${train_rmse:.2f}")
    print(f"Test RMSE: ${test_rmse:.2f}")
    print(f"Train R²: {train_r2:.4f}")
    print(f"Test R²: {test_r2:.4f}")
    
    # Сохраняем модель
    os.makedirs("models", exist_ok=True)
    model_path = "models/model.pkl"
    joblib.dump(model, model_path)
    print(f"\nModel saved to {model_path}")
    
    return model, metrics, (X_test, y_test, y_test_pred, dates_test)


if __name__ == "__main__":
    # Обучаем модель на данных AAPL
    print("=" * 50)
    print("Training ML Model for Trading System")
    print("=" * 50)
    
    model, metrics, test_data = train_model(
        ticker="AAPL",
        model_type="random_forest",
        period="2y"
    )
    
    print("\nTraining completed!")

