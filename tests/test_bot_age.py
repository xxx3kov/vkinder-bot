
import sys
from pathlib import Path

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from vkinder_bot.bot.handlers import VKinderBot


def test_calculate_age():
    """Тест: правильно ли рассчитывается возраст"""

    bot = VKinderBot()

    # Тест 1: Полная дата рождения
    age_full = bot.calculate_age("15.03.1990")
    assert isinstance(age_full, int), "Возраст должен быть числом"
    assert age_full > 0, "Возраст должен быть положительным"
    print(f"✅ Тест 1 пройден: возраст {age_full} лет для даты 15.03.1990")

    # Тест 2: Неполная дата (только день и месяц)
    age_partial = bot.calculate_age("15.03")
    assert age_partial == 25, "Для неполной даты должен возвращаться возраст 25"
    print(f"✅ Тест 2 пройден: для неполной даты возраст = {age_partial}")

    # Тест 3: Пустая дата
    age_empty = bot.calculate_age("")
    assert age_empty == 25, "Для пустой даты должен возвращаться возраст 25"
    print(f"✅ Тест 3 пройден: для пустой даты возраст = {age_empty}")

    # Тест 4: None
    age_none = bot.calculate_age(None)
    assert age_none == 25, "Для None должен возвращаться возраст 25"
    print(f"✅ Тест 4 пройден: для None возраст = {age_none}")

    print("\n🎉 Все тесты расчета возраста пройдены!")


if __name__ == "__main__":
    test_calculate_age()