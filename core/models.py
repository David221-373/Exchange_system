from django.conf import settings
from django.db import models


class City(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    address = models.CharField(max_length=500, blank=True, help_text="Адрес офиса для публикации на сайте")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class LegalPage(models.Model):
    """Управляемая юридическая/информационная страница (AML, правила)."""

    slug = models.SlugField(max_length=64, unique=True)
    title = models.CharField(max_length=200)
    sort_order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Порядок в футере и списках: меньше — выше.",
    )

    class Meta:
        verbose_name = "Юридическая страница"
        verbose_name_plural = "Юридические страницы"
        ordering = ["sort_order", "title"]

    def __str__(self) -> str:
        return self.slug

    def latest_revision(self):
        return self.revisions.order_by("-created_at").first()


class LegalPageRevision(models.Model):
    page = models.ForeignKey(LegalPage, on_delete=models.CASCADE, related_name="revisions")
    body = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ревизия страницы"
        verbose_name_plural = "Ревизии страниц"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.page.slug} @ {self.created_at:%Y-%m-%d %H:%M}"
