import random, string
from django.db import models

def generate_code():
    return 'KIL' + ''.join(random.choices(string.digits, k=6))

class AdmissionApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('interview', 'Called for Interview'),
    ]
    application_code = models.CharField(max_length=20, default=generate_code, unique=True)
    full_name = models.CharField(max_length=100)
    parent_name = models.CharField(max_length=100)
    parent_phone = models.CharField(max_length=20)
    class_applying = models.CharField(max_length=50)
    previous_school = models.CharField(max_length=100, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application_code} - {self.full_name}"