import csv
import io
import urllib.parse
from decimal import Decimal
from collections import defaultdict

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse

from.models import FeeStructure, FeePayment, Donation, OtherPayment, Expense, BankImportLog, PaymentReminderLog
from students.models import Student
from academics.models import ClassRoom
from accounts.views import is_accountant

# ================== HELPER FUNCTIONS ==================
def format_phone(phone):
    """Convert 07XX or +2557XX to 2557XX"""
    if not phone:
        return ""
    phone = str(phone).strip().replace(" ", "").replace("-", "")
    if phone.startswith("0"):
        phone = "255" + phone[1:]
    elif phone.startswith("+255"):
        phone = phone[1:]
    elif not phone.startswith("255"):
        phone = "255" + phone
    return phone

def build_whatsapp_message(bill):
    """Single bill message"""
    guardian = bill.student.guardian
    guardian_name = f"{getattr(guardian, 'first_name', '')} {getattr(guardian, 'last_name', '')}".strip().title()
    if not guardian_name: guardian_name = "Parent"

    due_date_str = bill.due_date.strftime('%d %b %Y') if bill.due_date else "Not Set"

    message = f"Hello {guardian_name},\n\n"
    message += f"*Fee Reminder from School*\n\n"
    message += f"*Student*: {bill.student.first_name} {bill.student.last_name}\n"
    message += f"*Class*: {bill.student.class_room}\n"
    message += f"*Term*: {bill.fee_structure.term} {bill.fee_structure.academic_year}\n"
    message += f"*Balance*: TZS {bill.balance:,.0f}\n"
    message += f"*Due Date*: {due_date_str}\n\n"
    if bill.bank_control_number:
        message += f"*Pay Using Control No*: `{bill.bank_control_number}`\nVia NMB/CRDB/GePG\n"
    else:
        message += f"*Control No*: Pending. School will send soon.\n\n"
    message += f"Thank you"
    return message

def build_grouped_whatsapp_message(bills):
    """Grouped message for 1 guardian with multiple students"""
    if not bills: return ""
    guardian = bills[0].student.guardian
    guardian_name = f"{getattr(guardian, 'first_name', '')} {getattr(guardian, 'last_name', '')}".strip().title()
    if not guardian_name: guardian_name = "Parent"

    message = f"Hello {guardian_name},\n\n"
    message += f"*Fee Reminder from School*\n\n"

    total_balance = Decimal('0')
    for i, bill in enumerate(bills, 1):
        due_date_str = bill.due_date.strftime('%d %b %Y') if bill.due_date else "Not Set"
        student_name = f"{bill.student.first_name} {bill.student.last_name}".title()
        message += f"*{i}. {student_name}* - {bill.student.class_room}\n"
        message += f"Balance: TZS {bill.balance:,.0f}\n"
        message += f"Term: {bill.fee_structure.term} {bill.fee_structure.academic_year}\n"
        if bill.bank_control_number:
            message += f"Control No: `{bill.bank_control_number}`\n"
        message += f"Due: {due_date_str}\n---\n"
        total_balance += bill.balance

    message += f"\n*Total Balance*: TZS {total_balance:,.0f}\n\n"
    message += f"Thank you"
    return message

# ================== EXISTING VIEWS ==================
@login_required
@user_passes_test(is_accountant)
def dashboard(request):
    total_paid = FeePayment.objects.aggregate(total=Sum('amount_paid'))['total'] or 0
    total_donations = Donation.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_other = OtherPayment.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_income = total_paid + total_donations + total_other

    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    balance = total_income - total_expenses

    total_due = FeePayment.objects.aggregate(total=Sum('amount_due'))['total'] or 0
    pending_fees = total_due - total_paid

    total_unpaid_bills = FeePayment.objects.filter(invoice_status__in=['unpaid', 'partial', 'overdue']).count()
    total_paid_bills = FeePayment.objects.filter(invoice_status='paid').count()

    recent_paid = FeePayment.objects.filter(amount_paid__gt=0).select_related('student').order_by('-payment_date')[:5]

    recent_transactions = []
    for p in FeePayment.objects.filter(amount_paid__gt=0).order_by('-payment_date')[:5]:
        recent_transactions.append({'date': p.payment_date, 'type': 'Fee', 'amount': p.amount_paid, 'is_income': True})
    for d in Donation.objects.order_by('-donation_date')[:3]:
        recent_transactions.append({'date': d.donation_date, 'type': 'Donation', 'amount': d.amount, 'is_income': True})
    for e in Expense.objects.order_by('-expense_date')[:3]:
        recent_transactions.append({'date': e.expense_date, 'type': 'Expense', 'amount': e.amount, 'is_income': False})

    recent_transactions = [t for t in recent_transactions if t['date']]
    recent_transactions = sorted(recent_transactions, key=lambda x: x['date'], reverse=True)[:8]

    context = {
        'total_fees_collected': total_paid, 'pending_fees': pending_fees,
        'total_unpaid_bills': total_unpaid_bills, 'total_paid_bills': total_paid_bills,
        'recent_paid': recent_paid, 'total_expenses': total_expenses,
        'total_donations': total_donations, 'total_income': total_income,
        'balance': balance, 'recent_transactions': recent_transactions,
    }
    return render(request, 'finance/dashboard.html', context)

