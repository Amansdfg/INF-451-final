"""
Middleware для проверки авторизации в Streamlit
"""
import streamlit as st
from typing import Optional, Callable
from .auth_manager import AuthManager


def require_auth(func: Callable) -> Callable:
    """
    Декоратор для защиты страниц Streamlit
    
    Args:
        func: Функция страницы Streamlit
        
    Returns:
        Обернутая функция с проверкой авторизации
    """
    def wrapper(*args, **kwargs):
        auth_manager = AuthManager()
        user = auth_manager.get_current_user_from_session()
        
        if not user:
            # Показываем страницу логина
            show_login_page()
            return
        
        # Пользователь авторизован, выполняем функцию
        return func(*args, **kwargs)
    
    return wrapper


def get_current_user() -> Optional[dict]:
    """
    Получает текущего авторизованного пользователя
    
    Returns:
        Словарь с username и user_id или None
    """
    auth_manager = AuthManager()
    return auth_manager.get_current_user_from_session()


def show_login_page():
    """Показывает страницу логина"""
    st.title("🔐 Авторизация")
    
    tab1, tab2 = st.tabs(["Вход", "Регистрация"])
    
    with tab1:
        st.subheader("Вход в систему")
        with st.form("login_form"):
            username = st.text_input("Имя пользователя")
            password = st.text_input("Пароль", type="password")
            submit = st.form_submit_button("Войти")
            
            if submit:
                if username and password:
                    # Импортируем здесь, чтобы избежать циклических импортов
                    from database.db_manager import DBManager
                    db_manager = DBManager()
                    auth_manager = AuthManager()
                    
                    result = auth_manager.login(username, password, db_manager)
                    if result:
                        st.session_state.token = result["token"]
                        st.session_state.username = result["username"]
                        st.session_state.user_id = result["user_id"]
                        st.session_state.authenticated = True
                        st.success("Успешный вход!")
                        st.rerun()
                    else:
                        st.error("Неверное имя пользователя или пароль")
                else:
                    st.warning("Заполните все поля")
    
    with tab2:
        st.subheader("Регистрация")
        with st.form("register_form"):
            new_username = st.text_input("Имя пользователя", key="reg_username")
            new_email = st.text_input("Email", key="reg_email")
            new_password = st.text_input("Пароль", type="password", key="reg_password")
            confirm_password = st.text_input("Подтвердите пароль", type="password", key="reg_confirm")
            submit_reg = st.form_submit_button("Зарегистрироваться")
            
            if submit_reg:
                if new_username and new_email and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("Пароли не совпадают")
                    elif len(new_password) < 6:
                        st.warning("Пароль должен содержать минимум 6 символов")
                    else:
                        from database.db_manager import DBManager
                        db_manager = DBManager()
                        auth_manager = AuthManager()
                        
                        result = auth_manager.register(new_username, new_password, new_email, db_manager)
                        if result:
                            st.session_state.token = result["token"]
                            st.session_state.username = result["username"]
                            st.session_state.user_id = result["user_id"]
                            st.session_state.authenticated = True
                            st.success("Регистрация успешна! Вы вошли в систему.")
                            st.rerun()
                        else:
                            st.error("Пользователь с таким именем уже существует")
                else:
                    st.warning("Заполните все поля")

