from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from core.permissions import IsAdminRole
from news.models import NewsItem
from news.serializers import NewsItemSerializer


class NewsItemViewSet(viewsets.ModelViewSet):
    queryset = NewsItem.objects.select_related("author").all()
    serializer_class = NewsItemSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdminRole()]
        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
