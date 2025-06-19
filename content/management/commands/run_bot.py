from django.core.management.base import BaseCommand

from bot import BOT_TOKEN, run_bot


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if not BOT_TOKEN:
            self.stderr.write("Attention: Please set TELEGRAM_BOT_TOKEN environmental variable")
            return

        run_bot()
