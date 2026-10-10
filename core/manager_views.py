from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from orders.models import ExchangeOrder
from orders.services import ManagerActionError, manager_cancel_order, manager_complete_order, manager_take_order
from users.models import UserRole


def _is_manager(user):
    return user.is_authenticated and user.role == UserRole.MANAGER


@login_required
@user_passes_test(_is_manager)
def manager_desk(request):
    orders = ExchangeOrder.objects.select_related(
        "client", "handled_by", "rate__base_currency", "rate__quote_currency", "city"
    ).order_by("-created_at")
    return render(
        request,
        "core/manager_desk.html",
        {
            "orders": orders,
            "new_orders": orders.filter(status="created"),
            "in_progress": orders.filter(status="in_progress"),
            "done_orders": orders.filter(status="completed")[:30],
            "canceled_orders": orders.filter(status="canceled")[:30],
        },
    )


@login_required
@user_passes_test(_is_manager)
@require_POST
def manager_take(request, pk):
    try:
        manager_take_order(int(pk), request.user)
        messages.success(request, "Заявка взята в работу.")
    except ExchangeOrder.DoesNotExist:
        messages.error(request, "Заявка не найдена.")
    except ManagerActionError as exc:
        messages.error(request, str(exc))
    return redirect("manager-desk")


@login_required
@user_passes_test(_is_manager)
@require_POST
def manager_complete(request, pk):
    try:
        manager_complete_order(int(pk), request.user)
        messages.success(request, "Заявка отмечена как исполнена.")
    except ExchangeOrder.DoesNotExist:
        messages.error(request, "Заявка не найдена.")
    except ManagerActionError as exc:
        messages.error(request, str(exc))
    return redirect("manager-desk")


@login_required
@user_passes_test(_is_manager)
@require_POST
def manager_cancel(request, pk):
    try:
        manager_cancel_order(int(pk), request.user)
        messages.success(request, "Заявка отменена.")
    except ExchangeOrder.DoesNotExist:
        messages.error(request, "Заявка не найдена.")
    except ManagerActionError as exc:
        messages.error(request, str(exc))
    return redirect("manager-desk")