@login_required
@user_passes_test(is_accountant)
def generate_bills(request):
    if request.method == 'POST':
        fs_id = request.POST.get('fee_structure')
        stream = request.POST.get('stream', '')
        fee_structure = FeeStructure.objects.get(id=fs_id)

        class_code = fee_structure.student_class.upper().strip()
        name_to_code = {
            'BABY': 'BABY', 'MIDDLE': 'MIDDLE', 'TOP': 'TOP',
            'GRADE 1': 'G1', 'GRADE 2': 'G2', 'GRADE 3': 'G3', 'GRADE 4': 'G4',
            'GRADE 5': 'G5', 'GRADE 6': 'G6', 'GRADE 7': 'G7',
            'FORM 1': 'F1', 'FORM 2': 'F2', 'FORM 3': 'F3', 'FORM 4': 'F4',
            'FORM 5': 'F5', 'FORM 6': 'F6',
        }
        class_code = name_to_code.get(class_code, class_code)
        filters = {'level': class_code}
        if stream: filters['stream'] = stream
        class_room_obj = ClassRoom.objects.filter(**filters).first()

        if not class_room_obj:
            msg = f'Class "{fee_structure.student_class} {stream}" not found.' if stream else f'Class "{fee_structure.student_class}" not found.'
            messages.error(request, msg)
            return redirect('finance:generate_bills')

        students = Student.objects.filter(class_room=class_room_obj)
        if students.count() == 0:
            messages.warning(request, f'No students found in {class_room_obj}')
            return redirect('finance:generate_bills')

        created = 0; updated = 0
        for student in students:
            system_control = f"SYS{student.id}{fee_structure.id}"
            bill, was_created = FeePayment.objects.get_or_create(
                student=student, fee_structure=fee_structure,
                defaults={
                    'amount_due': fee_structure.amount, 'due_date': fee_structure.due_date,
                    'invoice_status': 'unpaid', 'system_control_number': system_control,
                    'bank_control_number': None,
                }
            )
            if was_created: created += 1
            else:
                if bill.amount_due!= fee_structure.amount:
                    bill.amount_due = fee_structure.amount
                    bill.due_date = fee_structure.due_date
                    bill.save()
                    updated += 1

        messages.success(request, f'{created} new bills, {updated} updated for {class_room_obj}. Next: Upload Bank controls.')
        return redirect('finance:upload_bank_controls')

    fee_structures = FeeStructure.objects.all()
    streams = ClassRoom.STREAM_CHOICES
    return render(request, 'finance/generate_bills.html', {'fee_structures': fee_structures, 'streams': streams})

@login_required
@user_passes_test(is_accountant)
def download_control_template(request):
    bills = FeePayment.objects.filter(bank_control_number__isnull=True)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="control_template.csv"'
    writer = csv.writer(response)
    writer.writerow(['AdmissionNo', 'StudentName', 'Amount', 'Bank_ControlNumber'])
    for bill in bills:
        student_name = f"{bill.student.first_name} {bill.student.last_name}".title()
        writer.writerow([bill.student.admission_no, student_name, bill.amount_due, ''])
    return response

