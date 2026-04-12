from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app_tcc", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="tccbranchmeta",
                    name="name",
                    field=models.CharField(blank=True, default="", max_length=255),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE branch_meta ADD COLUMN name VARCHAR(255) NOT NULL DEFAULT '';",
                    reverse_sql="ALTER TABLE branch_meta DROP COLUMN name;",
                ),
            ],
        ),
    ]
