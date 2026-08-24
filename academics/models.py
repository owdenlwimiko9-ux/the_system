from django.db import models
from django.db.models import Sum, Avg


class AcademicYear(models.Model):
    name = models.CharField(max_length=9, unique=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["-name"]
        verbose_name = "Academic Year"
        verbose_name_plural = "Academic Years"

    def __str__(self):
        return self.name


class Term(models.Model):
    TERM_CHOICES = [
        ("TERM1", "Term 1"),
        ("TERM2", "Term 2"),
        ("TERM3", "Term 3"),
        ("TERM4", "Term 4"),
    ]

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="terms"
    )

    name = models.CharField(
        max_length=10,
        choices=TERM_CHOICES
    )

    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        unique_together = ("academic_year", "name")
        ordering = ["academic_year", "name"]

    def __str__(self):
        return f"{self.academic_year} - {self.get_name_display()}"


class Teacher(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    photo = models.ImageField(upload_to='teachers/', blank=True, null=True)

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class ClassRoom(models.Model):
    # Group the levels into the 3 main systems
    LEVEL_GROUP = {
        # Pre & Primary
        'BABY': 'PRE_PRIMARY', 'MIDDLE': 'PRE_PRIMARY', 'TOP': 'PRE_PRIMARY',
        'G1': 'PRE_PRIMARY', 'G2': 'PRE_PRIMARY', 'G3': 'PRE_PRIMARY', 
        'G4': 'PRE_PRIMARY', 'G5': 'PRE_PRIMARY', 'G6': 'PRE_PRIMARY', 'G7': 'PRE_PRIMARY',
        # Ordinary Level - you'll add these later
        'F1': 'ORDINARY', 'F2': 'ORDINARY', 'F3': 'ORDINARY', 'F4': 'ORDINARY',
        # Advanced Level - you'll add these later  
        'F5': 'ADVANCED', 'F6': 'ADVANCED',
    }

    LEVEL_CHOICES = [
        # PRE & PRIMARY - Green
        ("BABY", "Baby"),
        ("MIDDLE", "Middle"),
        ("TOP", "Top"),
        ("G1", "Grade 1"),
        ("G2", "Grade 2"),
        ("G3", "Grade 3"),
        ("G4", "Grade 4"),
        ("G5", "Grade 5"),
        ("G6", "Grade 6"),
        ("G7", "Grade 7"),
        # ORDINARY LEVEL - Blue
        ("F1", "Form 1"),
        ("F2", "Form 2"),
        ("F3", "Form 3"),
        ("F4", "Form 4"),
        # ADVANCED LEVEL - Red
        ("F5", "Form 5"),
        ("F6", "Form 6"),
    ]

    STREAM_CHOICES = [
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
    ]

    level = models.CharField(
        max_length=10,
        choices=LEVEL_CHOICES
    )

    stream = models.CharField(
        max_length=1,
        choices=STREAM_CHOICES
    )

    class_teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="classrooms"
    )

    class Meta:
        unique_together = ("level", "stream")
        ordering = ["level", "stream"]

    def __str__(self):
        return f"{self.get_level_display()} {self.stream}"
    
    @property
    def level_group(self):
        """Returns: PRE_PRIMARY, ORDINARY, or ADVANCED"""
        return self.LEVEL_GROUP.get(self.level, 'PRE_PRIMARY')
    
class Subject(models.Model):
    name = models.CharField(max_length=100)

    class_room = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE,
        related_name="subjects"
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subjects"
    )

    class Meta:
        unique_together = ("name", "class_room")
        ordering = ["class_room", "name"]

    def __str__(self):
        return f"{self.name} - {self.class_room}"


class Exam(models.Model):
    EXAM_TYPES = [
        ("MIDTERM", "Mid Term"),
        ("TERMINAL", "Terminal"),
        ("MIDTERM", "Mid Term"),
        ("ANNUAL", "Annual"),
    ]

    name = models.CharField(max_length=100)

    exam_type = models.CharField(
        max_length=20,
        choices=EXAM_TYPES
    )

    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name="exams"
    )

    class_room = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE,
        related_name="exams"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["term", "class_room", "name"]

    def __str__(self):
        return f"{self.name} - {self.class_room}"


