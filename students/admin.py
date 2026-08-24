from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Student, Guardian, Attendance
from .resources import StudentResource

@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "phone", "email")
    search_fields = ("first_name", "last_name", "phone")

@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource
    list_display = ("admission_number", "full_name", "class_room", "guardian", "status")
    search_fields = ("admission_number", "first_name", "middle_name", "last_name")  # now you can search middle name too
    list_filter = ("status", "class_room", "gender")
    list_per_page = 25

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "status", "recorded_by")
    list_filter = ("status", "date", "student__class_room")
    search_fields = ("student__first_name", "student__middle_name", "student__last_name", "student__admission_number")
    date_hierarchy = "date"