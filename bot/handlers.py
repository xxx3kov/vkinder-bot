import random
import json
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from config import VK_GROUP_TOKEN, VK_USER_TOKEN
from vk_api.client import VK
from vk_api.search import SearchService
from database.db_session import SessionLocal
from database.repository import VKinderRepository
from bot.states import UserState, set_user_state


class VKinderBot:
    def __init__(self):
        # Клиент для поиска (с пользовательским токеном)
        self.vk_user = VK(access_token=VK_USER_TOKEN, user_id=None)

        # Репозиторий для работы с БД
        self.repository = VKinderRepository(SessionLocal())

        # Сервис поиска (вся логика поиска и фото)
        self.search_service = SearchService(self.vk_user, self.repository)

        # Сессия группы для ответов
        self.vk_group_session = vk_api.VkApi(token=VK_GROUP_TOKEN)
        self.vk_group = self.vk_group_session.get_api()
        self.longpoll = VkLongPoll(self.vk_group_session)

        # Хранилища данных
        self.current_candidate = {}  # текущий кандидат
        self.current_user = {}  # объект пользователя из БД

    def run(self):
        """Запуск бота"""
        print("Бот VKinder запущен...")
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                self.handle_event(event)

    def handle_event(self, event):
        """Обработка входящих сообщений"""
        user_id = event.user_id
        message = event.text.lower().strip()

        # Получаем или создаём пользователя в БД
        user_info = self.vk_user.users_info()
        if user_info:
            user = self.repository.get_or_create_user(
                vk_id=user_id,
                first_name=user_info.get("first_name", ""),
                last_name=user_info.get("last_name", ""),
                gender=user_info.get("sex", 0),
            )
            # Сохраняем объект пользователя
            self.current_user[user_id] = user

        # Обработка команд
        if message in ["начать", "меню", "🚫 меню"]:
            self.show_main_menu(user_id)

        elif message in ["найти пару", "👎 дальше"]:
            self.show_next_candidate(user_id)

        elif message == "⭐️ в избранное":
            self.add_to_favorites(user_id)

        elif message == "избранное":
            self.show_favorites(user_id)

        else:
            # Если команда не распознана - показываем меню
            self.show_main_menu(user_id)

    def show_main_menu(self, user_id):
        """Главное меню"""
        set_user_state(user_id, UserState.MAIN_MENU)

        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button("Найти пару", VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button("Избранное", VkKeyboardColor.PRIMARY)

        self.send_message(
            user_id,
            "👋 Привет! Я бот VKinder для поиска пар.\n\n"
            "Что ты хочешь сделать?",
            keyboard,
        )

    def show_next_candidate(self, user_id):
        """Показать следующего кандидата"""
        # Получаем кандидата через сервис поиска
        candidate = self.search_service.get_next_candidate(user_id)

        if not candidate:
            # Если кандидатов нет
            keyboard = VkKeyboard(one_time=False)
            keyboard.add_button("Найти пару", VkKeyboardColor.POSITIVE)
            keyboard.add_line()
            keyboard.add_button("Избранное", VkKeyboardColor.PRIMARY)
            message_text = "😕 К сожалению, не удалось найти новых кандидатов."
            self.send_message(user_id, message_text, keyboard)
            return

        # Сохраняем текущего кандидата
        self.current_candidate[user_id] = candidate

        # Клавиатура для действий с кандидатом
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button("⭐️ В избранное", VkKeyboardColor.PRIMARY)
        keyboard.add_button("👎 Дальше", VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button("🚫 Меню", VkKeyboardColor.SECONDARY)

        # Отправляем сообщение с фото
        self.send_message(
            user_id,
            f"{candidate['name']}\nСсылка: {candidate['link']}",
            keyboard,
            attachment=",".join(candidate["attachments"]),
        )

    def add_to_favorites(self, user_id):
        """Добавить текущего кандидата в избранное"""
        candidate = self.current_candidate.get(user_id)
        user = self.current_user.get(user_id)

        if not candidate:
            self.send_message(user_id, "❌ Сначала найди кандидата!")
            self.show_next_candidate(user_id)
            return

        if not user:
            self.send_message(user_id, "❌ Ошибка: пользователь не найден")
            self.show_main_menu(user_id)
            return

        # Сохраняем кандидата в БД
        db_candidate = self.repository.add_candidate(
            vk_id=candidate["id"],
            first_name=candidate["name"].split()[0],
            last_name=(
                candidate["name"].split()[1]
                if len(candidate["name"].split()) > 1
                else ""
            ),
            vk_link=candidate["link"],
            photos_links=json.dumps(candidate["attachments"]),
        )

        # Добавляем в избранное
        if db_candidate:
            self.repository.add_to_viewed(
                user.id,
                db_candidate.id,
                is_favorite=True
            )
            self.send_message(
                user_id, f"⭐️ {candidate['name']} добавлен(а) в избранное!"
            )
        else:
            self.send_message(user_id, "❌ Ошибка при добавлении в избранное")

        # Показываем следующего кандидата
        self.show_next_candidate(user_id)

    def show_favorites(self, user_id):
        """Показать список избранных"""
        user = self.current_user.get(user_id)

        if not user:
            self.send_message(user_id, "❌ Ошибка: пользователь не найден")
            self.show_main_menu(user_id)
            return

        favorites = self.repository.get_favorites(user.id)

        if not favorites:
            keyboard = VkKeyboard(one_time=False)
            keyboard.add_button("Найти пару", VkKeyboardColor.POSITIVE)
            keyboard.add_line()
            keyboard.add_button("Меню", VkKeyboardColor.SECONDARY)

            self.send_message(
                user_id, "😕 У тебя пока нет избранных кандидатов.", keyboard
            )
            return

        set_user_state(user_id, UserState.SHOW_FAVORITES)

        for fav in favorites:
            # Преобразуем строку с фото обратно в список
            attachments = []
            if fav.photos_links:
                try:
                    attachments = json.loads(fav.photos_links)
                except json.JSONDecodeError:
                    attachments = []

            self.send_message(
                user_id,
                f"⭐️ {fav.first_name} {fav.last_name}\nСсылка: {fav.vk_link}",
                attachment=",".join(attachments) if attachments else None,
            )

        # Возвращаем в главное меню
        self.show_main_menu(user_id)

    def send_message(self, user_id, text, keyboard=None, attachment=None):
        """Универсальный метод отправки сообщений"""
        params = {
            "user_id": user_id,
            "message": text,
            "random_id": random.getrandbits(64),
        }

        if keyboard:
            params["keyboard"] = keyboard.get_keyboard()

        if attachment:
            params["attachment"] = attachment

        self.vk_group.messages.send(**params)
