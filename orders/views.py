from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsClientRole, IsManagerRole
from orders.models import ExchangeOrder, OrderStatus
from orders.serializers import ExchangeOrderAdminSerializer, ExchangeOrderSerializer
from orders.services import ManagerActionError, manager_cancel_order, manager_complete_order, manager_take_order


class ExchangeOrderViewSet(viewsets.ModelViewSet):
    queryset = ExchangeOrder.objects.select_related("client", "handled_by", "rate").all()
    serializer_class = ExchangeOrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "client", "handled_by", "rate"]

    def get_permissions(self):
        if self.action in {"take", "complete", "cancel"}:
            return [IsManagerRole()]
        if self.action in {"create"}:
            return [IsClientRole()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return self.queryset
        if user.role == "manager":
            return self.queryset
        return self.queryset.filter(client=user)

    def get_serializer_class(self):
        if self.request.user.role == "admin":
            return ExchangeOrderAdminSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(client=self.request.user, status=OrderStatus.CREATED)

    @action(detail=True, methods=["post"], permission_classes=[IsManagerRole])
    def take(self, request, pk=None):
        try:
            order = manager_take_order(int(pk), request.user)
        except ExchangeOrder.DoesNotExist:
            return Response({"detail": "Заявка не найдена."}, status=status.HTTP_404_NOT_FOUND)
        except ManagerActionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ExchangeOrderAdminSerializer(order).data)

    @action(detail=True, methods=["post"], permission_classes=[IsManagerRole])
    def complete(self, request, pk=None):
        try:
            order = manager_complete_order(int(pk), request.user)
        except ExchangeOrder.DoesNotExist:
            return Response({"detail": "Заявка не найдена."}, status=status.HTTP_404_NOT_FOUND)
        except ManagerActionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ExchangeOrderAdminSerializer(order).data)

    @action(detail=True, methods=["post"], permission_classes=[IsManagerRole])
    def cancel(self, request, pk=None):
        try:
            order = manager_cancel_order(int(pk), request.user)
        except ExchangeOrder.DoesNotExist:
            return Response({"detail": "Заявка не найдена."}, status=status.HTTP_404_NOT_FOUND)
        except ManagerActionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ExchangeOrderAdminSerializer(order).data)
