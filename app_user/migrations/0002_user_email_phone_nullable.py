# Generated manually: align ORM with nullable unique contact columns.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app_user", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="UPDATE user SET email = NULL WHERE email = '';",
            reverse_sql="UPDATE user SET email = '' WHERE email IS NULL;",
        ),
        migrations.RunSQL(
            sql="UPDATE user SET phone = NULL WHERE phone = '';",
            reverse_sql="UPDATE user SET phone = '' WHERE phone IS NULL;",
        ),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=255,
                null=True,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="phone",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=32,
                null=True,
                unique=True,
            ),
        ),
    ]
