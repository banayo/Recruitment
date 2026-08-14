from django.db import migrations, models


def forwards(apps, schema_editor):
    Requisition = apps.get_model("recruitment", "Requisition")
    Requisition.objects.filter(status="approved").update(status="hr_approved")


def backwards(apps, schema_editor):
    Requisition = apps.get_model("recruitment", "Requisition")
    Requisition.objects.filter(status="hr_approved").update(status="approved")
    Requisition.objects.filter(status="manager_approved").update(status="approved")


class Migration(migrations.Migration):

    dependencies = [
        ("recruitment", "0008_requisition_approver_note"),
    ]

    operations = [
        migrations.AlterField(
            model_name="requisition",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "รออนุมัติ"),
                    ("manager_approved", "หัวหน้าอนุมัติแล้ว"),
                    ("hr_approved", "ฝ่ายบุคคลอนุมัติแล้ว"),
                    ("rejected", "ยกเลิก"),
                    ("in_progress", "กำลังดำเนินการ"),
                    ("closed", "ปิด"),
                ],
                db_index=True,
                default="pending",
                max_length=20,
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
