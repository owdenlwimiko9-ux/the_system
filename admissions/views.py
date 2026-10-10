from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from .models import AdmissionApplication

def superuser_required(user):
    return user.is_superuser

def apply_view(request):
    if request.method == 'POST':
        AdmissionApplication.objects.create(
            full_name=request.POST.get('full_name'),
            parent_name=request.POST.get('parent_name'),
            parent_phone=request.POST.get('parent_phone'),
            email=request.POST.get('email'),
            class_applying=request.POST.get('class_applying'),
            previous_school=request.POST.get('previous_school'),
            message=request.POST.get('message'),
        )
        messages.success(request, 'Application submitted! We will call you soon.')
        return redirect('admissions:apply')
    return render(request, 'admissions/apply.html')

@user_passes_test(superuser_required, login_url='/')
def admission_list_view(request):
    applications = AdmissionApplication.objects.all().order_by('-created_at')
    return render(request, 'admissions/admission_list.html', {'applications': applications})

@user_passes_test(superuser_required, login_url='/')
def admission_approve(request, id):
    app = get_object_or_404(AdmissionApplication, id=id)
    app.status = 'Approved'
    app.save()
    return redirect('admissions:list')

@user_passes_test(superuser_required, login_url='/')
def admission_reject(request, id):
    app = get_object_or_404(AdmissionApplication, id=id)
    app.status = 'Rejected'
    app.save()
    return redirect('admissions:list')