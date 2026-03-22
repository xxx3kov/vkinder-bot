import sqlite3
import json
from contextlib import contextmanager

DATABASE = "vkinder.db"

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        # Удаляем старую таблицу, если существует (безопасно для новых установок)
        conn.execute("DROP TABLE IF EXISTS user_states")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_states (
                user_id INTEGER PRIMARY KEY,
                state TEXT NOT NULL,
                data TEXT DEFAULT '{}'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER,
                profile_id INTEGER,
                profile_data TEXT,
                PRIMARY KEY (user_id, profile_id)
            )
        """)
    print("✅ Таблицы успешно созданы в SQLite")

def get_user_state(user_id: int) -> str:
    with get_db_connection() as conn:
        row = conn.execute("SELECT state FROM user_states WHERE user_id = ?", (user_id,)).fetchone()
        return row["state"] if row else None

def set_user_state(user_id: int, state: str):
    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO user_states (user_id, state, data)
            VALUES (?, ?, COALESCE((SELECT data FROM user_states WHERE user_id = ?), ?))
        """, (user_id, state, user_id, json.dumps({})))

def get_user_data(user_id: int, key: str):
    with get_db_connection() as conn:
        row = conn.execute("SELECT data FROM user_states WHERE user_id = ?", (user_id,)).fetchone()
        if row and row["data"]:
            try:
                data = json.loads(row["data"])
                return data.get(key)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

def set_user_data(user_id: int, key: str, value):
    with get_db_connection() as conn:
        # Получаем текущие данные
        row = conn.execute("SELECT data FROM user_states WHERE user_id = ?", (user_id,)).fetchone()
        if row and row["data"]:
            try:
                data = json.loads(row["data"])
            except json.JSONDecodeError:
                data = {}
        else:
            data = {}

        # Обновляем значение
        data[key] = value

        # Сохраняем обратно
        conn.execute(
            "INSERT OR REPLACE INTO user_states (user_id, state, data) VALUES (?, COALESCE((SELECT state FROM user_states WHERE user_id = ?), ''), ?)",
            (user_id, user_id, json.dumps(data))
        )

def save_favorite(user_id: int, profile: dict):
    """Сохраняет профиль в избранное"""
    profile_id = profile["id"]
    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO favorites (user_id, profile_id, profile_data)
            VALUES (?, ?, ?)
        """, (user_id, profile_id, json.dumps(profile)))

def get_favorites(user_id: int) -> list:
    """Получает список избранных профилей"""
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT profile_data FROM favorites WHERE user_id = ?", (user_id,)
        ).fetchall()
        result = []
        for row in rows:
            try:
                result.append(json.loads(row["profile_data"]))
            except (json.JSONDecodeError, TypeError):
                continue
        return result