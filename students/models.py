from django.db import models
from django.utils import timezone
import datetime

class Guardian(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    alternative_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Student(models.Model):
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("TRANSFERRED", "Transferred"),
        ("GRADUATED", "Graduated"),
    ]

    admission_number = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        editable=False  # so users can't manually type a duplicate
    )

    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)

    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES
    )

    date_of_birth = models.DateField()

    guardian = models.ForeignKey(
        Guardian,
        on_delete=models.CASCADE,
        related_name="students"
    )

    class_room = models.ForeignKey(
        "academics.ClassRoom",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students"
    )

    photo = models.ImageField(
        upload_to="students/",
        blank=True,
        null=True
    )

    admission_date = models.DateField(auto_now_add=True)

    admission_year = models.PositiveIntegerField(
        default=datetime.date.today().year
    )

    nationality = models.CharField(
        max_length=50,
        default="Tanzanian"
    )

    religion = models.CharField(
        max_length=50,
        blank=True
    )

    blood_group = models.CharField(
        max_length=5,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["first_name", "last_name"]

    def save(self, *args, **kwargs):
        if not self.admission_number:
            year = datetime.date.today().year
            prefix = f"TSMS-{year}-"
            
            # Get the last student with this year's prefix
            last_student = Student.objects.filter(admission_number__startswith=prefix).order_by('admission_number').last()
            
            if last_student:
                try:
                    last_number = int(last_student.admission_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
                
            self.admission_number = f"{prefix}{new_number:04d}"

        super().save(*args, **kwargs)

    @property
    def full_name(self):
        name = f"{self.first_name} {self.middle_name} {self.last_name}"
        return " ".join(name.split()) # removes double spaces if no middle name

    @property
    def attendance_stats(self):
        total = self.attendance.count()
        present = self.attendance.filter(status="P").count()
        absent = self.attendance.filter(status="A").count()
        late = self.attendance.filter(status="L").count()

        percentage = (present / total * 100) if total else 0

        return {
            "total": total,
            "present": present,
            "absent": absent,
            "late": late,
            "percentage": round(percentage, 2),
        }

    def __str__(self):
        return f"{self.admission_number} - {self.full_name}"
    

class Attendance(models.Model):
    STATUS_CHOICES = [
        ("P", "Present"),
        ("A", "Absent"),
        ("L", "Late"),
        ("E", "Excused"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendance"
    )

    date = models.DateField(default=timezone.now)

    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default="P"
    )

    remarks = models.CharField(
        max_length=255,
        blank=True
    )

    recorded_by = models.ForeignKey(
        "academics.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_records"
    )

    class Meta:
        ordering = ["-date", "student__first_name"]
        unique_together = ("student", "date")
        verbose_name = "Attendance"
        verbose_name_plural = "Attendance"

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.get_status_display()}"