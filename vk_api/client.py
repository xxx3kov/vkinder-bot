"""
Базовый клиент для работы с API ВКонтакте.
Инициализация сессии, авторизация (токены) и общие методы (send_message).
"""

import requests


class VK:

    def __init__(self, access_token, user_id, version="5.199"):
        self.token = access_token
        self.id = user_id
        self.base_url = "https://api.vk.com/method/"
        self.version = version
        self.params = {
            "access_token": self.token,
            "v": self.version,
        }

    def users_info(self):
        url = f"{self.base_url}users.get"
        params = {"user_ids": self.id, "fields": "city, sex, bdate"}
        try:
            response = requests.get(url, params={**self.params, **params})
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                error_msg = data['error'].get('error_msg')
                print(f"Ошибка API в users_info: {error_msg}")
                return {}
            # Возвращаем первый элемент списка (самого пользователя)
            res = data.get("response", [])
            return res[0] if res else {}
        except (requests.RequestException, IndexError) as e:
            print(f"Сетевая ошибка в users_info: {e}")
            return {}

    def search_users(self, city_id, age_from, age_to, sex):
        url = f"{self.base_url}users.search"
        # 1 - ж, 2 - м. Если 1, ищем 2 (3-1=2). Если 2, ищем 1 (3-2=1)
        target_sex = 3 - sex
        params = {
            "city": city_id,
            "sex": target_sex,
            "age_from": age_from,
            "age_to": age_to,
            "fields": "is_closed, can_access_closed",
            "count": 50,
            "has_photo": 1,
        }
        try:
            response = requests.get(url, params={**self.params, **params})
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                error_msg = data['error'].get('error_msg')
                print(f"Ошибка API в search_users: {error_msg}")
                return []
            return data.get("response", {}).get("items", [])
        except requests.RequestException as e:
            print(f"Сетевая ошибка в search_users: {e}")
            return []

    def get_photos(self, owner_id):
        url = f"{self.base_url}photos.get"
        params = {"owner_id": owner_id, "extended": 1, "album_id": "profile"}
        try:
            response = requests.get(url, params={**self.params, **params})
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                error_msg = data['error'].get('error_msg')
                print(
                    f"Не удалось получить фото юзера {owner_id}: {error_msg}"
                )
                return []
            # Возвращаем только список объектов фотографий
            return data.get("response", {}).get("items", [])
        except requests.RequestException as e:
            print(f"Сетевая ошибка в get_photos: {e}")
            return []
