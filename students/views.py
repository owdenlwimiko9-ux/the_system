from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q, Count
from django.views.generic import ListView, UpdateView, DeleteView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.db import transaction
from django.urls import reverse_lazy
from datetime import date, timedelta
import pandas as pd
import io

# ReportLab for ID Cards
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

from.models import Student, Attendance, Guardian
from finance.models import FeePayment
from.forms import StudentForm, StudentBulkUploadForm
from academics.models import ClassRoom, Teacher, StudentReport, ExamResult
from accounts.views import is_teacher


LEVEL_GROUP_DISPLAY = {
    'PRE_PRIMARY': 'PRE-PRIMARY',
    'ORDINARY': 'ORDINARY LEVEL', 
    'ADVANCED': 'ADVANCED LEVEL',
}

# CLASS MAPPING: What user types in Excel -> What is in DB
CLASS_MAP = {
    'FORM 1': 'F1', 'FORM 2': 'F2', 'FORM 3': 'F3', 'FORM 4': 'F4', 'FORM 5': 'F5',
    'GRADE 1': 'G1', 'GRADE 2': 'G2', 'GRADE 3': 'G3', 'GRADE 4': 'G4', 
    'GRADE 5': 'G5', 'GRADE 6': 'G6', 'GRADE 7': 'G7',
    'BABY': 'BABY', 'MIDDLE': 'MIDDLE', 'TOP': 'TOP',
}

# ID CARD SETTINGS
SCHOOL_NAME = "YOUR SCHOOL NAME"
SCHOOL_MOTTO = "Education For Excellence"
PRIMARY_COLOR = HexColor("#0d47a1") # Dark Blue
SECONDARY_COLOR = HexColor("#1565c0") # Light Blue


