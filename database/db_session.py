"""
Модуль для управления сессиями SQLAlchemy.

Обеспечивает создание и управление сессиями БД с использованием
паттерна Thread-Local для безопасной работы в многопоточной среде.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DSN
from database.models import Base

engine = create_engine(DSN)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Создать все таблицы в БД"""
    # Base.metadata.drop_all(engine)  # удалить все таблицы, удаляется при
    # каждом запуске, если не закомментировать
    # print("Таблицы удалены")
    Base.metadata.create_all(engine)
    print(f"Созданы таблицы: {list(Base.metadata.tables.keys())}")


def get_db():
    """Функция для получения сессии"""
    db = SessionLocal()
    # logger.info("Сессия запущена успешно")
    return db
