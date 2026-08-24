from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Administrator"),
        ("teacher", "Teacher"),
        ("accountant", "Accountant"),
        ("headteacher", "Head Teacher"),
        ("parent", "Parent"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="teacher")
    phone = models.CharField(max_length=20, blank=True, null=True)

    # Link 1: If role=teacher, connect to academics.Teacher
    teacher_profile = models.OneToOneField(
        'academics.Teacher', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )

    # Link 2: If role=parent, connect to students.Guardian
    # This way parent sees all students under their Guardian
    guardian_profile = models.OneToOneField(
        'students.Guardian', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )