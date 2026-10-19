from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Avg, Sum
from django import forms
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from urllib.parse import quote
from django.utils import timezone
import openpyxl

from .models import AcademicYear, Term, ClassRoom, Subject, Teacher, Exam, ExamResult, StudentReport
from students.models import Student
from .forms import AcademicYearForm, TermForm, SubjectForm, ExamForm, ClassRoomForm

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['first_name', 'last_name', 'email', 'phone', 'photo']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

def get_ordinary_points(score):
    score = float(score or 0)
    if score >= 75: return 1
    elif score >= 65: return 2
    elif score >= 45: return 3
    elif score >= 30: return 4
    else: return 9

def get_advanced_points(score):
    score = float(score or 0)
    if score >= 75: return 1
    elif score >= 65: return 2
    elif score >= 45: return 3
    elif score >= 30: return 4
    else: return 5

def calculate_best_points(all_points, level_group):
    if not all_points: return 0, '-'
    if level_group == 'ORDINARY':
        if 9 in all_points: return sum(all_points), 'Division 0'
        best = sorted(all_points)[:7]
        total = sum(best)
        if 7 <= total <= 17: div = 'Division I'
        elif 18 <= total <= 21: div = 'Division II'
        elif 22 <= total <= 25: div = 'Division III'
        elif 26 <= total <= 34: div = 'Division IV'
        else: div = 'Division 0'
        return total, div
    if level_group == 'ADVANCED':
        if 5 in all_points: return sum(all_points), 'Division 0'
        best = sorted([p for p in all_points if p!=5])[:3]
        total = sum(best)
        if 3 <= total <= 9: div = 'Division I'
        elif 10 <= total <= 11: div = 'Division II'
        elif 12 <= total <= 13: div = 'Division III'
        elif 14 <= total <= 17: div = 'Division IV'
        else: div = 'Division 0'
        return total, div
    return 0, '-'

def _get_student_name(s):
    return f"{getattr(s,'first_name','')} {getattr(s,'middle_name','') or ''} {getattr(s,'last_name','')}".strip()

@login_required
def class_list(request):
    try: classes = list(ClassRoom.objects.all().order_by('level','stream'))
    except: classes = []
    for c in classes:
        try: c.student_count = Student.objects.filter(class_room=c, is_active=True).count()
        except: c.student_count = 0
    try: ac_year = AcademicYear.objects.filter(is_active=True).first()
    except: ac_year = None
    context = {
        'classes_count': ClassRoom.objects.count() if hasattr(ClassRoom,'objects') else 0,
        'students_count': Student.objects.count(),
        'teachers_count': Teacher.objects.count(),
        'subjects_count': Subject.objects.count(),
        'exams_count': Exam.objects.count(),
        'active_year': ac_year,
        'classes': classes
    }
    return render(request, "academics/class_list.html", context)

def class_create(request):
    form = ClassRoomForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Class created successfully')
        return redirect('academics:class_list')
    return render(request, "academics/class_form.html", {'form': form, 'title': 'Add Class'})

def class_update(request, pk):
    cls = get_object_or_404(ClassRoom, pk=pk)
    form = ClassRoomForm(request.POST or None, instance=cls)
    if form.is_valid():
        form.save()
        messages.success(request, 'Class updated successfully')
        return redirect('academics:class_list')
    return render(request, "academics/class_form.html", {'form': form, 'title': 'Edit Class'})

def class_detail(request, pk):
    class_room = get_object_or_404(ClassRoom, id=pk)
    students = Student.objects.filter(class_room=class_room, is_active=True).order_by('first_name')
    subjects = Subject.objects.filter(class_room=class_room)
    academic_year = AcademicYear.objects.filter(is_active=True).first()
    teachers = Teacher.objects.filter(subjects__in=subjects).distinct() if subjects.exists() else Teacher.objects.none()
    exams = Exam.objects.filter(class_room=class_room).select_related('term').order_by('term__start_date', 'id', 'name')
    
    term_exams = {}
    for exam in exams:
        term_label = exam.term.name if exam.term else "General"
        if term_label not in term_exams:
            term_exams[term_label] = []
        # FIXED: order by class_position, not position
        reports = StudentReport.objects.filter(exam=exam, student__class_room=class_room).select_related('student').order_by('class_position')
        term_exams[term_label].append({
            'exam': exam,
            'reports': reports
        })
    
    latest_exam = exams.last() if exams.exists() else None
    
    return render(request, 'academics/class_detail.html', {
        'class_room': class_room,
        'students': students,
        'student_count': students.count(),
        'subjects': subjects,
        'teachers': teachers,
        'academic_year': academic_year,
        'term_exams': term_exams,
        'latest_exam': latest_exam,
        'exams': exams,
    })

