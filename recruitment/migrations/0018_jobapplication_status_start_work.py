from django.db import migrations, models


def forwards(apps, schema_editor):
    JobApplication = apps.get_model("recruitment", "JobApplication")
    JobApplication.objects.filter(status="offered").update(status="start_work")
    JobApplication.objects.filter(status="hired").update(status="working")
    JobApplication.objects.filter(status="rejected").update(status="not_come_work")


def backwards(apps, schema_editor):
    JobApplication = apps.get_model("recruitment", "JobApplication")
    JobApplication.objects.filter(status="start_work").update(status="offered")
    JobApplication.objects.filter(status="working").update(status="hired")
    JobApplication.objects.filter(status="not_come_work").update(status="rejected")


class Migration(migrations.Migration):
    dependencies = [
        ("recruitment", "0017_jobapplication_start_work_date"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
        migrations.AlterField(
            model_name="jobapplication",
            name="status",
            field=models.CharField(
                choices=[
                    ("applied", "สมัครใหม่"),
                    ("interviewing", "นัดสัมภาษณ์"),
                    ("not_selected", "สัมภาษณ์ไม่ผ่าน"),
                    ("start_work", "นัดเริ่มงาน"),
                    ("not_come_work", "ไม่มาทำงาน"),
                    ("working", "ทำงานอยู่"),
                    ("resigned", "ลาออก"),
                    ("cancelled", "ยกเลิก"),
                ],
                default="applied",
                max_length=20,
                verbose_name="สถานะใบสมัคร",
            ),
        ),
    ]
