from django.shortcuts import render
from django.db.models import Count, Avg
from students.models import Student
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404
from academics.models import ClassRoom, Subject, Teacher, AcademicYear, Term, Exam, ExamResult, StudentReport

def superuseruser_requred(user):
    return user.is_superuser

@user_passes_test(superuseruser_requred, login_url='/')
def dashboard_view(request):
    # Stats
    total_students = Student.objects.count()
    total_classes = ClassRoom.objects.count()
    total_teachers = Teacher.objects.count()
    total_subjects = Subject.objects.count()
    
    students_per_class = ClassRoom.objects.annotate(student_count=Count('students')).order_by('level', 'stream')
    
    # Academic - FIXED
    current_year = AcademicYear.objects.filter(is_active=True).first()
    
    exam_performance = []
    active_exam_name = "None"
    total_reports = 0
    
    if current_year:
        # Get last 4 exams for this year
        exams = Exam.objects.filter(term__academic_year=current_year).order_by('-id')[:4]
        total_reports = StudentReport.objects.filter(exam__term__academic_year=current_year).count()
        
        for exam in exams:
            exam_results = ExamResult.objects.filter(exam=exam)
            if exam_results.exists():
                avg_score = exam_results.aggregate(avg=Avg('average_marks'))['avg'] or 0
                pass_count = exam_results.filter(average_marks__gte=40).count()
                total_papers = exam_results.count()
                pass_percentage = (pass_count / total_papers * 100) if total_papers > 0 else 0
                
                exam_performance.append({
                    'name': exam.name,
                    'term': exam.term.name,
                    'avg_score': round(avg_score, 2),
                    'pass_percentage': round(pass_percentage, 2),
                    'total_students': total_papers
                })
        
        # Set active exam to the latest one
        if exams:
            active_exam_name = exams[0].name

    context = {
        'total_students': total_students,
        'total_classes': total_classes,
        'total_teachers': total_teachers,
        'total_subjects': total_subjects,
        'students_per_class': students_per_class,
        'exam_performance': exam_performance,
        'total_reports': total_reports,
        'active_exam_name': active_exam_name,
        'current_year': current_year,
    }
    return render(request, 'dashboard/main_dashboard.html', context)