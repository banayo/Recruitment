from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recruitment", "0009_requisition_split_approval_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="line_user_id",
            field=models.CharField(
                blank=True,
                help_text="LINE userId จาก LINE Login สำหรับแจ้งเตือน",
                max_length=64,
                null=True,
                unique=True,
            ),
        ),
    ]
