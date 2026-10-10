from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from core.permissions import IsAdminRole, IsClientRole
from reviews.models import Review
from reviews.serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related("order", "client").all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in {"create"}:
            return [IsClientRole()]
        if self.action in {"destroy"}:
            return [IsAdminRole()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or user.role == "admin":
            return self.queryset
        return self.queryset.filter(client=user)

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)
