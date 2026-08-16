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
        max_length=50, blank=True, help_text="person_unid ของผู้จัดการตรงของผู้ใช้งานนี้"
    )
    gender = models.CharField(max_length=50, blank=True, help_text="เพศของผู้ใช้งานนี้")
    division = models.CharField(max_length=100, blank=True, help_text="ฝ่ายของผู้ใช้งานนี้")
    department = models.CharField(max_length=100, blank=True, help_text="แผนกของผู้ใช้งานนี้")
    location = models.CharField(max_length=100, blank=True, help_text="สถานที่ของผู้ใช้งานนี้")
    nickname = models.CharField(max_length=100, blank=True, help_text="ชื่อเล่นของผู้ใช้งานนี้")
    company_code = models.CharField(
        max_length=50, blank=True, help_text="รหัสบริษัทของผู้ใช้งานนี้"
    )
    role = models.CharField(
        max_length=50, blank=True, default="", help_text="From Authentik claim `role` (e.g. HR)"
    )
    line_user_id = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        help_text="LINE userId จาก LINE Login สำหรับแจ้งเตือน",
    )

    def __str__(self):
        return self.nickname or self.get_full_name() or self.person_unid or self.username


class Company(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="ชื่อบริษัท")
    is_active = models.BooleanField(default=True, verbose_name="เปิดใช้งาน")

    class Meta:
        verbose_name = "1. ชื่อบริษัท"
        verbose_name_plural = "1. ชื่อบริษัท (Master Data)"

    def __str__(self):
        return self.name


class WorkLocation(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="สถานที่ทำงาน")
    is_active = models.BooleanField(default=True, verbose_name="เปิดใช้งาน")

    class Meta:
        verbose_name = "2. สถานที่ทำงาน"
        verbose_name_plural = "2. สถานที่ทำงาน (Master Data)"

    def __str__(self):
        return self.name


class EmployeeLevel(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="ระดับพนักงาน")
    is_active = models.BooleanField(default=True, verbose_name="เปิดใช้งาน")

    class Meta:
        verbose_name = "3. ระดับพนักงาน"
        verbose_name_plural = "3. ระดับพนักงาน (Master Data)"

    def __str__(self):
        return self.name


class Division(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Department(models.Model):
    division = models.ForeignKey(
        Division,
        on_delete=models.PROTECT,
        related_name="departments",
        help_text="ฝ่ายที่ตำแหน่งนี้อยู่",
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
    description = models.TextField(blank=True, help_text="คำอธิบายของตำแหน่งนี้")
    current_headcount = models.PositiveIntegerField(
        default=0, help_text="จำนวนคนปัจจุบันในตำแหน่งนี้"
    )
    target_headcount = models.PositiveIntegerField(
        default=0,
        help_text="ความจุของตำแหน่งนี้ (เพิ่มขึ้นเมื่อคำขออัตรากำลังถูกอนุมัติ)",
    )

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

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requisitions",
        help_text="ผู้ขอสร้างใบนี้",
    )
    approver_unid = models.CharField(max_length=50, db_index=True)
    position = models.ForeignKey(
        JobPosition,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="requisitions",
        help_text="ตำแหน่งที่ผู้ใช้งานของผู้ใช้งานนี้",
    )
    position_title = models.CharField(
        max_length=200, blank=True, help_text="ชื่อตำแหน่งที่ผู้ใช้งานของผู้ใช้งานนี้"
    )
    required_headcount = models.PositiveIntegerField(
        help_text="จำนวนคนที่ผู้ใช้งานของผู้ใช้งานนี้ของผู้ใช้งานนี้"
    )
    approved_headcount = models.PositiveIntegerField(
        default=0, help_text="จำนวนคนที่ผู้ใช้งานของผู้ใช้งานนี้ของผู้ใช้งานนี้"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.NORMAL
    )
    job_description = models.TextField(
        blank=True, help_text="คำอธิบายของตำแหน่งที่ผู้ใช้งานของผู้ใช้งานนี้"
    )
    approver_note = models.TextField(blank=True, help_text="หมายเหตุของผู้อนุมัติ")
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


class Candidate(models.Model):
    title_name_th = models.CharField(
        max_length=20, null=True, blank=True, verbose_name="คำนำหน้า (ไทย)"
    )
    first_name_th = models.CharField(max_length=100, verbose_name="ชื่อ (ไทย)")
    last_name_th = models.CharField(max_length=100, verbose_name="นามสกุล (ไทย)")
    title_name = models.CharField(
        max_length=20, null=True, blank=True, verbose_name="คำนำหน้า (Eng)"
    )
    first_name = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="ชื่อ (Eng)"
    )
    last_name = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="นามสกุล (Eng)"
    )
    nickname = models.CharField(
        max_length=30, null=True, blank=True, verbose_name="ชื่อเล่น"
    )
    email = models.EmailField(
        max_length=100, unique=True, null=True, blank=True, verbose_name="อีเมล"
    )
    phone_number = models.CharField(
        max_length=15, unique=True, verbose_name="เบอร์โทรศัพท์"
    )
    phone_number1 = models.CharField(
        max_length=15, null=True, blank=True, verbose_name="เบอร์โทรศัพท์สำรอง"
    )
    idcard = models.CharField(
        max_length=13, null=True, blank=True, verbose_name="เลขบัตรประชาชน"
    )
    birthday = models.DateField(null=True, blank=True, verbose_name="วันเกิด")
    address = models.TextField(null=True, blank=True, verbose_name="ที่อยู่บัตรประชาชน")
    province = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="จังหวัด"
    )
    amphure = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="เขต/อำเภอ"
    )
    tambon = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="แขวง"
    )
    zip = models.CharField(
        max_length=5, null=True, blank=True, verbose_name="รหัสไปรษณีย์"
    )
    address_present = models.TextField(
        null=True, blank=True, verbose_name="ที่อยู่ปัจจุบัน"
    )
    province_present = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="จังหวัดปัจจุบัน"
    )
    amphure_present = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="เขต/อำเภอปัจจุบัน"
    )
    tambon_present = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="แขวงปัจจุบัน"
    )
    zip_present = models.CharField(
        max_length=5, null=True, blank=True, verbose_name="รหัสไปรษณีย์ปัจจุบัน"
    )
    marital_status = models.CharField(
        max_length=10, null=True, blank=True, verbose_name="สถานภาพ"
    )
    sex = models.CharField(max_length=5, null=True, blank=True, verbose_name="เพศ")
    profile_picture = models.ImageField(
        upload_to="candidate_photos/", null=True, blank=True, verbose_name="รูปถ่าย"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ผู้สมัคร"
        verbose_name_plural = "ผู้สมัคร"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name_th} {self.last_name_th}".strip()


