from rest_framework import serializers

from .models import FAQ


class FAQSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()  # Shows username, not user id

    class Meta:
        model = FAQ
        fields = ["id", "question", "answer", "created_at", "created_by"]
