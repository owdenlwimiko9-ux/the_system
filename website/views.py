from django.shortcuts import render, redirect
from admissions.models import AdmissionApplication
from django.contrib import messages

def home(request):
    return render(request, 'website/home.html')

def about(request):
    return render(request, 'website/about.html')

def programs(request):
    return render(request, 'website/programs.html')

def admission(request):
    if request.method == 'POST':
        AdmissionApplication.objects.create(
            full_name=request.POST.get('full_name'),
            parent_name=request.POST.get('parent_name', ''),
            parent_phone=request.POST.get('parent_phone'),
            class_applying=request.POST.get('class_applying') or request.POST.get('class_name', ''),
            previous_school=request.POST.get('previous_school', ''),
            message=request.POST.get('message', '')
        )
        messages.success(request, 'Application submitted successfully! We will contact you soon.')
        return redirect('admission')
    return render(request, 'website/admission.html')

def teachers(request):
    return render(request, 'website/teachers.html')

def school_management(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return redirect('dashboard:home')