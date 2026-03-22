
import sys
import os
import tempfile
from pathlib import Path

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.db_session import init_db, set_user_state, get_user_state, DATABASE


def test_database_save_and_load():
    """Тест: сохранить состояние пользователя и загрузить его"""
    
    # Создаем временную базу данных
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    
    # Сохраняем оригинальный путь к БД
    original_db = DATABASE
    
    try:
        # Подменяем путь к БД на временный
        import database.db_session as db_module
        db_module.DATABASE = temp_db.name
        
        # Инициализируем базу данных
        init_db()
        
        # Сохраняем состояние пользователя
        user_id = 12345
        state = "searching"
        set_user_state(user_id, state)
        
        # Загружаем состояние пользователя
        loaded_state = get_user_state(user_id)
        
        # Проверяем, что сохранилось корректно
        assert loaded_state == state, f"Ожидалось {state}, получено {loaded_state}"
        
        print(f"✅ Тест пройден: состояние '{state}' успешно сохранено и загружено")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        raise
    finally:
        # Восстанавливаем оригинальный путь к БД
        db_module.DATABASE = original_db
        # Удаляем временный файл
        try:
            os.unlink(temp_db.name)
        except:
            pass


if __name__ == "__main__":
    test_database_save_and_load()