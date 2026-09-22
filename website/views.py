from django.shortcuts import render, redirect

def home(request):
    return render(request, 'website/home.html')

def about(request):
    return render(request, 'website/about.html')

def programs(request):
    return render(request, 'website/programs.html')

def admission(request):
    return render(request, 'website/admission.html')

def teachers(request):
    return render(request, 'website/teachers.html')

def school_management(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return redirect('dashboard:home')