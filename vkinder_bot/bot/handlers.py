import sys
import os
import json
import logging
from typing import Optional, Dict, Any, List

# Добавляем корень проекта в путь (важно сделать это до всех импортов)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Теперь можно импортировать database
from database.db_session import (
    get_user_state as db_get_state,
    set_user_state as db_set_state,
    get_user_data as db_get_data,
    set_user_data as db_set_data,
    save_favorite as db_save_favorite,
    get_favorites as db_get_favorites,
)

from config import VK_GROUP_TOKEN, VK_USER_TOKEN
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType
from vkinder_bot.bot.states import UserState

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Проверка наличия токенов
if not VK_GROUP_TOKEN:
    logger.error("❌ VK_GROUP_TOKEN не найден. Проверьте .env файл")
    raise ValueError("VK_GROUP_TOKEN не найден")

if not VK_USER_TOKEN:
    logger.error("❌ VK_USER_TOKEN не найден. Проверьте .env файл")
    raise ValueError("VK_USER_TOKEN не найден")

# Сессии API
try:
    user_vk_session = VkApi(token=VK_USER_TOKEN)
    user_api = user_vk_session.get_api()
    logger.info("✅ Пользовательская сессия VK создана")
except Exception as e:
    logger.error(f"❌ Ошибка создания пользовательской сессии: {e}")
    raise

try:
    bot_vk_session = VkApi(token=VK_GROUP_TOKEN)
    bot_api = bot_vk_session.get_api()
    longpoll = VkLongPoll(bot_vk_session)
    logger.info("✅ Бот-сессия VK создана")
except Exception as e:
    logger.error(f"❌ Ошибка создания бот-сессии: {e}")
    raise


