from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from .models import AdmissionApplication
from django.contrib import messages

def superuser_required(user):
    return user.is_superuser

def apply(request):
    if request.method == 'POST':
        app = AdmissionApplication.objects.create(
            full_name=request.POST.get('full_name'),
            parent_name=request.POST.get('parent_name'),
            parent_phone=request.POST.get('parent_phone'),
            class_applying=request.POST.get('class_applying'),
            previous_school=request.POST.get('previous_school',''),
            message=request.POST.get('message','')
        )
        return redirect('admissions_status', code=app.application_code)
    return render(request, 'admissions/apply.html')

def status(request, code):
    application = get_object_or_404(AdmissionApplication, application_code=code)
    return render(request, 'admissions/status.html', {'app': application})

def track(request):
    result = None
    if request.method == 'POST':
        phone = request.POST.get('phone')
        result = AdmissionApplication.objects.filter(parent_phone__icontains=phone).order_by('-created_at')
    return render(request, 'admissions/track.html', {'result': result})

# --- NEW MANAGE VIEWS ---
@user_passes_test(superuser_required, login_url='/')
def manage_list(request):
    applications = AdmissionApplication.objects.all().order_by('-created_at')
    return render(request, 'admissions/manage_list.html', {'applications': applications})

@user_passes_test(superuser_required, login_url='/')
def manage_detail(request, pk):
    app = get_object_or_404(AdmissionApplication, pk=pk)
    return render(request, 'admissions/manage_detail.html', {'app': app})

@user_passes_test(superuser_required, login_url='/')
def manage_approve(request, pk):
    app = get_object_or_404(AdmissionApplication, pk=pk)
    app.status = 'Approved'
    app.save()
    messages.success(request, f'{app.full_name} Approved')
    return redirect('admissions_manage')

@user_passes_test(superuser_required, login_url='/')
def manage_reject(request, pk):
    app = get_object_or_404(AdmissionApplication, pk=pk)
    app.status = 'Rejected'
    app.save()
    messages.success(request, f'{app.full_name} Rejected')
    return redirect('admissions_manage')