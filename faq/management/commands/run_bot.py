import os

from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from faq.models import StartMessage
from faq.retriever import FAQRetriever

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")


class Command(BaseCommand):
    help = "Запускает Telegram FAQ-бота для ПостМолодость с поддержкой RAG"

    PAGE_SIZE = 10

    def handle(self, *args, **kwargs):
        if not BOT_TOKEN:
            self.stderr.write("Ошибка: Установите переменную окружения TELEGRAM_BOT_TOKEN или укажите токен в коде.")
            return

        retriever = FAQRetriever()

        def make_faq_keyboard(faqs, page, page_size):
            start = page * page_size
            end = start + page_size
            page_faqs = faqs[start:end]
            keyboard = [[InlineKeyboardButton(faq["question"], callback_data=f"faq_{faq['id']}")] for faq in page_faqs]
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"page_{page-1}"))
            if end < len(faqs):
                nav_buttons.append(InlineKeyboardButton("➡️ Далее", callback_data=f"page_{page+1}"))
            if nav_buttons:
                keyboard.append(nav_buttons)
            return InlineKeyboardMarkup(keyboard)

        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            messages = await sync_to_async(list)(StartMessage.objects.order_by("id"))
            if not messages:
                text = (
                    "*👋 Добро пожаловать в ПостМолодость FAQ-бот!*\n\n"
                    "Вы можете задать любой вопрос о нашем пространстве — настольные игры, психотерапия, "
                    "публичные мероприятия и многое другое.\n"
                    "Просто напишите ваш вопрос или используйте команду /list, чтобы увидеть все доступные темы."
                )
                await update.message.reply_text(text, parse_mode="Markdown")
            else:
                for msg in messages:
                    await update.message.reply_text(msg.message, parse_mode="Markdown")

        async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_q = update.message.text
            user_emb = retriever.model.encode([user_q], normalize_embeddings=True)[0]
            scores = retriever.embeddings @ user_emb

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
                [InlineKeyboardButton(retriever.faqs[i]["question"], callback_data=f"faq_{retriever.faqs[i]['id']}")]
                for i in top_indices
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await update.message.reply_text(
                "Вот наиболее подходящие вопросы. Нажмите на интересующий, чтобы увидеть ответ:",
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )

        async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            await query.answer()
            data = query.data

            sorted_faqs = sorted(retriever.faqs, key=lambda f: f["question"].lower())
            page_size = self.PAGE_SIZE

            if data.startswith("faq_"):
                faq_id = int(data[4:])
                faq = next((f for f in retriever.faqs if f["id"] == faq_id), None)
                if faq:
                    question = faq["question"]
                    answer = faq["answer"]
                    text = f"*{question}*\n\n{answer}"
                    await query.message.reply_text(text, parse_mode="Markdown")
                else:
                    await query.message.reply_text("Извините, ответ не найден.", parse_mode="Markdown")

            elif data.startswith("page_"):
                page = int(data[5:])
                reply_markup = make_faq_keyboard(sorted_faqs, page, page_size)
                await query.edit_message_reply_markup(reply_markup=reply_markup)

        async def list_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
            faqs = retriever.faqs
            if not faqs:
                await update.message.reply_text("Список вопросов пока пуст.", parse_mode="Markdown")
                return

            sorted_faqs = sorted(faqs, key=lambda f: f["question"].lower())
            page = 0
            reply_markup = make_faq_keyboard(sorted_faqs, page, self.PAGE_SIZE)
            await update.message.reply_text(
                "Все доступные вопросы:\n\n(Нажмите на вопрос, чтобы получить ответ)",
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )

        async def refresh_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await sync_to_async(retriever.refresh_faqs)()
            await update.message.reply_text("Список вопросов и ответов был успешно обновлён!", parse_mode="Markdown")

        async def post_init(application):
            commands = [
                BotCommand("start", "Показать приветствие и инструкцию"),
                BotCommand("list", "Показать все доступные темы (по алфавиту)"),
                BotCommand("refresh", "Обновить список вопросов и ответов (для админов)"),
            ]
            await application.bot.set_my_commands(commands)

        app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("list", list_questions))
        app.add_handler(CommandHandler("refresh", refresh_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
        app.add_handler(CallbackQueryHandler(button))

        app.run_polling()
