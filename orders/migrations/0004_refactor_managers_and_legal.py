import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def forwards_fix_status(apps, schema_editor):
    ExchangeOrder = apps.get_model("orders", "ExchangeOrder")
    ExchangeOrder.objects.filter(status="in_review").update(status="in_progress")


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0003_exchangeorder_city_exchangeorder_contact_email_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(forwards_fix_status, migrations.RunPython.noop),
        migrations.RenameField(
            model_name="exchangeorder",
            old_name="executor",
            new_name="handled_by",
        ),
        migrations.AlterField(
            model_name="exchangeorder",
            name="handled_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="managed_orders",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Менеджер",
            ),
        ),
        migrations.AlterField(
            model_name="exchangeorder",
            name="status",
            field=models.CharField(
                choices=[
                    ("created", "Новая заявка"),
                    ("in_progress", "В обработке"),
                    ("completed", "Исполнена"),
                    ("canceled", "Отменена"),
                ],
                default="created",
                max_length=20,
            ),
        ),
    ]
