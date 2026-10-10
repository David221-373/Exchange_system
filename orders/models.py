import random
from django.utils import timezone
from django.db import models

from core.models import City
from rates.models import ExchangeRate
from users.models import User


class OrderStatus(models.TextChoices):
    CREATED = "created", "Новая заявка"
    IN_PROGRESS = "in_progress", "В обработке"
    COMPLETED = "completed", "Исполнена"
    CANCELED = "canceled", "Отменена"


class ExchangeOrder(models.Model):
    public_id = models.CharField(max_length=20, unique=True, editable=False, null=True, blank=True)
    client = models.ForeignKey(User, on_delete=models.PROTECT, related_name="client_orders")
    handled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="managed_orders",
        null=True,
        blank=True,
        verbose_name="Менеджер",
    )
    rate = models.ForeignKey(ExchangeRate, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.CREATED)
    direction_label = models.CharField(max_length=120, default="")
    crypto_amount = models.DecimalField(max_digits=18, decimal_places=8)
    fiat_amount = models.DecimalField(max_digits=18, decimal_places=8)
    total_amount = models.DecimalField(max_digits=18, decimal_places=8)
    rate_buy_snapshot = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    rate_sell_snapshot = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name="orders", null=True, blank=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    planned_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Заявка на обмен"
        verbose_name_plural = "Заявки на обмен"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"])]

    def __str__(self) -> str:
        return f"{self.public_id} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.public_id:
            current_date = timezone.now().strftime("%Y%m%d")
            while True:
                random_part = f"{random.randint(0, 99999):05d}"
                candidate = f"INS-{current_date}-{random_part}"
                if not ExchangeOrder.objects.filter(public_id=candidate).exists():
                    self.public_id = candidate
                    break
        super().save(*args, **kwargs)
