from django.conf import settings
from django.db import models


class FAQ(models.Model):
    question = models.TextField(blank=False, null=False)
    answer = models.TextField(blank=False, null=False)
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
        return f"Q: {self.question[:50]}..."