# ================================
# ID CARD HELPER FUNCTION
# ================================
def generate_id_cards_pdf(request, students, title):
    """Helper to generate PDF with 4 cards per A4 page"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{title}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Card size: 85mm x 54mm
    card_w = 85 * mm
    card_h = 54 * mm
    margin_x = 10 * mm
    margin_y = 10 * mm
    gap_x = 10 * mm
    gap_y = 10 * mm

    x_positions = [margin_x, margin_x + card_w + gap_x]
    y_positions = [height - margin_y - card_h, height - margin_y - card_h*2 - gap_y]

    card_count = 0

    for student in students:
        col = card_count % 2
        row = (card_count // 2) % 2
        x = x_positions[col]
        y = y_positions[row]

        # ===== CARD BACKGROUND =====
        p.setFillColor(PRIMARY_COLOR)
        p.roundRect(x, y, card_w, card_h, 4*mm, fill=1, stroke=0)
        
        p.setFillColor(HexColor("#ffffff"))
        p.roundRect(x, y+card_h-15*mm, card_w, 15*mm, 4*mm, fill=1, stroke=0)

        # ===== HEADER =====
        p.setFillColor(PRIMARY_COLOR)
        p.setFont("Helvetica-Bold", 9)
        p.drawCentredString(x + card_w/2, y + card_h - 5*mm, SCHOOL_NAME)
        p.setFont("Helvetica", 6)
        p.drawCentredString(x + card_w/2, y + card_h - 9*mm, SCHOOL_MOTTO)

        # ===== PHOTO =====
        photo_x = x + 3*mm
        photo_y = y + 10*mm
        photo_size = 22*mm
        p.setStrokeColor(PRIMARY_COLOR)
        p.setLineWidth(1)
        p.rect(photo_x, photo_y, photo_size, photo_size, stroke=1, fill=0)
        
        if student.photo:
            try:
                img = ImageReader(student.photo.path)
                p.drawImage(img, photo_x+0.5*mm, photo_y+0.5*mm, photo_size-1*mm, photo_size-1*mm, mask='auto')
            except:
                p.setFont("Helvetica", 7)
                p.drawCentredString(photo_x + photo_size/2, photo_y + photo_size/2, "NO PHOTO")
        else:
            p.setFont("Helvetica", 7)
            p.drawCentredString(photo_x + photo_size/2, photo_y + photo_size/2, "NO PHOTO")

        # ===== STUDENT INFO =====
        text_x = x + 28*mm
        p.setFillColor(HexColor("#ffffff"))
        p.setFont("Helvetica-Bold", 9)
        p.drawString(text_x, y + card_h - 20*mm, student.full_name.upper())
        
        p.setFont("Helvetica", 7)
        p.drawString(text_x, y + card_h - 25*mm, f"ADM NO: {student.admission_number}")
        p.drawString(text_x, y + card_h - 29*mm, f"CLASS: {student.class_room}")
        p.drawString(text_x, y + card_h - 33*mm, f"DOB: {student.date_of_birth}")
        
        # Guardian bar
        p.setFillColor(SECONDARY_COLOR)
        p.rect(x, y, card_w, 8*mm, fill=1, stroke=0)
        p.setFillColor(HexColor("#ffffff"))
        p.setFont("Helvetica", 6)
        guardian_phone = student.guardian.phone if student.guardian else 'N/A'
        p.drawString(x + 2*mm, y + 3*mm, f"Guardian: {guardian_phone}")

        card_count += 1

        # New page after 4 cards
        if card_count % 4 == 0:
            p.showPage()

    p.save()
    return response


# ================================
# ID CARD VIEWS
# ================================
@login_required
@user_passes_test(is_teacher)
def student_id_card_single(request, pk):
    """Generate ID card for 1 student only"""
    student = get_object_or_404(Student.objects.select_related('class_room', 'guardian'), pk=pk)
    return generate_id_cards_pdf(request, [student], f"ID Card - {student.admission_number}")

@login_required
@user_passes_test(is_teacher)
def student_id_cards(request):
    """Generate ID cards for all ACTIVE students"""
    students = Student.objects.filter(status='ACTIVE').select_related('class_room', 'guardian').order_by('class_room__level', 'class_room__stream', 'first_name')
    return generate_id_cards_pdf(request, students, "All Students ID Cards")

@login_required
@user_passes_test(is_teacher)
def student_id_cards_by_class(request, class_id):
    """Generate ID cards for 1 class"""
    class_obj = get_object_or_404(ClassRoom, id=class_id)
    students = Student.objects.filter(class_room=class_obj, status='ACTIVE').select_related('guardian').order_by('first_name')
    return generate_id_cards_pdf(request, students, f"{class_obj} ID Cards")


# ================================
# STUDENT LIST - ADMIN/TEACHER
# ================================
@login_required
@user_passes_test(is_teacher)
def student_list(request):
    """List all students with search and filter"""
    query = request.GET.get("q")
    class_id = request.GET.get("class")
    status = request.GET.get("status")

    students = Student.objects.select_related('class_room', 'guardian').all().order_by('first_name', 'last_name')

    if query:
        students = students.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) |
            Q(middle_name__icontains=query) |
            Q(admission_number__icontains=query)
        )
    
    if class_id:
        students = students.filter(class_room_id=class_id)
    
    if status:
        students = students.filter(status=status)

    classes = ClassRoom.objects.all().order_by('level', 'stream')

    context = {
        'students': students,
        'classes': classes,
        'query': query,
        'selected_class': int(class_id) if class_id else None,
        'selected_status': status,
    }
    return render(request, "students/student_list.html", context)


# ================================
# PARENT DASHBOARD - FIXED
# ================================
class MyChildrenListView(ListView):
    model = Student
    template_name = 'students/my_children.html'
    context_object_name = 'students'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if user.role == 'parent':
            if not user.guardian_profile:
                messages.warning(self.request, "No Guardian profile linked to your account. Contact admin.")
                return Student.objects.none()
            return Student.objects.filter(guardian=user.guardian_profile).select_related('class_room')
        
        elif user.role in ['admin', 'headteacher', 'accountant', 'teacher']:
            return Student.objects.all().select_related('class_room', 'guardian')
        else:
            return Student.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        students_qs = context['students']

        student_data = []
        for student in students_qs:
            # 1. Attendance
            attendance_qs = Attendance.objects.filter(student=student)
            total = attendance_qs.count()
            present = attendance_qs.filter(status='P').count()
            percentage = round((present / total) * 100, 2) if total > 0 else 0

            # 2. BILLS
            invoices = FeePayment.objects.filter(student=student).select_related('fee_structure').order_by('-fee_structure__academic_year', '-fee_structure__term')
            total_bill = sum(i.amount_due for i in invoices)
            total_paid = sum(i.amount_paid for i in invoices)
            total_balance = sum(i.balance for i in invoices)

            # 3. Class and Level
            if student.class_room:
                class_name = str(student.class_room)
                level_group = student.class_room.level_group
                level_display = LEVEL_GROUP_DISPLAY.get(level_group, "Not Set")
            else:
                class_name = "Not Assigned"
                level_display = "Not Set"

            student_data.append({
                'obj': student,
                'class_name': class_name,
                'level_display': level_display,
                'attendance_percentage': percentage,
                'invoices': invoices,
                'total_bill': total_bill,
                'total_paid': total_paid,
                'total_balance': total_balance,
            })
        
        context['students'] = student_data
        return context


# ================================
# STUDENT DETAIL - PROTECTED
# ================================
def student_detail_protected(request, pk):
    """Student detail page - PROTECTED + WITH STATS + BILLS"""
    student = get_object_or_404(
        Student.objects.select_related('class_room', 'guardian'), 
        pk=pk
    )
    user = request.user

    if user.role == 'parent':
        if not user.guardian_profile or student.guardian!= user.guardian_profile:
            raise PermissionDenied("You do not have permission to view this student.")
    
    # 1. Attendance Stats
    attendance_qs = Attendance.objects.filter(student=student)
    total = attendance_qs.count()
    present = attendance_qs.filter(status='P').count()
    absent = attendance_qs.filter(status='A').count()
    late = attendance_qs.filter(status='L').count()
    excused = attendance_qs.filter(status='E').count()
    percentage = round((present / total) * 100, 2) if total > 0 else 0

    stats = {
        'total': total, 'present': present, 'absent': absent, 
        'late': late, 'excused': excused, 'percentage': percentage,
    }

    # 2. BILLS
    invoices = FeePayment.objects.filter(student=student).select_related('fee_structure').order_by('-fee_structure__academic_year', '-fee_structure__term')
    total_bill = sum(i.amount_due for i in invoices)
    total_paid = sum(i.amount_paid for i in invoices)
    total_balance = sum(i.balance for i in invoices)

    # 3. Academic Reports
    reports = StudentReport.objects.filter(student=student).select_related('exam', 'exam__term').order_by('-exam__term__start_date')
    terms = {}
    for report in reports:
        subjects = ExamResult.objects.filter(student=student, exam=report.exam).select_related('subject').order_by('subject__name')
        report.subjects = subjects
        term_name = report.exam.term.get_name_display()
        if term_name not in terms:
            terms[term_name] = []
        terms[term_name].append(report)

    # 4. Class and Level
    if student.class_room:
        class_name = str(student.class_room)
        level_group = student.class_room.level_group
        level_display = LEVEL_GROUP_DISPLAY.get(level_group, "Not Set")
    else:
        class_name = "Not Assigned"
        level_display = "Not Set"
        level_group = None

    context = {
        'student': student, 'stats': stats, 'terms': terms,
        'invoices': invoices, 'total_bill': total_bill, 'total_paid': total_paid, 'total_balance': total_balance,
        'level_group': level_group, 'class_name': class_name, 'level_display': level_display
    }
    return render(request, "students/student_detail.html", context)


# ================================
# OTHER CRUD VIEWS
# ================================
@login_required
def student_create(request):
    """Add new student"""
    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            messages.success(request, f"Student {student.full_name} added successfully! Admission No: {student.admission_number}")
            return redirect('students:student_detail', pk=student.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentForm()
    return render(request, "students/student_form.html", {'form': form, 'title': 'Add Student'})

@login_required
def student_update(request, pk):
    """Edit student"""
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"Student {student.full_name} updated successfully!")
            return redirect('students:student_detail', pk=student.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentForm(instance=student)
    return render(request, "students/student_form.html", {'form': form, 'title': 'Edit Student'})

def student_attendance_report(request, student_id):
    """Individual student attendance report"""
    student = get_object_or_404(Student, id=student_id)
    attendance = Attendance.objects.filter(student=student).order_by('-date')
    total = attendance.count()
    present = attendance.filter(status='P').count()
    absent = attendance.filter(status='A').count()
    late = attendance.filter(status='L').count()
    excused = attendance.filter(status='E').count()
    percentage = round((present / total) * 100, 2) if total > 0 else 0

    context = {
        'student': student, 'attendance': attendance, 'total': total,
        'present': present, 'absent': absent, 'late': late, 'excused': excused, 'percentage': percentage,
    }
    return render(request, "students/attendance_report.html", context)

def daily_attendance_summary(request):
    """Daily summary with clickable date navigation"""
    date_str = request.GET.get('date')
    today = timezone.now().date()
    selected_date = date.fromisoformat(date_str) if date_str else today
    
    prev_date = selected_date - timedelta(days=1)
    next_date = selected_date + timedelta(days=1)
    
    total_active_students = Student.objects.filter(status='ACTIVE').count()
    attendance_today = Attendance.objects.filter(date=selected_date)
    
    school_stats = {
        'total': total_active_students,
        'present': attendance_today.filter(status='P').count(),
        'absent': attendance_today.filter(status='A').count(),
        'late': attendance_today.filter(status='L').count(),
        'excused': attendance_today.filter(status='E').count(),
    }
    marked_students = attendance_today.values('student').distinct().count()
    school_stats['not_recorded'] = total_active_students - marked_students

    classes = ClassRoom.objects.all().annotate(
        total_students=Count('students', filter=Q(students__status='ACTIVE')),
        present=Count('students__attendance', filter=Q(students__attendance__date=selected_date, students__attendance__status='P')),
        absent=Count('students__attendance', filter=Q(students__attendance__date=selected_date, students__attendance__status='A')),
        late=Count('students__attendance', filter=Q(students__attendance__date=selected_date, students__attendance__status='L')),
        excused=Count('students__attendance', filter=Q(students__attendance__date=selected_date, students__attendance__status='E')),
    ).order_by('level', 'stream')

    return render(request, 'students/daily_attendance_summary.html', {
        'date': selected_date, 'today': today, 'prev_date': prev_date, 'next_date': next_date,
        'school_stats': school_stats, 'classes': classes,
    })

@login_required
@user_passes_test(is_teacher)
def take_class_attendance(request, class_id):
    """Mark attendance for a whole class"""
    class_room = get_object_or_404(ClassRoom, id=class_id)
    date_str = request.GET.get('date')
    today = timezone.now().date()
    selected_date = date.fromisoformat(date_str) if date_str else today

    students = Student.objects.filter(class_room=class_room, status='ACTIVE').order_by('first_name', 'last_name')
    teacher = Teacher.objects.filter(email=request.user.email).first() if request.user.is_authenticated else None

    if request.method == "POST":
        saved_count = 0
        for student in students:
            status = request.POST.get(f'student_{student.id}')
            if status:
                Attendance.objects.update_or_create(
                    student=student, date=selected_date,
                    defaults={'status': status, 'recorded_by': teacher}
                )
                saved_count += 1
        messages.success(request, f"Attendance for {class_room} saved for {selected_date}. {saved_count} records updated.")
        return redirect(f"{request.path}?date={selected_date}")

    existing_attendance = Attendance.objects.filter(date=selected_date, student__class_room=class_room)
    attendance_map = {a.student_id: a.status for a in existing_attendance}
    for student in students:
        student.today_status = attendance_map.get(student.id, '')

    context = {'class_room': class_room, 'students': students, 'today': selected_date, 'selected_date': selected_date}
    return render(request, "students/take_attendance.html", context)

def students_by_class(request, class_id):
    """List students in a specific class"""
    class_obj = get_object_or_404(ClassRoom, id=class_id)
    students = Student.objects.filter(class_room=class_obj, status='ACTIVE').order_by('first_name')
    context = {'class_obj': class_obj, 'students': students}
    return render(request, 'students/students_by_class.html', context)

class StudentUpdateView(UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:student_list')

class StudentDeleteView(DeleteView):
    model = Student
    success_url = reverse_lazy('students:student_list')


# ================================
# BULK UPLOAD - FIXED WITH MAPPING + GUARDIAN UPDATE
# ================================
@login_required
@user_passes_test(is_teacher)
def student_bulk_upload(request):
    """Bulk upload students via Excel/CSV"""
    if request.method == 'POST':
        form = StudentBulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
            except Exception as e:
                messages.error(request, f"Error reading file: {e}")
                return redirect('students:student_bulk_upload')

            success_count = 0
            skipped_count = 0
            error_rows = []

            with transaction.atomic():
                for index, row in df.iterrows():
                    row_num = index + 2
                    try:
                        # Required fields
                        required = ['first_name', 'last_name', 'guardian_phone', 'date_of_birth', 'gender']
                        if any(pd.isna(row.get(r)) for r in required):
                            error_rows.append(f"Row {row_num}: Missing required field")
                            continue

                        # 1. Get or Create Guardian - AND UPDATE IF EXISTS
                        phone = str(row['guardian_phone']).strip()
                        g_first = str(row.get('guardian_first_name', '')).strip()
                        g_last = str(row.get('guardian_last_name', '')).strip()
                        g_alt = str(row.get('alternative_phone', '')).strip()
                        g_email = str(row.get('guardian_email', '')).strip()
                        g_addr = str(row.get('guardian_address', '')).strip()

                        guardian, created = Guardian.objects.get_or_create(
                            phone=phone,
                            defaults={
                                'first_name': g_first,
                                'last_name': g_last,
                                'alternative_phone': g_alt,
                                'email': g_email,
                                'address': g_addr,
                            }
                        )

                        # If guardian already existed, update their details
                        if not created:
                            updated = False
                            if g_first and guardian.first_name!= g_first:
                                guardian.first_name = g_first; updated = True
                            if g_last and guardian.last_name!= g_last:
                                guardian.last_name = g_last; updated = True
                            if g_alt and guardian.alternative_phone!= g_alt:
                                guardian.alternative_phone = g_alt; updated = True
                            if g_email and guardian.email!= g_email:
                                guardian.email = g_email; updated = True
                            if g_addr and guardian.address!= g_addr:
                                guardian.address = g_addr; updated = True
                            
                            if updated:
                                guardian.save()
                                messages.info(request, f"Updated guardian {phone} with new details")

                        # 2. Get ClassRoom with mapping: "Form 1A" -> "F1" "A"
                        class_obj = None
                        class_input = str(row.get('class_room', '')).strip().upper()
                        if class_input:
                            if len(class_input) >= 2:
                                stream_part = class_input[-1] # A
                                level_key = class_input[:-1].strip() # FORM 1
                                db_level = CLASS_MAP.get(level_key)
                                
                                if db_level:
                                    class_obj = ClassRoom.objects.filter(level=db_level, stream=stream_part).first()
                                
                            if not class_obj:
                                error_rows.append(f"Row {row_num}: Class '{class_input}' not found. Valid: Form 1A, Baby A, Grade 3A")
                                continue

                        # 3. Check duplicate student
                        exists = Student.objects.filter(
                            first_name=str(row['first_name']).strip(),
                            last_name=str(row['last_name']).strip(),
                            date_of_birth=row['date_of_birth'],
                            guardian=guardian
                        ).exists()
                        if exists:
                            skipped_count += 1
                            continue

                        # 4. Create Student
                        Student.objects.create(
                            first_name=str(row['first_name']).strip(),
                            middle_name=str(row.get('middle_name', '')).strip(),
                            last_name=str(row['last_name']).strip(),
                            gender='M' if str(row['gender']).upper().startswith('M') else 'F',
                            date_of_birth=row['date_of_birth'],
                            guardian=guardian,
                            class_room=class_obj,
                            nationality=str(row.get('nationality', 'Tanzanian')).strip(),
                            religion=str(row.get('religion', '')).strip(),
                            blood_group=str(row.get('blood_group', '')).strip(),
                            status=str(row.get('status', 'ACTIVE')).upper(),
                        )
                        success_count += 1

                    except Exception as e:
                        error_rows.append(f"Row {row_num}: {e}")

            messages.success(request, f'{success_count} students uploaded. {skipped_count} skipped as duplicates.')
            for err in error_rows[:10]:
                messages.warning(request, err)
            
            return redirect('students:student_list')
    else:
        form = StudentBulkUploadForm()
    
    return render(request, 'students/student_bulk_upload.html', {'form': form})


@login_required
@user_passes_test(is_teacher)
def download_student_template(request):
    """Generate and download the excel template for bulk upload"""
    columns = [
        'first_name', 'middle_name', 'last_name', 'gender', 'date_of_birth',
        'guardian_first_name', 'guardian_last_name', 'guardian_phone', 
        'alternative_phone', 'guardian_email', 'guardian_address',
        'class_room', 'nationality', 'religion', 'blood_group', 'status'
    ]
    
    data = [
        ['John', 'Peter', 'Doe', 'M', '2010-05-12', 'Peter', 'Doe', '255712345678', '255765432109', 'peter@gmail.com', 'Dar es Salaam', 'Form 1A', 'Tanzanian', 'Christian', 'O+', 'ACTIVE'],
        ['Jane', '', 'Smith', 'F', '2011-03-20', 'Mary', 'Smith', '255698765432', '', 'Baby A', 'Tanzanian', '', '', 'ACTIVE'],
    ]
    
    df = pd.DataFrame(data, columns=columns)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Students', index=False)
    output.seek(0)
    
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=student_template.xlsx'
    return response