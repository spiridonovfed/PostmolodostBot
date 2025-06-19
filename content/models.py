from django.conf import settings
from django.db import models

MARKDOWN_HELP = "Форматирование: *жирный* , _курсив_ , `моноширинный` , [ссылка](https://example.com)"


class Topic(models.Model):
    title = models.TextField(blank=False, null=False)
    text = models.TextField(blank=False, null=False, help_text=MARKDOWN_HELP)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Topic: {self.title[:50]}"


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


class ImageForTopic(models.Model):
    topic = models.ForeignKey(Topic, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="topic_images/")
    caption = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Image for {self.topic.title[:20]}"
