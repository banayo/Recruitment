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
    approve_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="person_unid of this user's direct manager",
    )
    gender = models.CharField(max_length=50, blank=True)
    division = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    nickname = models.CharField(max_length=100, blank=True)
    company_code = models.CharField(max_length=50, blank=True)
    role = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="From Authentik claim `role` (e.g. HR)",
    )

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.nickname or self.get_full_name() or self.person_unid or self.username


class Division(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Department(models.Model):
    division = models.ForeignKey(
        Division, on_delete=models.PROTECT, related_name="departments"
    )
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class JobPosition(models.Model):
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="positions"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    current_headcount = models.PositiveIntegerField(
        default=0, help_text="People currently in this position"
    )
    target_headcount = models.PositiveIntegerField(
        default=0, help_text="Open headcount quota (incremented on approved requisitions)"
    )

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Requisition(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        IN_PROGRESS = "in_progress", "In Progress"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        URGENT = "urgent", "Urgent"
        NORMAL = "normal", "Normal"

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requisitions",
    )
    # Manager may not exist in DB yet (JIT) — store person_unid string, not FK
    approver_unid = models.CharField(max_length=50, db_index=True)
    position = models.ForeignKey(
        JobPosition,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="requisitions",
        help_text="Nullable until HR maps an official job position",
    )
    position_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Requested job title from the requester",
    )
    required_headcount = models.PositiveIntegerField(
        help_text="Headcount requested by the manager/requester"
    )
    approved_headcount = models.PositiveIntegerField(
        default=0, help_text="Headcount approved (may differ from required)"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.NORMAL
    )
    job_description = models.TextField(
        blank=True, help_text="Job details provided by the requester"
    )
    approver_note = models.TextField(
        blank=True, help_text="Notes written by the approving manager"
    )
    is_headcount_synced = models.BooleanField(
        default=False,
        help_text="True after approved quota has been applied to JobPosition.target_headcount",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["approver_unid", "status"]),
            models.Index(fields=["requester", "status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.approver_unid and self.requester_id:
            self.approver_unid = self.requester.approve_code
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Requisition #{self.pk} ({self.status})"
