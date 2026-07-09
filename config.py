"""Конфигурация проекта: загрузка ключей и настроек из .env."""

import os

from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# GigaChat (опционально — для переключения провайдера по кнопке)
GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")
GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat-2-Max")

# Файл с профилями экспертов
PROFILES_PATH = os.getenv("PROFILES_PATH", "data/profiles.json")
