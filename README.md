<center>Пока в разработке</center>

# VKinder — Бот для знакомств в ВКонтакте

Командный проект по поиску подходящих пар на основе данных профиля пользователя VK.

## Основные функции
- Поиск людей по городу, возрасту и полу.
- Отбор 3 самых популярных фотографий профиля (по количеству лайков).
- Возможность добавлять пользователей в список «Избранное».
- Просмотр списка избранных кандидатов.

## Технологический стек
- **Python 3.x**
- **PostgreSQL** (база данных)
- **SQLAlchemy** (ORM для работы с БД)
- **vk_api** (библиотека для взаимодействия с VK)

## 📁 Структура данных
```text
vkinder-bot/
├── .env                  # Конфигурация (не в репозитории!)
├── .env.example          # Шаблон конфигурации
├── .gitignore            # Список исключений для Git
├── requirements.txt      # Список библиотек
├── README.md             # Инструкция и описание проекта
├── config.py             # Читает .env, создает DSN для SQLAlchemy
|
├── database/
│   ├── models.py         # Классы Users, Candidates, Views (Base.metadata)
│   ├── repository.py     # Класс VKinderRepository (логика запросов)
│   └── db_session        # engine, SessionLocal, create_all()
│
├── vk_api/
│   ├── client.py         # Работа с API (сообщения, авторизация)
│   └── search.py         # Поиск людей по фильтрам (город, возраст, пол)
│
├── bot/
│   ├── handlers.py       # Обработка событий LongPoll и нажатий кнопок
│   └── states.py         # Управление состояниями
│
└── main.py               # Точка входа: инициализация БД и запуск бота
```

## 🗄️ База данных
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY, 
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL, 
    age INTEGER,
    vk_id BIGINT UNIQUE NOT NULL, 
    city VARCHAR(50) NOT NULL,
    gender # узнать что вк отдает по поводу пола (м/ж) или число
)

CREATE TABLE candidates (
    id SERIAL PRIMARY KEY, 
    vk_id BIGINT UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL
)

CREATE TABLE views (
    id SERIAL PRIMARY KEY, 
    is_favorite BOOLEAN NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE
)
```

<center>Пока в разработке</center>
