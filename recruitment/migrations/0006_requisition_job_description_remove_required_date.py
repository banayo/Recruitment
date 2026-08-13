from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recruitment", "0005_remove_job_code"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="requisition",
            name="required_date",
        ),
        migrations.AddField(
            model_name="requisition",
            name="job_description",
            field=models.TextField(
                blank=True, help_text="Job details provided by the requester"
            ),
        ),
    ]
