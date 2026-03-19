from sqlalchemy.orm import Session
from database.models import Users, Candidates, Views
from sqlalchemy.exc import IntegrityError


class VKinderRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_or_create_user(self, vk_id: int, **kwargs):
        """
        Находит пользователя по vk_id или создает нового.
        **kwargs позволяет передать: first_name, last_name, age, city, gender.
        """
        try:
            user = self.session.query(Users).filter_by(vk_id=vk_id).first()
            if not user:
                user = Users(vk_id=vk_id, **kwargs)
                self.session.add(user)

            else:
                for key, value in kwargs.items():
                    setattr(user, key, value)
            self.session.commit()
            self.session.refresh(user)
            return user
        except Exception as e:
            self.session.rollback()
            print(f"Ошибка при создании/обновлении пользователя {vk_id}: {e}")

    def add_candidate(
        self,
        vk_id: int,
        first_name: str,
        last_name: str,
        vk_link: str,
        photos_links: str,
    ):
        try:
            candidate = self.session.query(Candidates).filter_by(
                vk_id=vk_id).first()
            if not candidate:
                candidate = Candidates(
                    vk_id=vk_id,
                    first_name=first_name,
                    last_name=last_name,
                    vk_link=vk_link,
                    photos_links=photos_links,
                )
                self.session.add(candidate)
            else:
                # Если ссылки на фото обновились — актуализируем
                candidate.photos_links = photos_links
            self.session.commit()
            return candidate
        except Exception:
            self.session.rollback()
            return None

    def get_viewed_ids(self, user_id: int):
        """Получает список VK ID всех кандидатов, которых видел пользователь.

        Используется для фильтрации результатов поиска, чтобы бот не показывал
        одних и тех же людей повторно"""
        return (
            self.session.query(Candidates.vk_id)
            .join(Views)
            .filter_by(user_id=user_id)
            .scalars()
            .all()
        )

    def add_to_viewed(
            self,
            user_id: int,
            candidate_id: int,
            is_favorite: bool = False
    ):
        """
        Фиксирует факт просмотра анкеты или добавления в избранное.
        """
        try:
            new_view = Views(
                user_id=user_id,
                candidate_id=candidate_id,
                is_favorite=is_favorite
            )
            self.session.add(new_view)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            existing_view = (
                self.session.query(Views)
                .filter_by(user_id=user_id, candidate_id=candidate_id)
                .first()
            )
            existing_view.is_favorite = is_favorite
            self.session.commit()

    def get_favorites(self, user_id: int):
        """
        Возвращает список всех анкет, добавленных пользователем в избранное.
        """
        return (
            self.session.query(Candidates)
            .join(Views)
            .filter(Views.user_id == user_id, Views.is_favorite)
            .all()
        )
