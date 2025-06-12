from rest_framework import generics

from .models import FAQ
from .serializers import FAQSerializer


class FAQListView(generics.ListAPIView):
    queryset = FAQ.objects.all().order_by("-created_at")
    serializer_class = FAQSerializer