class JobApplication(models.Model):
    class Status(models.TextChoices):
        APPLIED = "applied", "สมัครใหม่"
        INTERVIEWING = "interviewing", "นัดสัมภาษณ์"
        NOT_SELECTED = "not_selected", "สัมภาษณ์ไม่ผ่าน"
        OFFERED = "offered", "เสนอจ้างงาน"
        HIRED = "hired", "รับเข้าทำงาน"
        REJECTED = "rejected", "ไม่มาทำงาน"
        CANCELLED = "cancelled", "ยกเลิก"

    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name="applications"
    )
    position = models.ForeignKey(
        JobPosition,
        on_delete=models.PROTECT,
        related_name="applications",
        verbose_name="ตำแหน่งที่สมัคร",
    )

    resume = models.FileField(
        upload_to="resumes/%Y/%m/", null=True, blank=True, verbose_name="ไฟล์ Resume"
    )
    portfolio = models.FileField(
        upload_to="portfolios/%Y/%m/",
        null=True,
        blank=True,
        verbose_name="ไฟล์ Portfolio",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.APPLIED,
        verbose_name="สถานะใบสมัคร",
    )
    origin = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="แหล่งที่มา (เช่น JobThai)"
    )
    hr_note = models.TextField(null=True, blank=True, verbose_name="บันทึกจาก HR")
    appointment_date = models.DateTimeField(
        null=True, blank=True, verbose_name="วันเวลานัดสัมภาษณ์"
    )
    interviewer_names = models.CharField(
        max_length=255, blank=True, default="", verbose_name="ผู้สัมภาษณ์"
    )
    interviewer_email = models.EmailField(
        max_length=100, null=True, blank=True, verbose_name="อีเมลผู้สัมภาษณ์หลัก"
    )
    ccmail = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="อีเมลผู้สัมภาษณ์เพิ่มเติม",
        help_text="คั่นด้วยจุลภาคเมื่อมีผู้สัมภาษณ์มากกว่า 1 คน",
    )
    is_online = models.BooleanField(default=False, verbose_name="สัมภาษณ์ออนไลน์")
    meeting_link = models.URLField(
        max_length=500, null=True, blank=True, verbose_name="ลิงก์ประชุม"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "ใบสมัครงาน"
        verbose_name_plural = "ใบสมัครงาน"

    @property
    def applied_date(self):
        return self.created_at

    def __str__(self):
        return f"{self.candidate} -> สมัครตำแหน่ง: {self.position}"


class EmployeeRecord(models.Model):
    employee_code = models.CharField(
        max_length=20, unique=True, verbose_name="รหัสพนักงาน"
    )
    candidate = models.OneToOneField(
        Candidate,
        on_delete=models.CASCADE,
        related_name="employee_record",
        verbose_name="ข้อมูลบุคคล",
    )
    application = models.OneToOneField(
        JobApplication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hired_record",
        verbose_name="อ้างอิงจากใบสมัคร",
    )
    start_date = models.DateField(verbose_name="วันที่เริ่มงาน")
    company = models.ForeignKey(
        Company, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="บริษัท"
    )
    location = models.ForeignKey(
        WorkLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="สถานที่ทำงาน",
    )
    employee_level = models.ForeignKey(
        EmployeeLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ระดับพนักงาน",
    )
    is_active = models.BooleanField(default=False, verbose_name="สถานะยังทำงานอยู่")
    resign_date = models.DateField(null=True, blank=True, verbose_name="วันที่ลาออก")
    resign_note = models.TextField(null=True, blank=True, verbose_name="หมายเหตุลาออก")
    update_tiger_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ประวัติพนักงาน"
        verbose_name_plural = "ประวัติพนักงาน"
        ordering = ["-start_date"]

    def __str__(self):
        return self.employee_code


RELATION_CHOICES = [
    ("father", "บิดา"),
    ("mother", "มารดา"),
    ("relative", "ญาติ"),
    ("sibling", "พี่น้อง"),
    ("other", "อื่นๆ"),
]


class Acquaintance(models.Model):
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="acquaintances",
        verbose_name="ข้อมูลผู้สมัคร",
    )
    name = models.CharField(max_length=200, verbose_name="ชื่อ-นามสกุล")
    phone_number = models.CharField(max_length=15, verbose_name="เบอร์โทรศัพท์")
    relation = models.CharField(
        max_length=20,
        choices=RELATION_CHOICES,
        null=True,
        blank=True,
        verbose_name="ความสัมพันธ์",
    )

    class Meta:
        verbose_name = "บุคคลอ้างอิง/คนรู้จัก"
        verbose_name_plural = "บุคคลอ้างอิง/คนรู้จัก"

    def __str__(self):
        return f"{self.name} ({self.get_relation_display()})"


