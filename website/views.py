from django.shortcuts import render, redirect
from admissions.models import AdmissionApplication
from django.contrib import messages

def home(request):
    if request.method == 'POST':
        try:
            full_name = request.POST.get('full_name', '').strip()
            parent_phone = request.POST.get('parent_phone', '').strip()
            
            if not full_name or not parent_phone:
                messages.error(request, 'Full Name and Parent Phone are required!')
                return redirect('home')

            app = AdmissionApplication.objects.create(
                full_name=full_name,
                parent_name=request.POST.get('parent_name', '').strip(),
                parent_phone=parent_phone,
                class_applying=request.POST.get('class_applying') or 'Not specified',
                previous_school=request.POST.get('previous_school', '').strip(),
                message=request.POST.get('message', '').strip(),
                status='Pending'
            )
            messages.success(request, f'Application submitted! Code: {app.application_code}')
        except Exception as e:
            messages.error(request, f'Failed: {e}')
        return redirect('home')
    return render(request, 'website/home.html')

def about(request):
    return render(request, 'website/about.html')

def programs(request):
    return render(request, 'website/programs.html')

def admission(request):
    if request.method == 'POST':
        try:
            full_name = request.POST.get('full_name', '').strip()
            parent_phone = request.POST.get('parent_phone', '').strip()
            if not full_name or not parent_phone:
                messages.error(request, 'Full Name and Parent Phone are required!')
                return redirect('admission')
            app = AdmissionApplication.objects.create(
                full_name=full_name,
                parent_name=request.POST.get('parent_name', '').strip(),
                parent_phone=parent_phone,
                class_applying=request.POST.get('class_applying') or 'Not specified',
                previous_school=request.POST.get('previous_school', '').strip(),
                message=request.POST.get('message', '').strip(),
                status='Pending'
            )
            messages.success(request, f'Application submitted! Code: {app.application_code}')
        except Exception as e:
            messages.error(request, f'Failed: {e}')
        return redirect('admission')
    return render(request, 'website/admission.html')

def teachers(request):
    return render(request, 'website/teachers.html')

def school_management(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return redirect('dashboard:home')