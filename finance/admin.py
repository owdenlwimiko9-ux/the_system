from django.contrib import admin

from django.contrib import admin
from .models import FeeStructure, FeePayment, Donation, OtherPayment, Expense

admin.site.register([FeeStructure, FeePayment, Donation, OtherPayment, Expense])