class Guarantor(models.Model):
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="guarantors",
        verbose_name="ข้อมูลผู้สมัคร",
    )
    name = models.CharField(max_length=200, verbose_name="ชื่อ-นามสกุล")
    address = models.TextField(null=True, blank=True, verbose_name="ที่อยู่ติดต่อ")
    phone_number = models.CharField(max_length=15, verbose_name="เบอร์โทรศัพท์")
    relation = models.CharField(
        max_length=20,
        choices=RELATION_CHOICES,
        null=True,
        blank=True,
        verbose_name="ความสัมพันธ์",
    )

    class Meta:
        verbose_name = "ผู้ค้ำประกัน"
        verbose_name_plural = "ผู้ค้ำประกัน"

    def __str__(self):
        return f"{self.name} (ค้ำประกันให้: {self.candidate.first_name_th})"


class Study(models.Model):
    COUNTRY_CHOICES = [
        ("thai", "ไทย"),
        ("foreign", "ต่างประเทศ"),
    ]
    EDUCATION_CHOICES = [
        ("middle_school", "ระดับชั้นมัธยมศึกษาตอนต้น"),
        ("high_school", "ระดับชั้นมัธยมศึกษาตอนปลาย"),
        ("vocational", "ประกาศนียบัตรวิชาชีพ (ปวช.)"),
        ("higher_vocational", "ประกาศนียบัตรวิชาชีพชั้นสูง (ปวส.)"),
        ("bachelor", "ระดับปริญญาตรี"),
        ("master", "ปริญญาโท"),
        ("doctorate", "ปริญญาเอก"),
    ]
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="studies",
        verbose_name="ข้อมูลผู้สมัคร",
    )
    institution = models.CharField(max_length=200, verbose_name="สถาบันที่จบ")
    graduation = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="ปีที่จบ"
    )
    grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="เกรดเฉลี่ย (GPA)",
    )
    country = models.CharField(
        max_length=30,
        choices=COUNTRY_CHOICES,
        default="thai",
        verbose_name="จบในประเทศไหน",
    )
    education = models.CharField(
        max_length=100, choices=EDUCATION_CHOICES, verbose_name="ระดับการศึกษา"
    )
    major = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="สาขาที่จบ"
    )

    class Meta:
        verbose_name = "ประวัติการศึกษา"
        verbose_name_plural = "ประวัติการศึกษา"
        ordering = ["-graduation"]

    def __str__(self):
        return f"{self.get_education_display()} - {self.institution}"
