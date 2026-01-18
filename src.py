import os  # Импортируем стандартный модуль для работы с операционной системой и переменными окружения
from dotenv import load_dotenv  # Импортируем функцию для загрузки переменных окружения из файла .env

load_dotenv()  # Загружаем переменные окружения из файла .env в текущую рабочую среду

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Получаем значение переменной окружения с API-ключом OpenAI
ASSISTANT_ID = os.getenv("ASSISTANT_ID")  # Получаем идентификатор ассистента OpenAI
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Получаем токен для Telegram-бота
