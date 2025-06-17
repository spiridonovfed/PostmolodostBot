from django.conf import settings
from django.db import models

MARKDOWN_HELP = "Форматирование: *жирный* , _курсив_ , `моноширинный` , [ссылка](https://example.com)"


class FAQ(models.Model):
    question = models.TextField(blank=False, null=False)
    answer = models.TextField(blank=False, null=False, help_text=MARKDOWN_HELP)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="added_faqs",
        verbose_name="Admin user who added this Q&A",
    )

    def __str__(self):
        return f"Question: {self.question[:50]}"

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"


class StartMessage(models.Model):
    message = models.TextField(blank=False, null=False, help_text=MARKDOWN_HELP)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="added_startmessages",
        verbose_name="Admin user who added this start message",
    )

    def __str__(self):
        return f"StartMessage {self.id}: {self.message[:50]}"

    class Meta:
        verbose_name = "Start message"
        verbose_name_plural = "Start messages"
        ordering = ["id"]
