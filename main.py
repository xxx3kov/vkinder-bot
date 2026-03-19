from bot.handlers import VKinderBot
from database.db_session import init_db
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    """Основная функция запуска бота"""
    try:
        # Инициализация базы данных
        print("Инициализация базы данных...")
        init_db()
        print("База данных готова")

        # Запуск бота
        print("Запуск VKinder бота...")
        bot = VKinderBot()
        bot.run()

    except KeyboardInterrupt:
        print("\nБот остановлен пользователем")
    except Exception as e:
        print(f"Ошибка: {e}")
        logging.error(f"Ошибка: {e}")


if __name__ == "__main__":
    main()