def class_dashboard(request, pk):
    return class_detail(request, pk)

def class_overview(request, class_id):
    return class_detail(request, class_id)

def year_list(request):
    return render(request, "academics/year_list.html", {'years': AcademicYear.objects.all()})

def year_create(request):
    form = AcademicYearForm(request.POST or None)
    if form.is_valid():
        if form.cleaned_data.get('is_active'): AcademicYear.objects.update(is_active=False)
        form.save()
        return redirect('academics:year_list')
    return render(request, "academics/year_form.html", {'form': form, 'title': 'Add Academic Year'})

def year_update(request, pk):
    year = get_object_or_404(AcademicYear, pk=pk)
    form = AcademicYearForm(request.POST or None, instance=year)
    if form.is_valid():
        if form.cleaned_data.get('is_active'): AcademicYear.objects.exclude(pk=pk).update(is_active=False)
        form.save()
        return redirect('academics:year_list')
    return render(request, "academics/year_form.html", {'form': form, 'title': 'Edit Academic Year'})

def year_activate(request, pk):
    AcademicYear.objects.update(is_active=False)
    y = get_object_or_404(AcademicYear, pk=pk)
    y.is_active=True; y.save()
    return redirect('academics:year_list')

def term_list(request):
    return render(request, 'academics/term_list.html', {'terms': Term.objects.select_related('academic_year').all().order_by('-start_date')})

def term_create(request):
    form = TermForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('academics:term_list')
    return render(request, "academics/term_form.html", {'form': form, 'title': 'Add Term'})

def term_update(request, pk):
    term = get_object_or_404(Term, pk=pk)
    form = TermForm(request.POST or None, instance=term)
    if form.is_valid():
        form.save()
        return redirect('academics:term_list')
    return render(request, "academics/term_form.html", {'form': form, 'title': 'Edit Term'})

def term_delete(request, pk):
    term = get_object_or_404(Term, pk=pk)
    if request.method == 'POST':
        term.delete()
        return redirect('academics:term_list')
    return render(request, "academics/term_confirm_delete.html", {'term': term})

def subject_list(request):
    subjects = Subject.objects.select_related('class_room', 'teacher').all()
    return render(request, 'academics/subject_list.html', {'subjects': subjects, 'assigned_count': subjects.filter(teacher__isnull=False).count(), 'unassigned_count': subjects.filter(teacher__isnull=True).count()})

def subject_create(request):
    form = SubjectForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('academics:subject_list')
    return render(request, "academics/subject_form.html", {'form': form, 'title': 'Add Subject'})

