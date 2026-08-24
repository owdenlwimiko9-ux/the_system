from django import forms
from .models import Attendance, Student, Guardian
from academics.models import ClassRoom

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        # REMOVED 'admission_number' because it auto-generates
        fields = [
            'first_name', 'middle_name', 'last_name', 
            'gender', 'date_of_birth', 'guardian', 'class_room', 
            'nationality', 'religion', 'blood_group', 'status', 'photo'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Middle Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'guardian': forms.Select(attrs={'class': 'form-select'}),
            'class_room': forms.Select(attrs={'class': 'form-select'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'religion': forms.TextInput(attrs={'class': 'form-control'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. O+'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'photo': 'Optional. Upload student passport photo.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['guardian'].queryset = Guardian.objects.all().order_by('first_name')
        self.fields['class_room'].queryset = ClassRoom.objects.all().order_by('level', 'stream')
        self.fields['middle_name'].required = False
        self.fields['photo'].required = False

class ClassAttendanceForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))
    status = forms.ChoiceField(choices=Attendance.STATUS_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))
    class_room = forms.ModelChoiceField(queryset=ClassRoom.objects.all(), widget=forms.Select(attrs={"class": "form-select"}))

class StudentBulkUploadForm(forms.Form):
    file = forms.FileField(label='Upload Excel or CSV file')