import os
import logging
import asyncio

from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ========== НАСТРОЙКИ ==========

BOT_TOKEN = os.getenv("8574767944:AAFbyzaPW7T7e5ieFkKdPcVOAYGe124ovKE")
GROQ_API_KEY = os.getenv("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")

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DevAI")

if not BOT_TOKEN:
    raise RuntimeError("Добавь переменную BOT_TOKEN на Bothost")

if not GROQ_API_KEY:
    raise RuntimeError("Добавь переменную GROQ_API_KEY на Bothost")

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
Ты DevAI — умный ИИ-помощник для разработчиков.

Ты умеешь:
- Писать код на Python, JavaScript, HTML, CSS и других языках.
- Создавать сайты и Telegram-ботов.
- Исправлять ошибки и объяснять их причины.
- Помогать с API, базами данных и серверами.
- Объяснять код простым языком.
- Создавать полноценные примеры проектов.

Отвечай на русском языке.
Форматируй код с помощью Markdown.
Если пользователь просит полный код, предоставляй его целиком.
Не утверждай, что запускал код, если этого не делал.
"""

# ========== МЕНЮ ==========

def get_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💻 Написать код",
                callback_data="code"
            ),
            InlineKeyboardButton(
                "🛠 Исправить ошибку",
                callback_data="fix"
            ),
        ],
        [
            InlineKeyboardButton(
                "🌐 Создать сайт",
                callback_data="site"
            ),
            InlineKeyboardButton(
                "🧠 Объяснить код",
                callback_data="explain"
            ),
        ],
        [
            InlineKeyboardButton(
                "⚡ Помощь с API",
                callback_data="api"
            ),
            InlineKeyboardButton(
                "💬 Общий чат",
                callback_data="chat"
            ),
        ],
    ])


MODES = {
    "code": "Помогай писать качественный код. Предоставляй полные примеры.",
    "fix": "Находи ошибки, объясняй причины и предлагай исправленный код.",
    "site": "Помогай создавать сайты на HTML, CSS и JavaScript.",
    "explain": "Объясняй программный код подробно и простым языком.",
    "api": "Помогай подключать API и показывай примеры интеграции.",
    "chat": "Отвечай на вопросы пользователя.",
}


# ========== КОМАНДЫ ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "chat"
    context.user_data["history"] = []

    await update.effective_message.reply_text(
        "🤖 Добро пожаловать в DevAI!\n\n"
        "Я нейросеть для разработчиков.\n\n"
        "💻 Генерирую код\n"
        "🌐 Создаю сайты\n"
        "🛠 Исправляю ошибки\n"
        "🧠 Объясняю программирование\n"
        "⚡ Помогаю с API\n\n"
        "Выбери режим или просто напиши вопрос.",
        reply_markup=get_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "📚 Команды:\n\n"
        "/start — главное меню\n"
        "/help — помощь\n"
        "/clear — очистить историю\n"
        "/model — информация о модели"
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["history"] = []
    await update.effective_message.reply_text(
        "🧹 История диалога очищена!"
    )


async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"🧠 Текущая модель: {MODEL}\n"
        "⚡ Провайдер: Groq"
    )


# ========== ПЕРЕКЛЮЧЕНИЕ РЕЖИМОВ ==========

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    mode = query.data
    context.user_data["mode"] = mode

    descriptions = {
        "code": "💻 Режим программирования включён!\nОпиши, что нужно написать.",
        "fix": "🛠 Режим исправления ошибок включён!\nПришли код и ошибку.",
        "site": "🌐 Режим создания сайтов включён!\nОпиши свой сайт.",
        "explain": "🧠 Режим объяснения кода включён!\nПришли код.",
        "api": "⚡ Режим помощи с API включён!\nОпиши задачу.",
        "chat": "💬 Общий чат включён!\nЗадавай вопросы.",
    }

    await query.message.reply_text(
        descriptions.get(mode, "Напиши свой вопрос.")
    )


# ========== GROQ AI ==========

async def ask_ai(prompt, context):
    history = context.user_data.setdefault("history", [])
    mode = context.user_data.get("mode", "chat")

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
            + "\n\nТекущий режим: "
            + MODES.get(mode, MODES["chat"]),
        }
    ]

    messages.extend(history[-10:])

    messages.append({
        "role": "user",
        "content": prompt,
    })

    response = await asyncio.to_thread(
        client.chat.completions.create,
        model=MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=4000,
    )

    answer = response.choices[0].message.content

    if not answer:
        answer = "Не удалось получить ответ. Попробуй ещё раз."

    history.extend([
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": answer},
    ])

    context.user_data["history"] = history[-10:]

    return answer


# ========== ОБРАБОТКА СООБЩЕНИЙ ==========

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not message or not message.text:
        return

    prompt = message.text.strip()

    if not prompt:
        return

    if len(prompt) > 12000:
        await message.reply_text(
            "⚠️ Сообщение слишком длинное. Сократи его до 12000 символов."
        )
        return

    status = await message.reply_text("🧠 DevAI думает...")

    try:
        answer = await ask_ai(prompt, context)

        # Telegram ограничивает длину сообщения
        chunks = [
            answer[i:i + 4000]
            for i in range(0, len(answer), 4000)
        ]

        await status.edit_text(chunks[0])

        for chunk in chunks[1:]:
            await message.reply_text(chunk)

    except Exception:
        logger.exception("Ошибка Groq API")

        await status.edit_text(
            "❌ Не удалось получить ответ.\n\n"
            "Проверь:\n"
            "• API-ключ Groq\n"
            "• Доступность выбранной модели\n"
            "• Лимиты API\n"
            "• Интернет-соединение хостинга"
        )


# ========== ЗАПУСК ==========

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("model", model_command))

    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler,
        )
    )

    logger.info("DevAI запускается!")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()