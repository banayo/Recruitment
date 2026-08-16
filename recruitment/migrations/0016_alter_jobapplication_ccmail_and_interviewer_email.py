from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recruitment", "0015_remove_jobapplication_employee_code_delete_interview"),
    ]

    operations = [
        migrations.AlterField(
            model_name="jobapplication",
            name="ccmail",
            field=models.CharField(
                blank=True,
                help_text="คั่นด้วยจุลภาคเมื่อมีผู้สัมภาษณ์มากกว่า 1 คน",
                max_length=500,
                null=True,
                verbose_name="อีเมลผู้สัมภาษณ์เพิ่มเติม",
            ),
        ),
        migrations.AlterField(
            model_name="jobapplication",
            name="interviewer_email",
            field=models.EmailField(
                blank=True,
                max_length=100,
                null=True,
                verbose_name="อีเมลผู้สัมภาษณ์หลัก",
            ),
        ),
    ]
