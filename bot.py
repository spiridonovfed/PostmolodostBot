import os

from asgiref.sync import sync_to_async
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from content.models import StartMessage, Topic
from retriever import TopicRetriever

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
KEYBOARD_PAGE_SIZE = 10

retriever = TopicRetriever()


def make_topic_keyboard(topics, page, page_size):
    current_start = page * page_size
    current_end = current_start + page_size
    topics_page = topics[current_start:current_end]

    keyboard = [[InlineKeyboardButton(topic["title"], callback_data=f"topic_{topic['id']}")] for topic in topics_page]

    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"page_{page - 1}"))
    if current_end < len(topics):
        navigation_buttons.append(InlineKeyboardButton("➡️ Далее", callback_data=f"page_{page + 1}"))
    if navigation_buttons:
        keyboard.append(navigation_buttons)
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages = await sync_to_async(list)(StartMessage.objects.order_by("id"))
    if not messages:
        return

    for msg in messages:
        await update.message.reply_text(msg.message, parse_mode="Markdown")


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_input_vector = retriever.model.encode([user_input], normalize_embeddings=True)[0]
    scores = retriever.embeddings @ user_input_vector

    min_score = 0.65
    top_k = 4

    top_indices = [i for i in scores.argsort()[::-1] if scores[i] >= min_score]

    if not top_indices:
        await update.message.reply_text(
            "Извините, я не смог найти подходящих тем. Попробуйте переформулировать "
            "вопрос или воспользуйтесь /list для просмотра всех тем.",
            parse_mode="Markdown",
        )
        return

    top_indices = top_indices[:top_k]
    buttons = [
        [InlineKeyboardButton(retriever.topics[i]["title"], callback_data=f"topic_{retriever.topics[i]['id']}")]
        for i in top_indices
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        "Наиболее подходящие темы:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    sorted_topics = sorted(retriever.topics, key=lambda t: t["title"].lower())
    page_size = KEYBOARD_PAGE_SIZE

    if data.startswith("topic_"):
        topic_id = int(data[6:])
        topic = await sync_to_async(lambda: Topic.objects.prefetch_related("images").get(id=topic_id))()
        title = topic.title
        text = topic.text
        text = f"*{title}*\n\n{text}"
        await query.message.reply_text(text, parse_mode="Markdown")

        images = list(topic.images.all())
        for img in images:
            img_path = img.image.path
            caption = img.caption or ""
            with open(img_path, "rb") as photo:
                await query.message.reply_photo(photo=photo, caption=caption if caption else None)

    elif data.startswith("page_"):
        page = int(data[5:])
        reply_markup = make_topic_keyboard(sorted_topics, page, page_size)
        await query.edit_message_reply_markup(reply_markup=reply_markup)


async def list_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topics = retriever.topics
    if not topics:
        await update.message.reply_text("Список тем пока пуст.", parse_mode="Markdown")
        return

    sorted_topics = sorted(topics, key=lambda t: t["title"].lower())
    page = 0
    reply_markup = make_topic_keyboard(sorted_topics, page, KEYBOARD_PAGE_SIZE)
    await update.message.reply_text(
        "Все доступные темы:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def refresh_topics_from_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await sync_to_async(retriever.refresh_topics_from_db)()
    await update.message.reply_text("Список тем был успешно обновлён!", parse_mode="Markdown")


async def post_init(application):
    commands = [
        BotCommand("start", "Показать приветствие"),
        BotCommand("list", "Показать все доступные темы (по алфавиту)"),
        BotCommand("refresh", "Обновить список тем из БД (для админов)"),
    ]
    await application.bot.set_my_commands(commands)


def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_topics))
    app.add_handler(CommandHandler("refresh", refresh_topics_from_db))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    app.add_handler(CallbackQueryHandler(handle_button))

    app.run_polling()
