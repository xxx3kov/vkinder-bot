from bot.handlers import VKinderBot
from database.db_session import init_db
import logging

from bot.handlers import VKinderBot
from database.db_session import init_db


import sys
import os

# Добавляем корень проекта в путь
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from vkinder_bot.bot.handlers import VKinderBot
from database.db_session import init_db


def main():
    print("Инициализация базы данных...")
    init_db()
    print("База данных готова")

    print("Запуск VKinder бота...")
    bot = VKinderBot()
    bot.run()


if __name__ == "__main__":
    main()