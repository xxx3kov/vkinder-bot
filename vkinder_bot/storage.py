"""
Единое хранилище для состояний и данных пользователей.
"""

_shared_storage = {
    '_user_states': {},
    '_user_data': {}
}


def get_user_state(user_id: int):
    return _shared_storage['_user_states'].get(user_id, None)


def set_user_state(user_id: int, state):
    _shared_storage['_user_states'][user_id] = state


def get_user_data(user_id: int, key: str, default=None):
    return _shared_storage['_user_data'].get(user_id, {}).get(key, default)


def set_user_data(user_id: int, key: str, value):
    if user_id not in _shared_storage['_user_data']:
        _shared_storage['_user_data'][user_id] = {}
    _shared_storage['_user_data'][user_id][key] = value


def get_favorites(user_id: int) -> list:
    return _shared_storage['_user_data'].get(user_id, {}).get("favorites", [])


def save_favorite(user_id: int, profile: dict):
    favorites = _shared_storage['_user_data'].setdefault(user_id, {}).setdefault("favorites", [])
    if not any(fav['id'] == profile['id'] for fav in favorites):
        favorites.append(profile)