from django.db import models


class DirectionType(models.TextChoices):
    CASH_TO_CRYPTO = "cash_to_crypto", "Наличные -> Крипта"
    CRYPTO_TO_CASH = "crypto_to_cash", "Крипта -> Наличные"
    CRYPTO_TO_CRYPTO = "crypto_to_crypto", "Крипта -> Крипта"


class Currency(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    is_crypto = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Валюта"
        verbose_name_plural = "Валюты"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class ExchangeRate(models.Model):
    base_currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="base_rates")
    quote_currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="quote_rates")
    direction_type = models.CharField(
        max_length=30, choices=DirectionType.choices, default=DirectionType.CRYPTO_TO_CRYPTO
    )
    margin = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=0.03,
        help_text="Маржа (спред) обменника. Пример: 0.03 = 3%",
    )
    buy_rate = models.DecimalField(max_digits=18, decimal_places=8)
    sell_rate = models.DecimalField(max_digits=18, decimal_places=8)
    source = models.CharField(max_length=50, default="manual")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Курс обмена"
        verbose_name_plural = "Курсы обмена"
        constraints = [
            models.UniqueConstraint(
                fields=["base_currency", "quote_currency", "direction_type"],
                name="unique_rate_pair",
            )
        ]
        indexes = [models.Index(fields=["is_active", "updated_at"])]

    def __str__(self) -> str:
        return f"{self.base_currency}/{self.quote_currency}"


class ExchangeRateHistory(models.Model):
    rate = models.ForeignKey(ExchangeRate, on_delete=models.CASCADE, related_name="history")
    buy_rate = models.DecimalField(max_digits=18, decimal_places=8)
    sell_rate = models.DecimalField(max_digits=18, decimal_places=8)
    source = models.CharField(max_length=50, default="manual")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "История курса"
        verbose_name_plural = "История курсов"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["created_at"])]
