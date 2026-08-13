from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recruitment", "0007_requisition_position_title"),
    ]

    operations = [
        migrations.AddField(
            model_name="requisition",
            name="approver_note",
            field=models.TextField(
                blank=True, help_text="Notes written by the approving manager"
            ),
        ),
    ]