class GradeScale(models.Model):
    grade = models.CharField(max_length=2)

    minimum_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    maximum_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    remark = models.CharField(max_length=100)

    class Meta:
        ordering = ["-minimum_mark"]

    def __str__(self):
        return f"{self.grade} ({self.minimum_mark}-{self.maximum_mark})"
    
class ExamResult(models.Model):

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="exam_results"
    )

    points = models.PositiveIntegerField(default=0)

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="results"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="results"
    )

    test_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    exam_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    total_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        editable=False
    )

    average_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        editable=False
    )

    grade = models.CharField(
        max_length=2,
        blank=True,
        editable=False
    )

    remark = models.CharField(
        max_length=100,
        blank=True,
        editable=False
    )

    position = models.PositiveIntegerField(
        null=True,
        blank=True,
        editable=False
    )


    class Meta:
        unique_together = (
            "student",
            "exam",
            "subject",
        )

        ordering = [
            "student__class_room",
            "subject",
            "-average_marks",
        ]


    def save(self, *args, **kwargs):

        # Calculate total marks
        self.total_marks = (
            self.test_marks +
            self.exam_marks
        )


        # Calculate average
        self.average_marks = (
            self.total_marks / 2
        )


        # Find grade
        scale = GradeScale.objects.filter(
            minimum_mark__lte=self.average_marks,
            maximum_mark__gte=self.average_marks
        ).first()


        if scale:
            self.grade = scale.grade
            self.remark = scale.remark

        else:
            self.grade = ""
            self.remark = ""


        # Save result first
        super().save(*args, **kwargs)


        # Calculate subject position
        results = ExamResult.objects.filter(
            exam=self.exam,
            subject=self.subject,
            student__class_room=self.student.class_room
        ).order_by(
            "-average_marks"
        )


        for position, result in enumerate(
            results,
            start=1
        ):

            if result.position != position:

                ExamResult.objects.filter(
                    id=result.id
                ).update(
                    position=position
                )


    def __str__(self):

        return (
            f"{self.student.full_name} - "
            f"{self.subject.name} - "
            f"{self.average_marks}"
        )
    
class StudentReport(models.Model):
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="reports"
    )

    division_points = models.PositiveIntegerField(default=0)
    division = models.CharField(max_length=20, default='-')

    total_points = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True, blank=True)

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="student_reports"
    )

    total_marks = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )

    average_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    class_position = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    total_students = models.PositiveIntegerField(
        default=0
    )

    teacher_remark = models.TextField(blank=True)

    head_teacher_remark = models.TextField(blank=True)

    def __str__(self):
        year = self.academic_year.name if self.academic_year else "N/A"
        return f"{self.student} - {self.exam} {year}"



    class Meta:
        unique_together = ("student", "exam")
        ordering = [
            "student__class_room",
            "class_position"
        ]


    def save(self, *args, **kwargs):

        # Calculate total and average from ExamResult
        results = ExamResult.objects.filter(
            student=self.student,
            exam=self.exam
        )

        self.total_marks = results.aggregate(
            total=Sum("total_marks")
        )["total"] or 0


        self.average_marks = results.aggregate(
            average=Avg("average_marks")
        )["average"] or 0


        # Automatic performance remark
        if self.average_marks >= 75:
            self.teacher_remark = "Excellent"

        elif self.average_marks >= 65:
            self.teacher_remark = "Very Good"

        elif self.average_marks >= 45:
            self.teacher_remark = "Good"

        elif self.average_marks >= 30:
            self.teacher_remark = "Fair"

        else:
            self.teacher_remark = "Needs Improvement"


        super().save(*args, **kwargs)


        # Calculate class position
        reports = StudentReport.objects.filter(
            exam=self.exam,
            student__class_room=self.student.class_room
        ).order_by("-average_marks")


        total = reports.count()


        for position, report in enumerate(reports, start=1):

            StudentReport.objects.filter(
                id=report.id
            ).update(
                class_position=position,
                total_students=total
            )


    def __str__(self):
        return f"{self.student.full_name} - {self.exam}"