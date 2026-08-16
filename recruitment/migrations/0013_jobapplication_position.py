import django.db.models.deletion
from django.db import migrations, models


def copy_requisition_position(apps, schema_editor):
    JobApplication = apps.get_model("recruitment", "JobApplication")
    for app in JobApplication.objects.select_related("requisition").all():
        position_id = getattr(app.requisition, "position_id", None) if app.requisition_id else None
        if position_id:
            app.position_id = position_id
            app.save(update_fields=["position_id"])
        else:
            app.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("recruitment", "0012_alter_candidate_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobapplication",
            name="position",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="applications",
                to="recruitment.jobposition",
                verbose_name="ตำแหน่งที่สมัคร",
            ),
        ),
        migrations.RunPython(copy_requisition_position, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="jobapplication",
            name="requisition",
        ),
        migrations.AlterField(
            model_name="jobapplication",
            name="position",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="applications",
                to="recruitment.jobposition",
                verbose_name="ตำแหน่งที่สมัคร",
            ),
        ),
    ]
