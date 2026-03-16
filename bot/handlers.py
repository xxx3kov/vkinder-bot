# Обработчики событий VK LongPoll.
# Здесь описывается реакция бота на сообщения,
# нажатия кнопок и переходы между состояниями (FSM).
from vk_api.longpoll import VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from bot.states import UserState, get_user_state, set_user_state, clear_user_state
from database.repository import VKinderRepository
from database.db_session import db_session
from vk_api.client import VKClient, create_keyboard
from vk_api.search import VKSearch
import random


class VKinderBot:
    def __init__(self):
        self.vk_client = VKClient()
        self.vk_search = VKSearch(self.vk_client)
        self.repository = VKinderRepository(db_session())

        # Хранилище для текущих кандидатов
        self.current_candidates = {}  # user_id -> list of candidates
        self.current_index = {}  # user_id -> current index

    def run(self):
        """Запуск бота"""
        print("Бот VKinder запущен...")

        for event in self.vk_client.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                self.handle_event(event)

    def handle_event(self, event):
        """Обработка входящих сообщений"""
        user_id = event.user_id
        message = event.text.lower()

        # Получаем или создаем пользователя
        user_info = self.vk_client.get_user_info(user_id)
        if user_info:
            self.repository.get_or_create_user(
                user_id,
                user_info.get('first_name'),
                user_info.get('last_name')
            )

        # Получаем текущее состояние
        state = get_user_state(user_id)

        # Обработка команд
        if message in ['начать', 'start', 'меню', 'menu']:
            self.show_main_menu(user_id)
        elif message == 'найти пару':
            self.start_searching(user_id)
        elif message == 'избранное':
            self.show_favorites(user_id)
        elif message == 'настройки':
            self.show_settings(user_id)
        else:
            self.handle_state(user_id, message, state)

    def show_main_menu(self, user_id):
        """Главное меню"""
        set_user_state(user_id, UserState.MAIN_MENU)

        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('Найти пару', VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('Избранное', VkKeyboardColor.PRIMARY)
        keyboard.add_button('Настройки', VkKeyboardColor.SECONDARY)

        message = (
            "👋 Привет! Я бот VKinder для поиска пар.\n\n"
            "Что ты хочешь сделать?"
        )

        self.vk_client.send_message(user_id, message, keyboard)

    def show_settings(self, user_id):
        """Меню настроек"""
        set_user_state(user_id, UserState.SETTINGS)

        user = self.repository.get_user(user_id)

        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('Изменить город', VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Изменить возраст', VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Назад', VkKeyboardColor.NEGATIVE)

        current_settings = (
            f"⚙️ Текущие настройки:\n\n"
            f"🏙 Город: {user.city if user.city else 'не указан'}\n"
            f"📅 Возраст: от {user.age_from} до {user.age_to} лет"
        )

        self.vk_client.send_message(user_id, current_settings, keyboard)

    def handle_state(self, user_id, message, state):
        """Обработка сообщений в зависимости от состояния"""

        if state == UserState.SETTINGS:
            if message == 'изменить город':
                set_user_state(user_id, UserState.SET_CITY)
                self.vk_client.send_message(
                    user_id,
                    "Введи название города для поиска:"
                )
            elif message == 'изменить возраст':
                set_user_state(user_id, UserState.SET_AGE_FROM)
                self.vk_client.send_message(
                    user_id,
                    "Введи минимальный возраст (от 18 до 99):"
                )
            elif message == 'назад':
                self.show_main_menu(user_id)

        elif state == UserState.SET_CITY:
            self.repository.update_user_preferences(user_id, city=message.capitalize())
            set_user_state(user_id, UserState.SETTINGS)
            self.vk_client.send_message(
                user_id,
                f"✅ Город {message.capitalize()} сохранен!"
            )
            self.show_settings(user_id)

        elif state == UserState.SET_AGE_FROM:
            try:
                age = int(message)
                if 18 <= age <= 99:
                    self.repository.update_user_preferences(user_id, age_from=age)
                    set_user_state(user_id, UserState.SET_AGE_TO)
                    self.vk_client.send_message(
                        user_id,
                        "Введи максимальный возраст:"
                    )
                else:
                    self.vk_client.send_message(
                        user_id,
                        "❌ Возраст должен быть от 18 до 99. Попробуй снова:"
                    )
            except ValueError:
                self.vk_client.send_message(
                    user_id,
                    "❌ Введи число от 18 до 99:"
                )

        elif state == UserState.SET_AGE_TO:
            try:
                age = int(message)
                if 18 <= age <= 99:
                    user = self.repository.get_user(user_id)
                    if age >= user.age_from:
                        self.repository.update_user_preferences(user_id, age_to=age)
                        set_user_state(user_id, UserState.SETTINGS)
                        self.vk_client.send_message(
                            user_id,
                            f"✅ Возраст сохранен!"
                        )
                        self.show_settings(user_id)
                    else:
                        self.vk_client.send_message(
                            user_id,
                            f"❌ Максимальный возраст должен быть больше минимального ({user.age_from})"
                        )
                else:
                    self.vk_client.send_message(
                        user_id,
                        "❌ Возраст должен быть от 18 до 99. Попробуй снова:"
                    )
            except ValueError:
                self.vk_client.send_message(
                    user_id,
                    "❌ Введи число от 18 до 99:"
                )

    def start_searching(self, user_id):
        """Начало поиска кандидатов"""
        user = self.repository.get_user(user_id)

        if not user.city:
            set_user_state(user_id, UserState.SET_CITY)
            self.vk_client.send_message(
                user_id,
                "Сначала укажи город для поиска:"
            )
            return

        # Получаем список уже просмотренных кандидатов
        viewed_ids = self.repository.get_viewed_candidates(user_id)

        # Ищем новых кандидатов
        candidates = self.vk_search.find_candidates(
            {
                'city': user.city,
                'sex': user.sex,
                'age_from': user.age_from,
                'age_to': user.age_to
            },
            viewed_ids
        )

        if not candidates:
            self.vk_client.send_message(
                user_id,
                "😕 К сожалению, не удалось найти новых кандидатов. Попробуй изменить настройки поиска."
            )
            self.show_main_menu(user_id)
            return

        # Сохраняем кандидатов
        self.current_candidates[user_id] = candidates
        self.current_index[user_id] = 0

        set_user_state(user_id, UserState.VIEWING_CANDIDATE)
        self.show_candidate(user_id)

    def show_candidate(self, user_id):
        """Показ кандидата"""
        candidates = self.current_candidates.get(user_id, [])
        index = self.current_index.get(user_id, 0)

        if index >= len(candidates):
            self.vk_client.send_message(
                user_id,
                "🎉 Ты просмотрел всех кандидатов! Начинаем новый поиск..."
            )
            self.start_searching(user_id)
            return

        candidate = candidates[index]

        # Сохраняем кандидата в базу
        user = self.repository.get_user(user_id)
        db_candidate = self.repository.save_candidate(user.id, candidate)

        # Клавиатура для действий
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('❤️ Нравится', VkKeyboardColor.POSITIVE)
        keyboard.add_button('👎 Не нравится', VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button('⭐️ В избранное', VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('🚫 Закончить', VkKeyboardColor.SECONDARY)

        # Формируем сообщение
        age_text = f", {candidate['age']} лет" if candidate.get('age') else ""
        city_text = f" из {candidate['city']}" if candidate.get('city') else ""

        message = (
            f"{candidate['first_name']} {candidate['last_name']}{age_text}{city_text}\n"
            f"Ссылка: {candidate['profile_link']}\n\n"
            f"Кандидат {index + 1} из {len(candidates)}"
        )

        # Отправляем с фото
        self.vk_client.send_photos(user_id, candidate['photos'], message, keyboard)

    def handle_candidate_action(self, user_id, action, candidate_data):
        """Обработка действий с кандидатом"""
        user = self.repository.get_user(user_id)
        candidate = self.repository.get_candidate_by_vk_id(user.id, candidate_data['id'])

        if action == 'like':
            self.repository.add_view(user.id, candidate.id, is_liked=True)
            self.vk_client.send_message(user_id, "❤️ Отлично! Ищем дальше...")

        elif action == 'dislike':
            self.repository.add_view(user.id, candidate.id, is_liked=False)
            self.vk_client.send_message(user_id, "👎 Продолжаем поиск...")

        elif action == 'favorite':
            view = self.repository.add_view(user.id, candidate.id, is_liked=True)
            view.is_favorite = True
            db_session().commit()
            self.vk_client.send_message(
                user_id,
                f"⭐️ {candidate_data['first_name']} добавлен(а) в избранное!"
            )

        # Переходим к следующему кандидату
        self.current_index[user_id] = self.current_index.get(user_id, 0) + 1
        self.show_candidate(user_id)

    def show_favorites(self, user_id):
        """Показ избранных кандидатов"""
        user = self.repository.get_user(user_id)
        favorites = self.repository.get_favorites(user.id)

        if not favorites:
            keyboard = VkKeyboard(one_time=False)
            keyboard.add_button('Найти пару', VkKeyboardColor.POSITIVE)
            keyboard.add_line()
            keyboard.add_button('Назад', VkKeyboardColor.NEGATIVE)

            self.vk_client.send_message(
                user_id,
                "😕 У тебя пока нет избранных кандидатов.",
                keyboard
            )
            return

        set_user_state(user_id, UserState.SHOW_FAVORITES)

        for fav in favorites:
            photos = json.loads(fav.photo_links) if fav.photo_links else []
            age_text = f", {fav.age} лет" if fav.age else ""

            message = (
                f"⭐️ {fav.first_name} {fav.last_name}{age_text}\n"
                f"Ссылка: {fav.profile_link}"
            )

            self.vk_client.send_photos(user_id, photos, message)

        # Возвращаем в главное меню
        self.show_main_menu(user_id)


# Обработка действий с кандидатами
def handle_candidate_callback(self, event):
    """Обработка callback от кнопок"""
    user_id = event.user_id
    payload = json.loads(event.payload)

    if payload['action'] == 'like':
        self.handle_candidate_action(user_id, 'like', payload['candidate'])
    elif payload['action'] == 'dislike':
        self.handle_candidate_action(user_id, 'dislike', payload['candidate'])
    elif payload['action'] == 'favorite':
        self.handle_candidate_action(user_id, 'favorite', payload['candidate'])
    elif payload['action'] == 'end':
        clear_user_state(user_id)
        self.show_main_menu(user_id)