@login_required
@user_passes_test(is_accountant)
def upload_bank_controls(request):
    if request.method == 'POST':
        file = request.FILES.get('control_file')
        if not file:
            messages.error(request, 'Please upload a CSV file')
            return redirect('finance:upload_bank_controls')

        decoded_file = file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        matched = 0; not_found = 0; errors = []; total = 0

        with transaction.atomic():
            for row in reader:
                total += 1
                try:
                    admission_no = row.get('AdmissionNo') or row.get('admission_no')
                    amount = Decimal(row.get('Amount', 0))
                    bank_control = row.get('Bank_ControlNumber') or row.get('ControlNumber')
                    if not admission_no or not bank_control:
                        errors.append(f"Row {total}: Missing AdmissionNo or ControlNumber"); continue

                    bill = FeePayment.objects.filter(
                        student__admission_no=admission_no, amount_due=amount,
                        bank_control_number__isnull=True
                    ).first()

                    if not bill:
                        not_found += 1
                        errors.append(f"Row {total}: Bill for {admission_no} TSh {amount} not found")
                        continue

                    bill.bank_control_number = bank_control
                    bill.control_number_source = 'other'
                    bill.save()
                    matched += 1
                except Exception as e:
                    errors.append(f"Row {total}: {e}")

        messages.success(request, f'Controls assigned: {matched}. Not found: {not_found}')
        if errors: messages.warning(request, f'Errors: {"; ".join(errors[:5])}')
        return redirect('finance:dashboard')

    pending_controls = FeePayment.objects.filter(bank_control_number__isnull=True, invoice_status='unpaid').count()
    return render(request, 'finance/upload_controls.html', {'pending_controls': pending_controls})

@login_required
@user_passes_test(is_accountant)
def import_bank_report(request):
    if request.method == 'POST':
        file = request.FILES.get('bank_file')
        bank_source = request.POST.get('bank_source', 'other')
        if not file:
            messages.error(request, 'Please upload a CSV file')
            return redirect('finance:import_bank_report')

        decoded_file = file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        matched = 0; not_found = 0; duplicate = 0; total = 0; errors = []

        with transaction.atomic():
            for row in reader:
                total += 1
                try:
                    control_no = row.get('ControlNumber') or row.get('control_number')
                    amount = Decimal(row.get('Amount', 0))
                    payment_date = row.get('PaymentDate') or row.get('payment_date')
                    trans_ref = row.get('TransactionRef') or row.get('transaction_ref')
                    if not control_no: errors.append(f"Row {total}: No control number"); continue

                    bill = FeePayment.objects.filter(bank_control_number=control_no).first()
                    if not bill: not_found += 1; errors.append(f"Row {total}: Control {control_no} not found"); continue
                    if bill.invoice_status == 'paid': duplicate += 1; continue

                    bill.amount_paid += amount
                    bill.payment_date = payment_date
                    bill.payment_method = 'Control'
                    bill.transaction_ref = trans_ref
                    bill.control_number_source = bank_source
                    bill.save()
                    matched += 1
                except Exception as e:
                    errors.append(f"Row {total}: {e}")

        BankImportLog.objects.create(
            file_name=file.name, bank_source=bank_source, imported_by=request.user,
            total_rows=total, matched=matched, not_found=not_found, duplicate=duplicate
        )
        messages.success(request, f'Import complete: {matched} matched, {not_found} not found, {duplicate} already paid')
        return redirect('finance:dashboard')

    logs = BankImportLog.objects.all().order_by('-imported_at')[:10]
    return render(request, 'finance/import_bank.html', {'logs': logs})

@login_required
@user_passes_test(is_accountant)
def unpaid_bills_list(request):
    bills = FeePayment.objects.filter(invoice_status__in=['unpaid', 'partial', 'overdue'])\
                      .select_related('student', 'student__class_room', 'fee_structure')\
                      .order_by('due_date')
    q = request.GET.get('q')
    if q: bills = bills.filter(student__first_name__icontains=q) | bills.filter(student__last_name__icontains=q)
    class_id = request.GET.get('class')
    if class_id: bills = bills.filter(student__class_room_id=class_id)
    total_outstanding = bills.aggregate(total=Sum('balance'))['total'] or 0
    context = {
        'bills': bills, 'total_outstanding': total_outstanding, 'count': bills.count(),
        'classes': ClassRoom.objects.all().order_by('level', 'stream')
    }
    return render(request, 'finance/unpaid_bills.html', context)

