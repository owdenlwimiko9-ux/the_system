from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import AdmissionApplication

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