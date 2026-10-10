from django.db import models

# Create your models here.
class AdmissionApplication(models.Model):
    full_name = models.CharField(max_length=200)
    parent_phone = models.CharField(max_length=20)
    class_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')

    def __str__(self):
        return self.full_name