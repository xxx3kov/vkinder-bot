
import sys
import os
import tempfile
from pathlib import Path

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.db_session import init_db, save_favorite, get_favorites, DATABASE


def test_favorites():
    """Тестирование работы избранного"""
    print("\n" + "=" * 50)
    print("ТЕСТ 3: Избранное")
    print("=" * 50)

    # Создаем временную базу данных
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()

    # Сохраняем оригинальный путь
    original_db = DATABASE

    try:
        # Подменяем путь к БД
        import database.db_session as db_module
        db_module.DATABASE = temp_db.name

        # Инициализация БД
        print("1. Инициализация базы данных...")
        init_db()
        print("   ✅ База данных готова")

        user_id = 12345

        # 2. Сохранение первого профиля
        print("2. Сохранение первого профиля...")
        profile1 = {
            "id": 789012,
            "first_name": "Анна",
            "last_name": "Иванова",
            "city": {"title": "Москва"},
            "age": 25
        }
        save_favorite(user_id, profile1)
        favorites = get_favorites(user_id)
        assert len(favorites) == 1, "Должен быть 1 профиль"
        print("   ✅ Первый профиль сохранен")

        # 3. Сохранение второго профиля
        print("3. Сохранение второго профиля...")
        profile2 = {
            "id": 345678,
            "first_name": "Елена",
            "last_name": "Сидорова",
            "city": {"title": "СПб"},
            "age": 28
        }
        save_favorite(user_id, profile2)
        favorites = get_favorites(user_id)
        assert len(favorites) == 2, "Должно быть 2 профиля"
        print("   ✅ Второй профиль сохранен")

        # 4. Проверка сохраненных данных
        print("4. Проверка сохраненных данных...")
        ids = [f["id"] for f in favorites]
        assert 789012 in ids, "Первый профиль не найден"
        assert 345678 in ids, "Второй профиль не найден"
        print("   ✅ Оба профиля найдены")

        # 5. Проверка содержимого
        print("5. Проверка содержимого профилей...")
        for fav in favorites:
            if fav["id"] == 789012:
                assert fav["first_name"] == "Анна", "Имя не совпадает"
                assert fav["last_name"] == "Иванова", "Фамилия не совпадает"
                print("   ✅ Профиль Анны проверен")
            elif fav["id"] == 345678:
                assert fav["first_name"] == "Елена", "Имя не совпадает"
                assert fav["last_name"] == "Сидорова", "Фамилия не совпадает"
                print("   ✅ Профиль Елены проверен")

        print("\n🎉 Тест избранного пройден успешно!")
        return True

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Восстанавливаем оригинальный путь
        db_module.DATABASE = original_db
        # Удаляем временный файл
        try:
            os.unlink(temp_db.name)
            print("\n🧹 Временная БД удалена")
        except:
            pass


if __name__ == "__main__":
    success = test_favorites()
    sys.exit(0 if success else 1)