@login_required
@user_passes_test(is_accountant)
def bill_detail(request, pk):
    bill = get_object_or_404(FeePayment.objects.select_related('student', 'fee_structure'), pk=pk)
    if request.method == 'POST':
        try: amount = Decimal(request.POST.get('amount', 0))
        except: amount = Decimal('0')
        payment_method = request.POST.get('payment_method', 'Cash')
        if amount <= 0: messages.error(request, 'Amount must be greater than 0')
        elif amount > bill.balance: messages.error(request, f'Amount cannot be greater than balance TSh {bill.balance}')
        else:
            with transaction.atomic():
                bill.amount_paid += amount
                bill.payment_method = payment_method
                bill.payment_date = timezone.now().date()
                bill.save()
            messages.success(request, f'TSh {amount:,.0f} recorded. New balance: TSh {bill.balance:,.0f}')
            return redirect('finance:bill_detail', pk=bill.pk)
    context = {'bill': bill}
    return render(request, 'finance/bill_detail.html', context)

# ================== MANUAL WHATSAPP REMINDERS ==================
@login_required
@user_passes_test(is_accountant)
def send_reminders_page(request):
    status = request.GET.get('status', 'unpaid')
    class_id = request.GET.get('class')

    bills = FeePayment.objects.filter(invoice_status=status, balance__gt=0).select_related(
        'student__guardian', 'student__class_room', 'fee_structure'
    ).order_by('student__guardian__phone', 'student__first_name')

    if class_id:
        bills = bills.filter(student__class_room_id=class_id)

    today = timezone.now().date()
    reminded_today_ids = PaymentReminderLog.objects.filter(
        sent_at__date=today, channel='whatsapp'
    ).values_list('fee_payment_id', flat=True)

    bulk_messages = []

    if request.method == "POST":
        if 'bulk_send' in request.POST:
            grouped = defaultdict(list)
            for bill in bills:
                guardian = bill.student.guardian
                if guardian and guardian.phone:
                    phone = format_phone(guardian.phone)
                    grouped[phone].append(bill)

            sent_count = 0
            for phone, bill_list in grouped.items():
                message = build_grouped_whatsapp_message(bill_list)
                encoded = urllib.parse.quote(message)
                wa_link = f"https://wa.me/{phone}?text={encoded}"
                guardian_name = f"{bill_list[0].student.guardian.first_name} {bill_list[0].student.guardian.last_name}".strip().title()
                bulk_messages.append({
                    'name': f"{len(bill_list)} Students - {guardian_name}",
                    'phone': phone,
                    'link': wa_link
                })

                # Use create not get_or_create to avoid MultipleObjectsReturned
                for bill in bill_list:
                    PaymentReminderLog.objects.create(
                        fee_payment=bill,
                        reminder_type='bulk_grouped',
                        channel='whatsapp',
                        sent_to=phone,
                        message=message,
                        status='sent'
                    )
                    sent_count += 1

            messages.success(request, f"Generated {len(bulk_messages)} WhatsApp messages for {sent_count} bills.")

        else: # Single send
            bill_id = request.POST.get('bill_id')
            bill = get_object_or_404(FeePayment, id=bill_id)
            guardian = bill.student.guardian
            if guardian and guardian.phone:
                phone = format_phone(guardian.phone)
                message = build_whatsapp_message(bill)
                encoded = urllib.parse.quote(message)
                whatsapp_url = f"https://wa.me/{phone}?text={encoded}"

                PaymentReminderLog.objects.create(
                    fee_payment=bill,
                    reminder_type='manual',
                    channel='whatsapp',
                    sent_to=phone,
                    message=message,
                    status='sent'
                )
                messages.success(request, f"WhatsApp link generated for {bill.student.first_name} {bill.student.last_name}")
                return redirect(whatsapp_url)
            else:
                messages.error(request, f"{bill.student.first_name} has no guardian phone number.")

    context = {
        'bills': bills, 'status': status,
        'classes': ClassRoom.objects.all().order_by('level', 'stream'),
        'selected_class': class_id, 'reminded_today_ids': list(reminded_today_ids),
        'bulk_messages': bulk_messages,
    }
    return render(request, 'finance/send_reminders.html', context)