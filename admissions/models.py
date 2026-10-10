from django.db import models

class AdmissionApplication(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    full_name = models.CharField(max_length=200)
    parent_name = models.CharField(max_length=200, blank=True)
    parent_phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    class_applying = models.CharField(max_length=100)
    previous_school = models.CharField(max_length=200, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.class_applying} ({self.status})"