def subject_update(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    form = SubjectForm(request.POST or None, instance=subject)
    if form.is_valid():
        form.save()
        return redirect('academics:subject_list')
    return render(request, "academics/subject_form.html", {'form': form, 'title': 'Edit Subject'})

def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        return redirect('academics:subject_list')
    return render(request, "academics/subject_confirm_delete.html", {'subject': subject})

def teacher_list(request):
    teachers = Teacher.objects.all()
    return render(request, 'academics/teacher_list.html', {'teachers': teachers, 'subjects_count': Subject.objects.count(), 'classes_count': ClassRoom.objects.count()})

def teacher_detail(request, pk):
    return render(request, 'academics/teacher_detail.html', {'teacher': get_object_or_404(Teacher, pk=pk)})

def teacher_create(request):
    form = TeacherForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect('academics:teacher_list')
    return render(request, "academics/teacher_form.html", {'form': form, 'title': 'Add Teacher'})

def teacher_update(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    form = TeacherForm(request.POST or None, request.FILES or None, instance=teacher)
    if form.is_valid():
        form.save()
        return redirect('academics:teacher_detail', pk=teacher.pk)
    return render(request, 'academics/teacher_form.html', {'form': form, 'teacher': teacher, 'title': 'Edit Teacher'})

def teacher_dashboard(request):
    teacher = Teacher.objects.filter(email=request.user.email).first()
    if not teacher: return render(request, 'academics/no_teacher_profile.html')
    return render(request, 'academics/teacher_dashboard.html', {'teacher': teacher, 'my_subjects': Subject.objects.filter(teacher=teacher), 'active_exams': Exam.objects.filter(is_active=True)})

def assign_subject_to_teacher(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        subject = get_object_or_404(Subject, id=request.POST.get('subject'))
        subject.teacher = teacher; subject.save()
        return redirect('academics:teacher_detail', pk=teacher.pk)
    return render(request, 'academics/assign_subject.html', {'teacher': teacher, 'subjects': Subject.objects.filter(teacher__isnull=True)})

def exam_list(request):
    return render(request, "academics/exam_list.html", {'exams': Exam.objects.select_related('term', 'class_room').all()})

def exam_create(request):
    form = ExamForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('academics:exam_list')
    return render(request, "academics/exam_form.html", {'form': form, 'title': 'Add Exam'})

def download_template(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    subjects = Subject.objects.filter(class_room=exam.class_room).order_by('name')
    students = Student.objects.filter(class_room=exam.class_room, is_active=True).order_by('first_name')
    wb = openpyxl.Workbook(); ws = wb.active
    headers = ['AdmissionNumber', 'StudentName']
    for s in subjects:
        headers.extend([f"{s.name}_Test", f"{s.name}_Exam"])
    ws.append(headers)
    for st in students:
        row = [st.admission_number, _get_student_name(st)] + ['' for _ in subjects for _ in range(2)]
        ws.append(row)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={exam.name}_Template.xlsx'
    wb.save(response)
    return response

def bulk_upload_results(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    subjects = list(Subject.objects.filter(class_room=exam.class_room).order_by('name'))
    if request.method == "POST" and request.FILES.get('excel_file'):
        wb = openpyxl.load_workbook(request.FILES['excel_file']); ws = wb.active
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row[0]: continue
            student = Student.objects.filter(admission_number=row[0], class_room=exam.class_room, is_active=True).first()
            if not student: continue
            col=2
            for subj in subjects:
                try:
                    t = float(row[col]) if row[col] not in [None,''] else 0
                    e = float(row[col+1]) if row[col+1] not in [None,''] else 0
                except: t=e=0
                col+=2
                ExamResult.objects.update_or_create(student=student, exam=exam, subject=subj, defaults={'test_marks': t, 'exam_marks': e})
        messages.success(request, f"Results uploaded for {exam.name}")
        return redirect('academics:class_detail', pk=exam.class_room.id)
    return render(request, "academics/bulk_upload.html", {'exam': exam})

def student_profile(request, pk):
    student = get_object_or_404(Student, pk=pk)
    return render(request, "students/student_profile.html", {'student': student, 'reports': StudentReport.objects.filter(student=student).order_by('-id')})

def report_detail(request, pk):
    report = get_object_or_404(StudentReport, pk=pk)
    breakdown = ExamResult.objects.filter(student=report.student, exam=report.exam).select_related('subject')
    return render(request, "academics/report_detail.html", {'report': report, 'student': report.student, 'breakdown': breakdown})

def report_list(request, pk):
    class_room = get_object_or_404(ClassRoom, pk=pk)
    return render(request, "academics/report_list.html", {'class_room': class_room, 'reports': StudentReport.objects.filter(student__class_room=class_room).order_by('class_position')})

def generate_reports(request, class_id):
    class_room = get_object_or_404(ClassRoom, id=class_id)
    students = Student.objects.filter(class_room=class_room, is_active=True)
    subjects = Subject.objects.filter(class_room=class_room)
    exams = Exam.objects.filter(class_room=class_room)
    academic_year = AcademicYear.objects.filter(is_active=True).first()

    if not exams.exists():
        messages.error(request, "No exams found for this class.")
        return redirect('academics:class_detail', pk=class_id)

    total_created = 0
    for exam in exams:
        if not ExamResult.objects.filter(exam=exam, student__class_room=class_room).exists():
            continue
        
        for student in students:
            results = ExamResult.objects.filter(student=student, exam=exam)
            if not results.exists():
                continue
            
            # Create report - total_marks and average will be calculated automatically in model save()
            report, created = StudentReport.objects.get_or_create(
                student=student,
                exam=exam,
                defaults={'academic_year': academic_year}
            )
            # Force recalculation
            report.academic_year = academic_year
            report.save()
            
            # Now calculate division based on results
            points_list = []
            for res in results:
                # average_marks in ExamResult is (test+exam)/2, use total for division
                score = float(res.total_marks or 0)
                # Your total_marks is test+exam, so for grading we use average or total?
                # Using total as score is 0-100 if test+exam =100. Adjust if needed.
                # Here we use average_marks which is 0-100
                score_for_grade = float(res.average_marks or 0)
                if class_room.level_group == 'ORDINARY':
                    points_list.append(get_ordinary_points(score_for_grade))
                elif class_room.level_group == 'ADVANCED':
                    points_list.append(get_advanced_points(score_for_grade))
            
            if class_room.level_group in ['ORDINARY', 'ADVANCED']:
                div_points, division = calculate_best_points(points_list, class_room.level_group)
            else:
                div_points = 0
                avg = float(report.average_marks or 0)
                if avg >= 75: division = 'A'
                elif avg >= 65: division = 'B'
                elif avg >= 45: division = 'C'
                elif avg >= 30: division = 'D'
                else: division = 'F'

            # Update division fields without triggering full save loop
            StudentReport.objects.filter(id=report.id).update(
                division_points=div_points,
                division=division,
                total_points=div_points
            )
            total_created += 1

    if total_created == 0:
        messages.warning(request, "No marks found. Upload marks first.")
    else:
        messages.success(request, f"Generated {total_created} reports for {class_room}")

    return redirect('academics:class_detail', pk=class_id)

def bulk_print_class_reports(request, class_id, exam_id):
    class_room = get_object_or_404(ClassRoom, id=class_id)
    exam = get_object_or_404(Exam, id=exam_id)
    students = Student.objects.filter(class_room=class_room, is_active=True).order_by('admission_number')
    result_data = [{'student': s, 'report': StudentReport.objects.filter(student=s, exam=exam).first(), 'subjects': ExamResult.objects.filter(student=s, exam=exam).select_related('subject')} for s in students]
    return render(request, 'academics/result_sheet.html', {'class_room': class_room, 'exam': exam, 'result_data': result_data})

def report_pdf(request, pk):
    return redirect('academics:report_detail', pk=pk)

def send_results_to_parents(request, class_id, term_number):
    messages.info(request, f"Send to parents for term {term_number} - Coming soon")
    return redirect('academics:class_detail', pk=class_id)

def send_whatsapp_page(request, class_id):
    return render(request, 'academics/send_whatsapp.html', {'class_room': get_object_or_404(ClassRoom, id=class_id), 'links': [], 'total': 0})

@login_required
def enter_marks(request, class_pk, exam_pk):
    class_room = get_object_or_404(ClassRoom, id=class_pk)
    exam = get_object_or_404(Exam, id=exam_pk)
    students = Student.objects.filter(class_room=class_room, is_active=True).order_by('first_name')
    subjects = Subject.objects.filter(class_room=class_room)
    if request.method == 'POST':
        for st in students:
            for subj in subjects:
                t = request.POST.get(f'test_{st.id}_{subj.id}', 0) or 0
                e = request.POST.get(f'exam_{st.id}_{subj.id}', 0) or 0
                try: t=float(t)
                except: t=0
                try: e=float(e)
                except: e=0
                ExamResult.objects.update_or_create(student=st, exam=exam, subject=subj, defaults={'test_marks': t, 'exam_marks': e})
        messages.success(request, "Marks saved successfully")
        return redirect('academics:class_detail', pk=class_pk)
    existing = {(r.student_id, r.subject_id): r for r in ExamResult.objects.filter(exam=exam)}
    return render(request, 'academics/enter_marks.html', {'class_room': class_room, 'exam': exam, 'students': students, 'subjects': subjects, 'existing': existing})