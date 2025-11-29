#!/usr/bin/env python3
"""
Скрипт для проверки подключения к базе данных
Используйте для локальной проверки БД
"""
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DBManager
import sqlite3

def main():
    print("=" * 60)
    print("Проверка подключения к базе данных")
    print("=" * 60)
    print()
    
    # Создаем экземпляр DBManager
    try:
        db = DBManager()
        print(f"✅ DBManager создан")
        print(f"📁 Путь к БД: {db.db_path}")
        print(f"📂 Файл существует: {'✅ Да' if os.path.exists(db.db_path) else '❌ Нет'}")
        print()
    except Exception as e:
        print(f"❌ Ошибка при создании DBManager: {e}")
        return
    
    # Проверяем подключение
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Проверяем версию SQLite
        cursor.execute("SELECT sqlite_version()")
        sqlite_version = cursor.fetchone()[0]
        print(f"✅ Подключение успешно!")
        print(f"📊 SQLite версия: {sqlite_version}")
        print()
        
        # Получаем список таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"📋 Найдено таблиц: {len(tables)}")
        print()
        
        # Показываем статистику по каждой таблице
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            # Получаем структуру
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"  📊 {table_name}:")
            print(f"     - Записей: {count}")
            print(f"     - Колонок: {len(columns)}")
        
        print()
        
        # Показываем пользователей
        print("👥 Пользователи:")
        cursor.execute("SELECT id, username, email, created_at FROM users")
        users = cursor.fetchall()
        
        if users:
            for user in users:
                print(f"  - ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Created: {user[3]}")
        else:
            print("  (нет пользователей)")
        
        print()
        
        # Показываем портфели
        print("💰 Портфели:")
        cursor.execute("""
            SELECT p.user_id, u.username, p.balance, p.updated_at 
            FROM portfolios p 
            LEFT JOIN users u ON p.user_id = u.id
        """)
        portfolios = cursor.fetchall()
        
        if portfolios:
            for p in portfolios:
                username = p[1] or f"User ID {p[0]}"
                print(f"  - {username}: ${p[2]:.2f} (обновлен: {p[3]})")
        else:
            print("  (нет портфелей)")
        
        print()
        
        # Показываем статистику
        cursor.execute("SELECT COUNT(*) FROM trade_history")
        trade_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM holdings")
        holdings_count = cursor.fetchone()[0]
        
        print("📈 Статистика:")
        print(f"  - Всего сделок: {trade_count}")
        print(f"  - Всего холдингов: {holdings_count}")
        
        conn.close()
        print()
        print("✅ Проверка завершена успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при работе с БД: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

