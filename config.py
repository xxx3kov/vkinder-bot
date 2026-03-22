from dotenv import load_dotenv
import os

# Загружаем переменные из .env
load_dotenv()

# Токены VK
VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN")
VK_USER_TOKEN = os.getenv("VK_USER_TOKEN")

# Настройки базы данных (SQLite)
DB_PATH = "sqlite:///vkinder.db"