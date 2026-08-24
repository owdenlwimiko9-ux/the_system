from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    AcademicYear,
    Term,
    Teacher,
    ClassRoom,
    Subject,
    Exam,
    GradeScale,
    ExamResult,
    StudentReport,
)

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
    )

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = (
        "academic_year",
        "name",
        "start_date",
        "end_date",
    )

    list_filter = (
        "academic_year",
        "name",
    )

    search_fields = (
        "name",
        "academic_year__name",
    )

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "phone",
        "email",
    )

    search_fields = (
        "first_name",
        "last_name",
        "phone",
        "email",
    )

@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = (
        "level",
        "stream",
        "class_teacher",
    )

    list_filter = (
        "level",
        "stream",
    )

    search_fields = (
        "level",
        "stream",
    )

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "class_room",
        "teacher",
    )

    list_filter = (
        "class_room",
        "teacher",
    )

    search_fields = (
        "name",
    )

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "exam_type",
        "class_room",
        "term",
        "is_active",
        "generate_reports_button", 
        "bulk_upload_button"
    )

    list_filter = (
        "exam_type",
        "term",
        "class_room",
        "is_active",
    )

    search_fields = (
        "name",
        "class_room__level",
    )

    def bulk_upload_button(self, obj):
        url = reverse('academics:bulk_upload_results', args=[obj.id])
        return format_html('<a class="button" href="{}">Upload Excel</a>', url)
    bulk_upload_button.short_description = 'Bulk Upload'

    def generate_reports_button(self, obj):
        # FIX: Added namespace 'academics:' and use class_room.id instead of exam.id
        url = reverse(
            "academics:generate_reports",
            args=[obj.class_room.id]
        )

        return format_html(
            '<a class="button" href="{}" style="background:#4CAF50; color:white; padding:5px 10px; border-radius:3px; text-decoration:none;">Generate Reports</a>',
            url
        )

    generate_reports_button.short_description = "Reports"

@admin.register(GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    list_display = (
        "grade",
        "minimum_mark",
        "maximum_mark",
        "remark",
    )

    ordering = (
        "-minimum_mark",
    )

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "exam",
        "subject",
        "test_marks",
        "exam_marks",
        "total_marks",
        "average_marks",
        "grade",
        "position",
    )

    list_filter = (
        "exam",
        "subject",
        "grade",
    )

    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__admission_number",
        "subject__name",
    )

    readonly_fields = (
        "total_marks",
        "average_marks",
        "grade",
        "remark",
        "position",
    )

@admin.register(StudentReport)
class StudentReportAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "student_class",
        "exam",
        "total_marks",
        "average_marks",
        "class_position",
        "total_students",
        "performance",
    )

    list_filter = (
        "exam",
        "student__class_room",
    )

    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__admission_number",
    )

    readonly_fields = (
        "total_marks",
        "average_marks",
        "class_position",
        "total_students",
    )

    fieldsets = (
        (
            "Student Information",
            {
                "fields": (
                    "student",
                    "exam",
                )
            }
        ),

        (
            "Performance",
            {
                "fields": (
                    "total_marks",
                    "average_marks",
                    "class_position",
                    "total_students",
                )
            }
        ),

        (
            "Remarks",
            {
                "fields": (
                    "teacher_remark",
                    "head_teacher_remark",
                )
            }
        ),
    )

    @admin.display(description="Class")
    def student_class(self, obj):
        return obj.student.class_room

    @admin.display(description="Performance")
    def performance(self, obj):
        avg = obj.average_marks or 0

        if avg >= 75:
            return "Excellent"

        elif avg >= 65:
            return "Very Good"

        elif avg >= 45:
            return "Good"

        elif avg >= 30:
            return "Fair"

        return "Needs Improvement"