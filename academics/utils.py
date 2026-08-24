from django.db import transaction
from .models import Exam, ExamResult, StudentReport
from students.models import Student

@transaction.atomic
def generate_student_reports(exam_id):
    exam = Exam.objects.select_related('class_room', 'term').get(id=exam_id)
    
    # 1. Get students in this class who have at least 1 result for this exam
    students_with_results = Student.objects.filter(
        class_room=exam.class_room,
        exam_results__exam=exam
    ).distinct()

    created_count = 0
    updated_count = 0

    for student in students_with_results:
        report, created = StudentReport.objects.get_or_create(
            student=student,
            exam=exam,
        )
        
        # Force recalc even if it existed
        report.save()  # This triggers total/average calc in StudentReport.save()
        
        if created:
            created_count += 1
        else:
            updated_count += 1

    # 2. Recalculate class positions ONCE after all reports are made
    _recalculate_class_positions(exam)

    return f"Created: {created_count}, Updated: {updated_count} reports"

def _recalculate_class_positions(exam):
    reports = StudentReport.objects.filter(
        exam=exam,
        student__class_room=exam.class_room
    ).order_by('-average_marks')
    
    total = reports.count()
    for position, report in enumerate(reports, start=1):
        StudentReport.objects.filter(id=report.id).update(
            class_position=position,
            total_students=total
        )