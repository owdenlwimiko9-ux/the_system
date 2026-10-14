from django.urls import path
from . import views

urlpatterns = [
    path('apply/', views.apply, name='admissions_apply'),
    path('status/<str:code>/', views.status, name='admissions_status'),
    path('track/', views.track, name='admissions_track'),
]