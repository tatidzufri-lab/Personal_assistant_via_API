"""Telegram-бот для генерации контента ВКонтакте.

Помогает эксперту в инфобизнесе создавать контент: идеи постов, готовые
публикации, прогревы, продающие тексты, кейсы, отработку возражений и
доработку черновиков. Учитывает стиль эксперта (профиль через /setup) и
умеет переключаться между OpenAI GPT-4o и GigaChat по кнопке.

Запуск: python bot.py
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import llm
import profiles
from config import TELEGRAM_TOKEN
from prompts import SCENARIOS, build_system_prompt, build_user_prompt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Состояние диалога настройки профиля (/setup)
SETUP_STATE = 0

# Сколько последних сообщений диалога передавать модели (без учёта системного)
HISTORY_LIMIT = 10

# Лимит Telegram на длину одного сообщения
TG_MESSAGE_LIMIT = 4096


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def get_provider(context: ContextTypes.DEFAULT_TYPE) -> str:
    """Текущий провайдер пользователя (по умолчанию OpenAI)."""
    return context.user_data.get("provider", llm.PROVIDER_OPENAI)


def main_menu_keyboard(context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardMarkup:
    """Главное меню: сценарии генерации + настройки."""
    rows = [
        [InlineKeyboardButton(SCENARIOS["ideas"]["button"], callback_data="scenario:ideas")],
        [
            InlineKeyboardButton(SCENARIOS["post"]["button"], callback_data="scenario:post"),
            InlineKeyboardButton(SCENARIOS["warmup"]["button"], callback_data="scenario:warmup"),
        ],
        [
            InlineKeyboardButton(SCENARIOS["selling"]["button"], callback_data="scenario:selling"),
            InlineKeyboardButton(SCENARIOS["case"]["button"], callback_data="scenario:case"),
        ],
        [InlineKeyboardButton(SCENARIOS["objections"]["button"], callback_data="scenario:objections")],
        [InlineKeyboardButton(SCENARIOS["improve"]["button"], callback_data="scenario:improve")],
        [
            InlineKeyboardButton(
                f"🧠 Модель: {llm.PROVIDER_LABELS[get_provider(context)]}",
                callback_data="model:menu",
            )
        ],
        [InlineKeyboardButton("⚙️ Профиль эксперта", callback_data="profile:show")],
    ]
    return InlineKeyboardMarkup(rows)


def after_answer_keyboard() -> InlineKeyboardMarkup:
    """Кнопки под сгенерированным ответом."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔁 Ещё вариант", callback_data="retry"),
                InlineKeyboardButton("📋 Меню", callback_data="menu"),
            ]
        ]
    )


async def send_long_text(update_or_query, text: str, reply_markup=None) -> None:
    """Отправляет текст, разбивая его на части при превышении лимита Telegram."""
    message = (
        update_or_query.message
        if isinstance(update_or_query, Update)
        else update_or_query
    )
    chunks = [text[i : i + TG_MESSAGE_LIMIT] for i in range(0, len(text), TG_MESSAGE_LIMIT)]
    for i, chunk in enumerate(chunks):
        is_last = i == len(chunks) - 1
        await message.reply_text(chunk, reply_markup=reply_markup if is_last else None)


