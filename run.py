#!/usr/bin/env python3
"""
Quick start script for the Multi-Agent Trading System
"""
import subprocess
import sys
import os

def main():
    """Запускает Streamlit приложение"""
    app_path = os.path.join(os.path.dirname(__file__), "ui", "app.py")
    
    if not os.path.exists(app_path):
        print(f"Error: {app_path} not found!")
        sys.exit(1)
    
    print("=" * 50)
    print("Multi-Agent Financial AI Trading System")
    print("=" * 50)
    print("\nЗапуск веб-интерфейса...")
    print("Приложение откроется в браузере автоматически.")
    print("Для остановки нажмите Ctrl+C\n")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])
    except KeyboardInterrupt:
        print("\n\nПриложение остановлено.")
    except Exception as e:
        print(f"\nОшибка при запуске: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

