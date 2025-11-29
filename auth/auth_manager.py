"""
Authentication Manager with JWT support
"""
import jwt
import bcrypt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
import streamlit as st


class AuthManager:
    """Управление аутентификацией и авторизацией с JWT"""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Инициализация AuthManager
        
        Args:
            secret_key: Секретный ключ для JWT (если None, используется из env или дефолтный)
        """
        # В продакшене используйте переменную окружения STREAMLIT_SECRETS или .streamlit/secrets.toml
        self.secret_key = secret_key or os.getenv(
            "JWT_SECRET_KEY", 
            "your-secret-key-change-in-production-2024"
        )
        self.algorithm = "HS256"
        self.token_expiry_days = 7
    
    def hash_password(self, password: str) -> str:
        """
        Хеширует пароль с помощью bcrypt
        
        Args:
            password: Пароль в открытом виде
            
        Returns:
            Хешированный пароль
        """
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Проверяет пароль против хеша
        
        Args:
            password: Пароль в открытом виде
            hashed: Хешированный пароль
            
        Returns:
            True если пароль верный
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    def generate_token(self, username: str, user_id: int) -> str:
        """
        Генерирует JWT токен для пользователя
        
        Args:
            username: Имя пользователя
            user_id: ID пользователя
            
        Returns:
            JWT токен
        """
        payload = {
            "username": username,
            "user_id": user_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=self.token_expiry_days)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Проверяет и декодирует JWT токен
        
        Args:
            token: JWT токен
            
        Returns:
            Payload токена или None если невалидный
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def login(self, username: str, password: str, db_manager) -> Optional[Dict]:
        """
        Выполняет вход пользователя
        
        Args:
            username: Имя пользователя
            password: Пароль
            db_manager: Экземпляр DBManager для проверки пользователя
            
        Returns:
            Словарь с токеном и информацией о пользователе или None
        """
        user = db_manager.get_user_by_username(username)
        if not user:
            return None
        
        if not self.verify_password(password, user['password_hash']):
            return None
        
        token = self.generate_token(username, user['id'])
        
        return {
            "token": token,
            "username": username,
            "user_id": user['id'],
            "email": user.get('email', '')
        }
    
    def register(self, username: str, password: str, email: str, db_manager) -> Optional[Dict]:
        """
        Регистрирует нового пользователя
        
        Args:
            username: Имя пользователя
            password: Пароль
            email: Email
            db_manager: Экземпляр DBManager
            
        Returns:
            Словарь с токеном и информацией о пользователе или None если ошибка
        """
        # Проверяем, существует ли пользователь
        if db_manager.get_user_by_username(username):
            return None  # Пользователь уже существует
        
        # Хешируем пароль
        password_hash = self.hash_password(password)
        
        # Создаем пользователя
        user_id = db_manager.create_user(username, password_hash, email)
        if not user_id:
            return None
        
        # Создаем начальный портфель
        db_manager.create_portfolio(user_id, initial_balance=10000.0)
        
        # Генерируем токен
        token = self.generate_token(username, user_id)
        
        return {
            "token": token,
            "username": username,
            "user_id": user_id,
            "email": email
        }
    
    def get_current_user_from_session(self) -> Optional[Dict]:
        """
        Получает текущего пользователя из Streamlit session state
        
        Returns:
            Информация о пользователе или None
        """
        if 'token' not in st.session_state:
            return None
        
        token = st.session_state.token
        payload = self.verify_token(token)
        
        if payload:
            return {
                "username": payload.get("username"),
                "user_id": payload.get("user_id")
            }
        return None

