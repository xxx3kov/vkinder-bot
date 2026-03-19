from enum import Enum


class UserState(Enum):
    """Состояния пользователя в диалоге с ботом"""

    MAIN_MENU = "main_menu"
    SHOW_FAVORITES = "show_favorites"


# Хранилище состояний пользователей
user_states = {}


def get_user_state(user_id):
    """Получить состояние пользователя"""
    return user_states.get(user_id, UserState.MAIN_MENU)


def set_user_state(user_id, state):
    """Установить состояние пользователя"""
    user_states[user_id] = state


def clear_user_state(user_id):
    """Очистить состояние пользователя"""
    if user_id in user_states:
        del user_states[user_id]
