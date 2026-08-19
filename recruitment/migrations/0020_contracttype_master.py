import django.db.models.deletion
from django.db import migrations, models


DEFAULT_TYPES = [
    ("permanent", "สัญญาพนักงานประจำ"),
    ("daily", "สัญญาพนักงานจ้างรายวัน"),
    ("ba", "สัญญาจ้าง BA"),
]


def forwards(apps, schema_editor):
    ContractType = apps.get_model("recruitment", "ContractType")
    EmployeeRecord = apps.get_model("recruitment", "EmployeeRecord")
    ContractTemplate = apps.get_model("recruitment", "ContractTemplate")
    by_code = {}
    for code, name in DEFAULT_TYPES:
        obj, _created = ContractType.objects.get_or_create(
            name=name, defaults={"is_active": True}
        )
        by_code[code] = obj

    def resolve(code):
        code = (code or "").strip()
        if not code:
            return None
        if code in by_code:
            return by_code[code]
        obj, _created = ContractType.objects.get_or_create(
            name=code, defaults={"is_active": True}
        )
        return obj

    for record in EmployeeRecord.objects.all():
        record.contract_type_ref = resolve(record.contract_type)
        record.save(update_fields=["contract_type_ref"])

    fallback = by_code["permanent"]
    for template in ContractTemplate.objects.all():
        template.contract_type_ref = resolve(template.contract_type) or fallback
        template.save(update_fields=["contract_type_ref"])


def backwards(apps, schema_editor):
    EmployeeRecord = apps.get_model("recruitment", "EmployeeRecord")
    ContractTemplate = apps.get_model("recruitment", "ContractTemplate")
    name_to_code = {name: code for code, name in DEFAULT_TYPES}
    for record in EmployeeRecord.objects.select_related("contract_type_ref"):
        name = record.contract_type_ref.name if record.contract_type_ref_id else ""
        record.contract_type = name_to_code.get(name, name[:20] if name else "")
        record.save(update_fields=["contract_type"])
    for template in ContractTemplate.objects.select_related("contract_type_ref"):
        name = template.contract_type_ref.name if template.contract_type_ref_id else ""
        template.contract_type = name_to_code.get(name, "permanent")
        template.save(update_fields=["contract_type"])


class Migration(migrations.Migration):

    dependencies = [
        ("recruitment", "0019_employeerecord_contract_type_and_contracttemplate"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContractType",
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
                    "name",
                    models.CharField(
                        max_length=100, unique=True, verbose_name="ประเภทสัญญา"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="เปิดใช้งาน"),
                ),
            ],
            options={
                "verbose_name": "ประเภทสัญญา",
                "verbose_name_plural": "ประเภทสัญญา (Master Data)",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="employeerecord",
            name="contract_type_ref",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="recruitment.contracttype",
                verbose_name="ประเภทสัญญา",
            ),
        ),
        migrations.AddField(
            model_name="contracttemplate",
            name="contract_type_ref",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="templates",
                to="recruitment.contracttype",
                verbose_name="ประเภทสัญญา",
            ),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.RemoveField(
            model_name="employeerecord",
            name="contract_type",
        ),
        migrations.RemoveField(
            model_name="contracttemplate",
            name="contract_type",
        ),
        migrations.RenameField(
            model_name="employeerecord",
            old_name="contract_type_ref",
            new_name="contract_type",
        ),
        migrations.RenameField(
            model_name="contracttemplate",
            old_name="contract_type_ref",
            new_name="contract_type",
        ),
        migrations.AlterField(
            model_name="contracttemplate",
            name="contract_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="templates",
                to="recruitment.contracttype",
                verbose_name="ประเภทสัญญา",
            ),
        ),
    ]
