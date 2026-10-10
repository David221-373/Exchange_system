
from django.db import migrations, models


def forwards_role_manager(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(role="executor").update(role="manager")


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("admin", "Администратор"),
                    ("client", "Клиент"),
                    ("manager", "Менеджер"),
                ],
                default="client",
                max_length=20,
            ),
        ),
        migrations.RunPython(forwards_role_manager, migrations.RunPython.noop),
    ]
