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

from faq.retriever import FAQRetriever

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")


class Command(BaseCommand):
    help = "Запускает Telegram FAQ-бота для ПостМолодость с поддержкой RAG"

    def handle(self, *args, **kwargs):
        if not BOT_TOKEN:
            self.stderr.write("Ошибка: Установите переменную окружения TELEGRAM_BOT_TOKEN или укажите токен в коде.")
            return

        retriever = FAQRetriever()

        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            msg = (
                "👋 Добро пожаловать в ПостМолодость FAQ-бот!\n\n"
                "Вы можете задать любой вопрос о нашем пространстве — настольные игры, психотерапия, "
                "публичные мероприятия и многое другое.\n"
                "Просто напишите ваш вопрос или используйте команду /list, чтобы увидеть все доступные темы."
            )
            await update.message.reply_text(msg)

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
                    "вопрос или воспользуйтесь /list для просмотра всех тем."
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
            )

        async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            await query.answer()
            data = query.data
            if data.startswith("faq_"):
                faq_id = int(data[4:])
                faq = next((f for f in retriever.faqs if f["id"] == faq_id), None)
                if faq:
                    await query.message.reply_text(faq["answer"])
                else:
                    await query.message.reply_text("Извините, ответ не найден.")

        async def list_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
            faqs = retriever.faqs
            if not faqs:
                await update.message.reply_text("Список вопросов пока пуст.")
                return

            sorted_faqs = sorted(faqs, key=lambda f: f["question"].lower())
            faq_text = "*Все доступные вопросы:*\n\n"
            for idx, faq in enumerate(sorted_faqs, 1):
                faq_text += f"{idx}. {faq['question']}\n"
            await update.message.reply_text(faq_text, parse_mode="Markdown")

        async def refresh_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await sync_to_async(retriever.refresh_faqs)()
            await update.message.reply_text("Список вопросов и ответов был успешно обновлён!")

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
