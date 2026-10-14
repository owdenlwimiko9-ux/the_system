from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
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
        return redirect('admissions:status', code=app.application_code)
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

@user_passes_test(superuser_required, login_url='/')
def manage_list(request):
    applications = AdmissionApplication.objects.all().order_by('-created_at')
    html = f"""
    <html><head><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body><div class="container-fluid mt-4">
    <h3>Admissions - {applications.count()} applications</h3>
    <table class="table table-striped table-sm">
    <tr><th>Name</th><th>Class</th><th>Previous School</th><th>Phone</th><th>Status</th><th>Action</th></tr>
    """
    for a in applications:
        prev = a.previous_school if hasattr(a, 'previous_school') and a.previous_school else '-'
        parent = a.parent_name if hasattr(a, 'parent_name') else ''
        html += f"<tr><td>{a.full_name}<br><small class='text-muted'>{parent}</small></td><td>{a.class_applying}</td><td>{prev}</td><td>{a.parent_phone}<br><small>{a.application_code}</small></td><td>{a.status}</td><td><a href='/admissions/approve/{a.id}/' class='btn btn-sm btn-success'>Approve</a> <a href='/admissions/reject/{a.id}/' class='btn btn-sm btn-danger'>Reject</a></td></tr>"
    if applications.count() == 0:
        html += "<tr><td colspan=6>No applications. Share /admissions/apply/ to parents</td></tr>"
    html += "</table><a href='/' class='btn btn-secondary'>Back</a> <a href='/admissions/' class='btn btn-primary'>Application Form</a></div></body></html>"
    return HttpResponse(html)

@user_passes_test(superuser_required, login_url='/')
def approve(request, id):
    app = get_object_or_404(AdmissionApplication, id=id)
    app.status = 'Approved'
    app.save()
    return redirect('admissions:manage')

@user_passes_test(superuser_required, login_url='/')
def reject(request, id):
    app = get_object_or_404(AdmissionApplication, id=id)
    app.status = 'Rejected'
    app.save()
    return redirect('admissions:manage')