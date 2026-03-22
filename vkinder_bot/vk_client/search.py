from datetime import date


class SearchService:
    def __init__(self, vk_client, repository):
        self.vk = vk_client
        self.repo = repository
        self.found_candidates = []
        self.search_offset = 0

    def _prepare_search_params(self, user_id):
        user_data = self.vk.users_info()

        bdate = user_data.get("bdate", "")
        age = 0

        if bdate and len(bdate.split(".")) == 3:
            birth_year = int(bdate.split(".")[-1])
            age = date.today().year - birth_year

        city_id = user_data.get("city", {}).get("id") or 1

        return {
            "city_id": city_id,
            "age_from": age - 2 if age else 18,  # Ищем +/- 2 года от своего
            "age_to": age + 2 if age else 35,
            "sex": user_data.get("sex", 1),
        }

    def get_next_candidate(self, user_id):
        if not self.found_candidates:
            params = self._prepare_search_params(user_id)
            self.found_candidates = self.vk.search_users(**params)

        seen_ids = set(self.repo.get_viewed_ids(user_id))

        while self.found_candidates:
            candidate = self.found_candidates.pop(0)
            c_id = candidate["id"]

            if c_id in seen_ids or candidate.get("is_closed"):
                continue

            photos_raw = self.vk.get_photos(c_id)
            if not photos_raw:
                continue

            attachments = self._sort_photos(photos_raw)

            return {
                "id": c_id,
                "name": (
                    f"{candidate.get('first_name')} "
                    f"{candidate.get('last_name')}"
                ),
                "link": f"https://vk.com/id{c_id}",
                "attachments": attachments,
            }
        return None

    def _sort_photos(self, photos_raw):
        sorted_photos = sorted(
            photos_raw,
            key=lambda x: x.get("likes", {}).get("count", 0),
            reverse=True,
        )
        top_3 = sorted_photos[:3]
        attachments = [f"photo{p['owner_id']}_{p['id']}" for p in top_3]

        return attachments
