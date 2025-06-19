from django.contrib import admin

from .models import ImageForTopic, StartMessage, Topic


class ImageForTopicInline(admin.TabularInline):
    model = ImageForTopic
    extra = 1


class TopicAdmin(admin.ModelAdmin):
    inlines = [ImageForTopicInline]
    list_display = ("title", "created_by", "created_at")

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class StartMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "created_by", "created_at")

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


admin.site.register(Topic, TopicAdmin)
admin.site.register(StartMessage, StartMessageAdmin)
