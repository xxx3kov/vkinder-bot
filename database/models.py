import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Users(Base):
    """Пользователь бота (тот, кто ищет)"""

    __tablename__ = "users"
    id = sq.Column(sq.Integer, primary_key=True)
    first_name = sq.Column(sq.String(50), nullable=False)
    last_name = sq.Column(sq.String(50), nullable=False)
    age = sq.Column(sq.Integer, nullable=True)
    vk_id = sq.Column(sq.BigInteger, unique=True, nullable=False)
    city = sq.Column(sq.String(50), nullable=True)
    gender = sq.Column(
        sq.String(10), nullable=False
    )  # узнать что вк отдает по поводу пола (м/ж) или число


class Candidates(Base):
    """Найденные анкеты (кандидаты для знакомства)"""

    __tablename__ = "candidates"
    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.BigInteger, unique=True, nullable=False)
    first_name = sq.Column(sq.String(50), nullable=False)
    last_name = sq.Column(sq.String(50), nullable=False)


class Views(Base):
    """История просмотров и избранное"""

    __tablename__ = "views"
    id = sq.Column(sq.Integer, primary_key=True)
    is_favorite = sq.Column(sq.Boolean, nullable=False, default=False)
    user_id = sq.Column(
        sq.Integer, sq.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    candidate_id = sq.Column(
        sq.Integer, sq.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    # связь
    user = relationship("Users", backref="views")
    candidate = relationship("Candidates", backref="views")
    # ограничитель 
    __table_args__ = (
        sq.UniqueConstraint("user_id", "candidate_id", name="unique_user_candidate"),
    )
