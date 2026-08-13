from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recruitment", "0006_requisition_job_description_remove_required_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="requisition",
            name="position_title",
            field=models.CharField(
                blank=True,
                help_text="Requested job title from the requester",
                max_length=200,
            ),
        ),
    ]
