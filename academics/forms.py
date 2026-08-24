from django import forms
from .models import AcademicYear, Term, Subject, Teacher, Exam, ClassRoom

class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ['name', 'is_active']  # only fields that exist in your model
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2025/2026'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ['academic_year', 'name', 'start_date', 'end_date']
        widgets = {
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'class_room', 'teacher']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'class_room': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
        }

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'exam_type', 'term', 'class_room', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'exam_type': forms.Select(attrs={'class': 'form-select'}),
            'term': forms.Select(attrs={'class': 'form-select'}),
            'class_room': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ['name', 'academic_year', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Term 1'}),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ClassRoomForm(forms.ModelForm):
    class Meta:
        model = ClassRoom
        fields = ['level', 'stream', 'class_teacher'] # academic_year REMOVED
        widgets = {
            'level': forms.Select(attrs={'class': 'form-select'}), # use Select because you have choices
            'stream': forms.Select(attrs={'class': 'form-select'}),
            'class_teacher': forms.Select(attrs={'class': 'form-select'}),
        }