from django.core.management.base import BaseCommand

import bot


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if not bot.BOT_TOKEN:
            self.stderr.write("Attention: Please set TELEGRAM_BOT_TOKEN environmental variable")
            return

        bot.run_bot()
