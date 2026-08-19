import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recruitment", "0018_jobapplication_status_start_work"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="employeerecord",
            name="contract_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("permanent", "สัญญาพนักงานประจำ"),
                    ("daily", "สัญญาพนักงานจ้างรายวัน"),
                    ("ba", "สัญญาจ้าง BA"),
                ],
                default="",
                max_length=20,
                verbose_name="ประเภทสัญญา",
            ),
        ),
        migrations.CreateModel(
            name="ContractTemplate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "contract_type",
                    models.CharField(
                        choices=[
                            ("permanent", "สัญญาพนักงานประจำ"),
                            ("daily", "สัญญาพนักงานจ้างรายวัน"),
                            ("ba", "สัญญาจ้าง BA"),
                        ],
                        max_length=20,
                        verbose_name="ประเภทสัญญา",
                    ),
                ),
                ("name", models.CharField(max_length=200, verbose_name="ชื่อเอกสาร")),
                (
                    "file",
                    models.FileField(
                        upload_to="contract_templates/",
                        verbose_name="ไฟล์แม่แบบ (.docx)",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="เปิดใช้งาน"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="อัปโหลดโดย",
                    ),
                ),
            ],
            options={
                "verbose_name": "แม่แบบสัญญา",
                "verbose_name_plural": "แม่แบบสัญญา",
                "ordering": ["contract_type", "name"],
            },
        ),
    ]
