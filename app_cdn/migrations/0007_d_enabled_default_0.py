# Generated manually - d.enabled default 0

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app_cdn", "0006_invalid_rename_did_ct"),
    ]

    operations = [
        migrations.AlterField(
            model_name="distribution",
            name="enabled",
            field=models.BooleanField(default=False),
        ),
    ]
