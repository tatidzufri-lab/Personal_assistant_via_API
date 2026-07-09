"""Единый интерфейс к языковым моделям: OpenAI (GPT-4o) и GigaChat.

Оба провайдера принимают одинаковый формат сообщений
[{"role": "system"|"user"|"assistant", "content": "..."}]
и возвращают текст ответа, поэтому бот может переключаться между ними по кнопке.
"""

import logging
import re

from openai import AsyncOpenAI

from config import (
    GIGACHAT_CREDENTIALS,
    GIGACHAT_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)

logger = logging.getLogger(__name__)


def strip_markdown(text: str) -> str:
    """Убирает markdown-разметку, которую ВК не отображает.

    Страховка на случай, если модель нарушит правило из системного промпта.
    """
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # **жирный**
    text = re.sub(r"__(.+?)__", r"\1", text)  # __подчёркнутый__
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)  # ## заголовки
    return text

# Идентификаторы провайдеров и их отображаемые названия
PROVIDER_OPENAI = "openai"
PROVIDER_GIGACHAT = "gigachat"

PROVIDER_LABELS = {
    PROVIDER_OPENAI: f"OpenAI ({OPENAI_MODEL})",
    PROVIDER_GIGACHAT: f"GigaChat ({GIGACHAT_MODEL})",
}

_openai_client: AsyncOpenAI | None = None
_gigachat_client = None


def _get_openai() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


def _get_gigachat():
    global _gigachat_client
    if _gigachat_client is None:
        # Импортируем лениво, чтобы бот работал и без установленного gigachat,
        # пока пользователь не переключится на этот провайдер
        from gigachat import GigaChat

        _gigachat_client = GigaChat(
            credentials=GIGACHAT_CREDENTIALS,
            model=GIGACHAT_MODEL,
            scope="GIGACHAT_API_PERS",
            verify_ssl_certs=False,
        )
    return _gigachat_client


def provider_available(provider: str) -> bool:
    """Проверяет, заданы ли в .env ключи для провайдера."""
    if provider == PROVIDER_OPENAI:
        return bool(OPENAI_API_KEY)
    if provider == PROVIDER_GIGACHAT:
        return bool(GIGACHAT_CREDENTIALS)
    return False


async def generate(provider: str, messages: list[dict]) -> str:
    """Отправляет диалог выбранному провайдеру и возвращает текст ответа."""
    if provider == PROVIDER_GIGACHAT:
        answer = await _generate_gigachat(messages)
    else:
        answer = await _generate_openai(messages)
    return strip_markdown(answer)


async def _generate_openai(messages: list[dict]) -> str:
    response = await _get_openai().chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.8,
    )
    return response.choices[0].message.content.strip()


async def _generate_gigachat(messages: list[dict]) -> str:
    client = _get_gigachat()
    response = await client.achat({"messages": messages})
    return response.choices[0].message.content.strip()
