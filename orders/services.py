from django.db import transaction
from django.utils import timezone

from orders.models import ExchangeOrder, OrderStatus


class ManagerActionError(Exception):
    """Ошибка бизнес-логики действия менеджера."""


def manager_take_order(order_pk: int, user) -> ExchangeOrder:
    with transaction.atomic():
        order = ExchangeOrder.objects.select_for_update().get(pk=order_pk)
        if order.status != OrderStatus.CREATED:
            raise ManagerActionError("Можно взять только новую заявку.")
        if order.handled_by_id:
            raise ManagerActionError("Заявку уже взял другой менеджер.")
        order.handled_by = user
        order.status = OrderStatus.IN_PROGRESS
        order.save(update_fields=["handled_by", "status"])
    return order


def manager_complete_order(order_pk: int, user) -> ExchangeOrder:
    with transaction.atomic():
        order = ExchangeOrder.objects.select_for_update().get(pk=order_pk)
        if order.status != OrderStatus.IN_PROGRESS:
            raise ManagerActionError('Можно завершить только заявку со статусом «В обработке».')
        if order.handled_by_id != user.id:
            raise ManagerActionError("Эту заявку ведёт другой менеджер.")
        order.status = OrderStatus.COMPLETED
        order.completed_at = timezone.now()
        order.save(update_fields=["status", "completed_at"])
    return order


def manager_cancel_order(order_pk: int, user) -> ExchangeOrder:
    with transaction.atomic():
        order = ExchangeOrder.objects.select_for_update().get(pk=order_pk)
        if order.status not in {OrderStatus.IN_PROGRESS, OrderStatus.CREATED}:
            raise ManagerActionError("Эту заявку нельзя отменить.")
        if order.status == OrderStatus.IN_PROGRESS and order.handled_by_id != user.id:
            raise ManagerActionError("Эту заявку ведёт другой менеджер.")
        order.status = OrderStatus.CANCELED
        order.save(update_fields=["status"])
    return order
