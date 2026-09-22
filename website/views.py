from django.shortcuts import render, redirect

def home(request):
    return render(request, 'website/home.html')

def about(request):
    return render(request, 'website/home.html')  # we will make about later

def academics(request):
    return render(request, 'website/home.html')

def admission(request):
    return render(request, 'website/home.html')

def teachers(request):
    return render(request, 'website/home.html')

def school_management(request):
    # THIS IS THE CONNECTION TO YOUR SYSTEM
    if not request.user.is_authenticated:
        return redirect('login')  # goes to your templates/registration/login.html
    return redirect('dashboard:home')  # goes to your sidebar system