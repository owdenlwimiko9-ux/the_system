from django.db import models
from students.models import Student 
from django.utils import timezone

PAYMENT_METHODS = [
    ('Cash', 'Cash'),
    ('Bank', 'Bank Transfer'),
    ('Mobile', 'Mobile Money'),
    ('Control', 'Control Number'), # for Bank/GePG
]

CONTROL_SOURCES = [
    ('manual', 'Manual Entry'),
    ('nmb', 'NMB Bank'),
    ('crdb', 'CRDB Bank'),
    ('gepg', 'GePG'),
    ('selcom', 'Selcom'),
    ('other', 'Other Bank'),
]

INVOICE_STATUS = [
    ('unpaid', 'Unpaid'),
    ('partial', 'Partial'),
    ('paid', 'Paid'),
    ('overdue', 'Overdue'),
]

class FeeStructure(models.Model):
    """The bill template - How much each class should pay per term"""
    TERM_CHOICES = [
        ('Term 1', 'Term 1'),
        ('Term 2', 'Term 2'), 
        ('Term 3', 'Term 3'),
        ('Term 4', 'Term 4')
    ]
    
    student_class = models.CharField(max_length=50, help_text="e.g. Form 1A, Grade 5")
    academic_year = models.CharField(max_length=9, default="2026")
    term = models.CharField(max_length=10, choices=TERM_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total fees for the term")
    description = models.CharField(max_length=200, blank=True, null=True)
    due_date = models.DateField(null=True, blank=True, help_text="Last date to pay without penalty")

    def __str__(self):
        return f"{self.student_class} - {self.term} {self.academic_year}: TSh {self.amount:,.0f}"

    class Meta:
        unique_together = ['student_class', 'academic_year', 'term']
        ordering = ['-academic_year', 'term']

class FeePayment(models.Model):
    """
    This is both the BILL and the PAYMENT. 
    1 row = 1 student bill for 1 term. 
    Status changes from unpaid -> paid when payment is recorded
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_payments')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='payments')
    
    # BILLING
    amount_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True, help_text="Copied from FeeStructure on creation")
    
    # CONTROL NUMBERS - NOW UNIVERSAL FOR ANY BANK
    system_control_number = models.CharField(
        max_length=20, unique=True, null=True, blank=True, db_index=True,
        help_text="Internal tracking number before bank assigns one"
    )
    bank_control_number = models.CharField(
        max_length=20, unique=True, null=True, blank=True, db_index=True,
        help_text="Real control number from Bank/GePG. Parents use this to pay"
    )
    control_number_source = models.CharField(max_length=20, choices=CONTROL_SOURCES, default='manual')
    
    # PAYMENT TRACKING
    invoice_status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='unpaid', db_index=True)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    
    # PAYMENT DETAILS - filled when paid
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='Control')
    transaction_ref = models.CharField(max_length=100, null=True, blank=True, help_text="Bank ref from bank report")
    receipt_no = models.CharField(max_length=50, unique=True, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto set due_date from FeeStructure if not set
        if not self.due_date and self.fee_structure:
            self.due_date = self.fee_structure.due_date

        # Auto generate internal system control if none
        if not self.system_control_number:
            year = self.fee_structure.academic_year if self.fee_structure else "2026"
            self.system_control_number = f"SYS{year}{self.student.id}{self.fee_structure.id}"

        # Prevent overpayment: cap amount_paid to amount_due
        if self.amount_paid > self.amount_due:
            self.amount_paid = self.amount_due

        # Auto calculate balance and status
        self.balance = self.amount_due - self.amount_paid
        if self.balance < 0:
            self.balance = 0
        
        if self.amount_paid >= self.amount_due and self.amount_due > 0:
            self.invoice_status = 'paid'
            self.balance = 0
        elif self.amount_paid > 0:
            self.invoice_status = 'partial'
        elif self.due_date and timezone.now().date() > self.due_date:
            if self.invoice_status == 'unpaid':
                self.invoice_status = 'overdue'
        else:
            self.invoice_status = 'unpaid'
                
        super().save(*args, **kwargs)

    def get_control_number(self):
        """Return Bank control if available, else system control"""
        return self.bank_control_number or self.system_control_number  # <-- FIXED THIS LINE

    def __str__(self):
        control = self.get_control_number() or "No Control"
        return f"{self.student} - {self.fee_structure.term} - {control} - {self.invoice_status}"

    class Meta:
        ordering = ['-created_at']
        unique_together = ['student', 'fee_structure'] # 1 bill per student per term
        verbose_name = "Fee Bill/Payment"
        verbose_name_plural = "Fee Bills/Payments"

class Donation(models.Model):
    """Donations from parents, NGOs, etc"""
    donor_name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    donation_date = models.DateField(default=timezone.now)
    purpose = models.CharField(max_length=200, help_text="e.g. Library Books, Building Fund")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='Cash')
    receipt_no = models.CharField(max_length=50, unique=True, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Donation: {self.donor_name} - TSh {self.amount:,.0f}"

    class Meta:
        ordering = ['-donation_date']

class OtherPayment(models.Model):
    """Other income: Uniform, Exam, Trip, etc"""
    CATEGORY_CHOICES = [
        ('Uniform', 'Uniform Sales'),
        ('Exam', 'Exam Fees'),
        ('Trip', 'School Trip'),
        ('Registration', 'Registration Fees'),
        ('Other', 'Other Income'),
    ]
    
    description = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Other')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    paid_by = models.CharField(max_length=200, blank=True, null=True, help_text="Student name or source")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='Cash')
    receipt_no = models.CharField(max_length=50, unique=True, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.description} - TSh {self.amount:,.0f}"

    class Meta:
        ordering = ['-payment_date']

class Expense(models.Model):
    """School expenses"""
    CATEGORY_CHOICES = [
        ('Salary', 'Staff Salaries'),
        ('Utilities', 'Electricity, Water'),
        ('Supplies', 'Books, Stationery'),
        ('Maintenance', 'Repairs, Maintenance'),
        ('Other', 'Other Expense'),
    ]
    
    description = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Other')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField(default=timezone.now)
    paid_to = models.CharField(max_length=200, blank=True, null=True)
    receipt_no = models.CharField(max_length=50, unique=True, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.description} - TSh {self.amount:,.0f}"

    class Meta:
        ordering = ['-expense_date']

class BankImportLog(models.Model): # Renamed from NMBImportLog
    """Track each Bank payment file imported"""
    file_name = models.CharField(max_length=255)
    bank_source = models.CharField(max_length=20, choices=CONTROL_SOURCES, default='other')
    imported_at = models.DateTimeField(auto_now_add=True)
    imported_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    total_rows = models.IntegerField(default=0)
    matched = models.IntegerField(default=0)
    not_found = models.IntegerField(default=0)
    duplicate = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.bank_source} - {self.file_name} - {self.imported_at.date()}"
    
    class Meta:
        ordering = ['-imported_at']


class PaymentReminderLog(models.Model):
    REMINDER_TYPE = [
        ('due_soon', 'Due Soon'),
        ('overdue', 'Overdue'),
        ('payment_received', 'Payment Received'),
    ]
    CHANNEL = [
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
    ]
    fee_payment = models.ForeignKey(FeePayment, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPE)
    channel = models.CharField(max_length=20, choices=CHANNEL, default='sms')
    sent_to = models.CharField(max_length=20, help_text="Phone number")
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='sent') # sent, failed

    def __str__(self):
        return f"{self.fee_payment.student} - {self.reminder_type}"