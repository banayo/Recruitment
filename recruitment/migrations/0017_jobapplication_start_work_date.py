from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recruitment", "0016_alter_jobapplication_ccmail_and_interviewer_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobapplication",
            name="start_work_date",
            field=models.DateField(
                blank=True, null=True, verbose_name="วันที่นัดเริ่มงาน"
            ),
        ),
    ]
