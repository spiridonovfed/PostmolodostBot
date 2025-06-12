from django.contrib import admin

from .models import FAQ


class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "created_by", "created_at")

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


admin.site.register(FAQ, FAQAdmin)
