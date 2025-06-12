import os

from django.core.management.base import BaseCommand
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from faq.retriever import FAQRetriever

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")


class Command(BaseCommand):
    help = "Runs the Telegram FAQ bot using RAG"

    def handle(self, *args, **kwargs):
        if not BOT_TOKEN:
            self.stderr.write("Error: Set TELEGRAM_BOT_TOKEN env variable or hardcode your token.")
            return

        retriever = FAQRetriever()

        async def send_faq_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
            # Store retriever in bot_data for efficiency, or just use the one created above.
            faqs = retriever.faqs
            if not faqs:
                await update.message.reply_text("No FAQs available yet.")
                return

            faq_text = "*Available Questions:*\n\n"
            for idx, faq in enumerate(faqs, 1):
                faq_text += f"{idx}. {faq['question']}\n"
            await update.message.reply_text(faq_text, parse_mode="Markdown")

        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            msg = (
                "👋 Welcome to ПостМолодость FAQ Bot!\n\n"
                "You can ask any question about our space—board games, therapy, public events, and more.\n"
                "Try typing your question, or pick from the list below."
            )
            await update.message.reply_text(msg)
            await send_faq_list(update, context)

        async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            q = update.message.text
            answer, score = retriever.get_best_answer(q)
            if answer:
                reply = answer
            else:
                reply = "Sorry, I don't know the answer to that yet. " "Try asking in a different way or contact staff."
            await update.message.reply_text(reply)

        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
        app.run_polling()