async def run_generation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет накопленный диалог модели и показывает результат."""
    chat = update.effective_chat
    provider = get_provider(context)
    user_id = update.effective_user.id

    profile = profiles.get_profile(user_id)
    system = {"role": "system", "content": build_system_prompt(profile)}
    history = context.user_data.get("history", [])[-HISTORY_LIMIT:]

    status = await chat.send_message(
        f"⏳ Генерирую через {llm.PROVIDER_LABELS[provider]}..."
    )
    await chat.send_action(ChatAction.TYPING)

    try:
        answer = await llm.generate(provider, [system] + history)
    except Exception:
        logger.exception("Ошибка генерации (%s)", provider)
        await status.edit_text(
            "😔 Не получилось сгенерировать ответ. Проверьте ключи API "
            "или попробуйте ещё раз чуть позже."
        )
        return

    context.user_data.setdefault("history", []).append(
        {"role": "assistant", "content": answer}
    )

    await status.delete()
    if len(answer) <= TG_MESSAGE_LIMIT:
        await chat.send_message(answer, reply_markup=after_answer_keyboard())
    else:
        chunks = [
            answer[i : i + TG_MESSAGE_LIMIT]
            for i in range(0, len(answer), TG_MESSAGE_LIMIT)
        ]
        for i, chunk in enumerate(chunks):
            is_last = i == len(chunks) - 1
            await chat.send_message(
                chunk, reply_markup=after_answer_keyboard() if is_last else None
            )


# ---------------------------------------------------------------------------
# Команды
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    has_profile = profiles.get_profile(user_id) is not None
    greeting = (
        "👋 Привет! Я — ваш контент-ассистент для ВКонтакте.\n\n"
        "Помогу придумать идеи постов, написать прогрев, продающий текст, "
        "кейс, отработать возражения или доработать ваш черновик — "
        "в вашем стиле и с оформлением под ВК.\n\n"
    )
    if has_profile:
        greeting += "Выберите, что создаём 👇"
    else:
        greeting += (
            "⚙️ Совет: начните с команды /setup — расскажите о себе, "
            "и я буду писать в вашем стиле.\n\nИли сразу выберите сценарий 👇"
        )
    await update.message.reply_text(greeting, reply_markup=main_menu_keyboard(context))


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Выберите, что создаём 👇", reply_markup=main_menu_keyboard(context)
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "ℹ️ Как пользоваться ботом\n\n"
        "1. /setup — настройте бота под свой стиль (ниша, аудитория, тон, офферы). "
        "Это займёт 2 минуты и сильно улучшит тексты.\n\n"
        "2. /menu — выберите сценарий: идеи, готовый пост, прогрев, продающий пост, "
        "кейс, отработка возражений или доработка вашего текста.\n\n"
        "3. Ответьте на вопрос бота — и получите результат.\n\n"
        "4. После генерации можно попросить правки обычным сообщением "
        "(«сделай короче», «добавь юмора», «замени CTA на запись в лс») "
        "или нажать «Ещё вариант».\n\n"
        "Другие команды:\n"
        "/profile — посмотреть или изменить профиль\n"
        "/model — переключить нейросеть (OpenAI ↔ GigaChat)\n"
        "/reset — очистить контекст текущего диалога"
    )


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("history", None)
    context.user_data.pop("scenario", None)
    context.user_data.pop("awaiting_input", None)
    await update.message.reply_text(
        "🧹 Контекст очищен. Выберите новый сценарий 👇",
        reply_markup=main_menu_keyboard(context),
    )


async def cmd_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Выберите нейросеть для генерации:",
        reply_markup=model_keyboard(context),
    )


async def cmd_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_profile(update.message, update.effective_user.id)


async def show_profile(message, user_id: int) -> None:
    profile = profiles.get_profile(user_id)
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✏️ Настроить заново", callback_data="profile:redo")],
            [InlineKeyboardButton("🗑 Сбросить", callback_data="profile:reset")],
            [InlineKeyboardButton("📋 Меню", callback_data="menu")],
        ]
    )
    if profile:
        await message.reply_text(
            "⚙️ Ваш профиль эксперта:\n\n" + profiles.format_profile(profile),
            reply_markup=keyboard,
        )
    else:
        await message.reply_text(
            "Профиль пока не настроен — я пишу в нейтральном тоне.\n"
            "Запустите настройку командой /setup.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("📋 Меню", callback_data="menu")]]
            ),
        )


# ---------------------------------------------------------------------------
# Настройка профиля (/setup) — диалог из 5 вопросов
# ---------------------------------------------------------------------------

async def setup_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["setup_answers"] = {}
    context.user_data["setup_index"] = 0
    await update.effective_chat.send_message(
        "⚙️ Настроим бота под ваш стиль. Я задам 5 коротких вопросов.\n"
        "Отменить настройку можно командой /cancel.\n"
    )
    await update.effective_chat.send_message(profiles.PROFILE_FIELDS[0][1])
    return SETUP_STATE


async def setup_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    index = context.user_data["setup_index"]
    field_key = profiles.PROFILE_FIELDS[index][0]
    context.user_data["setup_answers"][field_key] = update.message.text.strip()

    index += 1
    if index < len(profiles.PROFILE_FIELDS):
        context.user_data["setup_index"] = index
        await update.message.reply_text(profiles.PROFILE_FIELDS[index][1])
        return SETUP_STATE

    profiles.save_profile(update.effective_user.id, context.user_data["setup_answers"])
    context.user_data.pop("setup_answers", None)
    context.user_data.pop("setup_index", None)
    await update.message.reply_text(
        "✅ Готово! Профиль сохранён — теперь тексты будут в вашем стиле.\n\n"
        "Посмотреть профиль: /profile\nВыберите, что создаём 👇",
        reply_markup=main_menu_keyboard(context),
    )
    return ConversationHandler.END


async def setup_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("setup_answers", None)
    context.user_data.pop("setup_index", None)
    await update.message.reply_text(
        "Настройка отменена. Вернуться к ней можно командой /setup.",
        reply_markup=main_menu_keyboard(context),
    )
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Переключение модели
# ---------------------------------------------------------------------------

def model_keyboard(context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardMarkup:
    current = get_provider(context)
    rows = []
    for provider, label in llm.PROVIDER_LABELS.items():
        mark = "✅ " if provider == current else ""
        rows.append(
            [InlineKeyboardButton(mark + label, callback_data=f"model:set:{provider}")]
        )
    rows.append([InlineKeyboardButton("📋 Меню", callback_data="menu")])
    return InlineKeyboardMarkup(rows)


# ---------------------------------------------------------------------------
# Обработка нажатий кнопок
# ---------------------------------------------------------------------------

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu":
        await query.message.reply_text(
            "Выберите, что создаём 👇", reply_markup=main_menu_keyboard(context)
        )

    elif data.startswith("scenario:"):
        scenario_key = data.split(":", 1)[1]
        context.user_data["scenario"] = scenario_key
        context.user_data["awaiting_input"] = True
        context.user_data["history"] = []  # новый сценарий — новый контекст
        await query.message.reply_text(
            f"{SCENARIOS[scenario_key]['button']}\n\n{SCENARIOS[scenario_key]['ask']}"
        )

    elif data == "retry":
        history = context.user_data.get("history")
        if not history:
            await query.message.reply_text(
                "Сначала выберите сценарий 👇", reply_markup=main_menu_keyboard(context)
            )
            return
        context.user_data["history"].append(
            {
                "role": "user",
                "content": "Предложи другой вариант того же текста: сохрани задачу "
                "и требования, но измени подачу, заголовок и структуру.",
            }
        )
        await run_generation(update, context)

    elif data == "model:menu":
        await query.message.reply_text(
            "Выберите нейросеть для генерации:", reply_markup=model_keyboard(context)
        )

    elif data.startswith("model:set:"):
        provider = data.split(":", 2)[2]
        if not llm.provider_available(provider):
            await query.message.reply_text(
                f"⚠️ {llm.PROVIDER_LABELS[provider]} не настроен: добавьте ключ "
                "в файл .env и перезапустите бота."
            )
            return
        context.user_data["provider"] = provider
        await query.message.reply_text(
            f"🧠 Переключил модель: теперь генерирую через "
            f"{llm.PROVIDER_LABELS[provider]}.\n\nВыберите, что создаём 👇",
            reply_markup=main_menu_keyboard(context),
        )

    elif data == "profile:show":
        await show_profile(query.message, update.effective_user.id)

    elif data == "profile:reset":
        profiles.delete_profile(update.effective_user.id)
        await query.message.reply_text(
            "🗑 Профиль сброшен. Настроить заново: /setup",
            reply_markup=main_menu_keyboard(context),
        )

    elif data == "profile:redo":
        await query.message.reply_text("Запустите настройку командой /setup 🙂")


# ---------------------------------------------------------------------------
# Обработка текстовых сообщений
# ---------------------------------------------------------------------------

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    scenario_key = context.user_data.get("scenario")

    # Первый ответ после выбора сценария — подставляем его в шаблон промпта
    if context.user_data.get("awaiting_input") and scenario_key:
        context.user_data["awaiting_input"] = False
        user_prompt = build_user_prompt(scenario_key, text)
        context.user_data["history"] = [{"role": "user", "content": user_prompt}]
        await run_generation(update, context)
        return

    # Продолжение диалога — правки к уже сгенерированному тексту
    if context.user_data.get("history"):
        context.user_data["history"].append({"role": "user", "content": text})
        await run_generation(update, context)
        return

    # Сообщение без выбранного сценария — показываем меню
    await update.message.reply_text(
        "Выберите сценарий, и я помогу с контентом 👇",
        reply_markup=main_menu_keyboard(context),
    )


# ---------------------------------------------------------------------------
# Запуск
# ---------------------------------------------------------------------------

def main() -> None:
    if not TELEGRAM_TOKEN:
        raise SystemExit("Не задан TELEGRAM_TOKEN в файле .env")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    setup_conversation = ConversationHandler(
        entry_points=[CommandHandler("setup", setup_start)],
        states={
            SETUP_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_answer)]
        },
        fallbacks=[CommandHandler("cancel", setup_cancel)],
    )

    app.add_handler(setup_conversation)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("model", cmd_model))
    app.add_handler(CommandHandler("profile", cmd_profile))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("✅ Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