class VKinderBot:
    def __init__(self):
        """Инициализация бота"""
        self.session = bot_vk_session
        self.vk = bot_api
        self.longpoll = longpoll
        logger.info("✅ VKinderBot инициализирован")

    def run(self):
        """Запуск прослушивания сообщений"""
        logger.info("✅ Бот запущен. Ожидание сообщений...")
        try:
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    self.handle_message(event.user_id, event.text)
        except Exception as e:
            logger.error(f"❌ Ошибка в цикле обработки сообщений: {e}")
            raise

    def handle_message(self, user_id: int, text: str):
        """Обработка команд пользователя"""
        text_lower = text.strip().lower()
        state = get_user_state(user_id)

        # Если пользователь только начал диалог и нет параметров
        if state == UserState.MAIN_MENU and text_lower not in ["старт", "start", "/start", "начать", "поиск", "🔍 поиск",
                                                               "найти"]:
            self.send_message(
                user_id,
                "👋 Привет! Я бот для знакомств VKinder.\n\n"
                "📝 Напишите **старт**, чтобы начать поиск.\n"
                "Или используйте кнопки меню 👇",
                keyboard=self.main_menu_keyboard()
            )
            return

        # Обработка команд
        if text_lower in ["старт", "start", "/start", "начать", "поиск", "🔍 поиск", "найти"]:
            self.get_user_info_and_start_search(user_id)

        elif text_lower in ["избранное", "❤️ избранное", "favorites", "избранные"] and state == UserState.MAIN_MENU:
            self.show_favorites(user_id)

        elif text_lower in ["дальше", "👎 дальше", "next", "пропустить"] and state == UserState.SEARCHING:
            self.find_next_person(user_id)

        elif text_lower in ["нравится", "❤️ нравится", "like", "добавить"] and state == UserState.SEARCHING:
            profile = get_user_state_data(user_id, "current_profile")
            if profile:
                save_favorite(user_id, profile)
                self.send_message(user_id, "❤️ Добавлено в избранное!", keyboard=self.search_keyboard())
            self.find_next_person(user_id)

        elif text_lower in ["назад", "↩️ назад", "back", "меню"]:
            self.send_message(user_id, "↩️ Возвращаемся в меню.", keyboard=self.main_menu_keyboard())
            set_user_state(user_id, UserState.MAIN_MENU)

        else:
            self.send_message(
                user_id,
                "❓ Неизвестная команда.\n\n"
                "📝 Доступные команды:\n"
                "• **старт** - начать поиск\n"
                "• **избранное** - показать избранных\n"
                "• **назад** - вернуться в меню\n\n"
                "Или используйте кнопки меню 👇",
                keyboard=self.main_menu_keyboard()
            )

    def get_user_info_and_start_search(self, user_id: int):
        """Получаем данные пользователя и начинаем поиск"""
        try:
            # Получаем информацию о пользователе
            response = user_api.users.get(
                user_ids=user_id,
                fields="sex,city,bdate,relation,country"
            )[0]

            logger.info(f"Получены данные пользователя {user_id}: {response}")

            # Проверяем наличие пола
            if not response.get('sex') or response['sex'] == 0:
                self.send_message(
                    user_id,
                    "⚠️ Укажите, пожалуйста, ваш пол в настройках профиля VK.\n"
                    "После этого напишите **старт** снова.\n\n"
                    "Как указать пол:\n"
                    "1. Зайдите в свой профиль VK\n"
                    "2. Нажмите «Редактировать»\n"
                    "3. Выберите пол\n"
                    "4. Сохраните изменения",
                    keyboard=self.main_menu_keyboard()
                )
                return

            # Рассчитываем возраст
            age = self.calculate_age(response.get('bdate'))

            # Если возраст не определен
            if not age:
                self.send_message(
                    user_id,
                    "⚠️ Укажите полную дату рождения в профиле VK для точного поиска.\n"
                    "Сейчас буду искать по умолчанию (25-35 лет).\n\n"
                    "Как указать дату рождения:\n"
                    "1. Зайдите в свой профиль VK\n"
                    "2. Нажмите «Редактировать»\n"
                    "3. Укажите день, месяц и год рождения\n"
                    "4. Сохраните изменения",
                    keyboard=self.main_menu_keyboard()
                )
                age = 25

            # Получаем информацию о городе
            city_id = response['city']['id'] if 'city' in response else None
            city_title = response['city']['title'] if 'city' in response else ""

            # Если город не указан
            if not city_title:
                self.send_message(
                    user_id,
                    "ℹ️ Город не указан в профиле. Поиск будет выполняться по всем городам.\n\n"
                    "Для более точного поиска укажите город в настройках профиля VK.",
                    keyboard=self.main_menu_keyboard()
                )

            sex = response.get('sex', 0)

            # Определяем противоположный пол
            search_sex = 1 if sex == 2 else 2 if sex == 1 else 1
            search_sex_text = "Девушек" if search_sex == 1 else "Парней"

            # Сохраняем параметры поиска
            search_params = {
                "age_from": max(18, age - 5),
                "age_to": min(65, age + 5),
                "sex": search_sex,
                "hometown": city_title,
                "city_id": city_id
            }

            set_user_state_data(user_id, "search_params", search_params)
            set_user_state(user_id, UserState.SEARCHING)

            # Отправляем подтверждение с параметрами
            self.send_message(
                user_id,
                f"✅ Параметры поиска установлены:\n\n"
                f"👤 Ваш пол: {'Мужской' if sex == 2 else 'Женский'}\n"
                f"🔍 Ищем: {search_sex_text}\n"
                f"📅 Возраст: от {search_params['age_from']} до {search_params['age_to']} лет\n"
                f"🏙 Город: {city_title if city_title else 'Любой'}\n\n"
                f"🔍 Начинаю поиск...",
                keyboard=self.search_keyboard()
            )

            self.find_next_person(user_id)

        except Exception as e:
            logger.error(f"❌ Ошибка получения данных пользователя {user_id}: {e}")
            self.send_message(
                user_id,
                "❌ Не удалось получить данные из профиля.\n\n"
                "Убедитесь, что:\n"
                "1️⃣ Ваш профиль открыт\n"
                "2️⃣ Указаны пол и дата рождения\n"
                "3️⃣ Город указан (необязательно)\n\n"
                "Напишите **старт** после исправления настроек.",
                keyboard=self.main_menu_keyboard()
            )
            set_user_state(user_id, UserState.MAIN_MENU)

    def find_next_person(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Поиск следующего подходящего пользователя"""
        try:
            # Получаем параметры поиска
            search_params = get_user_state_data(user_id, "search_params")

            if not search_params:
                logger.warning(f"Параметры поиска не найдены для user_id={user_id}")
                self.send_message(
                    user_id,
                    "❌ Не заданы параметры поиска.\n"
                    "Начните с команды **старт**.",
                    keyboard=self.main_menu_keyboard()
                )
                set_user_state(user_id, UserState.MAIN_MENU)
                return None

            # Проверяем обязательные параметры
            required_keys = ['age_from', 'age_to', 'sex']
            if not all(key in search_params for key in required_keys):
                logger.warning(f"Некорректные параметры поиска для {user_id}: {search_params}")
                self.send_message(
                    user_id,
                    "❌ Параметры поиска повреждены.\n"
                    "Пожалуйста, запустите поиск заново командой **старт**.",
                    keyboard=self.main_menu_keyboard()
                )
                set_user_state(user_id, UserState.MAIN_MENU)
                return None

            # Получаем текущий offset
            offset = get_user_state_data(user_id, "offset", 0)

            # Выполняем поиск
            logger.info(f"Поиск для {user_id}: возраст {search_params['age_from']}-{search_params['age_to']}, "
                        f"пол {search_params['sex']}, город {search_params.get('hometown', 'любой')}, offset={offset}")

            response = user_api.users.search(
                age_from=search_params['age_from'],
                age_to=search_params['age_to'],
                sex=search_params['sex'],
                hometown=search_params.get('hometown', ''),
                has_photo=1,
                is_closed=False,
                offset=offset,
                count=10,
                fields="photo_id,verified,sex,bdate,city,country,home_town,has_photo,photo_max"
            )

            # Фильтруем закрытые профили
            items = [p for p in response['items'] if not p.get('is_closed', True) and p.get('id') != user_id]

            if not items:
                logger.info(f"Нет подходящих анкет для {user_id} (offset={offset})")
                self.send_message(
                    user_id,
                    "👥 Нет больше подходящих анкет.\n\n"
                    "Попробуйте:\n"
                    "• Расширить возрастные рамки\n"
                    "• Изменить город поиска\n"
                    "• Запустить поиск заново командой **старт**",
                    keyboard=self.main_menu_keyboard()
                )
                set_user_state(user_id, UserState.MAIN_MENU)
                return None

            # Берем первую анкету
            profile = items[0]

            # Сохраняем информацию о текущей анкете и увеличиваем offset
            set_user_state_data(user_id, "current_profile", profile)
            set_user_state_data(user_id, "offset", offset + 1)

            # Отправляем анкету с фото
            self.send_profile_with_photos(user_id, profile)
            return profile

        except Exception as e:
            logger.error(f"❌ Ошибка поиска для {user_id}: {e}")
            self.send_message(
                user_id,
                "❌ Ошибка при поиске. Попробуйте позже или запустите поиск заново командой **старт**.",
                keyboard=self.main_menu_keyboard()
            )
            set_user_state(user_id, UserState.MAIN_MENU)
            return None

    def send_profile_with_photos(self, user_id: int, profile: Dict[str, Any]):
        """Отправка анкеты с тремя лучшими фото"""
        try:
            # Формируем информацию об анкете
            name = f"{profile['first_name']} {profile['last_name']}"
            vk_id = profile['id']

            # Возраст
            if 'bdate' in profile and profile['bdate']:
                bdate = profile['bdate']
                if bdate.count('.') == 2:
                    age = self.calculate_age(bdate)
                    bdate = f"{age} лет ({bdate})"
            else:
                bdate = "Не указан"

            # Город
            city = profile.get('city', {}).get('title', 'Не указан')

            # Ссылка на профиль
            link = f"https://vk.com/id{vk_id}"

            # Проверка верификации
            verified = "✓ Верифицирован" if profile.get('verified') else ""

            # Формируем сообщение
            message_parts = [
                f"👤 {name}",
                f"📅 {bdate}",
                f"🏙 {city}",
                f"🔗 {link}"
            ]

            if verified:
                message_parts.append(verified)

            message = "\n".join(message_parts)

            # Получаем топ-3 фото
            photos = self.get_top3_photos(vk_id)
            attachment = ",".join(photos) if photos else None

            # Если нет фото, отправляем без вложений
            if not photos:
                message += "\n\n📸 Фотографии отсутствуют"

            self.send_message(user_id, message, attachment=attachment, keyboard=self.search_keyboard())

        except Exception as e:
            logger.error(f"❌ Ошибка отправки анкеты: {e}")
            self.send_message(user_id, "❌ Ошибка при отображении анкеты", keyboard=self.search_keyboard())

    def get_top3_photos(self, user_id: int) -> List[str]:
        """Получить три самых популярных фото (по лайкам)"""
        try:
            # Получаем фото из профиля
            response = user_api.photos.get(
                owner_id=user_id,
                album_id="profile",
                extended=1,
                count=25
            )

            if not response.get('items'):
                logger.info(f"Нет фото у пользователя {user_id}")
                return []

            # Сортируем по количеству лайков
            sorted_photos = sorted(
                response['items'],
                key=lambda x: x['likes']['count'],
                reverse=True
            )

            # Берем топ-3
            top_photos = sorted_photos[:3]

            # Формируем attachments
            attachments = [f"photo{user_id}_{p['id']}" for p in top_photos]

            logger.info(f"Получено {len(attachments)} фото для пользователя {user_id}")
            return attachments

        except Exception as e:
            logger.error(f"❌ Ошибка загрузки фото для {user_id}: {e}")
            return []

    def show_favorites(self, user_id: int):
        """Показать избранных"""
        try:
            favorites = get_favorites(user_id)

            if not favorites:
                self.send_message(
                    user_id,
                    "❤️ Список избранных пуст.\n\n"
                    "Когда вам понравится анкета, нажмите кнопку «Нравится».",
                    keyboard=self.main_menu_keyboard()
                )
                return

            # Отправляем информацию о количестве избранных
            self.send_message(
                user_id,
                f"❤️ У вас {len(favorites)} избранных:\n\n",
                keyboard=self.main_menu_keyboard()
            )

            # Отправляем каждого избранного
            for profile in favorites:
                name = f"{profile['first_name']} {profile['last_name']}"
                link = f"https://vk.com/id{profile['id']}"
                message = f"❤️ {name}\n🔗 {link}"

                photos = self.get_top3_photos(profile['id'])
                attachment = ",".join(photos) if photos else None

                self.send_message(user_id, message, attachment=attachment)

            self.send_message(
                user_id,
                "✨ Чтобы продолжить поиск, нажмите **старт**",
                keyboard=self.main_menu_keyboard()
            )

        except Exception as e:
            logger.error(f"❌ Ошибка показа избранных для {user_id}: {e}")
            self.send_message(
                user_id,
                "❌ Ошибка при загрузке избранных",
                keyboard=self.main_menu_keyboard()
            )

    def send_message(self, user_id: int, message: str, attachment: str = None, keyboard: dict = None):
        """Отправка сообщения"""
        try:
            # Подготавливаем клавиатуру
            keyboard_json = json.dumps(keyboard, ensure_ascii=False) if keyboard else None

            # Отправляем сообщение
            self.vk.messages.send(
                user_id=user_id,
                message=message,
                attachment=attachment,
                keyboard=keyboard_json,
                random_id=0
            )

        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения пользователю {user_id}: {e}")

    def main_menu_keyboard(self) -> Dict[str, Any]:
        """Клавиатура главного меню"""
        return {
            "inline": True,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "text",
                            "label": "🔍 Поиск"
                        },
                        "color": "primary"
                    },
                    {
                        "action": {
                            "type": "text",
                            "label": "❤️ Избранное"
                        },
                        "color": "secondary"
                    }
                ]
            ]
        }

    def search_keyboard(self) -> Dict[str, Any]:
        """Клавиатура поиска"""
        return {
            "inline": True,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "text",
                            "label": "❤️ Нравится"
                        },
                        "color": "positive"
                    },
                    {
                        "action": {
                            "type": "text",
                            "label": "👎 Дальше"
                        },
                        "color": "negative"
                    }
                ],
                [
                    {
                        "action": {
                            "type": "text",
                            "label": "↩️ Назад"
                        },
                        "color": "secondary"
                    }
                ]
            ]
        }

    @staticmethod
    @staticmethod
    def calculate_age(bdate: str) -> int:
        """Рассчитать возраст по дате рождения"""
        if not bdate:
            return 25

        try:
            parts = bdate.split('.')
            if len(parts) < 2:
                return 25

            # Если есть только день и месяц
            if len(parts) == 2:
                return 25

            year = int(parts[2])
            from datetime import datetime
            current_year = datetime.now().year
            age = current_year - year

            # Проверяем корректность возраста
            if age < 18 or age > 100:
                return 25

            return age

        except Exception:
            return 25


# === Функции состояния через SQLite ===

def get_user_state(user_id: int) -> UserState:
    """Получить состояние пользователя"""
    state = db_get_state(user_id)
    return UserState(state) if state in [s.value for s in UserState] else UserState.MAIN_MENU


def set_user_state(user_id: int, state: UserState):
    """Установить состояние пользователя"""
    db_set_state(user_id, state.value)


def get_user_state_data(user_id: int, key: str, default=None):
    """Получить данные пользователя по ключу"""
    data = db_get_data(user_id, key)
    return data if data is not None else default


def set_user_state_data(user_id: int, key: str, value):
    """Установить данные пользователя по ключу"""
    db_set_data(user_id, key, value)


def save_favorite(user_id: int, profile: dict):
    """Сохранить в избранное"""
    db_save_favorite(user_id, profile)


def get_favorites(user_id: int) -> list:
    """Получить список избранных"""
    return db_get_favorites(user_id)