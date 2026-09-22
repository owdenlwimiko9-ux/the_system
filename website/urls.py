from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('programs/', views.academics, name='programs'),
    path('admission/', views.admission, name='admission'),
    path('teachers/', views.teachers, name='teachers'),
    path('school-management/', views.school_management, name='school_management'),
]