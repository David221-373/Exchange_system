from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "admin", "Администратор"
    CLIENT = "client", "Клиент"
    MANAGER = "manager", "Менеджер"


class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.CLIENT)
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        indexes = [models.Index(fields=["role"])]

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        # Keep role consistent with Django superuser privileges.
        if self.is_superuser and self.role != UserRole.ADMIN:
            self.role = UserRole.ADMIN
        super().save(*args, **kwargs)
