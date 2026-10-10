from django.db import models

from orders.models import ExchangeOrder
from users.models import User


class Review(models.Model):
    order = models.OneToOneField(ExchangeOrder, on_delete=models.CASCADE, related_name="review")
    client = models.ForeignKey(User, on_delete=models.PROTECT, related_name="reviews")
    score = models.PositiveSmallIntegerField()
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(score__gte=1, score__lte=5), name="review_score_between_1_5")
        ]

    def __str__(self) -> str:
        return f"Review #{self.pk} for order #{self.order_id}"
