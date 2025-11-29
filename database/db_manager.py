"""
Database Manager with SQLite
Работает как локально, так и на Streamlit Cloud
"""
import sqlite3
import os
import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime
import json


class DBManager:
    """Управление базой данных SQLite"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Инициализация DBManager
        
        Args:
            db_path: Путь к файлу БД (если None, используется дефолтный)
        """
        # Для Streamlit Cloud используем правильный путь
        if db_path is None:
            # Пробуем использовать .streamlit/ для постоянного хранения
            # или data/ для локальной разработки
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Создаем директорию если не существует
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            
            # Путь к БД
            self.db_path = os.path.join(data_dir, "trading_system.db")
        else:
            self.db_path = db_path
        
        # Инициализируем БД
        self.init_database()
    
    def get_connection(self):
        """Получает соединение с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Для доступа по имени колонок
        return conn
    
    def init_database(self):
        """Инициализирует таблицы БД"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица портфелей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                balance REAL DEFAULT 10000.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id)
            )
        """)
        
        # Таблица холдингов (акции в портфеле)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                shares INTEGER NOT NULL,
                avg_price REAL NOT NULL,
                total_cost REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, ticker)
            )
        """)
        
        # Таблица истории торгов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_history (
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
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ========== User Management ==========
    
    def create_user(self, username: str, password_hash: str, email: str = "") -> Optional[int]:
        """
        Создает нового пользователя
        
        Returns:
            ID созданного пользователя или None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO users (username, password_hash, email)
                VALUES (?, ?, ?)
            """, (username, password_hash, email))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Получает пользователя по username"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Получает пользователя по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    # ========== Portfolio Management ==========
    
    def create_portfolio(self, user_id: int, initial_balance: float = 10000.0) -> bool:
        """Создает портфель для пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO portfolios (user_id, balance)
                VALUES (?, ?)
            """, (user_id, initial_balance))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def get_portfolio(self, user_id: int) -> Optional[Dict]:
        """Получает портфель пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM portfolios WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def update_portfolio_balance(self, user_id: int, new_balance: float) -> bool:
        """Обновляет баланс портфеля"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE portfolios 
            SET balance = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (new_balance, user_id))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def get_holdings(self, user_id: int) -> List[Dict]:
        """Получает все холдинги пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM holdings WHERE user_id = ?
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_holding(self, user_id: int, ticker: str, shares: int, 
                      avg_price: float, total_cost: float) -> bool:
        """Обновляет или создает холдинг"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Проверяем, существует ли холдинг
        cursor.execute("""
            SELECT * FROM holdings WHERE user_id = ? AND ticker = ?
        """, (user_id, ticker))
        
        existing = cursor.fetchone()
        
        if existing:
            # Обновляем существующий
            cursor.execute("""
                UPDATE holdings 
                SET shares = ?, avg_price = ?, total_cost = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND ticker = ?
            """, (shares, avg_price, total_cost, user_id, ticker))
        else:
            # Создаем новый
            cursor.execute("""
                INSERT INTO holdings (user_id, ticker, shares, avg_price, total_cost)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, ticker, shares, avg_price, total_cost))
        
        conn.commit()
        conn.close()
        return True
    
    def delete_holding(self, user_id: int, ticker: str) -> bool:
        """Удаляет холдинг"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM holdings WHERE user_id = ? AND ticker = ?
        """, (user_id, ticker))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    # ========== Trade History ==========
    
    def add_trade(self, user_id: int, ticker: str, action: str, 
                  shares: int, price: float, total: float, 
                  balance_after: float, confidence: float = 0.0) -> bool:
        """Добавляет сделку в историю"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trade_history 
            (user_id, timestamp, ticker, action, shares, price, total, balance_after, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, datetime.now().isoformat(), ticker, action, shares, 
              price, total, balance_after, confidence))
        
        conn.commit()
        conn.close()
        return True
    
    def get_trade_history(self, user_id: int) -> pd.DataFrame:
        """Получает историю торгов пользователя"""
        conn = self.get_connection()
        
        query = """
            SELECT * FROM trade_history 
            WHERE user_id = ?
            ORDER BY timestamp DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()
        
        return df
    
    def get_trade_history_count(self, user_id: int) -> int:
        """Получает количество сделок пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM trade_history WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        
        return count

