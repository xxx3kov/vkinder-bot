from sqlalchemy.orm import Session
from database.models import Users, Candidates, Views


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
            # будущий логгер

    def add_candidate(self, vk_id: int, **kwargs):
        """
        Добавляет анкету в базу(Candidates), если её там еще нет.
        **kwargs позволяет передать: first_name, last_name, age, city, gender.
        """
        try:
            candidate = self.session.query(Candidates).filter_by(vk_id=vk_id).first()
            if not candidate:
                candidate = Candidates(vk_id=vk_id, **kwargs)
                self.session.add(candidate)
            self.session.commit()
            self.session.refresh(candidate)
            return candidate
        except Exception as e:
            self.session.rollback()

    def get_viewed_ids(self, user_id: int):
        """Получает список VK ID всех кандидатов, которых уже видел пользователь.
        
        Используется для фильтрации результатов поиска, чтобы бот не показывал 
        одних и тех же людей повторно"""
        pass

    def add_to_viewed(self, user_id: int, candidate_id: int, is_favorite: bool = False):
        """
        Фиксирует факт просмотра анкеты или добавления в избранное.
        """
        pass

    def get_favorites(self, user_id: int):
        """
        Возвращает список всех анкет, добавленных пользователем в избранное.
        """
        pass