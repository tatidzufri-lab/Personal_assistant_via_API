"""Хранение профилей экспертов.

Профиль — это описание стиля конкретного эксперта (ниша, аудитория, тон,
офферы, особенности подачи). Профили хранятся в JSON-файле по id пользователя
Telegram и подставляются в системный промпт при генерации.
"""

import json
import os

from config import PROFILES_PATH

# Поля профиля и вопросы, которые бот задаёт при настройке (/setup)
PROFILE_FIELDS: list[tuple[str, str]] = [
    (
        "niche",
        "1/5. Представьтесь: как вас зовут и в какой нише вы работаете?\n\n"
        "Например: «Анна, наставник экспертов по запускам» или "
        "«Сергей, психолог, работаю с выгоранием».",
    ),
    (
        "audience",
        "2/5. Кто ваша целевая аудитория? Опишите, кто эти люди, "
        "какие у них боли и желания.",
    ),
    (
        "tone",
        "3/5. Каким тоном вы общаетесь с аудиторией? Какая лексика вам свойственна?\n\n"
        "Например: «на ты, дружелюбно, с юмором и без пафоса» или "
        "«на вы, спокойно и экспертно, без сленга и эмодзи».",
    ),
    (
        "offers",
        "4/5. Какие продукты вы продаёте и какие офферы обычно используете?\n\n"
        "Например: «курс по контенту за 30 000 ₽, бесплатная диагностика как вход в воронку».",
    ),
    (
        "style_notes",
        "5/5. Особенности подачи и табу: любимые форматы, фишки, "
        "чего в текстах быть не должно?\n\n"
        "Например: «люблю истории из практики, не пишу капслоком, не обещаю "
        "конкретных цифр дохода». Если особенностей нет — напишите «нет».",
    ),
]


def _load_all() -> dict:
    if not os.path.exists(PROFILES_PATH):
        return {}
    with open(PROFILES_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_all(profiles: dict) -> None:
    os.makedirs(os.path.dirname(PROFILES_PATH) or ".", exist_ok=True)
    with open(PROFILES_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)


def get_profile(user_id: int) -> dict | None:
    """Возвращает профиль пользователя или None, если он не настроен."""
    return _load_all().get(str(user_id))


def save_profile(user_id: int, profile: dict) -> None:
    """Сохраняет профиль пользователя в JSON-файл."""
    profiles = _load_all()
    profiles[str(user_id)] = profile
    _save_all(profiles)


def delete_profile(user_id: int) -> None:
    """Удаляет профиль пользователя (сброс настройки)."""
    profiles = _load_all()
    if profiles.pop(str(user_id), None) is not None:
        _save_all(profiles)


def format_profile(profile: dict) -> str:
    """Человекочитаемое представление профиля для показа в чате."""
    return (
        f"👤 Имя и ниша: {profile.get('niche', '—')}\n\n"
        f"🎯 Аудитория: {profile.get('audience', '—')}\n\n"
        f"🗣 Тон и лексика: {profile.get('tone', '—')}\n\n"
        f"💼 Продукты и офферы: {profile.get('offers', '—')}\n\n"
        f"✨ Особенности подачи: {profile.get('style_notes', '—')}"
    )
