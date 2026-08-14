from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Profile from Authentik claims.
    role is stored on the user (HR / USER) — not from groups, not in session.
    division/department are claim snapshots (varchar), not FKs to org master tables.
    """

    authentik_sub = models.CharField(max_length=255, unique=True)
    person_unid = models.CharField(max_length=50, unique=True)
    approve_code = models.CharField(max_length=50, blank=True, help_text="person_unid ของผู้จัดการตรงของผู้ใช้งานนี้")
    gender = models.CharField(max_length=50, blank=True, help_text="เพศของผู้ใช้งานนี้")
    division = models.CharField(max_length=100, blank=True, help_text="ฝ่ายของผู้ใช้งานนี้")
    department = models.CharField(max_length=100, blank=True, help_text="แผนกของผู้ใช้งานนี้")
    location = models.CharField(max_length=100, blank=True, help_text="สถานที่ของผู้ใช้งานนี้")
    nickname = models.CharField(max_length=100, blank=True, help_text="ชื่อเล่นของผู้ใช้งานนี้")
    company_code = models.CharField(max_length=50, blank=True, help_text="รหัสบริษัทของผู้ใช้งานนี้")
    role = models.CharField(max_length=50, blank=True, default="", help_text="From Authentik claim `role` (e.g. HR)")

    def __str__(self):
        return self.nickname or self.get_full_name() or self.person_unid or self.username


class Division(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Department(models.Model):
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name="departments", help_text="ฝ่ายที่ตำแหน่งนี้อยู่")
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class JobPosition(models.Model):
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="positions")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="คำอธิบายของตำแหน่งนี้")
    current_headcount = models.PositiveIntegerField(default=0, help_text="จำนวนคนปัจจุบันในตำแหน่งนี้")
    target_headcount = models.PositiveIntegerField(default=0, help_text="ความจุของตำแหน่งนี้ (เพิ่มขึ้นเมื่อคำขออัตรากำลังถูกอนุมัติ)")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Requisition(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "รออนุมัติ"
        MANAGER_APPROVED = "manager_approved", "หัวหน้าอนุมัติแล้ว"
        HR_APPROVED = "hr_approved", "ฝ่ายบุคคลอนุมัติแล้ว"
        REJECTED = "rejected", "ยกเลิก"
        IN_PROGRESS = "in_progress", "กำลังดำเนินการ"
        CLOSED = "closed", "ปิด"

    class Priority(models.TextChoices):
        URGENT = "urgent", "ด่วน"
        NORMAL = "normal", "ปกติ"

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requisitions", help_text="ผู้ขอสร้างใบนี้")
    approver_unid = models.CharField(max_length=50, db_index=True)
    position = models.ForeignKey(JobPosition, on_delete=models.PROTECT, null=True, blank=True, related_name="requisitions", help_text="ตำแหน่งที่ผู้ใช้งานของผู้ใช้งานนี้")
    position_title = models.CharField(max_length=200, blank=True, help_text="ชื่อตำแหน่งที่ผู้ใช้งานของผู้ใช้งานนี้")
    required_headcount = models.PositiveIntegerField(help_text="จำนวนคนที่ผู้ใช้งานของผู้ใช้งานนี้ของผู้ใช้งานนี้")
    approved_headcount = models.PositiveIntegerField(default=0, help_text="จำนวนคนที่ผู้ใช้งานของผู้ใช้งานนี้ของผู้ใช้งานนี้")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    job_description = models.TextField(blank=True, help_text="คำอธิบายของตำแหน่งที่ผู้ใช้งานของผู้ใช้งานนี้")
    approver_note = models.TextField(blank=True, help_text="หมายเหตุของผู้อนุมัติ")
    is_headcount_synced = models.BooleanField(default=False, help_text="True after approved quota has been applied to JobPosition.target_headcount")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["approver_unid", "status"]), models.Index(fields=["requester", "status"])]

    def save(self, *args, **kwargs):
        if not self.approver_unid and self.requester_id:
            self.approver_unid = self.requester.approve_code
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Requisition #{self.pk} ({self.status})"
