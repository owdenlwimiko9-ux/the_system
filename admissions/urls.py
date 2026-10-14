from django.urls import path
from . import views

urlpatterns = [
    path('apply/', views.apply, name='admissions_apply'),
    path('status/<str:code>/', views.status, name='admissions_status'),
    path('track/', views.track, name='admissions_track'),
    path('manage/', views.manage_list, name='admissions_manage'),
    path('manage/<int:pk>/', views.manage_detail, name='admissions_manage_detail'),
    path('manage/<int:pk>/approve/', views.manage_approve, name='admissions_approve'),
    path('manage/<int:pk>/reject/', views.manage_reject, name='admissions_reject'),
]