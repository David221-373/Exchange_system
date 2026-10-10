from django.contrib import admin

from core.models import City, LegalPage, LegalPageRevision


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order", "is_active")
    search_fields = ("name", "slug", "address")
    list_filter = ("is_active",)


class LegalPageRevisionInline(admin.TabularInline):
    model = LegalPageRevision
    extra = 1
    fields = ("body", "author")


@admin.register(LegalPage)
class LegalPageAdmin(admin.ModelAdmin):
    list_display = ("sort_order", "slug", "title")
    search_fields = ("slug", "title")
    ordering = ("sort_order", "title")
    inlines = [LegalPageRevisionInline]
