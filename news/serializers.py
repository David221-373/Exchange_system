from rest_framework import serializers

from news.models import NewsItem


class NewsItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsItem
        fields = "__all__"
        read_only_fields = ["author", "published_at"]
