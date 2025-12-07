# Урок PEs06. Проект: Персональный помощник через API

## Описание

В этом проекте разрабатывается Telegram-бот — персональный помощник для генерации карточек товаров для маркетплейсов.  
Бот интегрируется с ИИ-ассистентами (OpenAI Assistant, GigaChat) и реализован с использованием библиотеки LangChain.

***

## Структура проекта

- **OpenAI Assistant:**  
  Код интеграции: [`main_open_ai.py`](https://github.com/ZerocoderUniversity/AI-course-prompt-engineering-3.0/blob/7e7dfebdb0a5d213e4e61f56835994f2fd079e04/01_Project_Personal%20API-assistant/main_open_ai.py)

- **GigaChat:**  
  Код интеграции: [`main_giga.py`](https://github.com/ZerocoderUniversity/AI-course-prompt-engineering-3.0/blob/7e7dfebdb0a5d213e4e61f56835994f2fd079e04/01_Project_Personal%20API-assistant/main_giga.py)

- **LangChain:**  
  Реализация с библиотекой LangChain: [`main_lang.py`](https://github.com/ZerocoderUniversity/AI-course-prompt-engineering-3.0/blob/7e7dfebdb0a5d213e4e61f56835994f2fd079e04/01_Project_Personal%20API-assistant/main_lang.py)

- **Загрузка ключей и паролей (.env):**  
  Автоматическая загрузка: [`src.py`](https://github.com/ZerocoderUniversity/AI-course-prompt-engineering-3.0/blob/e16af58d6c1ee5d21b2880a2402bb58a25721875/01_Project_Personal%20API-assistant/src.py)

***

## Важно!

Перед запуском создайте файл `.env` с вашими ключами и паролями.

***

## Что такое файл .env?

Файл `.env` — это текстовый файл для хранения переменных окружения (например, ключей API и паролей), необходимых приложению.

**Формат строки:**

```
КЛЮЧ=значение
```

**Пример файла `.env`:**

```
OPENAI_API_KEY=sk-xxx-xxx
ASSISTANT_ID=asst-xxx-xxx
TELEGRAM_TOKEN=123456789:AbcDefGHIjklMNOpQRstUvWxyXz
GIGACHAT_CREDENTIALS=my_gigachat_service_token
LANGFUSE_SECRET_KEY=my_langfuse_secret
LANGFUSE_PUBLIC_KEY=my_langfuse_public
LANGFUSE_HOST=https://my.langfuse.server
```

- Слева — имя (ключ) переменной  
- Справа — её значение

**Рекомендация:**  
Добавьте `.env` в `.gitignore`, чтобы секреты не попадали в публичный репозиторий.
